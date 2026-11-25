# core/services/risque.py
"""
Service de gestion du risque et de la bankroll.

Orchestre :
- core.betting.bankroll (gestion bankroll, Kelly fractionné)
- core.betting.gestion_risques (plan anti-perte, limites)
- core.domaine.Bankroll
"""

from __future__ import annotations

from typing import Any

from core.domaine import Bankroll
from core.exceptions import BankrollInsuffisanteError
from core.utils.logs import log_info, log_error


class ServiceRisque:
    """Service de gestion du risque et de la bankroll utilisateur."""

    def verifier_mise_autorisee(
        self,
        bankroll: Bankroll,
        montant: float,
    ) -> dict[str, Any]:
        """Vérifie si une mise est autorisée par rapport à la bankroll.

        Args:
            bankroll: État de la bankroll de l'utilisateur.
            montant: Montant de la mise demandée.

        Returns:
            Dictionnaire {autorisee, plafond, montant, raison}.
        """
        plafond = bankroll.plafond_mise()
        autorisee = montant <= plafond

        return {
            "autorisee": autorisee,
            "plafond": plafond,
            "montant": montant,
            "pourcentage_bankroll": (montant / bankroll.montant_total * 100)
            if bankroll.montant_total > 0
            else 0.0,
            "raison": None if autorisee else "Mise dépasse le plafond de la bankroll",
        }

    def calculer_mise_kelly(
        self,
        bankroll: Bankroll,
        proba: float,
        cote: float,
        fraction_kelly: float = 0.25,
    ) -> dict[str, Any]:
        """Calcule la mise optimale selon la formule de Kelly fractionné.

        Kelly : f = (p * b - q) / b  où b = cote - 1, p = proba, q = 1 - p
        Kelly fractionné : f * fraction_kelly (par défaut 25% pour prudence).

        Args:
            bankroll: État de la bankroll.
            proba: Probabilité estimée de gain (0-1).
            cote: Cote proposée.
            fraction_kelly: Fraction de Kelly à appliquer (0.0 à 1.0).

        Returns:
            Dictionnaire {mise_kelly, mise_recommandee, autorisee, plafond}.
        """
        if not (0.0 <= proba <= 1.0) or cote <= 1.0:
            return {"mise_kelly": 0.0, "mise_recommandee": 0.0, "autorisee": False, "plafond": 0.0}

        b = cote - 1.0
        p = proba
        q = 1.0 - p
        kelly_fraction = (p * b - q) / b if b > 0 else 0.0

        if kelly_fraction <= 0:
            return {"mise_kelly": 0.0, "mise_recommandee": 0.0, "autorisee": False, "plafond": 0.0}

        mise_kelly = bankroll.montant_total * kelly_fraction * fraction_kelly
        mise_recommandee = min(mise_kelly, bankroll.plafond_mise())
        autorisee = mise_recommandee > 0

        return {
            "mise_kelly": round(mise_kelly, 2),
            "mise_recommandee": round(mise_recommandee, 2),
            "autorisee": autorisee,
            "plafond": bankroll.plafond_mise(),
            "kelly_pct": round(kelly_fraction * 100, 2),
        }

    def verifier_plan_anti_perte(
        self,
        pertes_consecutives: int,
        est_combine: bool = False,
        mise_demandee: float = 0.0,
    ) -> dict[str, Any]:
        """Vérifie si le plan anti-perte bloque une mise.

        Après 3 pertes consécutives, bloque les gros combinés.

        Args:
            pertes_consecutives: Nombre de pertes consécutives.
            est_combine: Si le pari est un combiné.
            mise_demandee: Montant de la mise demandée.

        Returns:
            Dictionnaire {bloque, raison, conseil}.
        """
        if pertes_consecutives >= 3 and est_combine:
            return {
                "bloque": True,
                "raison": "Plan anti-perte activé : 3 pertes consécutives, combinés bloqués",
                "conseil": "Proposez un pari simple ou attendez une victoire",
            }

        if pertes_consecutives >= 5:
            return {
                "bloque": True,
                "raison": "Plan anti-perte activé : 5 pertes consécutives, tous les paris bloqués",
                "conseil": "Pause suggérée de 24h",
            }

        return {
            "bloque": False,
            "raison": None,
            "conseil": None,
        }
