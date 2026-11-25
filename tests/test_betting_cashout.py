# tests/test_betting_cashout.py
"""Tests du simulateur de cash-out (fonctionnalités 5 et 46)."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from core.betting.cashout import (
    calculer_cashout,
    calculer_cashout_partiel,
    est_interessant_cashout,
)


def test_calculer_cashout_total_gain():
    mise = 1000.0
    cote_initiale = 2.0
    cote_actuelle = 1.5
    resultat = calculer_cashout(mise, cote_initiale, cote_actuelle)
    assert resultat["mise"] == 1000.0
    assert resultat["gain_potentiel"] == 2000.0
    assert resultat["montant_cashout"] == 750.0
    assert resultat["benefice_net"] == -250.0


def test_calculer_cashout_cote_baissse_perte():
    resultat = calculer_cashout(500.0, 3.0, 2.0)
    assert resultat["montant_cashout"] == 333.33
    assert resultat["benefice_net"] == -166.67


def test_calculer_cashout_cote_augmente_gain():
    resultat = calculer_cashout(1000.0, 2.0, 3.0)
    assert resultat["montant_cashout"] == 1500.0
    assert resultat["benefice_net"] == 500.0


def test_calculer_cashout_mise_invalide():
    with pytest.raises(ValueError, match="strictement positive"):
        calculer_cashout(0.0, 2.0, 2.0)
    with pytest.raises(ValueError, match="strictement positive"):
        calculer_cashout(-100.0, 2.0, 2.0)


def test_calculer_cashout_cote_invalide():
    with pytest.raises(ValueError, match="> 1.0"):
        calculer_cashout(1000.0, 1.0, 2.0)
    with pytest.raises(ValueError, match="> 1.0"):
        calculer_cashout(1000.0, 2.0, 0.5)


def test_calculer_cashout_partiel():
    resultat = calculer_cashout_partiel(
        mise=1000.0,
        cote_initiale=2.0,
        cote_actuelle=1.5,
        fraction=0.5,
    )
    assert resultat["montant_encaisse"] == 375.0
    assert resultat["mise_restante"] == 500.0
    assert resultat["benefice_partiel"] == -125.0


def test_calculer_cashout_partiel_fraction_invalide():
    with pytest.raises(ValueError, match="entre 0 et 1"):
        calculer_cashout_partiel(1000.0, 2.0, 2.0, 0.0)
    with pytest.raises(ValueError, match="entre 0 et 1"):
        calculer_cashout_partiel(1000.0, 2.0, 2.0, 1.5)


def test_calculer_cashout_partiel_fraction_un():
    resultat = calculer_cashout_partiel(
        mise=1000.0,
        cote_initiale=2.0,
        cote_actuelle=1.5,
        fraction=1.0,
    )
    assert resultat["montant_encaisse"] == 750.0
    assert resultat["mise_restante"] == 0.0


def test_est_interessant_cashout_ratio_suffisant():
    assert est_interessant_cashout(2.0, 1.8, seuil_min=0.8) is True
    assert est_interessant_cashout(2.0, 1.5, seuil_min=0.7) is True


def test_est_interessant_cashout_ratio_insuffisant():
    assert est_interessant_cashout(2.0, 1.0, seuil_min=1.1) is False
    assert est_interessant_cashout(2.0, 1.5, seuil_min=0.9) is False


def test_est_interessant_cashout_cote_invalide():
    assert est_interessant_cashout(1.0, 2.0) is False
    assert est_interessant_cashout(2.0, 1.0) is False
