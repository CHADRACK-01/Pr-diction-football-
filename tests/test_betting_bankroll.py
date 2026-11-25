# tests/test_betting_bankroll.py
"""Tests de gestion de bankroll et mise Kelly (fonctionnalités 41 et 42)."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from core.betting.bankroll import (
    calculer_mise_kelly,
    plan_mise_fixe,
    plan_mise_progresif,
)
from core.domaine import Bankroll


@pytest.fixture
def bankroll_pleine():
    return Bankroll(user_id=1, montant_total=10000.0, pourcentage_mise=2.0)


@pytest.fixture
def bankroll_vide():
    return Bankroll(user_id=2, montant_total=0.0, pourcentage_mise=2.0)


def test_calculer_mise_kelly_valeur_positive(bankroll_pleine):
    resultat = calculer_mise_kelly(bankroll_pleine, proba=0.6, cote=2.5)
    assert resultat["kelly_fraction"] > 0
    assert resultat["mise_kelly"] > 0
    assert resultat["mise_recommandee"] > 0
    assert resultat["autorisee"] is True


def test_calculer_mise_kelly_ev_negatif(bankroll_pleine):
    resultat = calculer_mise_kelly(bankroll_pleine, proba=0.3, cote=2.0)
    assert resultat["kelly_fraction"] == 0.0
    assert resultat["mise_kelly"] == 0.0
    assert resultat["mise_recommandee"] == 0.0
    assert resultat["autorisee"] is False


def test_calculer_mise_kelly_plafond(bankroll_pleine):
    resultat = calculer_mise_kelly(bankroll_pleine, proba=0.9, cote=2.0, fraction_kelly=1.0)
    assert resultat["mise_recommandee"] <= bankroll_pleine.plafond_mise()


def test_calculer_mise_kelly_proba_invalide(bankroll_pleine):
    with pytest.raises(ValueError, match="entre 0 et 1"):
        calculer_mise_kelly(bankroll_pleine, proba=1.5, cote=2.0)
    with pytest.raises(ValueError, match="entre 0 et 1"):
        calculer_mise_kelly(bankroll_pleine, proba=-0.1, cote=2.0)


def test_calculer_mise_kelly_cote_invalide(bankroll_pleine):
    with pytest.raises(ValueError, match="supérieure à 1.0"):
        calculer_mise_kelly(bankroll_pleine, proba=0.5, cote=1.0)
    with pytest.raises(ValueError, match="supérieure à 1.0"):
        calculer_mise_kelly(bankroll_pleine, proba=0.5, cote=0.5)


def test_calculer_mise_kelly_fraction_invalide(bankroll_pleine):
    with pytest.raises(ValueError, match="entre 0 et 1"):
        calculer_mise_kelly(bankroll_pleine, proba=0.5, cote=2.0, fraction_kelly=1.5)


def test_calculer_mise_kelly_bankroll_vide(bankroll_vide):
    resultat = calculer_mise_kelly(bankroll_vide, proba=0.6, cote=2.5)
    assert resultat["mise_recommandee"] == 0.0
    assert resultat["autorisee"] is False


def test_plan_mise_fixe(bankroll_pleine):
    # Plafond = 2% of 10000 = 200, so 5% request gets capped
    resultat = plan_mise_fixe(bankroll_pleine, pourcentage=5.0)
    assert resultat["mise"] == 200.0  # capped by plafond
    assert resultat["pourcentage_applique"] == 5.0
    assert resultat["plafond"] == bankroll_pleine.plafond_mise()
    assert resultat["autorisee"] is True


def test_plan_mise_fixe_sous_plafond(bankroll_pleine):
    # 1% of 10000 = 100, under plafond of 200
    resultat = plan_mise_fixe(bankroll_pleine, pourcentage=1.0)
    assert resultat["mise"] == 100.0
    assert resultat["pourcentage_applique"] == 1.0


def test_plan_mise_fixe_defaut(bankroll_pleine):
    resultat = plan_mise_fixe(bankroll_pleine)
    assert resultat["pourcentage_applique"] == 2.0
    assert resultat["mise"] == 200.0


def test_plan_mise_fixe_plafond(bankroll_pleine):
    resultat = plan_mise_fixe(bankroll_pleine, pourcentage=10.0)
    assert resultat["mise"] == bankroll_pleine.plafond_mise()


def test_plan_mise_fixe_pourcentage_invalide(bankroll_pleine):
    with pytest.raises(ValueError, match="entre 0 et 10"):
        plan_mise_fixe(bankroll_pleine, pourcentage=0.0)
    with pytest.raises(ValueError, match="entre 0 et 10"):
        plan_mise_fixe(bankroll_pleine, pourcentage=15.0)


def test_plan_mise_progresif_martingale(bankroll_pleine):
    resultat = plan_mise_progresif(
        bankroll_pleine, pertes_consecutives=0, type_plan="martingale_douce"
    )
    assert resultat["multiplicateur"] == 1.0
    assert resultat["mise"] == bankroll_pleine.montant_total * 2.0 / 100.0


def test_plan_mise_progresif_martingale_apres_pertes(bankroll_pleine):
    resultat = plan_mise_progresif(
        bankroll_pleine, pertes_consecutives=2, type_plan="martingale_douce"
    )
    assert resultat["multiplicateur"] == pytest.approx(2.25)
    assert resultat["avertissement"] is None


def test_plan_mise_progresif_martingale_avertissement(bankroll_pleine):
    resultat = plan_mise_progresif(
        bankroll_pleine, pertes_consecutives=3, type_plan="martingale_douce"
    )
    assert resultat["avertissement"] is not None


def test_plan_mise_progresif_fibonacci(bankroll_pleine):
    resultat = plan_mise_progresif(
        bankroll_pleine, pertes_consecutives=0, type_plan="fibonacci"
    )
    assert resultat["multiplicateur"] == 1.0


def test_plan_mise_progresif_fibonacci_apres_pertes(bankroll_pleine):
    resultat = plan_mise_progresif(
        bankroll_pleine, pertes_consecutives=3, type_plan="fibonacci"
    )
    assert resultat["multiplicateur"] == 3.0


def test_plan_mise_progresif_plafond(bankroll_pleine):
    resultat = plan_mise_progresif(
        bankroll_pleine, pertes_consecutives=10, type_plan="martingale_douce"
    )
    assert resultat["mise"] <= bankroll_pleine.plafond_mise()


def test_bankroll_plafond_mise(bankroll_pleine):
    assert bankroll_pleine.plafond_mise() == 200.0


def test_bankroll_montant_total_negatif():
    with pytest.raises(ValueError, match="montant_total"):
        Bankroll(user_id=1, montant_total=-100.0)
