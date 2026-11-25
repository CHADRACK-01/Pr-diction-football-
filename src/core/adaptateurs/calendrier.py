# core/adaptateurs/calendrier.py
"""
Adaptateur de calendrier (Google Calendar).

Utilisé pour : synchronisation des matchs avec Google Calendar (fonctionnalité 86).
Configuration : GOOGLE_CALENDAR_CREDENTIALS ou GOOGLE_CALENDAR_API_KEY.
"""

from __future__ import annotations

import os
from typing import Any

from core.adaptateurs.base import FournisseurCalendrier, ResultatAdaptateur, _resultat


class AdaptateurCalendrier(FournisseurCalendrier):
    """Adaptateur Google Calendar pour créer des événements de matchs."""

    def __init__(self):
        self._credentials = os.environ.get("GOOGLE_CALENDAR_CREDENTIALS", "")
        self._api_key = os.environ.get("GOOGLE_CALENDAR_API_KEY", "")
        self._calendar_id = os.environ.get("GOOGLE_CALENDAR_ID", "primary")

    def creer_evenement(
        self,
        titre: str,
        debut: str,
        description: str = "",
        timezone: str = "Africa/Kinshasa",
    ) -> ResultatAdaptateur:
        """Crée un événement dans Google Calendar.

        Retourne (succes, id_evenement, erreur).
        Si aucun credential n'est configuré, retourne succes=False.
        """
        if not self._credentials and not self._api_key:
            return _resultat(False, None, "Aucun credential Google Calendar configuré")
        try:
            return self._creer_via_api(titre, debut, description, timezone)
        except Exception as e:  # pragma: no cover - dépend du SDK Google
            return _resultat(False, None, f"Erreur Google Calendar : {type(e).__name__}")

    def _creer_via_api(self, titre: str, debut: str, description: str, timezone: str) -> ResultatAdaptateur:
        # Placeholder : implémentation avec googleapiclient.discovery
        return _resultat(False, None, "Google Calendar SDK non encore implémenté")
