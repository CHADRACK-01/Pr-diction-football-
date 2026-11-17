# tests/test_value_bet.py
"""Tests du calcul unifié du value bet et des seuils prédictifs."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

import config
from core import value_bet
from core.value_bet import calculer_ev, est_value_bet, analyser_value_bet


@pytest.fixture(autouse=True)
def _silence_logs(monkeypatch):
    """Neutralise l'envoi Telegram déclenché par log_warning."""
    monkeypatch.setattr(value_bet, "log_warning", lambda *a, **k: None)


def test_calculer_ev_signe():
    assert calculer_ev(0.5, 2.5) == pytest.approx(0.25)
    assert calculer_ev(0.5, 2.0) == pytest.approx(0.0)
    assert calculer_ev(0.5, 1.5) == pytest.approx(-0.25)


def test_est_value_bet_seuil_configure_et_surchargeable():
    # EV = 0.5 * 2.5 - 1 = 0.25 > VALUE_BET_MIN_EV (0.05)
    assert est_value_bet(0.5, 2.5) is True
    # EV = 0.5 * 2.05 - 1 = 0.025 < 0.05
    assert est_value_bet(0.5, 2.05) is False
    # Surcharge du seuil vers le bas : l'issue devient un value bet
    assert est_value_bet(0.5, 2.05, seuil=0.01) is True
    # Surcharge du seuil vers le haut : l'issue n'est plus un value bet
    assert est_value_bet(0.5, 2.5, seuil=0.5) is False


def test_est_value_bet_entrees_invalides():
    assert est_value_bet(0.5, 1.0) is False
    assert est_value_bet(0.5, 0.99) is False
    assert est_value_bet(0.5, None) is False
    assert est_value_bet(1.5, 3.0) is False
    assert est_value_bet(-0.1, 3.0) is False


def test_analyser_value_bet_invalides_retourne_none():
    assert analyser_value_bet(0.5, 1.0) is None
    assert analyser_value_bet(0.5, 0.99) is None
    assert analyser_value_bet(1.2, 3.0) is None
    assert analyser_value_bet(-0.2, 3.0) is None


def test_analyser_value_bet_cles_attendues():
    analyse = analyser_value_bet(0.5, 2.5, "1 (Domicile)")
    assert set(analyse) == {"label", "proba", "cote_bot", "cote_book", "is_value"}
    assert analyse["label"] == "1 (Domicile)"
    assert analyse["is_value"] is True
    assert analyse["cote_bot"] == pytest.approx(2.0)
    assert analyse["cote_book"] == pytest.approx(2.5)


def test_verdict_unifie_paris_builder_nouveau_prediction():
    from core import paris_builder, nouveau_prediction

    # Les deux modules partagent la même implémentation pure
    assert paris_builder.est_value_bet is value_bet.est_value_bet
    assert nouveau_prediction.analyser_value_bet is value_bet.analyser_value_bet

    for proba, cote in [(0.5, 2.5), (0.5, 2.05), (0.6, 1.5), (0.7, 1.6)]:
        verdict_builder = paris_builder.est_value_bet(proba, cote)
        analyse = nouveau_prediction.analyser_value_bet(proba, cote)
        assert verdict_builder == analyse["is_value"]


def test_config_hors_bornes_leve_runtimeerror(monkeypatch):
    monkeypatch.setattr(config, "_ERREURS_ENV", [])
    monkeypatch.setenv("SEUIL_CONF_SUR", "5.0")

    valeur = config._lire_flottant("SEUIL_CONF_SUR", 0.75, 0.0, 1.0)
    assert valeur is None
    assert config._ERREURS_ENV

    # Variables critiques neutralisées pour isoler l'échec des seuils
    monkeypatch.setattr(config, "TOKEN", "x")
    monkeypatch.setattr(config, "TURSO_URL", "x")
    monkeypatch.setattr(config, "TURSO_TOKEN", "x")
    monkeypatch.setattr(config, "ADMIN_ID", 1)
    monkeypatch.setattr(config, "CANAL_ID", -100)

    with pytest.raises(RuntimeError):
        config.verifier_configuration()
