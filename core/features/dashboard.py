# core/features/dashboard.py
"""
Dashboard ROI personnel (implémentation réelle).
"""

from core.utils.logs import log_info, log_warning
from core.features.impl_reelles import dashboard_roi_personnel as _reel_roi


# ---------------------------------------------------------------------------
# Feature #49 - Dashboard ROI personnel
# ---------------------------------------------------------------------------
def dashboard_roi_personnel(*args, **kwargs):
    return _reel_roi(*args, **kwargs)

