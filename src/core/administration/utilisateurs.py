# core/administration/utilisateurs.py
"""
Gestion des utilisateurs par statut (gratuit, Premium, expiré, bloqué, VIP, revendeur).

Contrat métier pour les actions admin sur les utilisateurs.
"""

from __future__ import annotations

from typing import Any

from core.utils.logs import log_info, log_error


def gestion_utilisateurs_statut(
    action: str,
    user_id: int,
    **kwargs,
) -> dict[str, Any]:
    """Gère le statut d'un utilisateur.

    Args:
        action: "bannir", "debannir", "premium", "free", "vip", "revendeur".
        user_id: ID de l'utilisateur Telegram.
        **kwargs: raison (pour bannir), date_expiration (pour premium), etc.

    Returns:
        Dictionnaire {succes, message, user_id, action}.
    """
    try:
        raison = kwargs.get("raison", "")
        date_expiration = kwargs.get("date_expiration")

        log_info(
            f"Action utilisateur : {action} sur user {user_id}",
            "ADMINISTRATION",
            extra={"action": action, "user_id": user_id, "raison": raison},
        )

        # La persistance réelle se fait via users/admin.py, users/account_base.py
        # Cette fonction définit le contrat métier.

        return {
            "succes": True,
            "message": f"Action {action} effectuée sur l'utilisateur {user_id} (à persister via users/)",
            "user_id": user_id,
            "action": action,
        }
    except Exception as e:
        log_error(
            "Erreur gestion utilisateur",
            "ADMINISTRATION",
            exception=e,
            extra={"action": action, "user_id": user_id},
        )
        return {"succes": False, "message": str(e)}
