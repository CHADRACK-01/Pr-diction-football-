# core/prediction.py
"""
API publique de prédiction + sauvegarde historique.
- Ajout de la compétition dans l'historique
- Distinction score_predit / score_reel
"""

from datetime import datetime, timezone, timedelta

from core.predictions.nouveau_prediction import predire_match_v2
from core.utils.logs import log_info, log_error, log_warning

TZ_KINSHASA = timezone(timedelta(hours=1))


def predire_match(home_input, away_input, competition="default", cotes_book=None):
    """Wrapper public de predire_match_v2."""
    log_info(
        f"Prédiction demandée : {home_input} vs {away_input} ({competition})",
        "PREDICTION",
        extra={"home": home_input, "away": away_input, "competition": competition},
    )
    return predire_match_v2(
        home_team=home_input,
        away_team=away_input,
        competition=competition,
        cotes_book=cotes_book,
    )


def sauvegarder_historique(home_team, away_team, competition,
                           p_h, p_d, p_a, best_i, best_j):
    """
    Sauvegarde un pronostic dans resultats_pronostics.
    - `date_match` = date Kinshasa
    - `score_predit` = score exact prédit (pas le score réel)
    - `score_reel` = NULL (rempli plus tard par results_checker)
    - `competition` = nom propre (permet la désambiguïsation)
    """
    from users.db import db_execute

    options = [("1X", p_h + p_d), ("X2", p_d + p_a), ("12", p_h + p_a)]
    meilleure = max(options, key=lambda x: x[1])[0]
    score_predit = f"{best_i}-{best_j}"
    date_match = datetime.now(TZ_KINSHASA).strftime("%Y-%m-%d")

    rowcount = db_execute(
        """
        INSERT INTO resultats_pronostics
        (date_match, home_team, away_team, competition, pronostic_reco,
         score_predit, score_reel, est_gagnant, tentatives_verification)
        VALUES (?, ?, ?, ?, ?, ?, NULL, NULL, 0)
        """,
        params=[date_match, home_team, away_team, competition,
                meilleure, score_predit],
        db_context={"table": "resultats_pronostics", "operation": "insert"},
    )

    if rowcount is None or rowcount == 0:
        log_error(
            message="Impossible de sauvegarder l'historique",
            module="PREDICTION",
            extra={
                "home": home_team, "away": away_team,
                "competition": competition, "reco": meilleure,
            },
        )
        return False

    log_info(
        f"Historique sauvegardé : {home_team} vs {away_team} ({meilleure})",
        "PREDICTION",
        extra={"competition": competition, "score_predit": score_predit},
    )
    return True
