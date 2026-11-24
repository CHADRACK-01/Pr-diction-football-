# core/betting/value_bet.py
"""
Calcul pur du value bet.

Module sans base de données ni réseau : uniquement des fonctions de calcul
réutilisées par paris_builder et nouveau_prediction pour garantir un verdict
identique (EV strictement supérieure au seuil configuré VALUE_BET_MIN_EV).
"""

from __future__ import annotations

from typing import Optional

from config import VALUE_BET_MIN_EV
from core.utils.logs import log_warning


def calculer_ev(proba: float, cote: float) -> float:
    """Calcule l'espérance mathématique EV = (proba * cote) - 1.

    Args:
        proba: Probabilité de l'issue, comprise entre 0 et 1.
        cote: Cote proposée par le bookmaker.

    Returns:
        Valeur de l'espérance mathématique. Positive = value bet.
    """
    return (proba * cote) - 1


def est_value_bet(
    proba: float,
    cote: float,
    seuil: float | None = None,
) -> bool:
    """Retourne True si la cote est jouable et que l'EV dépasse le seuil.

    Le seuil par défaut est VALUE_BET_MIN_EV (config). Retourne False si la
    cote est absente ou <= 1.0, ou si la probabilité sort de [0, 1].

    Args:
        proba: Probabilité estimée de l'issue (0-1).
        cote: Cote bookmaker.
        seuil: Seuil EV minimal. Si None, utilise VALUE_BET_MIN_EV.

    Returns:
        True si c'est un value bet, False sinon.
    """
    if cote is None or cote <= 1.0:
        return False
    if proba is None or not (0.0 <= proba <= 1.0):
        return False
    seuil_effectif = VALUE_BET_MIN_EV if seuil is None else seuil
    return calculer_ev(proba, cote) > seuil_effectif


def analyser_value_bet(
    proba: float,
    cote_book: float,
    label: str | None = None,
) -> dict | None:
    """Analyse une issue et retourne son verdict de value bet.

    Retourne un dictionnaire
    ``{'label', 'proba', 'cote_bot', 'cote_book', 'is_value', 'ev'}``.
    Retourne None (après log_warning) si la cote book est absente ou <= 1.0,
    ou si la probabilité sort de [0, 1].

    Args:
        proba: Probabilité estimée de l'issue (0-1).
        cote_book: Cote proposée par le bookmaker.
        label: Libellé du pari (ex: "1", "N", "2", "Over 2.5").

    Returns:
        Dictionnaire du verdict ou None si les données sont invalides.
    """
    if cote_book is None or cote_book <= 1.0:
        log_warning(
            f"Cote book invalide pour le value bet : {cote_book!r}",
            "VALUE_BET",
        )
        return None
    if proba is None or not (0.0 <= proba <= 1.0):
        log_warning(
            f"Probabilité invalide pour le value bet : {proba!r}",
            "VALUE_BET",
        )
        return None

    ev = calculer_ev(proba, cote_book)
    return {
        "label": label,
        "proba": proba,
        "cote_bot": proba,
        "cote_book": cote_book,
        "is_value": ev > VALUE_BET_MIN_EV,
        "ev": ev,
    }
