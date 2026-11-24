"""Tests des garde-fous professionnels des prédictions et mises."""

import pytest

from core.validation_prediction import (
    valider_probabilites,
    construire_libelle_prediction,
    valider_mise,
)


def test_probabilites_valides():
    assert valider_probabilites({"p_h": 0.5, "p_d": 0.25, "p_a": 0.25}) == (0.5, 0.25, 0.25)


def test_probabilites_hors_bornes_refusees():
    with pytest.raises(ValueError):
        valider_probabilites({"p_h": 1.2, "p_d": -0.1, "p_a": -0.1})


def test_somme_probabilites_refusee():
    with pytest.raises(ValueError):
        valider_probabilites({"p_h": 0.2, "p_d": 0.2, "p_a": 0.2})


def test_libelle_negarantit_pas_de_gain():
    resultat = construire_libelle_prediction({"p_h": 0.6, "p_d": 0.2, "p_a": 0.2})
    assert resultat["libelle"] == "Domicile"
    assert resultat["incertitude"] > 0


def test_mise_est_limitee_a_5_pourcent():
    assert valider_mise(600, 10000)["autorisee"] is False
    assert valider_mise(400, 10000)["autorisee"] is True
