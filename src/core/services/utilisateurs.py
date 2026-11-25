# core/services/utilisateurs.py
"""
Service de gestion des utilisateurs et abonnements.

Orchestre :
- users/ pour la persistance (statut, expiration, langue, notifications)
- core.domaine.Utilisateur
"""

from __future__ import annotations

from typing import Any

from core.domaine import Utilisateur
from core.exceptions import UtilisateurError, AbonnementExpiréError
from core.utils.logs import log_info, log_error


class ServiceUtilisateurs:
    """Service de gestion des profils utilisateurs et statuts d'abonnement."""

    def verifier_acces_premium(self, user_id: int, date_expiration: str | None) -> dict[str, Any]:
        """Vérifie si un utilisateur a un accès Premium valide.

        Args:
            user_id: ID de l'utilisateur Telegram.
            date_expiration: Date d'expiration de l'abonnement (YYYY-MM-DD) ou None.

        Returns:
            Dictionnaire {est_premium, expiré, jours_restants, message}.
        """
        from datetime import datetime, timezone, timedelta

        if date_expiration is None:
            return {
                "est_premium": False,
                "expire": True,
                "jours_restants": 0,
                "message": "Abonnement gratuit - aucune expiration configurée",
            }

        try:
            exp = datetime.strptime(date_expiration, "%Y-%m-%d").replace(
                tzinfo=timezone(timedelta(hours=1))
            )
            maintenant = datetime.now(timezone(timedelta(hours=1)))
            jours_restants = (exp - maintenant).days

            if jours_restants <= 0:
                return {
                    "est_premium": False,
                    "expire": True,
                    "jours_restants": 0,
                    "message": "Abonnement expiré",
                }

            return {
                "est_premium": True,
                "expire": False,
                "jours_restants": jours_restants,
                "message": f"Premium actif - {jours_restants} jour(s) restant(s)",
            }
        except ValueError as e:
            log_error(
                "Date d'expiration invalide",
                "SERVICE_UTILISATEURS",
                exception=e,
                extra={"user_id": user_id, "date_expiration": date_expiration},
            )
            raise UtilisateurError(f"Date d'expiration invalide : {date_expiration}") from e

    def get_profil(self, user_id: int) -> Utilisateur | None:
        """Retourne le profil utilisateur (placeholder - persistance via users/).

        Args:
            user_id: ID de l'utilisateur Telegram.

        Returns:
            Objet Utilisateur ou None si non trouvé.
        """
        # La persistance réelle se fait via users.account_base, users.admin, etc.
        # Cette fonction définit le contrat métier.
        return None
