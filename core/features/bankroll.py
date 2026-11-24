# core/features/bankroll.py
"""
Gestion de bankroll (implémentation réelle).
"""

from core.utils.logs import log_info, log_warning
from core.features.impl_reelles import (
    gestion_kelly_automatique as _reel_kelly,
    plan_mise_fixe_progressif as _reel_plan_mise,
)


# ---------------------------------------------------------------------------
# Feature #41 - Gestion Kelly automatique
# ---------------------------------------------------------------------------
def gestion_kelly_automatique(*args, **kwargs):
    return _reel_kelly(*args, **kwargs)


# ---------------------------------------------------------------------------
# Feature #42 - Plan de mise fixe ou progressif
# ---------------------------------------------------------------------------
def plan_mise_fixe_progressif(*args, **kwargs):
    return _reel_plan_mise(*args, **kwargs)

