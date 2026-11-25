# tests/test_core_existant.py
"""
Tests des modules core existants et fonctionnels.

Conformément à la section 12 du référentiel REGLES_ET_METHODES.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from core.betting.value_bet import analyser_value_bet, calculer_ev, est_value_bet
from core.config_adaptateurs import ConfigAdaptateurs, charger_config_adaptateurs
from core.domaine import (
    Bankroll,
    Match,
    Probabilites1N2,
    Utilisateur,
)
from core.exceptions import (
    ApiExterneError,
    BotException,
    ConfigurationError,
    CoteInvalideError,
    FonctionnaliteInconnueError,
    ModeleIndisponibleError,
    PariError,
    QuotaApiDepasseError,
)
from core.feature_registry import (
    lister_non_implantees,
    lister_par_groupe,
    lister_requerant_dependance,
    obtenir_fonctionnalite,
    obtenir_statut_global,
)
from core.predictions.poisson import (
    calculer_lambdas,
    matrice_scores,
    proba_1n2,
    proba_btts,
    proba_over,
    proba_over_under,
    proba_poisson,
    top_scores,
)

# ---------------------------------------------------------------------------
# Tests du calcul value bet
# ---------------------------------------------------------------------------

class TestValueBet:
    def test_calculer_ev_positif(self):
        assert calculer_ev(0.60, 2.0) == pytest.approx(0.20)

    def test_calculer_ev_negatif(self):
        assert calculer_ev(0.40, 2.0) == pytest.approx(-0.20)

    def test_est_value_bet_oui(self):
        assert est_value_bet(0.60, 2.10) is True

    def test_est_value_bet_non(self):
        assert est_value_bet(0.40, 2.10) is False

    def test_est_value_bet_cote_invalide(self):
        assert est_value_bet(0.60, 1.0) is False
        assert est_value_bet(0.60, 0.5) is False
        assert est_value_bet(0.60, None) is False

    def test_est_value_bet_proba_hors_bornes(self):
        assert est_value_bet(1.5, 2.0) is False
        assert est_value_bet(-0.1, 2.0) is False
        assert est_value_bet(None, 2.0) is False

    def test_analyser_value_bet_retourne_dict(self):
        r = analyser_value_bet(0.60, 2.10, "1 (Domicile)")
        assert r is not None
        assert r["label"] == "1 (Domicile)"
        assert r["proba"] == 0.60
        assert r["cote_book"] == 2.10
        assert r["is_value"] is True
        assert "ev" in r

    def test_analyser_value_bet_cote_invalide_retourne_none(self):
        assert analyser_value_bet(0.60, 1.0, "1") is None
        assert analyser_value_bet(None, 2.0, "1") is None


# ---------------------------------------------------------------------------
# Tests de la loi de Poisson
# ---------------------------------------------------------------------------

class TestPoisson:
    def test_proba_poisson_somme(self):
        total = sum(proba_poisson(k, 2.5) for k in range(0, 11))
        assert abs(total - 1.0) < 0.01

    def test_proba_poisson_zero(self):
        assert proba_poisson(0, 0.0) == 1.0

    def test_proba_poisson_lamb_negatif(self):
        with pytest.raises(ValueError):
            proba_poisson(1, -1.0)

    def test_calculer_lambdas(self):
        lh, la = calculer_lambdas(1.5, 1.2, 1.0, 0.8)
        assert lh > 0
        assert la > 0

    def test_matrice_scores_somme_un(self):
        grille = matrice_scores(1.5, 1.2, max_buts=5)
        total = sum(grille.values())
        assert abs(total - 1.0) < 1e-9

    def test_proba_1n2(self):
        res = proba_1n2(1.5, 1.2)
        assert "p_h" in res
        assert "p_d" in res
        assert "p_a" in res
        assert abs(res["p_h"] + res["p_d"] + res["p_a"] - 1.0) < 1e-9

    def test_proba_over_under(self):
        res = proba_over_under(1.5, 1.2, 2.5)
        assert "over" in res
        assert "under" in res
        assert abs(res["over"] + res["under"] - 1.0) < 1e-9

    def test_proba_btts(self):
        res = proba_btts(1.5, 1.2)
        assert "btts_oui" in res
        assert "btts_non" in res
        assert abs(res["btts_oui"] + res["btts_non"] - 1.0) < 1e-9

    def test_top_scores(self):
        scores = top_scores(1.5, 1.2, top=3)
        assert len(scores) == 3
        assert scores[0][2] >= scores[1][2] >= scores[2][2]

    def test_proba_over(self):
        p = proba_over(1.5, 1.2, 2.5)
        assert 0.0 <= p <= 1.0


# ---------------------------------------------------------------------------
# Tests des dataclasses du domaine
# ---------------------------------------------------------------------------

class TestDomaine:
    def test_match_valide(self):
        m = Match(
            home_team="Real Madrid",
            away_team="Barcelone",
            competition="Liga",
            date="2024-01-15",
            cote_home=2.1,
        )
        assert m.home_team == "Real Madrid"
        assert m.cote_home == 2.1

    def test_match_cote_invalide(self):
        with pytest.raises(ValueError):
            Match(home_team="A", away_team="B", competition="C", date="2024-01-01", cote_home=0.5)

    def test_match_equipe_vide(self):
        with pytest.raises(ValueError):
            Match(home_team="", away_team="B", competition="C", date="2024-01-01")

    def test_probabilites1N2_valide(self):
        p = Probabilites1N2(p_home=0.5, p_draw=0.3, p_away=0.2)
        assert p.favori == "home"
        assert p.confiance == 0.5

    def test_probabilites1N2_somme_invalide(self):
        with pytest.raises(ValueError):
            Probabilites1N2(p_home=0.5, p_draw=0.5, p_away=0.5)

    def test_probabilites1N2_hors_bornes(self):
        with pytest.raises(ValueError):
            Probabilites1N2(p_home=1.5, p_draw=0.0, p_away=0.0)

    def test_bankroll_plafond(self):
        b = Bankroll(user_id=1, montant_total=100000, pourcentage_mise=2.0)
        assert b.plafond_mise() == 2000.0

    def test_bankroll_montant_negatif(self):
        with pytest.raises(ValueError):
            Bankroll(user_id=1, montant_total=-100)

    def test_utilisateur_est_premium(self):
        u = Utilisateur(user_id=1, statut="premium", date_expiration="2025-12-31")
        assert u.est_premium is True
        u2 = Utilisateur(user_id=2, statut="free")
        assert u2.est_premium is False


# ---------------------------------------------------------------------------
# Tests des exceptions
# ---------------------------------------------------------------------------

class TestExceptions:
    def test_bot_exception_to_dict(self):
        e = BotException("Test erreur", code="ERR_TEST", details={"cle": "valeur"})
        d = e.to_dict()
        assert d["exception"] == "BotException"
        assert d["code"] == "ERR_TEST"
        assert d["message"] == "Test erreur"
        assert d["details"] == {"cle": "valeur"}

    def test_configuration_error_herite_bot_exception(self):
        assert issubclass(ConfigurationError, BotException)

    def test_modele_indisponible_herite_bot_exception(self):
        assert issubclass(ModeleIndisponibleError, BotException)

    def test_pari_error_herite_bot_exception(self):
        assert issubclass(PariError, BotException)

    def test_cote_invalide_herite_pari_error(self):
        assert issubclass(CoteInvalideError, PariError)

    def test_api_externe_herite_bot_exception(self):
        assert issubclass(ApiExterneError, BotException)

    def test_quota_depasse_herite_api_externe(self):
        assert issubclass(QuotaApiDepasseError, ApiExterneError)

    def test_fonctionnalite_inconnue_herite_bot_exception(self):
        assert issubclass(FonctionnaliteInconnueError, BotException)


# ---------------------------------------------------------------------------
# Tests du registre des fonctionnalités
# ---------------------------------------------------------------------------

class TestFeatureRegistry:
    def test_obtenir_statut_global_retourne_dict(self):
        statut = obtenir_statut_global()
        assert isinstance(statut, dict)
        assert len(statut) > 0

    def test_obtenir_fonctionnalite_existante(self):
        info = obtenir_fonctionnalite("2")
        assert info["nom"] == "Détecteur de Value Bet"
        assert "statut_impl" in info
        assert "dependances_externes" in info

    def test_obtenir_fonctionnalite_inexistante(self):
        with pytest.raises(KeyError):
            obtenir_fonctionnalite("99999")

    def test_lister_non_implantees(self):
        non_impl = lister_non_implantees()
        assert isinstance(non_impl, list)
        for f in non_impl:
            assert f["statut_impl"] == "a_implanter"

    def test_lister_par_groupe(self):
        paris = lister_par_groupe("Paris")
        assert isinstance(paris, list)
        for f in paris:
            assert f["groupe"] == "Paris"

    def test_lister_requerant_dependance(self):
        api_deps = lister_requerant_dependance("api_football")
        assert isinstance(api_deps, list)
        assert len(api_deps) >= 0


# ---------------------------------------------------------------------------
# Tests de la configuration des adaptateurs
# ---------------------------------------------------------------------------

class TestConfigAdaptateurs:
    def test_charger_config_retourne_config(self):
        cfg = charger_config_adaptateurs()
        assert isinstance(cfg, ConfigAdaptateurs)

    def test_sportif_non_configuré_sans_cle(self):
        with patch.dict("os.environ", {"API_FOOTBALL_KEY_1": "", "API_FOOTBALL_KEY_2": ""}, clear=True):
            cfg = charger_config_adaptateurs()
            assert cfg.sportif_configuré() is False

    def test_sportif_configuré_avec_cle(self):
        with patch.dict("os.environ", {"API_FOOTBALL_KEY_1": "abc123"}, clear=True):
            cfg = charger_config_adaptateurs()
            assert cfg.sportif_configuré() is True

    def test_paiement_non_configuré(self):
        with patch.dict("os.environ", {"AIRTEL_API_KEY": "", "AIRTEL_API_URL": ""}, clear=True):
            cfg = charger_config_adaptateurs()
            assert cfg.paiement_configuré("airtel") is False

    def test_meteo_non_configuré(self):
        with patch.dict("os.environ", {"OPENWEATHER_API_KEY": ""}, clear=True):
            cfg = charger_config_adaptateurs()
            assert cfg.meteo_configuré() is False

    def test_audio_non_configuré(self):
        with patch.dict("os.environ", {"TTS_API_KEY": ""}, clear=True):
            cfg = charger_config_adaptateurs()
            assert cfg.audio_configuré() is False

    def test_calendrier_non_configuré(self):
        with patch.dict("os.environ", {"GOOGLE_CALENDAR_CREDENTIALS": "", "GOOGLE_CALENDAR_API_KEY": ""}, clear=True):
            cfg = charger_config_adaptateurs()
            assert cfg.calendrier_configuré() is False

    def test_reseaux_sociaux_non_configurés(self):
        with patch.dict("os.environ", {"TELEGRAM_TOKEN": "", "CANAL_ID": ""}, clear=True):
            cfg = charger_config_adaptateurs()
            assert cfg.reseaux_sociaux_configurés() is False
