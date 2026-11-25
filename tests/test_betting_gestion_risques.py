# tests/test_betting_gestion_risques.py
"""Tests de gestion des risques et plan anti-perte (fonctionnalités 47, 48, 54)."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from core.betting.gestion_risques import (
    checklist_avant_pari,
    filtre_reussite_par_ligue,
    plan_anti_perte,
)


def test_plan_anti_perte_cinq_pertes_bloque_tout():
    resultat = plan_anti_perte(pertes_consecutives=5)
    assert resultat["bloque"] is True
    assert resultat["mise_max_autorisee"] == 0.0
    assert "24h" in resultat["conseil"]


def test_plan_anti_perte_trois_pertes_combine_bloque():
    resultat = plan_anti_perte(
        pertes_consecutives=3, est_combine=True, mise_demandee=5000.0
    )
    assert resultat["bloque"] is True
    assert "combinés bloqués" in resultat["raison"]


def test_plan_anti_perte_trois_pertes_simple_autorise_prudent():
    resultat = plan_anti_perte(
        pertes_consecutives=3, est_combine=False, mise_demandee=10000.0
    )
    assert resultat["bloque"] is False
    assert resultat["mise_max_autorisee"] == 5000.0


def test_plan_anti_perte_zero_perte():
    resultat = plan_anti_perte(pertes_consecutives=0, mise_demandee=5000.0)
    assert resultat["bloque"] is False
    assert resultat["raison"] is None
    assert resultat["mise_max_autorisee"] == 5000.0


def test_plan_anti_perte_quatre_pertes_combine():
    resultat = plan_anti_perte(
        pertes_consecutives=4, est_combine=True, mise_demandee=5000.0
    )
    assert resultat["bloque"] is True


def test_filtre_reussite_par_ligue_autorisee():
    perf = {
        "Ligue 1": {"taux_reussite": 0.60, "nb_matchs": 50, "roi": 0.10},
    }
    resultat = filtre_reussite_par_ligue(perf, "Ligue 1")
    assert resultat["autorisee"] is True
    assert resultat["taux_reussite"] == 0.60
    assert resultat["nb_matchs"] == 50


def test_filtre_reussite_par_ligue_taux_trop_bas():
    perf = {
        "Ligue 2": {"taux_reussite": 0.40, "nb_matchs": 50, "roi": -0.05},
    }
    resultat = filtre_reussite_par_ligue(perf, "Ligue 2")
    assert resultat["autorisee"] is False
    assert "dessous du seuil" in resultat["reason"]


def test_filtre_reussite_par_ligue_pas_assez_matchs():
    perf = {
        "Ligue 3": {"taux_reussite": 0.80, "nb_matchs": 5, "roi": 0.20},
    }
    resultat = filtre_reussite_par_ligue(perf, "Ligue 3")
    assert resultat["autorisee"] is False


def test_filtre_reussite_par_ligue_inconnue():
    perf = {}
    resultat = filtre_reussite_par_ligue(perf, "Ligue Inconnue")
    assert resultat["autorisee"] is False
    assert resultat["taux_reussite"] is None
    assert "Aucune donnée historique" in resultat["reason"]


def test_checklist_avant_pari_complete():
    resultat = checklist_avant_pari(
        compo_verifiee=True,
        meteo_verifiee=True,
        mise_verifiee=True,
        bankroll_suffisante=True,
        news_equipe_verifiee=True,
    )
    assert resultat["complete"] is True
    assert resultat["elements_manquants"] == []


def test_checklist_avant_pari_incomplete():
    resultat = checklist_avant_pari(
        compo_verifiee=True,
        meteo_verifiee=False,
        mise_verifiee=True,
        bankroll_suffisante=False,
        news_equipe_verifiee=False,
    )
    assert resultat["complete"] is False
    assert "météo / pelouse" in resultat["elements_manquants"]
    assert "bankroll suffisante" in resultat["elements_manquants"]
    assert "actualités de l'équipe" in resultat["elements_manquants"]
