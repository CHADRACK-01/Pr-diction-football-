# core/features/interface.py
"""
Stubs pour l'interface utilisateur (mini-app, mode nuit, expert).
Catégorie : interface / expérience
"""

from core.utils.logs import log_info, log_warning

# ---------------------------------------------------------------------------
# Feature #30 - Mini-app Telegram visuelle
# ---------------------------------------------------------------------------
def mini_app_telegram(*args, **kwargs):
    """
    Tableau de bord sous forme de cartes.
    Dépendances externes : Telegram Web Apps.
    """
    log_warning("mini_app_telegram appelé - stub à compléter", "FEATURES#30")
    return {
        "status": "a_implanter",
        "feature_id": 30,
        "libelle": "Mini-app Telegram visuelle",
        "message": "À implémenter : tableau de bord sous forme de cartes",
        "dependances": ["Telegram Web Apps"],
    }


# ---------------------------------------------------------------------------
# Feature #88 - Mode nuit économie de données
# ---------------------------------------------------------------------------
def mode_nuit_economie_donnees(*args, **kwargs):
    """
    Messages texte ultra-légers.
    Dépendances externes : aucune.
    """
    log_warning("mode_nuit_economie_donnees appelé - stub à compléter", "FEATURES#88")
    return {
        "status": "a_implanter",
        "feature_id": 88,
        "libelle": "Mode nuit économie de données",
        "message": "À implémenter : messages texte ultra-légers",
        "dependances": [],
    }


# ---------------------------------------------------------------------------
# Feature #90 - Mode expert débloquable
# ---------------------------------------------------------------------------
def mode_expert_debloquable(*args, **kwargs):
    """
    Accès à xG, Elo et Monte Carlo après 30 jours.
    Dépendances externes : xG, Elo, Monte Carlo.
    """
    log_warning("mode_expert_debloquable appelé - stub à compléter", "FEATURES#90")
    return {
        "status": "a_implanter",
        "feature_id": 90,
        "libelle": "Mode expert débloquable",
        "message": "À implémenter : accès xG/Elo/Monte Carlo après 30 jours",
        "dependances": ["xG", "Elo", "Monte Carlo"],
    }
