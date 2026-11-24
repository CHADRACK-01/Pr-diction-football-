# core/services/paris.py
"""
Service de paris et coupons.

Orchestre :
- core.betting.value_bet (calcul EV, value bet)
- core.betting.cashout (cash-out total et partiel)
- core.betting.paris_builder (génération de coupons, combinés)
- core.domotaine.ValueBetVerdict, Match
"""

from __future__ import annotations

from typing import Any

from core.domaine import Match, ValueBetVerdict
from core.betting.value_bet import est_value_bet, analyser_value_bet, calculer_ev
from core.utils.logs import log_info, log_error


class ServiceParis:
    """Service de gestion des paris et coupons."""

    def analyser_value_bet(
        self,
        proba: float,
        cote_book: float,
        label: str | None = None,
    ) -> dict[str, Any] | None:
        """Analyse si une issue représente un value bet.

        Args:
            proba: Probabilité estimée de l'issue (0-1).
            cote_book: Cote proposée par le bookmaker.
            label: Libellé du pari (ex: "1", "N", "2", "Over 2.5").

        Returns:
            Dictionnaire du verdict ou None si les données sont invalides.
        """
        try:
            verdict = analyser_value_bet(proba, cote_book, label)
            if verdict is None:
                return None
            return {
                "label": verdict["label"],
                "proba": verdict["proba"],
                "cote_book": verdict["cote_book"],
                "ev": verdict["ev"],
                "is_value": verdict["is_value"],
            }
        except Exception as e:
            log_error(
                "Erreur analyse value bet",
                "SERVICE_PARIS",
                exception=e,
                extra={"proba": proba, "cote": cote_book, "label": label},
            )
            return None

    def calculer_cashout(
        self,
        mise: float,
        cote_initiale: float,
        cote_actuelle: float,
    ) -> dict[str, float]:
        """Calcule le montant du cash-out.

        Formule : gain_actuel = mise * cote_actuelle / cote_initiale
        (approximation simplifiée pour le cash-out total).

        Args:
            mise: Montant misé initialement.
            cote_initiale: Cote au moment du pari.
            cote_actuelle: Cote actuelle du même pari.

        Returns:
            Dictionnaire avec mise, gain_potentiel, montant_cashout, benefice_net.
        """
        if mise <= 0 or cote_initiale <= 1.0 or cote_actuelle <= 1.0:
            return {"mise": 0.0, "gain_potentiel": 0.0, "montant_cashout": 0.0, "benefice_net": 0.0}

        gain_potentiel = mise * cote_initiale
        # Le cash-out estime la valeur actuelle du ticket
        montant_cashout = mise * (cote_actuelle / cote_initiale)
        benefice_net = montant_cashout - mise

        return {
            "mise": round(mise, 2),
            "gain_potentiel": round(gain_potentiel, 2),
            "montant_cashout": round(montant_cashout, 2),
            "benefice_net": round(benefice_net, 2),
        }

    def calculer_cashout_partiel(
        self,
        mise: float,
        cote_initiale: float,
        cote_actuelle: float,
        fraction: float,
    ) -> dict[str, float]:
        """Calcule un cash-out partiel.

        Args:
            mise: Montant misé initialement.
            cote_initiale: Cote au moment du pari.
            cote_actuelle: Cote actuelle.
            fraction: Fraction du ticket à encaisser (0.0 à 1.0).

        Returns:
            Dictionnaire avec montant_encaisse, mise_restante, benefice_partiel.
        """
        if not (0.0 < fraction <= 1.0):
            return {"montant_encaisse": 0.0, "mise_restante": mise, "benefice_partiel": 0.0}

        cashout_total = self.calculer_cashout(mise, cote_initiale, cote_actuelle)
        montant_encaisse = cashout_total["montant_cashout"] * fraction
        mise_restante = mise * (1.0 - fraction)

        return {
            "montant_encaisse": round(montant_encaisse, 2),
            "mise_restante": round(mise_restante, 2),
            "benefice_partiel": round(montant_encaisse - (mise * fraction), 2),
        }
