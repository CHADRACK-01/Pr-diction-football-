# core/features/parrainage.py
"""
Stubs pour le classement des parrains.
Catégorie : parrainage / affiliation
"""

from core.utils.logs import log_info, log_warning

# ---------------------------------------------------------------------------
# Feature #73 - Classement des parrains
# ---------------------------------------------------------------------------
def classement_parrains(*args, **kwargs):
    """
    Présente les meilleurs parrains du mois.
    Dépendances externes : aucune.
    """
    log_warning("classement_parrains appelé - stub à compléter", "FEATURES#73")
    return {
        "status": "a_implanter",
        "feature_id": 73,
        "libelle": "Classement des parrains",
        "message": "À implémenter : présentation des meilleurs parrains du mois",
        "dependances": [],
    }
