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

        Délègue à :func:`core.betting.bankroll.calculer_mise_kelly` (source de vérité).

        Args:
            bankroll: État de la bankroll.
            proba: Probabilité estimée de gain (0-1).
            cote: Cote proposée.
            fraction_kelly: Fraction de Kelly à appliquer (0.0 à 1.0).

        Returns:
            Dictionnaire {mise_kelly, mise_recommandee, autorisee, plafond, kelly_pct}.
        """
        from core.betting.bankroll import calculer_mise_kelly as _calculer_mise_kelly

        res = _calculer_mise_kelly(bankroll, proba, cote, fraction_kelly)
        return {
            "mise_kelly": res["mise_kelly"],
            "mise_recommandee": res["mise_recommandee"],
            "autorisee": res["autorisee"],
            "plafond": res["plafond_bankroll"],
            "kelly_pct": round(res["kelly_fraction"] * 100, 2),
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
