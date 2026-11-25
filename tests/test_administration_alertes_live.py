# tests/test_administration_alertes_live.py
"""Tests des alertes live (core/administration/alertes_live.py)."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from core.administration.alertes_live import formater_alerte_but


def test_formater_alerte_but_complet():
    message = formater_alerte_but(
        match_home="TP Mazembe",
        match_away="Vita Club",
        score_home=2,
        score_away=1,
        buteur="Muleka",
        minute=67,
    )
    assert "BUT" in message
    assert "TP Mazembe 2 - 1 Vita Club" in message
    assert "Muleka" in message
    assert "67'" in message


def test_formater_alerte_but_sans_buteur():
    message = formater_alerte_but(
        match_home="Equipe A",
        match_away="Equipe B",
        score_home=1,
        score_away=0,
    )
    assert "Buteur inconnu" in message


def test_formater_alerte_but_sans_minute():
    message = formater_alerte_but(
        match_home="Equipe A",
        match_away="Equipe B",
        score_home=1,
        score_away=0,
        buteur="Dupont",
    )
    assert "Dupont" in message
    assert "'" not in message.split("Dupont")[1].split("\n")[0]
