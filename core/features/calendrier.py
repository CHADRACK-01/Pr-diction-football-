# core/features/calendrier.py
"""
Stubs pour le calendrier et équipes favorites.
Catégorie : calendrier / utilisateur
"""

from core.utils.logs import log_info, log_warning

# ---------------------------------------------------------------------------
# Feature #10 - Calendrier personnalisé « Mes équipes »
# ---------------------------------------------------------------------------
def calendrier_equipes_favorites(*args, **kwargs):
    """
    Sélection jusqu'à cinq équipes favorites.
    Dépendances externes : aucune.
    """
    log_warning("calendrier_equipes_favorites appelé - stub à compléter", "FEATURES#10")
    return {
        "status": "a_implanter",
        "feature_id": 10,
        "libelle": "Calendrier personnalisé « Mes équipes »",
        "message": "À implémenter : sélection jusqu'à 5 équipes favorites",
        "dependances": [],
    }


# ---------------------------------------------------------------------------
# Feature #85 - Alertes ultra-ciblées pour les équipes favorites
# ---------------------------------------------------------------------------
def alertes_equipes_favorites(*args, **kwargs):
    """
    Information juste avant le match pour les équipes favorites.
    Dépendances externes : aucune.
    """
    log_warning("alertes_equipes_favorites appelé - stub à compléter", "FEATURES#85")
    return {
        "status": "a_implanter",
        "feature_id": 85,
        "libelle": "Alertes équipe favorite ultra-ciblée",
        "message": "À implémenter : alertes ciblées avant match pour équipes favorites",
        "dependances": [],
    }
