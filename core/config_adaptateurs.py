# core/config_adaptateurs.py
"""
Configuration centralisée des adaptateurs tiers.

L'utilisateur final n'a qu'à modifier ce fichier (ou les variables
d'environnement correspondantes) pour activer ses clés API.

Aucune clé n'est codée en dur : si une variable est absente, l'adaptateur
correspondant retourne ``succes=False`` avec un message clair.

Variables d'environnement lues :
  - API_FOOTBALL_KEY_1, API_FOOTBALL_KEY_2  (données sportives)
  - AIRTEL_API_KEY, AIRTEL_API_URL          (paiement Airtel)
  - MPESA_API_KEY, MPESA_API_URL            (paiement M-Pesa)
  - ORANGE_API_KEY, ORANGE_API_URL          (paiement Orange)
  - OPENWEATHER_API_KEY                     (météo)
  - TTS_API_KEY, TTS_FOURNISSEUR            (audio)
  - GOOGLE_CALENDAR_CREDENTIALS, GOOGLE_CALENDAR_API_KEY, GOOGLE_CALENDAR_ID  (calendrier)
  - TELEGRAM_TOKEN, CANAL_ID                (réseaux sociaux / canal Telegram)
  - FACEBOOK_PAGE_ID, FACEBOOK_ACCESS_TOKEN (Facebook)
  - INSTAGRAM_BUSINESS_ID, INSTAGRAM_ACCESS_TOKEN (Instagram)
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass(frozen=True)
class ConfigAdaptateurs:
    """Configuration agrégée de tous les adaptateurs tiers."""

    # Données sportives
    api_football_cles: list[str] = field(default_factory=list)

    # Paiements Mobile Money
    airtel_cle: str = ""
    airtel_url: str = ""
    mpesac_cle: str = ""
    mpesac_url: str = ""
    orange_cle: str = ""
    orange_url: str = ""

    # Météo
    openweather_cle: str = ""

    # Audio / TTS
    tts_cle: str = ""
    tts_fournisseur: str = "google"

    # Calendrier
    google_calendar_credentials: str = ""
    google_calendar_api_key: str = ""
    google_calendar_id: str = "primary"

    # Réseaux sociaux
    telegram_token: str = ""
    telegram_canal: str = ""
    facebook_page_id: str = ""
    facebook_access_token: str = ""
    instagram_business_id: str = ""
    instagram_access_token: str = ""

    def sportif_configuré(self) -> bool:
        return bool(self.api_football_cles)

    def paiement_configuré(self, operateur: str = "airtel") -> bool:
        operateur = operateur.lower()
        if operateur == "airtel":
            return bool(self.airtel_cle and self.airtel_url)
        if operateur == "m-pesa":
            return bool(self.mpesac_cle and self.mpesac_url)
        if operateur == "orange":
            return bool(self.orange_cle and self.orange_url)
        return False

    def meteo_configuré(self) -> bool:
        return bool(self.openweather_cle)

    def audio_configuré(self) -> bool:
        return bool(self.tts_cle)

    def calendrier_configuré(self) -> bool:
        return bool(self.google_calendar_credentials or self.google_calendar_api_key)

    def reseaux_sociaux_configurés(self) -> bool:
        return bool(self.telegram_token and self.telegram_canal)


def charger_config_adaptateurs() -> ConfigAdaptateurs:
    """Construit la configuration depuis les variables d'environnement.

    C'est le seul endroit où l'utilisateur doit ajouter ses clés API
    (ou définir les variables d'environnement correspondantes).
    """
    cles = [k for k in (os.environ.get("API_FOOTBALL_KEY_1", ""), os.environ.get("API_FOOTBALL_KEY_2", "")) if k]

    return ConfigAdaptateurs(
        api_football_cles=cles,
        airtel_cle=os.environ.get("AIRTEL_API_KEY", ""),
        airtel_url=os.environ.get("AIRTEL_API_URL", ""),
        mpesac_cle=os.environ.get("MPESA_API_KEY", ""),
        mpesac_url=os.environ.get("MPESA_API_URL", ""),
        orange_cle=os.environ.get("ORANGE_API_KEY", ""),
        orange_url=os.environ.get("ORANGE_API_URL", ""),
        openweather_cle=os.environ.get("OPENWEATHER_API_KEY", ""),
        tts_cle=os.environ.get("TTS_API_KEY", ""),
        tts_fournisseur=os.environ.get("TTS_FOURNISSEUR", "google"),
        google_calendar_credentials=os.environ.get("GOOGLE_CALENDAR_CREDENTIALS", ""),
        google_calendar_api_key=os.environ.get("GOOGLE_CALENDAR_API_KEY", ""),
        google_calendar_id=os.environ.get("GOOGLE_CALENDAR_ID", "primary"),
        telegram_token=os.environ.get("TELEGRAM_TOKEN", ""),
        telegram_canal=os.environ.get("CANAL_ID", ""),
        facebook_page_id=os.environ.get("FACEBOOK_PAGE_ID", ""),
        facebook_access_token=os.environ.get("FACEBOOK_ACCESS_TOKEN", ""),
        instagram_business_id=os.environ.get("INSTAGRAM_BUSINESS_ID", ""),
        instagram_access_token=os.environ.get("INSTAGRAM_ACCESS_TOKEN", ""),
    )
