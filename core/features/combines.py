# core/features/combines.py
"""
Combinés et assurances (implémentation réelle).
"""

from core.utils.logs import log_info, log_warning
from core.features.impl_reelles import assurance_combine as _reel_assurance


# ---------------------------------------------------------------------------
# Feature #43 - Constructeur de combiné par risque (stub - dépendance modèle IA)
# ---------------------------------------------------------------------------
def constructeur_combine_risque(*args, **kwargs):
    log_warning("constructeur_combine_risque appelé - dépendance modèle IA", "FEATURES#43")
    return {
        "status": "a_implanter",
        "feature_id": 43,
        "libelle": "Constructeur de combiné par risque",
        "message": "À implémenter : construction de combiné selon cote demandée",
        "dependances": ["modèle IA"],
    }


# ---------------------------------------------------------------------------
# Feature #44 - Double sûr du jour (stub - dépendance modèle IA)
# ---------------------------------------------------------------------------
def double_sur_du_jour(*args, **kwargs):
    log_warning("double_sur_du_jour appelé - dépendance modèle IA", "FEATURES#44")
    return {
        "status": "a_implanter",
        "feature_id": 44,
        "libelle": "Double sûr du jour",
        "message": "À implémenter : combinaison de deux choix à forte confiance",
        "dependances": ["modèle IA"],
    }


# ---------------------------------------------------------------------------
# Feature #45 - Assurance combiné (réelle)
# ---------------------------------------------------------------------------
def assurance_combine(*args, **kwargs):
    return _reel_assurance(*args, **kwargs)

