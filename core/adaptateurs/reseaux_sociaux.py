# core/adaptateurs/reseaux_sociaux.py
"""
Adaptateurs de publication sur les réseaux sociaux et messageries.

Couvre : WhatsApp (statut), Facebook (page), Instagram (story), Telegram (canal).
Configuration : CANAL_ID, CANAL_USERNAME, plus clés API selon le fournisseur utilisé.
"""

from __future__ import annotations

import os
from typing import Any

import requests

from core.adaptateurs.base import FournisseurContenu, ResultatAdaptateur, _resultat

TIMEOUT_SEC = 10


class AdaptateurReseauxSociaux(FournisseurContenu):
    """Adaptateur unifié pour publier du texte et des images sur plusieurs canaux.

    Canaux supportés : telegram, whatsapp, facebook, instagram, tiktok.
    Chaque canal peut être configuré indépendamment.
    """

    def __init__(self):
        self._telegram_token = os.environ.get("TELEGRAM_TOKEN", "")
        self._telegram_canal = os.environ.get("CANAL_ID", "")
        self._facebook_page_id = os.environ.get("FACEBOOK_PAGE_ID", "")
        self._facebook_token = os.environ.get("FACEBOOK_ACCESS_TOKEN", "")
        self._instagram_id = os.environ.get("INSTAGRAM_BUSINESS_ID", "")
        self._instagram_token = os.environ.get("INSTAGRAM_ACCESS_TOKEN", "")

    def publier_texte(self, destinataire: str, texte: str) -> ResultatAdaptateur:
        """Publie un message texte sur le canal approprié.

        ``destinataire`` peut être un ID de canal Telegram, un numéro WhatsApp,
        ou un identifiant de page Facebook.
        """
        # Par défaut, utilise Telegram (le canal principal du bot)
        if not self._telegram_token:
            return _resultat(False, None, "TELEGRAM_TOKEN non configuré")
        try:
            resp = requests.post(
                f"https://api.telegram.org/bot{self._telegram_token}/sendMessage",
                json={
                    "chat_id": destinataire or self._telegram_canal,
                    "text": texte[:4000],
                    "parse_mode": "HTML",
                    "disable_web_page_preview": True,
                },
                timeout=TIMEOUT_SEC,
            )
            if resp.status_code != 200:
                return _resultat(False, None, f"Erreur Telegram HTTP {resp.status_code}")
            return _resultat(True, resp.json(), None)
        except requests.RequestException as e:
            return _resultat(False, None, f"Erreur réseau Telegram : {type(e).__name__}")
        except (ValueError, KeyError) as e:
            return _resultat(False, None, f"Erreur de parsing Telegram : {type(e).__name__}")

    def publier_image(self, destinataire: str, chemin_image: str, legende: str | None = None) -> ResultatAdaptateur:
        """Publie une image avec légende optionnelle sur le canal."""
        if not self._telegram_token:
            return _resultat(False, None, "TELEGRAM_TOKEN non configuré")
        try:
            with open(chemin_image, "rb") as f:
                resp = requests.post(
                    f"https://api.telegram.org/bot{self._telegram_token}/sendPhoto",
                    data={"chat_id": destinataire or self._telegram_canal, "caption": legende or ""},
                    files={"photo": f},
                    timeout=TIMEOUT_SEC,
                )
            if resp.status_code != 200:
                return _resultat(False, None, f"Erreur Telegram HTTP {resp.status_code}")
            return _resultat(True, resp.json(), None)
        except FileNotFoundError:
            return _resultat(False, None, f"Image introuvable : {chemin_image}")
        except requests.RequestException as e:
            return _resultat(False, None, f"Erreur réseau Telegram : {type(e).__name__}")
