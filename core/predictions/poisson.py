# core/predictions/poisson.py
"""Calculs de probabilités par la loi de Poisson.

Module pur : aucune base de données, aucun accès réseau. Toutes les
probabilités manipulées ou retournées sont exprimées en 0-1.
"""

from __future__ import annotations

import math

try:
    from config import COEF_AVANTAGE_TERRAIN, POISSON_MAX_BUTS
except ImportError:  # pragma: no cover - hors application (config indisponible)
    # Valeurs par défaut documentées : le module reste utilisable seul.
    COEF_AVANTAGE_TERRAIN = 0.10
    POISSON_MAX_BUTS = 5


# Espérance de buts minimale : une équipe ne peut pas être parfaitement nulle.
LAMBDA_MIN: float = 0.5


def proba_poisson(k: int, lamb: float) -> float:
    """Probabilité d'observer exactement ``k`` buts pour une espérance ``lamb``.

    Args:
        k: Nombre de buts (entier >= 0).
        lamb: Espérance de buts (float >= 0).

    Returns:
        Probabilité de Poisson P(X = k) dans [0, 1].

    Raises:
        ValueError: Si ``lamb`` est négatif.
    """
    if lamb < 0:
        raise ValueError("lambda doit être positif ou nul")
    if k < 0:
        raise ValueError("k doit être un entier positif ou nul")
    return (lamb ** k) * math.exp(-lamb) / math.factorial(k)


def calculer_lambdas(
    bm_h: float,
    bm_a: float,
    be_h: float,
    be_a: float,
    coef_avantage_terrain: float = COEF_AVANTAGE_TERRAIN,
) -> tuple[float, float]:
    """Espérances de buts corrigées par la défense adverse et l'avantage du terrain.

    ``bm_h``/``bm_a`` sont les buts marqués moyens, ``be_h``/``be_a`` les buts
    encaissés moyens. L'attaque d'une équipe est moyennée avec la défense de
    l'adversaire ; seul le camp à domicile bénéficie de l'avantage du terrain.

    Args:
        bm_h: Buts marqués moyens à domicile.
        bm_a: Buts marqués moyens à l'extérieur.
        be_h: Buts encaissés moyens à domicile.
        be_a: Buts encaissés moyens à l'extérieur.
        coef_avantage_terrain: Coefficient d'avantage terrain (0-1).

    Returns:
        Tuple (lambda_home, lambda_away), chacun >= LAMBDA_MIN.
    """
    lambda_home = (bm_h + be_a) / 2 * (1 + coef_avantage_terrain)
    lambda_away = (bm_a + be_h) / 2
    return max(LAMBDA_MIN, lambda_home), max(LAMBDA_MIN, lambda_away)


def proba_score(i: int, j: int, lambda_home: float, lambda_away: float) -> float:
    """Probabilité (0-1) du score exact ``i``-``j``.

    Args:
        i: Buts de l'équipe à domicile.
        j: Buts de l'équipe à l'extérieur.
        lambda_home: Espérance de buts domicile.
        lambda_away: Espérance de buts extérieur.

    Returns:
        Probabilité du score exact i-j.
    """
    return proba_poisson(i, lambda_home) * proba_poisson(j, lambda_away)


def matrice_scores(
    lambda_home: float,
    lambda_away: float,
    max_buts: int = POISSON_MAX_BUTS,
) -> dict[tuple[int, int], float]:
    """Grille ``(i, j) -> probabilité`` renormalisée (somme = 1).

    La troncature à ``max_buts`` abandonne une masse de probabilité
    résiduelle ; la renormalisation garantit une loi de probabilité complète.

    Args:
        lambda_home: Espérance de buts domicile.
        lambda_away: Espérance de buts extérieur.
        max_buts: Nombre maximal de buts considérés par équipe.

    Returns:
        Dictionnaire {(i, j): probabilité} pour i, j in [0, max_buts].

    Raises:
        ValueError: Si la masse totale est nulle (cas dégénéré).
    """
    grille: dict[tuple[int, int], float] = {}
    total = 0.0
    for i in range(max_buts + 1):
        for j in range(max_buts + 1):
            proba = proba_score(i, j, lambda_home, lambda_away)
            grille[(i, j)] = proba
            total += proba
    if total <= 0:
        raise ValueError("Masse de probabilité nulle : lambdas invalides.")
    for cle in grille:
        grille[cle] /= total
    return grille


