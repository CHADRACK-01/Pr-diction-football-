# core/features/debrief.py
"""
Stubs pour le débrief et checklist.
Catégorie : débrief / sécurité
"""

from core.utils.logs import log_info, log_warning

# ---------------------------------------------------------------------------
# Feature #53 - Débrief automatique après-match
# ---------------------------------------------------------------------------
def debrief_apres_match(*args, **kwargs):
    """
    Explique les facteurs ayant fait gagner ou perdre.
    Dépendances externes : résultats matchs.
    """
    log_warning("debrief_apres_match appelé - stub à compléter", "FEATURES#53")
    return {
        "status": "a_implanter",
        "feature_id": 53,
        "libelle": "Débrief automatique après-match",
        "message": "À implémenter : explication des facteurs de gain/perte",
        "dependances": ["résultats matchs"],
    }


# ---------------------------------------------------------------------------
# Feature #54 - Checklist avant pari
# ---------------------------------------------------------------------------
def checklist_avant_pari(*args, **kwargs):
    """
    Vérification des compositions, météo et mise.
    Dépendances externes : compositions, météo, mise.
    """
    log_warning("checklist_avant_pari appelé - stub à compléter", "FEATURES#54")
    return {
        "status": "a_implanter",
        "feature_id": 54,
        "libelle": "Checklist avant pari",
        "message": "À implémenter : vérification compositions, météo, mise",
        "dependances": ["compositions", "météo", "mise"],
    }
