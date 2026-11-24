# core/features/virtuel.py
"""
Stubs pour les paris virtuels et ligue privée.
Catégorie : virtuel / engagement
"""

from core.utils.logs import log_info, log_warning

# ---------------------------------------------------------------------------
# Feature #67 - Paris virtuels avec argent fictif
# ---------------------------------------------------------------------------
def paris_virtuels_argent_fictif(*args, **kwargs):
    """
    Permet de tester sans argent réel.
    Dépendances externes : aucune.
    """
    log_warning("paris_virtuels_argent_fictif appelé - stub à compléter", "FEATURES#67")
    return {
        "status": "a_implanter",
        "feature_id": 67,
        "libelle": "Paris virtuels avec argent fictif",
        "message": "À implémenter : paris sans argent réel pour tester",
        "dependances": [],
    }


# ---------------------------------------------------------------------------
# Feature #68 - Ligue privée entre amis
# ---------------------------------------------------------------------------
def ligue_privee_amis(*args, **kwargs):
    """
    Crée des groupes de compétition personnalisés.
    Dépendances externes : aucune.
    """
    log_warning("ligue_privee_amis appelé - stub à compléter", "FEATURES#68")
    return {
        "status": "a_implanter",
        "feature_id": 68,
        "libelle": "Ligue privée entre amis",
        "message": "À implémenter : groupes de compétition personnalisés",
        "dependances": [],
    }
