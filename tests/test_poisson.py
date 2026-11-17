# tests/test_poisson.py
"""Tests du module pur ``core/poisson.py`` : probabilités en 0-1."""

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


def test_matrice_scores_renormalisee():
    grille = poisson.matrice_scores(1.5, 1.2, max_buts=5)
    assert abs(sum(grille.values()) - 1.0) < 1e-9
    assert all(0.0 <= proba <= 1.0 for proba in grille.values())


def test_proba_score_est_un_produit():
    attendu = poisson.proba_poisson(1, 1.5) * poisson.proba_poisson(2, 1.2)
    assert poisson.proba_score(1, 2, 1.5, 1.2) == attendu


def test_top_scores_decroissants_et_en_01():
    classement = poisson.top_scores(1.5, 1.2, max_buts=5, top=5)
    assert len(classement) == 5
    probas = [proba for _, _, proba in classement]
    assert probas == sorted(probas, reverse=True)
    assert all(0.0 <= proba <= 1.0 for proba in probas)


def test_over_plus_under_egale_un():
    grille = poisson.matrice_scores(1.4, 1.1, max_buts=5)
    over = poisson.proba_over(1.4, 1.1, seuil=2.5, max_buts=5)
    under = sum(proba for (i, j), proba in grille.items() if i + j <= 2)
    assert abs(over + under - 1.0) < 1e-9


def test_proba_over_croissante_avec_lambda():
    faible = poisson.proba_over(0.8, 0.8)
    forte = poisson.proba_over(2.5, 2.5)
    assert forte > faible


def test_proba_btts_entre_zero_et_un():
    proba = poisson.proba_btts(1.5, 1.2)
    assert 0.0 <= proba <= 1.0


def test_lambdas_corrigees_par_defense_adverse():
    fermee = poisson.calculer_lambdas(1.5, 1.2, 0.5, 0.5)
    ouverte = poisson.calculer_lambdas(1.5, 1.2, 2.5, 2.5)
    assert ouverte[0] > fermee[0]
    assert ouverte[1] > fermee[1]


def test_avantage_terrain_applique_au_domicile_seulement():
    avec = poisson.calculer_lambdas(1.5, 1.2, 1.5, 1.2, coef_avantage_terrain=0.10)
    sans = poisson.calculer_lambdas(1.5, 1.2, 1.5, 1.2, coef_avantage_terrain=0.0)
    assert avec[0] > sans[0]
    assert avec[1] == sans[1]
