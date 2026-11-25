# core/adaptateurs/meteo.py
"""
Adaptateur météo (OpenWeatherMap ou équivalent).

Utilisé pour : alerte météo et pelouse (fonctionnalité 35).
Configuration : OPENWEATHER_API_KEY.
"""

from __future__ import annotations

import os
from typing import Any

import requests

from core.adaptateurs.base import FournisseurMeteo, ResultatAdaptateur, _resultat

TIMEOUT_SEC = 10


class AdaptateurMeteo(FournisseurMeteo):
    """Adaptateur OpenWeatherMap pour les conditions météo d'une ville."""

    def __init__(self):
        self._cle = os.environ.get("OPENWEATHER_API_KEY", "")

    def get_meteo(self, ville: str) -> ResultatAdaptateur:
        """Retourne les conditions météo actuelles d'une ville.

        Retourne (succes, donnees_meteo, erreur).
        Si aucune clé n'est configurée, retourne succes=False.
        """
        if not self._cle:
            return _resultat(False, None, "Aucune clé OpenWeather configurée (OPENWEATHER_API_KEY)")
        try:
            resp = requests.get(
                "https://api.openweathermap.org/data/2.5/weather",
                params={"q": ville, "appid": self._cle, "units": "metric", "lang": "fr"},
                timeout=TIMEOUT_SEC,
            )
            if resp.status_code != 200:
                return _resultat(False, None, f"Erreur OpenWeather HTTP {resp.status_code}")
            donnees = resp.json()
            return _resultat(True, {
                "ville": ville,
                "temperature": donnees.get("main", {}).get("temp"),
                "humidite": donnees.get("main", {}).get("humidity"),
                "condition": donnees.get("weather", [{}])[0].get("description"),
                "pluie": donnees.get("rain", {}).get("1h", 0),
                "vent": donnees.get("wind", {}).get("speed"),
            }, None)
        except requests.RequestException as e:
            return _resultat(False, None, f"Erreur réseau OpenWeather : {type(e).__name__}")
        except (ValueError, KeyError) as e:
            return _resultat(False, None, f"Erreur de parsing OpenWeather : {type(e).__name__}")
