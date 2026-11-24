"""Tests des moteurs locaux des fonctionnalités 138 à 700."""

from core.fonctionnalites_700 import (
    test_ab,
    calculer_marge_nette,
    evaluer_seuil_rentabilite,
    heure_pointe_evenements,
    score_brier,
    log_loss,
    detecter_doublons_matchs,
    fraicheur_donnees,
    generer_corpus_regression,
)


def test_ab_est_reparti_stablement():
    assert test_ab(12345) in {"A", "B"}
    assert test_ab(12345) == test_ab(12345)


def test_marge_nette_retenue():
    resultat = calculer_marge_nette(10000, frais_fixe=500, frais_pourcent=5)
    assert resultat["net"] == 9000


def test_seuil_rentabilite():
    assert evaluer_seuil_rentabilite(150, 100)["rentable"] is True


def test_heure_pointe_retourne_le_top():
    heures = heure_pointe_evenements(["2026-11-23T20:00:00", "2026-11-23T20:30:00", "2026-11-23T18:00:00"])
    assert heures[0][0] == 20


def test_scores_calibrage():
    assert score_brier([0.7, 0.2], [1, 0]) > 0
    assert log_loss([0.7, 0.2], [1, 0]) > 0


def test_doublons_matchs():
    match = {"date": "2026-11-23", "home": "Mazembe", "away": "Vita", "competition": "Linafoot"}
    resultat = detecter_doublons_matchs([match, dict(match)])
    assert len(resultat["doublons"]) == 1


def test_fraicheur_donnees():
    assert fraicheur_donnees(["2026-11-23T12:00:00"], maximum_minutes=30)["fraiche"] is False


def test_corpus_regression_est_stable():
    corpus = generer_corpus_regression([{"p": 1}, {"p": 2}], graine=42)
    assert corpus["nb_cas"] == 2
    assert len(corpus["empreinte"]) == 64
