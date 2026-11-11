# users/matchs.py
"""
Gestion des matchs en base.
- Insertion idempotente avec gestion d'erreur par ligne
- Fenêtre "saison en cours" basée sur l'année scolaire football
- Nettoyage des vieilles données (calcul exact)
"""

from datetime import datetime, timedelta

from users.db import db_execute, db_fetchone, db_fetchall, get_connection
from core.utils.logs import log_info, log_error, log_warning

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
    Insère une liste de matchs (idempotent via ON CONFLICT DO NOTHING).
    Retourne le nombre de matchs traités (pas forcément insérés).
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
            INSERT INTO matchs ({", ".join(CHAMPS_MATCH)})
            VALUES ({", ".join(["?"] * len(CHAMPS_MATCH))})
            ON CONFLICT (date, home_team, away_team, competition) DO NOTHING
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
                            db_context={
                                "table": "matchs",
                                "params": {
                                    "date": vals[0],
                                    "home": vals[1],
                                    "away": vals[2],
                                    "competition": vals[-1],
                                },
                            },
                            exception=e,
                        )
            conn.commit()
        except Exception as e:
            log_error(
                message="Erreur d'ouverture/commit connexion pour insertion de matchs",
                module="MATCHS",
                exception=e,
            )
        finally:
            if conn is not None:
                try:
                    conn.close()
                except Exception as e:
                    log_warning(
                        message="Impossible de fermer la connexion (inserer_matchs)",
                        module="MATCHS",
                        exception=e,
                    )

    if erreurs > 5:
        log_warning(
            message=f"{erreurs} erreurs d'insertion au total (5 premières loggées)",
            module="MATCHS",
        )

    log_info(
        f"{total_traites} match(s) traité(s) ({erreurs} erreurs).",
        "MATCHS",
    )
    return total_traites


def compter_matchs():
    """Compte le nombre total de matchs."""
    row = db_fetchone(
        "SELECT COUNT(*) FROM matchs",
        db_context={"table": "matchs", "operation": "count"},
    )
    return row[0] if row else 0


def get_equipes_saison_en_cours(competition):
    """
    Récupère les équipes de la saison en cours.

    Stratégie :
    1. Fenêtre de 180 jours (saison en cours) dans le futur
    2. Fallback : 365 derniers jours si la fenêtre future est vide
    """
    if not competition:
        log_warning(
            message="Compétition vide pour get_equipes_saison_en_cours",
            module="MATCHS",
        )
        return []

    try:
        # Fenêtre future : 180 jours (saison en cours)
        date_debut = datetime.now().strftime("%Y-%m-%d")
        date_fin = (datetime.now() + timedelta(days=180)).strftime("%Y-%m-%d")

        rows = db_fetchall(
            """
            SELECT DISTINCT home_team FROM matchs
            WHERE competition = ? AND date >= ? AND date <= ?
            UNION
            SELECT DISTINCT away_team FROM matchs
            WHERE competition = ? AND date >= ? AND date <= ?
            ORDER BY home_team ASC
            """,
            params=[competition, date_debut, date_fin,
                    competition, date_debut, date_fin],
            db_context={"table": "matchs", "operation": "get_equipes_futur",
                        "params": {"competition": competition}},
        )
        equipes = [row[0] for row in rows if row and row[0]]
        source = "calendrier futur (180j)"

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
                WHERE competition = ? AND date >= ?
                UNION
                SELECT DISTINCT away_team FROM matchs
                WHERE competition = ? AND date >= ?
                ORDER BY home_team ASC
                """,
                params=[competition, date_limite, competition, date_limite],
                db_context={"table": "matchs", "operation": "get_equipes_fallback",
                            "params": {"competition": competition}},
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

        log_info(
            f"{len(equipes)} équipes pour {competition} (source: {source})",
            "MATCHS",
        )
        return equipes
    except Exception as e:
        log_error(
            message="Impossible de récupérer les équipes",
            module="MATCHS",
            extra={"competition": competition},
            exception=e,
        )
        return []


def nettoyer_vieilles_donnees(annees=5):
    """Supprime les matchs de plus de X années (calcul exact avec bissextiles)."""
    if not isinstance(annees, int) or annees <= 0:
        log_warning(
            message="Paramètre 'annees' invalide",
            module="MATCHS",
            extra={"annees": annees},
        )
        return 0

    # Calcul exact : on soustrait les années à la date d'aujourd'hui
    date_limite_dt = datetime.now().replace(
        year=datetime.now().year - annees
    )
    date_limite = date_limite_dt.strftime("%Y-%m-%d")

    row = db_fetchone(
        "SELECT COUNT(*) FROM matchs WHERE date < ?",
        params=[date_limite],
        db_context={"table": "matchs", "operation": "count_old"},
    )
    nb_a_supprimer = row[0] if row else 0

    if nb_a_supprimer == 0:
        log_info(f"Aucun match de plus de {annees} ans.", "MATCHS")
        return 0

    rowcount = db_execute(
        "DELETE FROM matchs WHERE date < ?",
        params=[date_limite],
        db_context={"table": "matchs", "operation": "cleanup"},
    )

    if rowcount is None:
        log_error(
            message="Échec de suppression des vieux matchs",
            module="MATCHS",
            extra={"annees": annees, "date_limite": date_limite},
        )
        return 0

    log_info(
        f"{rowcount} matchs de plus de {annees} ans supprimés.",
        "MATCHS",
        extra={"annees": annees, "date_limite": date_limite},
    )
    return rowcount
