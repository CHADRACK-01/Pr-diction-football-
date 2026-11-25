# core/adaptateurs/api_football.py
"""
Adaptateur API-Football pour les données sportives.

Fournit : matchs en direct, cotes, résultats, matchs du jour.
Configuration requise : API_FOOTBALL_KEY_1, API_FOOTBALL_KEY_2 dans l'environnement.

Si aucune clé n'est configurée, retourne ResultatAdaptateur(succes=False).
"""

from __future__ import annotations

import os
from typing import Any

import requests

from core.adaptateurs.base import (
    FournisseurDonneesSportives,
    ResultatAdaptateur,
    _resultat,
)

BASE_URL = "https://v3.football.api-sports.io"
TIMEOUT_SEC = 10


class AdaptateurApiFootball(FournisseurDonneesSportives):
    """Adaptateur vers l'API Football (api-football.com).

    Gère la rotation entre deux clés API et le contrôle de quota.
    """

    def __init__(self, cles: list[str] | None = None):
        self._cles = cles or [k for k in (os.environ.get("API_FOOTBALL_KEY_1", ""), os.environ.get("API_FOOTBALL_KEY_2", "")) if k]
        self._index_cle = 0

    def _headers(self) -> dict[str, str]:
        cle = self._cles[self._index_cle] if self._cles else ""
        return {"x-rapidapi-key": cle, "x-rapidapi-host": "v3.football.api-sports.io"}

    def _rotater_cle(self) -> None:
        if len(self._cles) > 1:
            self._index_cle = (self._index_cle + 1) % len(self._cles)

    def _get(self, endpoint: str, params: dict[str, Any] | None = None) -> ResultatAdaptateur:
        if not self._cles:
            return _resultat(False, None, "Aucune clé API-Football configurée (API_FOOTBALL_KEY_1 / API_FOOTBALL_KEY_2)")
        try:
            resp = requests.get(f"{BASE_URL}/{endpoint}", headers=self._headers(), params=params or {}, timeout=TIMEOUT_SEC)
            if resp.status_code == 401 or resp.status_code == 403:
                self._rotater_cle()
                return self._get(endpoint, params)  # retry avec la clé suivante
            if resp.status_code != 200:
                return _resultat(False, None, f"API-Football erreur HTTP {resp.status_code}")
            donnees = resp.json()
            if not donnees.get("success", True) and "errors" in donnees:
                return _resultat(False, None, str(donnees["errors"]))
            return _resultat(True, donnees.get("response", []), None)
        except requests.RequestException as e:
            return _resultat(False, None, f"Erreur réseau API-Football : {type(e).__name__}")
        except (ValueError, KeyError) as e:
            return _resultat(False, None, f"Erreur de parsing API-Football : {type(e).__name__}")

    def get_matchs_live(self, competition: str | None = None) -> ResultatAdaptateur:
        params: dict[str, Any] = {"live": "all"}
        if competition:
            params["league"] = competition
        return self._get("fixtures", params)

    def get_cotes(self, match_id: str) -> ResultatAdaptateur:
        return self._get("odds", {"fixture": match_id})

    def get_resultat(self, match_id: str) -> ResultatAdaptateur:
        return self._get("fixtures", {"id": match_id})

    def get_matchs_du_jour(self, date: str) -> ResultatAdaptateur:
        return self._get("fixtures", {"date": date})
