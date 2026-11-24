# core/features/explication.py
"""
Stubs pour l'explication du prono.
Catégorie : explication / prédiction
"""

from core.utils.logs import log_info, log_warning

# ---------------------------------------------------------------------------
# Feature #65 - Explication du prono
# ---------------------------------------------------------------------------
def explication_prono(*args, **kwargs):
    """
    Justifie le choix avec les facteurs principaux.
    Dépendances externes : modèle IA.
    """
    log_warning("explication_prono appelé - stub à compléter", "FEATURES#65")
    return {
        "status": "a_implanter",
        "feature_id": 65,
        "libelle": "Explication du prono",
        "message": "À implémenter : justification du choix avec facteurs principaux",
        "dependances": ["modèle IA"],
    }
