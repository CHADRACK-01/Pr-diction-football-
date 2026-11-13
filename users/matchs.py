# users/matchs.py
import json
import requests
from datetime import datetime, timedelta

from users.db import db_execute, db_fetchone, db_fetchall, get_connection
from core.utils.logs import log_info, log_error, log_warning
from config import MAPPING_COMPETITIONS, FOOTBALL_DATA_KEY

TAILLE_LOT = 500
CHAMPS_MATCH = [
    "date", "home_team", "away_team",
    "fthg", "ftag", "ftr",
    "hthg", "htag", "htr",
    "hs", "as_shots", "hst", "ast",
    "hc", "ac", "hf", "af",
    "hy", "ay", "hr", "ar",
    "b365h", "b365d", "b365a",
    "competition", "saison"
]

CODES_API = {
    "premier_league": "PL", "championship": "ELC", "laliga": "PD", 
    "segunda_division": "SD", "serie_a": "SA", "serie_b": "SB", 
    "ligue_1": "FL1", "ligue_2": "FL2", "bundesliga_1": "BL1", 
    "bundesliga_2": "BL2", "champions_league": "CL",
}

# =========================================================
# INSERTION EN BASE (Utilisé par l'orchestrateur et l'API)
# =========================================================
def inserer_matchs(liste_matchs):
    """
    Insère une liste de matchs (idempotent via INSERT OR IGNORE).
    """
    if not liste_matchs:
        return 0

    total_traites = 0
    erreurs = 0

    for i in range(0, len(liste_matchs), TAILLE_LOT):
        lot = liste_matchs[i:i + TAILLE_LOT]
        valeurs = []
        for m in lot:
            valeurs.append(tuple(m.get(c) for c in CHAMPS_MATCH))

        query = f"""
            INSERT OR IGNORE INTO matchs ({", ".join(CHAMPS_MATCH)})
            VALUES ({", ".join(["?"] * len(CHAMPS_MATCH))})
        """

        conn = None
        try:
            conn = get_connection()
            for vals in valeurs:
                try:
                    conn.execute(query, vals)
                    total_traites += 1
                except Exception as e:
                    erreurs += 1
                    if erreurs <= 5:
                        log_error(
                            message="Erreur d'insertion d'un match",
                            module="MATCHS",
                            db_context={"table": "matchs", "params": {"date": vals[0], "home": vals[1]}},
                            exception=e,
                        )
            conn.commit()
        except Exception as e:
            log_error(message="Erreur commit insertion", module="MATCHS", exception=e)
        finally:
            if conn is not None:
                try: conn.close()
                except: pass

    log_info(f"{total_traites} match(s) traité(s) ({erreurs} erreurs).", "MATCHS")
    return total_traites


def compter_matchs():
    """Compte le nombre total de matchs."""
    row = db_fetchone("SELECT COUNT(*) FROM matchs", db_context={"table": "matchs"})
    return row[0] if row else 0


