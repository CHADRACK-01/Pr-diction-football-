"""Compatibilité historique : importez depuis core.notifications."""

from core.notifications.programmed import (
    formater_conseils_matchs,
    envoyer_notifications_matinales,
)

__all__ = ["formater_conseils_matchs", "envoyer_notifications_matinales"]
