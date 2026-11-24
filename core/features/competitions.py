# core/features/competitions.py
"""
Stubs pour les championnats africains.
Catégorie : compétitions / données
"""

from core.utils.logs import log_info, log_warning

# ---------------------------------------------------------------------------
# Feature #18 - Pronostics championnats africains
# ---------------------------------------------------------------------------
def championnats_africains(*args, **kwargs):
    """
    Linafoot, CAN, CAF et Afrique du Sud.
    Dépendances externes : API football africain.
    """
    log_warning("championnats_africains appelé - stub à compléter", "FEATURES#18")
    return {
        "status": "a_implanter",
        "feature_id": 18,
        "libelle": "Pronostics championnats africains",
        "message": "À implémenter : pronostics Linafoot, CAN, CAF, Afrique du Sud",
        "dependances": ["API football africain"],
    }
