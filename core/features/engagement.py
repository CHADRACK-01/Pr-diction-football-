# core/features/engagement.py
"""
Stubs pour l'engagement utilisateur (quiz, XP, roue, etc.).
Catégorie : engagement
"""

from core.utils.logs import log_info, log_warning

# ---------------------------------------------------------------------------
# Feature #12 - Quiz et sondages avant-match
# ---------------------------------------------------------------------------
def quiz_avant_match(*args, **kwargs):
    """
    Attribution de points XP pour les bonnes réponses.
    Dépendances externes : sondages Telegram.
    """
    log_warning("quiz_avant_match appelé - stub à compléter", "FEATURES#12")
    return {
        "status": "a_implanter",
        "feature_id": 12,
        "libelle": "Quiz et sondages avant-match",
        "message": "À implémenter : quiz/sondages avec attribution de XP",
        "dependances": ["sondages Telegram"],
    }


# ---------------------------------------------------------------------------
# Feature #70 - Boutique XP
# ---------------------------------------------------------------------------
def boutique_xp(*args, **kwargs):
    """
    Échange des points contre Premium ou analyses VIP.
    Dépendances externes : aucune.
    """
    log_warning("boutique_xp appelé - stub à compléter", "FEATURES#70")
    return {
        "status": "a_implanter",
        "feature_id": 70,
        "libelle": "Boutique XP",
        "message": "À implémenter : échange de points contre Premium/analyses VIP",
        "dependances": [],
    }


# ---------------------------------------------------------------------------
# Feature #71 - Bonus de connexion quotidienne
# ---------------------------------------------------------------------------
def bonus_connexion_quotidienne(*args, **kwargs):
    """
    Attribue des XP et récompenses cumulées.
    Dépendances externes : aucune.
    """
    log_warning("bonus_connexion_quotidienne appelé - stub à compléter", "FEATURES#71")
    return {
        "status": "a_implanter",
        "feature_id": 71,
        "libelle": "Bonus de connexion quotidienne",
        "message": "À implémenter : XP et récompenses cumulées à la connexion",
        "dependances": [],
    }


# ---------------------------------------------------------------------------
# Feature #72 - Roue quotidienne gratuite
# ---------------------------------------------------------------------------
def roue_quotidienne(*args, **kwargs):
    """
    Prix aléatoires, XP ou remise.
    Dépendances externes : aucune.
    """
    log_warning("roue_quotidienne appelé - stub à compléter", "FEATURES#72")
    return {
        "status": "a_implanter",
        "feature_id": 72,
        "libelle": "Roue quotidienne gratuite",
        "message": "À implémenter : roue avec prix aléatoires, XP ou remise",
        "dependances": [],
    }
