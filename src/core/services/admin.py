# core/services/admin.py
"""
Service d'administration du bot.

Orchestre :
- core.administration.dashboard_admin.dashboard_admin_temps_reel
- core.administration.sauvegarde.sauvegarde_manuelle, restauration_backup
- core.administration.utilisateurs.gestion_utilisateurs_statut
- core.feature_registry.obtenir_statut_global
"""

from __future__ import annotations

from typing import Any

from core.administration.sauvegarde import sauvegarde_manuelle, restauration_backup
from core.administration.utilisateurs import gestion_utilisateurs_statut
from core.administration.dashboard_admin import dashboard_admin_temps_reel
from core.feature_registry import obtenir_statut_global, lister_non_implantees
from core.utils.logs import log_info, log_error


class ServiceAdmin:
    """Service d'administration : dashboard, sauvegardes, gestion utilisateurs, catalogue."""

    def get_dashboard(self) -> dict[str, Any]:
        """Retourne les données du dashboard administrateur temps réel."""
        try:
            return dashboard_admin_temps_reel()
        except Exception as e:
            log_error(
                "Erreur dashboard admin",
                "SERVICE_ADMIN",
                exception=e,
            )
            return {"erreur": str(e)}

    def sauvegarder(self) -> dict[str, Any]:
        """Déclenche une sauvegarde manuelle de la base de données.

        Returns:
            Dictionnaire {succes, message, taille_ko}.
        """
        try:
            return sauvegarde_manuelle()
        except Exception as e:
            log_error(
                "Erreur sauvegarde",
                "SERVICE_ADMIN",
                exception=e,
            )
            return {"succes": False, "message": str(e)}

    def restaurer(self, identifiant_sauvegarde: str) -> dict[str, Any]:
        """Restaure une sauvegarde de la base de données.

        Args:
            identifiant_sauvegarde: Identifiant ou nom de fichier de la sauvegarde.

        Returns:
            Dictionnaire {succes, message}.
        """
        try:
            return restauration_backup(identifiant_sauvegarde)
        except Exception as e:
            log_error(
                "Erreur restauration",
                "SERVICE_ADMIN",
                exception=e,
            )
            return {"succes": False, "message": str(e)}

    def get_statut_fonctionnalites(self) -> dict[str, dict[str, Any]]:
        """Retourne le statut de toutes les 700 fonctionnalités."""
        return obtenir_statut_global()

    def lister_non_implantees(self) -> list[dict[str, Any]]:
        """Liste les fonctionnalités non encore implémentées."""
        return lister_non_implantees()

    def gestion_utilisateurs(self, action: str, user_id: int, **kwargs) -> dict[str, Any]:
        """Gère les utilisateurs par statut (bannir, débannir, activer premium, etc.).

        Args:
            action: "bannir", "debannir", "premium", "free", "vip".
            user_id: ID de l'utilisateur.
            **kwargs: Paramètres supplémentaires (raison, date_expiration, etc.).

        Returns:
            Dictionnaire {succes, message}.
        """
        try:
            return gestion_utilisateurs_statut(action, user_id, **kwargs)
        except Exception as e:
            log_error(
                "Erreur gestion utilisateurs",
                "SERVICE_ADMIN",
                exception=e,
                extra={"action": action, "user_id": user_id},
            )
            return {"succes": False, "message": str(e)}
