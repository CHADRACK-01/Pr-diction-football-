# core/services/alertes.py
"""
Service d'alertes live et notifications.

Orchestre :
- core.administration.alertes_live.verifier_buts_live
- core.administration.pic_erreurs.controler_et_alerter
- core.administration.controle_quota.controler_et_alerter
- core.administration.alerte_apis.verifier_et_alerter
"""

from __future__ import annotations

from typing import Any, Callable

from core.administration.alertes_live import verifier_buts_live
from core.administration.pic_erreurs import controler_et_alerter as controler_pic
from core.administration.controle_quota import controler_et_alerter as controler_quota
from core.administration.alerte_apis import verifier_et_alerter as verifier_apis
from core.utils.logs import log_info, log_error


class ServiceAlertes:
    """Service d'alertes live, de santé des APIs et de pics d'erreurs."""

    def verifier_buts_live(self, bot: Any) -> int:
        """Vérifie les buts en direct et envoie les alertes.

        Args:
            bot: Instance du bot Telegram (pyTelegramBotAPI TeleBot).

        Returns:
            Nombre d'alertes envoyées.
        """
        try:
            return verifier_buts_live(bot)
        except Exception as e:
            log_error(
                "Erreur alertes live",
                "SERVICE_ALERTES",
                exception=e,
            )
            return 0

    def controler_sante_apis(self, envoyer_alerte: Callable[[str], None]) -> None:
        """Contrôle la santé des APIs et alerte l'admin si une source est morte.

        Args:
            envoyer_alerte: Callable acceptant un message texte pour l'admin.
        """
        try:
            verifier_apis(envoyer_alerte)
        except Exception as e:
            log_error(
                "Erreur contrôle santé APIs",
                "SERVICE_ALERTES",
                exception=e,
            )

    def controler_pic_erreurs(self, envoyer_alerte: Callable[[str], None]) -> int:
        """Détecte un pic d'erreurs et envoie une alerte si nécessaire.

        Args:
            envoyer_alerte: Callable acceptant un message texte pour l'admin.

        Returns:
            1 si une alerte a été envoyée, 0 sinon.
        """
        try:
            return controler_pic(envoyer_alerte)
        except Exception as e:
            log_error(
                "Erreur contrôle pic d'erreurs",
                "SERVICE_ALERTES",
                exception=e,
            )
            return 0

    def controler_quota_apis(self, envoyer_alerte: Callable[[str], None]) -> int:
        """Contrôle le quota des APIs et alerte si une clé approche de sa limite.

        Args:
            envoyer_alerte: Callable acceptant un message texte pour l'admin.

        Returns:
            Nombre d'alertes envoyées.
        """
        try:
            return controler_quota(envoyer_alerte)
        except Exception as e:
            log_error(
                "Erreur contrôle quota APIs",
                "SERVICE_ALERTES",
                exception=e,
            )
            return 0
