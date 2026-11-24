# core/features/historique.py
"""
Stubs pour les fonctionnalités d'historique.
Catégorie : historique / données
"""

from core.utils.logs import log_info, log_warning

# ---------------------------------------------------------------------------
# Feature #7 - Historique vérifiable public (30 derniers jours)
# ---------------------------------------------------------------------------
def historique_verifiable(*args, **kwargs):
    """
    Affichage des matchs gagnés ou perdus.
    Dépendances externes : aucune.
    """
    log_warning("historique_verifiable appelé - stub à compléter", "FEATURES#7")
    return {
        "status": "a_implanter",
        "feature_id": 7,
        "libelle": "Historique vérifiable public (30 derniers jours)",
        "message": "À implémenter : affichage des 30 derniers jours gagnés/perdus",
        "dependances": [],
    }


# ---------------------------------------------------------------------------
# Feature #38 - Historique face-à-face visuel
# ---------------------------------------------------------------------------
def historique_face_a_face_visuel(*args, **kwargs):
    """
    Tableau des confrontations précédentes.
    Dépendances externes : historique confrontations.
    """
    log_warning("historique_face_a_face_visuel appelé - stub à compléter", "FEATURES#38")
    return {
        "status": "a_implanter",
        "feature_id": 38,
        "libelle": "Historique face-à-face visuel",
        "message": "À implémenter : tableau des confrontations précédentes",
        "dependances": ["historique confrontations"],
    }
