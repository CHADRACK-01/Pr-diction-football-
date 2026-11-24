# core/features/comparateurs.py
"""
Stubs pour les comparateurs de bookmakers et cotes.
Catégorie : comparateurs / paris
"""

from core.utils.logs import log_info, log_warning

# ---------------------------------------------------------------------------
# Feature #14 - Comparateur de bookmakers RDC
# ---------------------------------------------------------------------------
def comparateur_bookmakers_rdc(*args, **kwargs):
    """
    Compare les cotes entre plusieurs opérateurs.
    Dépendances externes : API bookmakers Airtel Money/M-Pesa/Orange.
    """
    log_warning("comparateur_bookmakers_rdc appelé - stub à compléter", "FEATURES#14")
    return {
        "status": "a_implanter",
        "feature_id": 14,
        "libelle": "Comparateur de bookmakers RDC",
        "message": "À implémenter : comparaison des cotes entre opérateurs RDC",
        "dependances": ["API bookmakers Airtel Money/M-Pesa/Orange"],
    }


# ---------------------------------------------------------------------------
# Feature #28 - Comparateur domicile et extérieur
# ---------------------------------------------------------------------------
def comparateur_domicile_exterieur(*args, **kwargs):
    """
    Compare les probabilités selon le lieu du match.
    Dépendances externes : modèle IA.
    """
    log_warning("comparateur_domicile_exterieur appelé - stub à compléter", "FEATURES#28")
    return {
        "status": "a_implanter",
        "feature_id": 28,
        "libelle": "Comparateur domicile et extérieur",
        "message": "À implémenter : comparaison des probabilités domicile/extérieur",
        "dependances": ["modèle IA"],
    }
