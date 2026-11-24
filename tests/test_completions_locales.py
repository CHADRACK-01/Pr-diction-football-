"""Tests des complétions locales maximales demandées par le projet."""

import math

from core.analyses_avancees import (
    simuler_monte_carlo,
    calculer_elo_live,
    detecter_derby,
    calculer_fatigue_calendrier,
)
from core.gestion_risques import evaluer_plan_anti_perte, calculer_martingale_douce


def test_monte_carlo_est_deterministe_et_couvre_tous_resultats():
    resultat = simuler_monte_carlo(1.5, 1.2, simulations=1000, graine=42)
    assert resultat["simulations"] == 1000
    assert math.isclose(sum(resultat["probabilites"].values()), 1.0, abs_tol=0.03)
    assert set(resultat["probabilites"]) == {"1", "N", "2"}


def test_elo_live_applique_un_seul_but():
    elo = calculer_elo_live(1500, 1500, score_actuel=(1, 0), but_equipe="home")
    assert elo["home"] > 1500
    assert elo["away"] < 1500


def test_derby_mazembe_vita_est_detecte():
    assert detecter_derby("TP Mazembe", "AS Vita Club") is True


def test_fatigue_trois_matchs_en_sept_jours():
    assert calculer_fatigue_calendrier(["2026-11-18", "2026-11-21", "2026-11-24"])["epuisement"] >= 6


def test_plan_anti_perte_bloque_apres_trois_defaites():
    decision = evaluer_plan_anti_perte(["P", "P", "P"])
    assert decision["bloquer_gros_combine"] is True
    assert decision["niveau"] == "securise"


def test_martingale_douce_est_limitee():
    assert calculer_martingale_douce(1000, perte=2) == 2000
    assert calculer_martingale_douce(1000, perte=20) == 5000
