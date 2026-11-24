# core/features/stats.py
"""
Stubs pour les statistiques IA.
Catégorie : stats / prédiction
"""

from core.utils.logs import log_info, log_warning

# ---------------------------------------------------------------------------
# Feature #20 - Statistiques de l'IA en temps réel
# ---------------------------------------------------------------------------
def stats_ia_temps_reel(*args, **kwargs):
    """
    Performances hebdomadaires par marché.
    Dépendances externes : modèle IA.
    """
    log_warning("stats_ia_temps_reel appelé - stub à compléter", "FEATURES#20")
    return {
        "status": "a_implanter",
        "feature_id": 20,
        "libelle": "Statistiques de l'IA en temps réel",
        "message": "À implémenter : performances hebdomadaires par marché",
        "dependances": ["modèle IA"],
    }


# ---------------------------------------------------------------------------
# Feature #22 - Détecteur de série et momentum
# ---------------------------------------------------------------------------
def detecteur_serie_momentum(*args, **kwargs):
    """
    Repérage des équipes en forme.
    Dépendances externes : historique matchs.
    """
    log_warning("detecteur_serie_momentum appelé - stub à compléter", "FEATURES#22")
    return {
        "status": "a_implanter",
        "feature_id": 22,
        "libelle": "Détecteur de série et momentum",
        "message": "À implémenter : détection des équipes en forme",
        "dependances": ["historique matchs"],
    }
