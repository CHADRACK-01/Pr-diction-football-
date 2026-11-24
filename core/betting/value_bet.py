# core/value_bet.py
"""
Calcul pur du value bet.

Module sans base de données ni réseau : uniquement des fonctions de calcul
réutilisées par paris_builder et nouveau_prediction pour garantir un verdict
identique (EV strictement supérieure au seuil configuré VALUE_BET_MIN_EV).
"""

from typing import Optional, Dict

from config import VALUE_BET_MIN_EV
from core.utils.logs import log_warning


def calculer_ev(proba: float, cote: float) -> float:
    """Calcule l'espérance mathématique EV = (proba * cote) - 1."""
    return (proba * cote) - 1


def est_value_bet(proba: float, cote: float, seuil: Optional[float] = None) -> bool:
    """
    Retourne True si la cote est jouable et que l'EV dépasse le seuil.

    Le seuil par défaut est VALUE_BET_MIN_EV (config). Retourne False si la
    cote est absente ou <= 1.0, ou si la probabilité sort de [0, 1].
    """
    if cote is None or cote <= 1.0:
        return False
    if proba is None or not (0.0 <= proba <= 1.0):
        return False
    seuil_effectif = VALUE_BET_MIN_EV if seuil is None else seuil
    return calculer_ev(proba, cote) > seuil_effectif


def analyser_value_bet(proba: float, cote_book: float,
                       label: Optional[str] = None) -> Optional[Dict]:
    """
    Analyse une issue et retourne son verdict de value bet.

    Retourne un dictionnaire ``{'label', 'proba', 'cote_bot', 'cote_book',
    'is_value'}``. Retourne None (après log_warning) si la cote book est
    absente ou <= 1.0, ou si la probabilité sort de [0, 1].
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

    return {
        "label": label,
        "proba": proba,
        "cote_bot": round(1 / proba, 2) if proba > 0 else None,
        "cote_book": cote_book,
        "is_value": est_value_bet(proba, cote_book),
    }
