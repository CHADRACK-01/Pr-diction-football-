# core/features/filtres.py
"""
Stubs pour les filtres et détections spéciales.
Catégorie : filtres / paris
"""

from core.utils.logs import log_info, log_warning

# ---------------------------------------------------------------------------
# Feature #8 - Filtre anti-piège (derbies)
# ---------------------------------------------------------------------------
def filtre_anti_piege(*args, **kwargs):
    """
    Badge rouge pour les matchs dangereux, notamment les derbies.
    Dépendances externes : base derbies.
    """
    log_warning("filtre_anti_piege appelé - stub à compléter", "FEATURES#8")
    return {
        "status": "a_implanter",
        "feature_id": 8,
        "libelle": "Filtre anti-piège (derbies)",
        "message": "À implémenter : badge rouge sur les matchs dangereux/derbies",
        "dependances": ["base derbies"],
    }


# ---------------------------------------------------------------------------
# Feature #59 - Détecteur de derby et rivalité
# ---------------------------------------------------------------------------
def detecteur_derby(*args, **kwargs):
    """
    Ajoute un badge rouge aux matchs sensibles.
    Dépendances externes : base derbies.
    """
    log_warning("detecteur_derby appelé - stub à compléter", "FEATURES#59")
    return {
        "status": "a_implanter",
        "feature_id": 59,
        "libelle": "Détecteur de derby et rivalité",
        "message": "À implémenter : détection des derbies et rivalités connues",
        "dependances": ["base derbies"],
    }


# ---------------------------------------------------------------------------
# Feature #48 - Filtre de réussite par ligue
# ---------------------------------------------------------------------------
def filtre_reussite_ligue(*args, **kwargs):
    """
    Compare les performances historiques des ligues.
    Dépendances externes : historique par ligue.
    """
    log_warning("filtre_reussite_ligue appelé - stub à compléter", "FEATURES#48")
    return {
        "status": "a_implanter",
        "feature_id": 48,
        "libelle": "Filtre de réussite par ligue",
        "message": "À implémenter : comparaison des performances historiques par ligue",
        "dependances": ["historique par ligue"],
    }
