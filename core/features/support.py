# core/features/support.py
"""
Stubs pour les tickets support et réponses rapides.
Catégorie : support
"""

from core.utils.logs import log_info, log_warning

# ---------------------------------------------------------------------------
# Feature #126 - Tickets support avec statut
# ---------------------------------------------------------------------------
def tickets_support_statut(*args, **kwargs):
    """
    Nouveau, en cours, résolu et assignation.
    Dépendances externes : aucune.
    """
    log_warning("tickets_support_statut appelé - stub à compléter", "FEATURES#126")
    return {
        "status": "a_implanter",
        "feature_id": 126,
        "libelle": "Tickets support avec statut",
        "message": "À implémenter : tickets support avec statut/assignation",
        "dependances": [],
    }


# ---------------------------------------------------------------------------
# Feature #127 - Réponses rapides administrateur
# ---------------------------------------------------------------------------
def reponses_rapides_admin(*args, **kwargs):
    """
    Modèles pour les paiements et codes.
    Dépendances externes : aucune.
    """
    log_warning("reponses_rapides_admin appelé - stub à compléter", "FEATURES#127")
    return {
        "status": "a_implanter",
        "feature_id": 127,
        "libelle": "Réponses rapides administrateur",
        "message": "À implémenter : modèles de réponses pour paiements/codes",
        "dependances": [],
    }