# =========================================================
# LOGIQUE DE SÉLECTION (Waterfall Niveau 1 -> 2 -> 3)
# =========================================================
def get_equipes_saison_en_cours(competition):
    if not competition:
        return []

    noms_vers_codes = {v: k for k, v in MAPPING_COMPETITIONS.items()}
    comp_interne = noms_vers_codes.get(competition, competition)
    comp_clean = comp_interne.lower().replace("_", "").replace(" ", "").replace("-", "")
    
    now = datetime.now()
    annee_debut = now.year if now.month >= 7 else now.year - 1
    saison_str = f"{annee_debut}-{annee_debut+1}"

    # --- NIVEAU 1 : Base de données locale (Saison en cours) ---
    try:
        rows = db_fetchall(
            """
            SELECT DISTINCT home_team FROM matchs
            WHERE (LOWER(REPLACE(REPLACE(REPLACE(TRIM(competition), '_', ''), ' ', ''), '-', '')) = ?) 
              AND saison = ?
            UNION
            SELECT DISTINCT away_team FROM matchs
            WHERE (LOWER(REPLACE(REPLACE(REPLACE(TRIM(competition), '_', ''), ' ', ''), '-', '')) = ?) 
              AND saison = ?
            ORDER BY home_team ASC
            """,
            params=[comp_clean, saison_str, comp_clean, saison_str]
        )
        equipes_db = [row[0] for row in rows if row and row[0]]
        
        if equipes_db:
            log_info(f"Niveau 1 (DB) : {len(equipes_db)} équipes pour {competition} ({saison_str})", "MATCHS")
            return sorted(equipes_db)
    except Exception as e:
        log_warning(f"Erreur Niveau 1 (DB) pour {competition}", "MATCHS", exception=e)

    # --- NIVEAU 2 : API avec Cache ---
    log_warning(f"Niveau 1 (DB) vide pour {competition}. Passage au Niveau 2 (API).", "MATCHS")
    
    try:
        cache = db_fetchone("SELECT equipes, date_maj FROM cache_equipes WHERE competition = ?", params=[comp_interne])
        if cache and cache[0] and cache[1]:
            date_maj = datetime.strptime(cache[1], "%Y-%m-%d %H:%M:%S")
            if (datetime.now() - date_maj).days < 7:
                log_info(f"Niveau 2 (Cache) utilisé pour {competition}", "MATCHS")
                return json.loads(cache[0])
    except Exception:
        pass

    code_api = CODES_API.get(comp_interne)
    if code_api and FOOTBALL_DATA_KEY:
        annee_api = now.year if now.month >= 7 else now.year - 1
        url = f"https://api.football-data.org/v4/competitions/{code_api}/teams?season={annee_api}"
        try:
            res = requests.get(url, headers={"X-Auth-Token": FOOTBALL_DATA_KEY}, timeout=10)
            if res.status_code == 200:
                equipes_api = [team["name"] for team in res.json().get("teams", [])]
                if equipes_api:
                    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    db_execute(
                        "INSERT OR REPLACE INTO cache_equipes (competition, equipes, date_maj) VALUES (?, ?, ?)",
                        params=[comp_interne, json.dumps(equipes_api), now_str]
                    )
                    log_info(f"Niveau 2 (API) : {len(equipes_api)} équipes pour {competition}", "MATCHS")
                    return sorted(equipes_api)
        except Exception as e:
            log_warning(f"Échec API pour {competition}", "MATCHS", exception=e)

    # --- NIVEAU 3 : Fallback absolu (365 derniers jours) ---
    log_warning(f"Niveau 2 (API) échoué. Passage au Niveau 3 (Fallback).", "MATCHS")
    
    try:
        date_limite = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
        rows = db_fetchall(
            """
            SELECT DISTINCT home_team FROM matchs
            WHERE (LOWER(REPLACE(REPLACE(REPLACE(TRIM(competition), '_', ''), ' ', ''), '-', '')) = ?) 
              AND date >= ?
            UNION
            SELECT DISTINCT away_team FROM matchs
            WHERE (LOWER(REPLACE(REPLACE(REPLACE(TRIM(competition), '_', ''), ' ', ''), '-', '')) = ?) 
              AND date >= ?
            ORDER BY home_team ASC
            """,
            params=[comp_clean, date_limite, comp_clean, date_limite]
        )
        equipes_fallback = [row[0] for row in rows if row and row[0]]
        return sorted(list(set(equipes_fallback)))
    except Exception as e:
        log_error("Erreur Niveau 3 (Fallback)", "MATCHS", exception=e)
        return []


# =========================================================
# NETTOYAGE
# =========================================================
def nettoyer_vieilles_donnees(annees=5):
    """Supprime les matchs de plus de X années."""
    if not isinstance(annees, int) or annees <= 0:
        return 0

    date_limite = datetime.now().replace(year=datetime.now().year - annees).strftime("%Y-%m-%d")
    
    row = db_fetchone("SELECT COUNT(*) FROM matchs WHERE date < ?", params=[date_limite])
    nb_a_supprimer = row[0] if row else 0

    if nb_a_supprimer == 0:
        return 0

    rowcount = db_execute("DELETE FROM matchs WHERE date < ?", params=[date_limite])
    log_info(f"{rowcount} matchs de plus de {annees} ans supprimés.", "MATCHS")
    return rowcount
