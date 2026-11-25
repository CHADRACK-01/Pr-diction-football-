# core/services/engagement.py
"""
Service d'engagement utilisateur (fonctionnalités 70-78).

Gère :
- XP et points de fidélité
- Bonus de connexion quotidienne
- Roue quotidienne gratuite
- Classement des parrains
- Boutique XP

Aucune dépendance externe : logique métier pure.
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Any

from core.utils.logs import log_info, log_warning

TZ_KINSHASA = timezone(timedelta(hours=1))


class ServiceEngagement:
    """Service de gestion de l'engagement utilisateur (XP, bonus, roue, parrainage)."""

    # --- XP ---

    def attribuer_xp(
        self,
        user_id: int,
        action: str,
        xp_base: int = 10,
    ) -> dict[str, Any]:
        """Attribue des XP à un utilisateur pour une action donnée.

        Args:
            user_id: ID de l'utilisateur Telegram.
            action: Type d'action ("connexion", "prono", "partage", "quiz", etc.).
            xp_base: Nombre de XP de base pour l'action.

        Returns:
            Dictionnaire {user_id, action, xp_attribues, total_xp, nouveau_niveau}.
        """
        # La persistance réelle se fait via users/ (credits, account_base)
        multiplicateurs = {
            "connexion": 1.0,
            "prono": 2.0,
            "partage": 3.0,
            "quiz": 5.0,
            "parrainage": 10.0,
        }
        mult = multiplicateurs.get(action, 1.0)
        xp_attribues = int(xp_base * mult)

        log_info(
            f"XP attribués : {xp_attribues} pour l'action '{action}' (user {user_id})",
            "ENGAGEMENT",
            extra={"user_id": user_id, "action": action, "xp": xp_attribues},
        )

        return {
            "user_id": user_id,
            "action": action,
            "xp_attribues": xp_attribues,
            "total_xp": xp_attribues,  # À remplacer par la lecture en base
            "nouveau_niveau": xp_attribues // 100 + 1,
        }

    def get_solde_xp(self, user_id: int) -> dict[str, Any]:
        """Retourne le solde XP d'un utilisateur.

        Args:
            user_id: ID de l'utilisateur Telegram.

        Returns:
            Dictionnaire {user_id, solde_xp, niveau, progression_vers_suivant}.
        """
        # Placeholder : persistance via users/
        return {
            "user_id": user_id,
            "solde_xp": 0,
            "niveau": 1,
            "progression_vers_suivant": 0.0,
            "message": "Solde XP à implémenter côté persistance users/",
        }

    # --- Bonus de connexion quotidienne ---

    # Déprécié : utilisez core.engagement.engagement_local.bonus_connexion_quotidienne
    # (source de vérité avec persistance et série de connexion).

    # --- Roue quotidienne ---

    def roue_quotidienne(
        self,
        user_id: int,
        derniere_utilisation: str | None = None,
    ) -> dict[str, Any]:
        """Fait tourner la roue quotidienne gratuite (une fois par jour).

        Args:
            user_id: ID de l'utilisateur Telegram.
            derniere_utilisation: Date de la dernière utilisation ou None.

        Returns:
            Dictionnaire {peut_jouer, gain, xp, message}.
        """
        maintenant = datetime.now(TZ_KINSHASA).strftime("%Y-%m-%d")

        if derniere_utilisation == maintenant:
            return {
                "peut_jouer": False,
                "gain": "Aucune",
                "xp": 0,
                "message": "Roue quotidienne déjà utilisée aujourd'hui.",
            }

        import random
        gains = [
            ("5 XP", 5, 0.40),
            ("10 XP", 10, 0.30),
            ("20 XP", 20, 0.20),
            ("50 XP", 50, 0.08),
            ("Ticket Premium 24h", 0, 0.02),
        ]
        tirage = random.random()
        cumul = 0.0
        gain = "5 XP"
        xp = 5
        for libelle, valeur, proba in gains:
            cumul += proba
            if tirage <= cumul:
                gain = libelle
                xp = valeur
                break

        log_info(
            f"Roue quotidienne user {user_id} : {gain} ({xp} XP)",
            "ENGAGEMENT",
            extra={"user_id": user_id, "gain": gain, "xp": xp},
        )

        return {
            "peut_jouer": True,
            "gain": gain,
            "xp": xp,
            "message": f"🎡 Roue quotidienne : vous avez gagné {gain} !",
            "date": maintenant,
        }

    # --- Classement des parrains ---

    def enregistrer_parrainage(
        self,
        parrain_id: int,
        filleul_id: int,
    ) -> dict[str, Any]:
        """Enregistre un parrainage et attribue des XP au parrain.

        Args:
            parrain_id: ID de l'utilisateur qui parraine.
            filleul_id: ID du nouvel utilisateur parrainé.

        Returns:
            Dictionnaire {succes, xp_parrain, message}.
        """
        xp_parrain = 50

        log_info(
            f"Parrainage : user {parrain_id} parraine {filleul_id} (+{xp_parrain} XP)",
            "ENGAGEMENT",
            extra={"parrain_id": parrain_id, "filleul_id": filleul_id, "xp": xp_parrain},
        )

        return {
            "succes": True,
            "xp_parrain": xp_parrain,
            "message": f"+{xp_parrain} XP pour le parrainage !",
        }

    def get_classement_parrains(
        self,
        limite: int = 10,
    ) -> list[dict[str, Any]]:
        """Retourne le classement des meilleurs parrains du mois.

        Args:
            limite: Nombre de parrains à retourner.

        Returns:
            Liste de dictionnaires {rang, user_id, nb_filleuls, xp_total}.
        """
        # Placeholder : persistance via users/account_referral.py
        return [
            {
                "rang": i + 1,
                "user_id": 0,
                "pseudo": f"Utilisateur {i + 1}",
                "nb_filleuls": 0,
                "xp_total": 0,
            }
            for i in range(limite)
        ]

    # --- Boutique XP ---

    def boutique_xp(
        self,
        user_id: int,
        article: str,
        cout_xp: int,
        solde_xp_utilisateur: int,
    ) -> dict[str, Any]:
        """Permet d'échanger des XP contre des récompenses (Premium, analyses VIP, etc.).

        Args:
            user_id: ID de l'utilisateur Telegram.
            article: Nom de l'article acheté ("premium_24h", "analyse_vip", etc.).
            cout_xp: Coût en XP de l'article.
            solde_xp_utilisateur: Solde XP actuel de l'utilisateur.

        Returns:
            Dictionnaire {succes, reste_xp, message}.
        """
        if solde_xp_utilisateur < cout_xp:
            return {
                "succes": False,
                "reste_xp": solde_xp_utilisateur,
                "message": f"XP insuffisantes : {cout_xp} requises, {solde_xp_utilisateur} disponibles.",
            }

        reste = solde_xp_utilisateur - cout_xp

        log_info(
            f"Achat boutique : user {user_id} achète '{article}' pour {cout_xp} XP",
            "ENGAGEMENT",
            extra={"user_id": user_id, "article": article, "cout_xp": cout_xp},
        )

        return {
            "succes": True,
            "article": article,
            "cout_xp": cout_xp,
            "reste_xp": reste,
            "message": f"Achat effectué : {article} (-{cout_xp} XP).",
        }
