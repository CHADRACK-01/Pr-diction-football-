# users/matchs.py
"""
Gestion des matchs en base.
- Insertion idempotente avec INSERT OR IGNORE
- Fenêtre "saison en cours" avec fallback passé
- Recherche de compétition ultra-tolérante (ignore les _, espaces, tirets)
"""

from datetime import datetime, timedelta

from users.db import db_execute, db_fetchone, db_fetchall, get_connection
from core.utils.logs import log_info, log_error, log_warning
from config import MAPPING_COMPETITIONS

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


def get_equipes_saison_en_cours(competition):
    """
    Récupère les équipes de la saison en cours.
    Utilise une recherche SQL ultra-tolérante pour ignorer les _, espaces et tirets.
    """
    if not competition:
        log_warning(message="Compétition vide", module="MATCHS")
        return []

    # On crée une clé de recherche propre : minuscules, sans _, sans espace, sans -
    comp_clean = competition.lower().replace("_", "").replace(" ", "").replace("-", "")
    
    # On utilise MAPPING_COMPETITIONS juste pour savoir si on doit chercher un code
    # Mais comme la recherche SQL est tolérante, ça marchera dans tous les cas.

    try:
        # 1. Fenêtre future : 180 jours
        date_debut = datetime.now().strftime("%Y-%m-%d")
        date_fin = (datetime.now() + timedelta(days=180)).strftime("%Y-%m-%d")

        rows = db_fetchall(
            """
            SELECT DISTINCT home_team FROM matchs
            WHERE (LOWER(REPLACE(REPLACE(REPLACE(competition, '_', ''), ' ', ''), '-', '')) = ?) 
              AND date >= ? AND date <= ?
            UNION
            SELECT DISTINCT away_team FROM matchs
            WHERE (LOWER(REPLACE(REPLACE(REPLACE(competition, '_', ''), ' ', ''), '-', '')) = ?) 
              AND date >= ? AND date <= ?
            ORDER BY home_team ASC
            """,
            params=[comp_clean, date_debut, date_fin,
                    comp_clean, date_debut, date_fin],
            db_context={"table": "matchs", "operation": "get_equipes_futur"},
        )
        equipes = [row[0] for row in rows if row and row[0]]
        source = "futur (180j)"

        # 2. Fallback : 365 derniers jours
        if not equipes:
            log_warning(
                message=f"Aucune équipe dans le futur pour {competition}, fallback passé",
                module="MATCHS",
                extra={"competition": competition},
            )
            date_limite = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
            rows = db_fetchall(
                """
                SELECT DISTINCT home_team FROM matchs
                WHERE (LOWER(REPLACE(REPLACE(REPLACE(competition, '_', ''), ' ', ''), '-', '')) = ?) 
                  AND date >= ?
                UNION
                SELECT DISTINCT away_team FROM matchs
                WHERE (LOWER(REPLACE(REPLACE(REPLACE(competition, '_', ''), ' ', ''), '-', '')) = ?) 
                  AND date >= ?
                ORDER BY home_team ASC
                """,
                params=[comp_clean, date_limite, comp_clean, date_limite],
                db_context={"table": "matchs", "operation": "get_equipes_fallback"},
            )
            equipes = [row[0] for row in rows if row and row[0]]
            source = "fallback passé (365j)"

        if not equipes:
            log_warning(
                message=f"Aucune équipe trouvée pour {competition} (base vide ?)",
                module="MATCHS",
                extra={"competition": competition},
            )
            return []

        log_info(f"{len(equipes)} équipes pour {competition} (source: {source})", "MATCHS")
        return equipes
        
    except Exception as e:
        log_error(message="Impossible de récupérer les équipes", module="MATCHS", extra={"competition": competition}, exception=e)
        return []


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
