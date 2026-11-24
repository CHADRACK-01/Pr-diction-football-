# core/features/jeu_responsable.py
"""
Jeu responsable (implémentation réelle).
"""

from core.utils.logs import log_info, log_warning
from core.features.impl_reelles import (
    avertissement_jeu_responsable as _reel_avertissement,
    plan_anti_perte as _reel_anti_perte,
)


# ---------------------------------------------------------------------------
# Feature #16 - Avertissement jeu responsable
# ---------------------------------------------------------------------------
def avertissement_jeu_responsable(*args, **kwargs):
    return _reel_avertissement(*args, **kwargs)


# ---------------------------------------------------------------------------
# Feature #47 - Plan anti-perte
# ---------------------------------------------------------------------------
def plan_anti_perte(*args, **kwargs):
    return _reel_anti_perte(*args, **kwargs)


# ---------------------------------------------------------------------------
# Feature #58 - Fatigue du calendrier (stub - dépendance calendrier externe)
# ---------------------------------------------------------------------------
def fatigue_calendrier(*args, **kwargs):
    log_warning("fatigue_calendrier appelé - dépendance externe calendrier", "FEATURES#58")
    return {
        "status": "a_implanter",
        "feature_id": 58,
        "libelle": "Fatigue du calendrier",
        "message": "À implémenter : détection des séquences serrées de matchs",
        "dependances": ["calendrier matchs"],
    }

