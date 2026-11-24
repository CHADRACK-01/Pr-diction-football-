"""Tests de couverture des fonctionnalités complétées localement."""

from core.analyses_avancees import simuler_monte_carlo
from core.gestion_risques import evaluer_cashout_partiel


def test_monte_carlo_retourne_une_distribution():
    resultat = simuler_monte_carlo(1.4, 1.1, simulations=500, graine=7)
    assert resultat["simulations"] == 500
    assert sum(resultat["probabilites"].values()) >= 0.97


def test_cashout_partiel_calcule_encaissement_et_reste():
    resultat = evaluer_cashout_partiel(100, 2.0, 1.8, fraction=0.5)
    assert resultat["encaisse_immediate"] == 45.0
    assert resultat["reste_enjeu"] == 45.0
