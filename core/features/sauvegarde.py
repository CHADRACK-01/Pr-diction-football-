# core/features/sauvegarde.py
"""
Stubs pour la sauvegarde et restauration.
Catégorie : sauvegarde / administration
"""

from core.utils.logs import log_info, log_warning

# ---------------------------------------------------------------------------
# Feature #130 - Sauvegarde manuelle en un clic
# ---------------------------------------------------------------------------
def sauvegarde_manuelle_un_clic(*args, **kwargs):
    """
    Envoi de la base au compte Telegram administrateur.
    Dépendances externes : compte Telegram admin.
    """
    log_warning("sauvegarde_manuelle_un_clic appelé - stub à compléter", "FEATURES#130")
    return {
        "status": "a_implanter",
        "feature_id": 130,
        "libelle": "Sauvegarde manuelle en un clic",
        "message": "À implémenter : envoi de la base au compte Telegram admin",
        "dependances": ["compte Telegram admin"],
    }


# ---------------------------------------------------------------------------
# Feature #131 - Restauration de sauvegarde
# ---------------------------------------------------------------------------
def restauration_sauvegarde(*args, **kwargs):
    """
    Sélection puis restauration d'une sauvegarde.
    Dépendances externes : aucune.
    """
    log_warning("restauration_sauvegarde appelé - stub à compléter", "FEATURES#131")
    return {
        "status": "a_implanter",
        "feature_id": 131,
        "libelle": "Restauration de sauvegarde",
        "message": "À implémenter : sélection et restauration d'une sauvegarde",
        "dependances": [],
    }
