# tests/test_predictions_regression.py
"""Régression (625) : corpus figé sur la couche pure ``core/poisson.py``.

Tolérance 1e-9. Le corpus utilise des espérances entières : après
renormalisation de la grille de Poisson, les sorties sont des fractions
exactes, ce qui rend la régression indépendante de la libm.
"""

import math
import os
import sys

DOSSIER_TESTS = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(DOSSIER_TESTS)
for chemin in (RACINE, DOSSIER_TESTS):
    if chemin not in sys.path:
        sys.path.insert(0, chemin)

from conftest import ENV_VALIDE

# ``core.poisson`` lit quelques seuils dans ``config`` : on garantit un
# environnement minimal valide pour l'import in-process.
for _cle, _valeur in ENV_VALIDE.items():
    os.environ.setdefault(_cle, _valeur)

from core import poisson

TOLERANCE = 1e-9


def test_matrice_scores_renormalisee_sur_corpus():
    for lambda_home, lambda_away, max_buts in ((1.0, 2.0, 6), (1.0, 1.0, 6)):
        grille = poisson.matrice_scores(lambda_home, lambda_away, max_buts=max_buts)
        assert abs(sum(grille.values()) - 1.0) < TOLERANCE


def test_proba_over_corpus_fige():
    # Grille 0..6 pour lambda_home=1 et lambda_away=2 : P(i+j <= 2) = 275400/647767.
    attendu = 372367 / 647767
    obtenu = poisson.proba_over(1.0, 2.0, seuil=2.5, max_buts=6)
    assert abs(obtenu - attendu) < TOLERANCE


def test_proba_btts_corpus_fige():
    # Même grille : P(i >= 1 et j >= 1) = 353782/647767.
    attendu = 353782 / 647767
    obtenu = poisson.proba_btts(1.0, 2.0, max_buts=6)
    assert abs(obtenu - attendu) < TOLERANCE


def test_proba_over_et_btts_esperances_egales():
    # Grille 0..6 pour lambda_home = lambda_away = 1.
    # total = (1957/720)^2 = 3829849/518400.
    # proba_over : P(i+j > 2.5) = 1 - 5/total = 1237849/3829849.
    obtenu_over = poisson.proba_over(1.0, 1.0, seuil=2.5, max_buts=6)
    assert abs(obtenu_over - 1237849 / 3829849) < TOLERANCE

    # proba_btts : P(i >= 1 et j >= 1) = (1237/1957)^2 = 1530169/3829849.
    obtenu_btts = poisson.proba_btts(1.0, 1.0, max_buts=6)
    assert abs(obtenu_btts - 1530169 / 3829849) < TOLERANCE
