# core/betting/cashout.py
"""
Simulateur de cash-out (fonctionnalités 5 et 46).

Calcule le montant de récupération d'un pari en cours selon :
- la mise initiale
- la cote initiale
- la cote actuelle au moment du cash-out

Aucune dépendance externe : calcul pur.
"""

from __future__ import annotations

from typing import Optional

from core.utils.logs import log_info, log_warning


def calculer_cashout(
    mise: float,
    cote_initiale: float,
    cote_actuelle: float,
) -> dict[str, float]:
    """Calcule le cash-out total d'un pari.

    Formule : montant_cashout = mise * (cote_actuelle / cote_initiale)

    Cette approximation suppose que la probabilité implicite du ticket
    reste proportionnelle au ratio des cotes.

    Args:
        mise: Montant misé initialement (> 0).
        cote_initiale: Cote au moment du pari (> 1.0).
        cote_actuelle: Cote actuelle du même pari (> 1.0).

    Returns:
        Dictionnaire avec mise, gain_potentiel, montant_cashout, benefice_net.

    Raises:
        ValueError: Si mise <= 0 ou l'une des cotes <= 1.0.
    """
    if mise <= 0:
        raise ValueError("La mise doit être strictement positive.")
    if cote_initiale <= 1.0:
        raise ValueError("La cote initiale doit être > 1.0.")
    if cote_actuelle <= 1.0:
        raise ValueError("La cote actuelle doit être > 1.0.")

    gain_potentiel = mise * cote_initiale
    montant_cashout = mise * (cote_actuelle / cote_initiale)
    benefice_net = montant_cashout - mise

    log_info(
        "Cash-out calculé",
        "CASHOUT",
        extra={
            "mise": mise,
            "cote_initiale": cote_initiale,
            "cote_actuelle": cote_actuelle,
            "montant_cashout": round(montant_cashout, 2),
        },
    )

    return {
        "mise": round(mise, 2),
        "gain_potentiel": round(gain_potentiel, 2),
        "montant_cashout": round(montant_cashout, 2),
        "benefice_net": round(benefice_net, 2),
    }


def calculer_cashout_partiel(
    mise: float,
    cote_initiale: float,
    cote_actuelle: float,
    fraction: float,
) -> dict[str, float]:
    """Calcule un cash-out partiel.

    Encaisse une fraction du ticket et laisse le reste en jeu.

    Args:
        mise: Montant misé initialement (> 0).
        cote_initiale: Cote au moment du pari (> 1.0).
        cote_actuelle: Cote actuelle (> 1.0).
        fraction: Fraction du ticket à encaisser (0.0 < fraction <= 1.0).

    Returns:
        Dictionnaire avec montant_encaisse, mise_restante, benefice_partiel.

    Raises:
        ValueError: Si fraction hors de (0, 1].
    """
    if not (0.0 < fraction <= 1.0):
        raise ValueError("La fraction doit être comprise entre 0 et 1 (exclus de 0).")

    cashout_total = calculer_cashout(mise, cote_initiale, cote_actuelle)
    montant_encaisse = cashout_total["montant_cashout"] * fraction
    mise_restante = mise * (1.0 - fraction)
    benefice_partiel = montant_encaisse - (mise * fraction)

    log_info(
        "Cash-out partiel calculé",
        "CASHOUT",
        extra={
            "mise": mise,
            "fraction": fraction,
            "montant_encaisse": round(montant_encaisse, 2),
        },
    )

    return {
        "montant_encaisse": round(montant_encaisse, 2),
        "mise_restante": round(mise_restante, 2),
        "benefice_partiel": round(benefice_partiel, 2),
    }


def est_interessant_cashout(
    cote_initiale: float,
    cote_actuelle: float,
    seuil_min: float = 1.10,
) -> bool:
    """Détermine si un cash-out est intéressant.

    Un cash-out est intéressant si la cote a baissé suffisamment pour
    offrir une valeur de récupération supérieure à la mise.

    Args:
        cote_initiale: Cote initiale du pari.
        cote_actuelle: Cote actuelle.
        seuil_min: Ratio minimum cote_actuelle / cote_initiale pour accepter.

    Returns:
        True si le cash-out est intéressant.
    """
    if cote_initiale <= 1.0 or cote_actuelle <= 1.0:
        return False
    ratio = cote_actuelle / cote_initiale
    return ratio >= seuil_min
