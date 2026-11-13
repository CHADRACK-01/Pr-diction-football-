# users/matchs.py
"""
Gestion des matchs en base.
- Insertion idempotente avec INSERT OR IGNORE
- Récupération dynamique des équipes via l'API Football-Data (saison en cours)
- Fallback sur la base de données locale si l'API échoue
"""

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
    "competition",
]

# Correspondance entre nos codes internes et les codes de l'API Football-Data.org
CODES_API_FOOTBALL_DATA = {
    "premier_league": "PL",
    "championship": "ELC",
    "laliga": "PD",
    "segunda_division": "SD",
    "serie_a": "SA",
    "serie_b": "SB",
    "ligue_1": "FL1",
    "ligue_2": "FL2",
    "bundesliga_1": "BL1",
    "bundesliga_2": "BL2",
    "champions_league": "CL",
}


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


def _get_equipes_via_api(competition_interne):
    """Tente de récupérer les équipes via l'API Football-Data.org."""
    if not FOOTBALL_DATA_KEY:
        return None

    code_api = CODES_API_FOOTBALL_DATA.get(competition_interne)
    if not code_api:
        return None

    # Calcul de l'année de la saison (ex: en 2026, la saison est 2026-2027, donc l'année est 2026)
    annee_saison = datetime.now().year
    if datetime.now().month < 7:  # Avant juillet, on est encore sur la saison précédente
        annee_saison -= 1

    url = f"https://api.football-data.org/v4/competitions/{code_api}/teams?season={annee_saison}"
    headers = {"X-Auth-Token": FOOTBALL_DATA_KEY}

    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 200:
            data = res.json()
            equipes = [team["name"] for team in data.get("teams", [])]
            if equipes:
                log_info(f"{len(equipes)} équipes récupérées via API pour {competition_interne}", "MATCHS")
                return equipes
    except Exception as e:
        log_warning(message=f"Échec API Football-Data pour {competition_interne}", module="MATCHS", exception=e)
    
    return None


def _get_equipes_via_db(competition_interne):
    """Fallback : récupère les équipes via la base de données locale."""
    # On crée une clé de recherche propre (minuscules, sans _, sans espace, sans -)
    comp_clean = competition_interne.lower().replace("_", "").replace(" ", "").replace("-", "")

    try:
        # 1. Fenêtre future : 180 jours
        date_debut = datetime.now().strftime("%Y-%m-%d")
        date_fin = (datetime.now() + timedelta(days=180)).strftime("%Y-%m-%d")

        rows = db_fetchall(
            """
            SELECT DISTINCT home_team FROM matchs
            WHERE (LOWER(REPLACE(REPLACE(REPLACE(TRIM(competition), '_', ''), ' ', ''), '-', '')) = ?) 
              AND date >= ? AND date <= ?
            UNION
            SELECT DISTINCT away_team FROM matchs
            WHERE (LOWER(REPLACE(REPLACE(REPLACE(TRIM(competition), '_', ''), ' ', ''), '-', '')) = ?) 
              AND date >= ? AND date <= ?
            ORDER BY home_team ASC
            """,
            params=[comp_clean, date_debut, date_fin, comp_clean, date_debut, date_fin],
        )
        equipes = [row[0] for row in rows if row and row[0]]
        source = "futur (180j)"

        # 2. Fallback : 365 derniers jours
        if not equipes:
            log_warning(f"Aucune équipe dans le futur pour {competition_interne}, fallback passé", "MATCHS")
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
                params=[comp_clean, date_limite, comp_clean, date_limite],
            )
            equipes = [row[0] for row in rows if row and row[0]]
            source = "fallback passé (365j)"

        return equipes
    except Exception as e:
        log_error(message="Impossible de récupérer les équipes via DB", module="MATCHS", exception=e)
        return []


def get_equipes_saison_en_cours(competition):
    """
    Récupère les équipes de la saison en cours.
    1. Tente d'abord via l'API (officiel).
    2. Si échec, utilise le fallback DB.
    """
    if not competition:
        return []

    # On détermine le code interne (ex: "Premier League" -> "premier_league")
    noms_vers_codes = {v: k for k, v in MAPPING_COMPETITIONS.items()}
    competition_interne = noms_vers_codes.get(competition, competition)
    
    # 1. Tentative via API
    equipes_api = _get_equipes_via_api(competition_interne)
    if equipes_api:
        return sorted(equipes_api)

    # 2. Fallback DB
    log_info(f"Utilisation du fallback DB pour {competition_interne}", "MATCHS")
    equipes_db = _get_equipes_via_db(competition_interne)
    
    if not equipes_db:
        log_warning(f"Aucune équipe trouvée pour {competition} (ni API ni DB)", "MATCHS")
        
    return sorted(equipes_db)


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
