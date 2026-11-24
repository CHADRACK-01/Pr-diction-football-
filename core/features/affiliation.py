# core/features/affiliation.py
"""
Stubs pour le suivi des liens d'affiliation.
Catégorie : affiliation / distribution
"""

from core.utils.logs import log_info, log_warning

# ---------------------------------------------------------------------------
# Feature #74 - Suivi des liens d'affiliation
# ---------------------------------------------------------------------------
def suivi_liens_affiliation(*args, **kwargs):
    """
    Historique et revenus liés à chaque lien.
    Dépendances externes : liens d'affiliation.
    """
    log_warning("suivi_liens_affiliation appelé - stub à compléter", "FEATURES#74")
    return {
        "status": "a_implanter",
        "feature_id": 74,
        "libelle": "Suivi des liens d'affiliation",
        "message": "À implémenter : historique et revenus par lien d'affiliation",
        "dependances": ["liens d'affiliation"],
    }
