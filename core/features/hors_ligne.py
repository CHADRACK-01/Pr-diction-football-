# core/features/hors_ligne.py
"""
Stubs pour le mode hors ligne / SMS.
Catégorie : hors ligne
"""

from core.utils.logs import log_info, log_warning

# ---------------------------------------------------------------------------
# Feature #13 - Mode sans Internet ou résumé SMS
# ---------------------------------------------------------------------------
def mode_hors_ligne_sms(*args, **kwargs):
    """
    Résumé ultra-court des pronostics.
    Dépendances externes : passerelle SMS.
    """
    log_warning("mode_hors_ligne_sms appelé - stub à compléter", "FEATURES#13")
    return {
        "status": "a_implanter",
        "feature_id": 13,
        "libelle": "Mode sans Internet ou résumé SMS",
        "message": "À implémenter : résumé ultra-court des pronostics via SMS",
        "dependances": ["passerelle SMS"],
    }