def proba_1n2(
    lambda_home: float,
    lambda_away: float,
    max_buts: int = POISSON_MAX_BUTS,
) -> dict[str, float]:
    """Probabilités 1N2 (domicile, nul, extérieur) depuis une grille Poisson.

    Args:
        lambda_home: Espérance de buts domicile.
        lambda_away: Espérance de buts extérieur.
        max_buts: Nombre maximal de buts considérés par équipe.

    Returns:
        Dictionnaire {'p_h': ..., 'p_d': ..., 'p_a': ...} avec somme = 1.
    """
    grille = matrice_scores(lambda_home, lambda_away, max_buts)
    p_h = sum(proba for (i, j), proba in grille.items() if i > j)
    p_d = sum(proba for (i, j), proba in grille.items() if i == j)
    p_a = sum(proba for (i, j), proba in grille.items() if i < j)
    total = p_h + p_d + p_a
    return {
        "p_h": p_h / total,
        "p_d": p_d / total,
        "p_a": p_a / total,
    }


def proba_over_under(
    lambda_home: float,
    lambda_away: float,
    seuil: float,
    max_buts: int = POISSON_MAX_BUTS,
) -> dict[str, float]:
    """Probabilités Over/Under sur le total de buts.

    Args:
        lambda_home: Espérance de buts domicile.
        lambda_away: Espérance de buts extérieur.
        seuil: Seuil de buts (ex: 2.5 pour Over 2.5).
        max_buts: Nombre maximal de buts considérés par équipe.

    Returns:
        Dictionnaire {'over': ..., 'under': ...} avec somme = 1.
    """
    grille = matrice_scores(lambda_home, lambda_away, max_buts)
    p_over = sum(proba for (i, j), proba in grille.items() if (i + j) > seuil)
    p_under = sum(proba for (i, j), proba in grille.items() if (i + j) <= seuil)
    total = p_over + p_under
    return {
        "over": p_over / total,
        "under": p_under / total,
    }


def proba_btts(
    lambda_home: float,
    lambda_away: float,
    max_buts: int = POISSON_MAX_BUTS,
) -> dict[str, float]:
    """Probabilités Both Teams To Score (les deux équipes marquent).

    Args:
        lambda_home: Espérance de buts domicile.
        lambda_away: Espérance de buts extérieur.
        max_buts: Nombre maximal de buts considérés par équipe.

    Returns:
        Dictionnaire {'btts_oui': ..., 'btts_non': ...} avec somme = 1.
    """
    grille = matrice_scores(lambda_home, lambda_away, max_buts)
    p_oui = sum(
        proba for (i, j), proba in grille.items() if i >= 1 and j >= 1
    )
    p_non = 1.0 - p_oui
    return {
        "btts_oui": p_oui,
        "btts_non": p_non,
    }


def top_scores(
    lambda_home: float,
    lambda_away: float,
    top: int = 3,
    max_buts: int = POISSON_MAX_BUTS,
) -> list[tuple[int, int, float]]:
    """Retourne les ``top`` scores les plus probables.

    Args:
        lambda_home: Espérance de buts domicile.
        lambda_away: Espérance de buts extérieur.
        top: Nombre de scores à retourner.
        max_buts: Nombre maximal de buts considérés par équipe.

    Returns:
        Liste de ``(buts_domicile, buts_exterieur, probabilite)`` triée par
        probabilité décroissante.
    """
    grille = matrice_scores(lambda_home, lambda_away, max_buts)
    scores = [
        (i, j, proba)
        for (i, j), proba in grille.items()
    ]
    scores.sort(key=lambda x: x[2], reverse=True)
    return scores[:top]


def proba_over(
    lambda_home: float,
    lambda_away: float,
    seuil: float = 2.5,
    max_buts: int = POISSON_MAX_BUTS,
) -> float:
    """Probabilité que le total de buts dépasse ``seuil`` (Over)."""
    grille = matrice_scores(lambda_home, lambda_away, max_buts)
    return sum(proba for (i, j), proba in grille.items() if (i + j) > seuil)
