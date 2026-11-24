# core/poisson.py
"""Calculs de probabilités par la loi de Poisson.

Module pur : aucune base de données, aucun accès réseau. Toutes les
probabilités manipulées ou retournées sont exprimées en 0-1.
"""

import math

try:
    from config import COEF_AVANTAGE_TERRAIN, POISSON_MAX_BUTS
except Exception:  # pragma: no cover - hors application (config indisponible)
    # Valeurs par défaut documentées : le module reste utilisable seul.
    COEF_AVANTAGE_TERRAIN = 0.10
    POISSON_MAX_BUTS = 5

# Espérance de buts minimale : une équipe ne peut pas être parfaitement nulle.
LAMBDA_MIN = 0.5


def proba_poisson(k, lamb):
    """Probabilité d'observer exactement ``k`` buts pour une espérance ``lamb``."""
    if lamb < 0:
        raise ValueError("lambda doit être positif ou nul")
    return (lamb ** k) * math.exp(-lamb) / math.factorial(k)


def calculer_lambdas(bm_h, bm_a, be_h, be_a, coef_avantage_terrain=COEF_AVANTAGE_TERRAIN):
    """
    Espérances de buts corrigées par la défense adverse et l'avantage du terrain.

    ``bm_h``/``bm_a`` sont les buts marqués moyens, ``be_h``/``be_a`` les buts
    encaissés moyens. L'attaque d'une équipe est moyennée avec la défense de
    l'adversaire ; seul le camp à domicile bénéficie de l'avantage du terrain.
    """
    lambda_home = (bm_h + be_a) / 2 * (1 + coef_avantage_terrain)
    lambda_away = (bm_a + be_h) / 2
    return max(LAMBDA_MIN, lambda_home), max(LAMBDA_MIN, lambda_away)


def proba_score(i, j, lambda_home, lambda_away):
    """Probabilité (0-1) du score exact ``i``-``j``."""
    return proba_poisson(i, lambda_home) * proba_poisson(j, lambda_away)


def matrice_scores(lambda_home, lambda_away, max_buts=POISSON_MAX_BUTS):
    """
    Grille ``(i, j) -> probabilité`` renormalisée (somme = 1).

    La troncature à ``max_buts`` abandonne une masse de probabilité
    résiduelle ; la renormalisation garantit une loi de probabilité complète.
    """
    grille = {}
    total = 0.0
    for i in range(max_buts + 1):
        for j in range(max_buts + 1):
            proba = proba_score(i, j, lambda_home, lambda_away)
            grille[(i, j)] = proba
            total += proba
    if total <= 0:
        raise ValueError("Somme des probabilités nulle : renormalisation impossible")
    return {score: proba / total for score, proba in grille.items()}


def top_scores(lambda_home, lambda_away, max_buts=POISSON_MAX_BUTS, top=3):
    """Scores exacts les plus probables : tuples ``(i, j, p)`` en 0-1."""
    grille = matrice_scores(lambda_home, lambda_away, max_buts=max_buts)
    classement = sorted(
        ((i, j, proba) for (i, j), proba in grille.items()),
        key=lambda score: score[2],
        reverse=True,
    )
    return classement[:top]


def proba_over(lambda_home, lambda_away, seuil=2.5, max_buts=POISSON_MAX_BUTS):
    """Probabilité (0-1) que le total de buts du match dépasse ``seuil``."""
    grille = matrice_scores(lambda_home, lambda_away, max_buts=max_buts)
    return sum(proba for (i, j), proba in grille.items() if i + j > seuil)


def proba_btts(lambda_home, lambda_away, max_buts=POISSON_MAX_BUTS):
    """Probabilité (0-1) que les deux équipes marquent au moins un but."""
    grille = matrice_scores(lambda_home, lambda_away, max_buts=max_buts)
    return sum(proba for (i, j), proba in grille.items() if i > 0 and j > 0)
