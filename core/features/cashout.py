# core/features/cashout.py
"""
Stubs pour les fonctionnalités de cash-out.
Catégorie : cashout / paris
"""

from core.utils.logs import log_info, log_warning

# ---------------------------------------------------------------------------
# Feature #5 - Simulateur de cash-out
# ---------------------------------------------------------------------------
def simulateur_cashout(*args, **kwargs):
    """
    Estime le gain selon la mise et la cote actuelle.
    Dépendances externes : API cotes live.
    """
    log_warning("simulateur_cashout appelé - stub à compléter", "FEATURES#5")
    return {
        "status": "a_implanter",
        "feature_id": 5,
        "libelle": "Simulateur de cash-out",
        "message": "À implémenter : estimation du gain selon mise et cote actuelle",
        "dependances": ["API cotes live"],
    }


# ---------------------------------------------------------------------------
# Feature #46 - Cash-out partiel simulé
# ---------------------------------------------------------------------------
def cashout_partiel(*args, **kwargs):
    """
    Propose d'encaisser une partie du pari.
    Dépendances externes : API cotes live.
    """
    log_warning("cashout_partiel appelé - stub à compléter", "FEATURES#46")
    return {
        "status": "a_implanter",
        "feature_id": 46,
        "libelle": "Cash-out partiel simulé",
        "message": "À implémenter : proposition d'encaissement partiel du pari",
        "dependances": ["API cotes live"],
    }
