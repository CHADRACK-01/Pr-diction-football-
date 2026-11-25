# tests/test_betting_paris_builder.py
"""Tests du constructeur de paris et coupons (fonctionnalités 43, 44, 45)."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from core.betting.paris_builder import (
    assurance_combine,
    double_sur_du_jour,
    generer_combine_par_risque,
    generer_coupons_du_jour,
)


PREDICTIONS = [
    {
        "home_team": "Equipe A",
        "away_team": "Equipe B",
        "competition": "Ligue 1",
        "p_h": 0.7,
        "p_d": 0.2,
        "p_a": 0.1,
        "favori": "home",
    },
    {
        "home_team": "Equipe C",
        "away_team": "Equipe D",
        "competition": "Ligue 1",
        "p_h": 0.6,
        "p_d": 0.25,
        "p_a": 0.15,
        "favori": "home",
    },
    {
        "home_team": "Equipe E",
        "away_team": "Equipe F",
        "competition": "Ligue 2",
        "p_h": 0.4,
        "p_d": 0.3,
        "p_a": 0.3,
        "favori": "home",
    },
]


def test_generer_coupons_du_jour_vide():
    assert generer_coupons_du_jour([]) == []


def test_generer_coupons_du_jour_selection():
    coupons = generer_coupons_du_jour(PREDICTIONS, nb_coupons=2)
    assert len(coupons) == 2
    assert coupons[0]["numero"] == 1
    assert "Equipe A" in coupons[0]["match"]
    assert coupons[0]["confiance"] == "modere"


def test_generer_coupons_du_jour_confiance_risque():
    preds_risque = [
        {
            "home_team": "X",
            "away_team": "Y",
            "competition": "L1",
            "p_h": 0.5,
            "p_d": 0.3,
            "p_a": 0.2,
            "favori": "home",
        }
    ]
    coupons = generer_coupons_du_jour(preds_risque)
    assert coupons[0]["confiance"] == "risque"


def test_double_sur_du_jour_insuffisant():
    assert double_sur_du_jour([PREDICTIONS[0]]) is None


def test_double_sur_du_jour_deux_selections():
    resultat = double_sur_du_jour(PREDICTIONS)
    assert resultat is not None
    assert len(resultat["selections"]) == 2
    assert "cote_estimee" in resultat
    assert "probabilite_combinee" in resultat


def test_generer_combine_par_risque_vide():
    assert generer_combine_par_risque([], cote_cible=2.0) is None


def test_generer_combine_par_risque_cible_invalide():
    assert generer_combine_par_risque(PREDICTIONS, cote_cible=1.0) is None


def test_generer_combine_par_risque_valide():
    resultat = generer_combine_par_risque(PREDICTIONS, cote_cible=2.0)
    assert resultat is not None
    assert "selections" in resultat
    assert "cote_totale" in resultat
    assert resultat["cote_cible"] == 2.0


def test_assurance_combine_vide():
    assert assurance_combine([], mise=100.0) is None


def test_assurance_combine_mise_invalide():
    assert assurance_combine([{"cote": 2.0}], mise=0.0) is None


def test_assurance_combine_resultat():
    selections = [{"cote": 2.0}, {"cote": 1.8}, {"cote": 2.2}]
    resultat = assurance_combine(selections, mise=100.0)
    assert resultat is not None
    assert resultat["mise"] == 100.0
    assert resultat["nb_selections"] == 3
    assert "gains_par_scenario" in resultat
    assert "0_sur_3" in resultat["gains_par_scenario"]
    assert "3_sur_3" in resultat["gains_par_scenario"]
    assert resultat["gains_par_scenario"]["0_sur_3"] == 0.0
