# core/betting/bankroll.py
"""
Gestion de bankroll et mise Kelly fractionné (fonctionnalités 41 et 42).

Calcule la mise optimale selon la formule de Kelly, avec fractionnement
pour la prudence, et vérifie les plafonds de bankroll.

Aucune dépendance externe : calcul pur.
"""

from __future__ import annotations

from core.domaine import Bankroll
from core.exceptions import BankrollInsuffisanteError
from core.utils.logs import log_info, log_warning


def calculer_mise_kelly(
    bankroll: Bankroll,
    proba: float,
    cote: float,
    fraction_kelly: float = 0.25,
) -> dict[str, float]:
    """Calcule la mise optimale selon Kelly fractionné.

    Formule Kelly : f = (p * b - q) / b
    où b = cote - 1, p = probabilité de gain, q = 1 - p.

    Kelly fractionné : mise = bankroll * f * fraction_kelly.

    Args:
        bankroll: État de la bankroll de l'utilisateur.
        proba: Probabilité estimée de gain (0.0 à 1.0).
        cote: Cote proposée par le bookmaker (> 1.0).
        fraction_kelly: Fraction de Kelly à appliquer (0.0 à 1.0, défaut 0.25).

    Returns:
        Dictionnaire avec kelly_fraction, mise_kelly, mise_recommandee,
        plafond_bankroll, pourcentage_bankroll, autorisee.

    Raises:
        ValueError: Si proba hors de [0,1], cote <= 1.0, fraction_kelly hors de [0,1].
    """
    if not (0.0 <= proba <= 1.0):
        raise ValueError("La probabilité doit être comprise entre 0 et 1.")
    if cote <= 1.0:
        raise ValueError("La cote doit être strictement supérieure à 1.0.")
    if not (0.0 <= fraction_kelly <= 1.0):
        raise ValueError("La fraction Kelly doit être comprise entre 0 et 1.")

    b = cote - 1.0
    p = proba
    q = 1.0 - p

    kelly_fraction = (p * b - q) / b if b > 0 else 0.0

    if kelly_fraction <= 0:
        return {
            "kelly_fraction": 0.0,
            "mise_kelly": 0.0,
            "mise_recommandee": 0.0,
            "plafond_bankroll": bankroll.plafond_mise(),
            "pourcentage_bankroll": 0.0,
            "autorisee": False,
        }

    mise_kelly = bankroll.montant_total * kelly_fraction * fraction_kelly
    mise_recommandee = min(mise_kelly, bankroll.plafond_mise())
    autorisee = mise_recommandee > 0

    pourcentage = (mise_recommandee / bankroll.montant_total * 100) if bankroll.montant_total > 0 else 0.0

    log_info(
        "Mise Kelly calculée",
        "BANKROLL",
        extra={
            "user_id": bankroll.user_id,
            "proba": proba,
            "cote": cote,
            "kelly_fraction": round(kelly_fraction, 4),
            "mise_recommandee": round(mise_recommandee, 2),
            "autorisee": autorisee,
        },
    )

    return {
        "kelly_fraction": round(kelly_fraction, 4),
        "mise_kelly": round(mise_kelly, 2),
        "mise_recommandee": round(mise_recommandee, 2),
        "plafond_bankroll": bankroll.plafond_mise(),
        "pourcentage_bankroll": round(pourcentage, 2),
        "autorisee": autorisee,
    }


def plan_mise_fixe(
    bankroll: Bankroll,
    pourcentage: float | None = None,
) -> dict[str, float]:
    """Plan de mise fixe : un pourcentage constant de la bankroll par pari.

    Args:
        bankroll: État de la bankroll.
        pourcentage: Pourcentage de la bankroll (défaut: 2.0% ou celui de la bankroll).

    Returns:
        Dictionnaire avec mise, pourcentage_applique, plafond, autorisee.
    """
    pct = pourcentage if pourcentage is not None else bankroll.pourcentage_mise
    if not (0.0 < pct <= 10.0):
        raise ValueError("Le pourcentage doit être compris entre 0 et 10.")

    mise = bankroll.montant_total * pct / 100.0
    plafond = bankroll.plafond_mise()
    mise = min(mise, plafond)

    return {
        "mise": round(mise, 2),
        "pourcentage_applique": round(pct, 2),
        "plafond": plafond,
        "autorisee": mise > 0,
    }


def plan_mise_progresif(
    bankroll: Bankroll,
    pertes_consecutives: int,
    type_plan: str = "martingale_douce",
) -> dict[str, float]:
    """Plan de mise progressif (Martingale douce ou Fibonacci).

    ⚠️ Attention : un plan de mise progressif peut pousser à miser davantage
    après une perte. Des garde-fous (plafond et pause) sont obligatoires.

    Args:
        bankroll: État de la bankroll.
        pertes_consecutives: Nombre de pertes consécutives.
        type_plan: "martingale_douce" ou "fibonacci".

    Returns:
        Dictionnaire avec mise, multiplicateur, autorisee, avertissement.
    """
    plafond = bankroll.plafond_mise()
    base = bankroll.montant_total * bankroll.pourcentage_mise / 100.0

    if type_plan == "fibonacci":
        # Suite de Fibonacci : 1, 1, 2, 3, 5, 8, 13...
        a, b = 1, 1
        for _ in range(max(0, pertes_consecutives)):
            a, b = b, a + b
        multiplicateur = float(a)
    else:  # martingale_douce
        # Multiplicateur 1.5x après chaque perte, plafonné à 3x
        multiplicateur = min(1.5 ** pertes_consecutives, 3.0)

    mise = base * multiplicateur
    mise = min(mise, plafond)

    avertissement = None
    if pertes_consecutives >= 3:
        avertissement = (
            "Plan de mise progressif après 3 pertes consécutives : "
            "risque accru. Pensez à faire une pause."
        )

    return {
        "mise": round(mise, 2),
        "multiplicateur": round(multiplicateur, 2),
        "plafond": plafond,
        "autorisee": mise > 0,
        "avertissement": avertissement,
    }
