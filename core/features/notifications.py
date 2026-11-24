# core/features/notifications.py
"""
Notifications (implémentation réelle pour les features sans dépendance).
"""

from core.utils.logs import log_info, log_warning
from core.features.impl_reelles import (
    notifications_heure_kinshasa as _reel_kinshasa,
    notifications_silencieuses as _reel_silencieux,
)


# ---------------------------------------------------------------------------
# Feature #50 - Notifications à l'heure de Kinshasa
# ---------------------------------------------------------------------------
def notifications_heure_kinshasa(*args, **kwargs):
    return _reel_kinshasa(*args, **kwargs)


# ---------------------------------------------------------------------------
# Feature #81 - Notifications silencieuses
# ---------------------------------------------------------------------------
def notifications_silencieuses(*args, **kwargs):
    return _reel_silencieux(*args, **kwargs)

