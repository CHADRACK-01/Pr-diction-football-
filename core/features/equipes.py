# core/features/equipes.py
"""
Stubs pour les transferts, entraîneur et tactique.
Catégorie : équipes / données
"""

from core.utils.logs import log_info, log_warning

# ---------------------------------------------------------------------------
# Feature #27 - Impact des transferts et changements d'entraîneur
# ---------------------------------------------------------------------------
def impact_transferts_entraineur(*args, **kwargs):
    """
    Recalcul de la forme.
    Dépendances externes : API transferts.
    """
    log_warning("impact_transferts_entraineur appelé - stub à compléter", "FEATURES#27")
    return {
        "status": "a_implanter",
        "feature_id": 27,
        "libelle": "Impact des transferts et changements d'entraîneur",
        "message": "À implémenter : recalcul de la forme après transferts/changement d'entraîneur",
        "dependances": ["API transferts"],
    }


# ---------------------------------------------------------------------------
# Feature #61 - Tactique entraîneur
# ---------------------------------------------------------------------------
def tactique_entraineur(*args, **kwargs):
    """
    Analyse l'impact d'un style défensif ou offensif.
    Dépendances externes : styles tactiques.
    """
    log_warning("tactique_entraineur appelé - stub à compléter", "FEATURES#61")
    return {
        "status": "a_implanter",
        "feature_id": 61,
        "libelle": "Tactique entraîneur",
        "message": "À implémenter : analyse de l'impact du style tactique",
        "dependances": ["styles tactiques"],
    }
