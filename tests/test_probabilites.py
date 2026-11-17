# tests/test_probabilites.py
"""Tests des probabilités de ``core.nouveau_prediction``."""

import os
import sys

DOSSIER_TESTS = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(DOSSIER_TESTS)
for chemin in (RACINE, DOSSIER_TESTS):
    if chemin not in sys.path:
        sys.path.insert(0, chemin)

from conftest import ENV_VALIDE

for _cle, _valeur in ENV_VALIDE.items():
    os.environ.setdefault(_cle, _valeur)

import config
from core import nouveau_prediction

FEATS = {"bm_h": 1.5, "bm_a": 1.2, "be_h": 1.3, "be_a": 1.1}


def _preparer(monkeypatch, models=None, features=None):
    monkeypatch.setattr(
        nouveau_prediction, "_get_team_features", lambda h, a: dict(FEATS)
    )
    monkeypatch.setattr(
        nouveau_prediction, "_probas_1n2", lambda modele, X: (0.5, 0.3, 0.2)
    )
    monkeypatch.setattr(nouveau_prediction, "_get_h2h", lambda h, a: [])
    monkeypatch.setattr(
        nouveau_prediction,
        "global_model_data",
        {
            "models": models if models is not None else {"1N2": object()},
            "features": features if features is not None else list(FEATS),
        },
    )


def test_dc_derivees_du_1n2(monkeypatch):
    _preparer(monkeypatch)
    resultat = nouveau_prediction.predire_match_v2("A", "B")
    assert abs(resultat["dc_1x"] - (resultat["p_h"] + resultat["p_d"])) < 1e-12
    assert abs(resultat["dc_x2"] - (resultat["p_d"] + resultat["p_a"])) < 1e-12
    assert abs(resultat["dc_12"] - (resultat["p_h"] + resultat["p_a"])) < 1e-12


def test_divergence_dc_journalisee(monkeypatch):
    _preparer(monkeypatch, models={"1N2": object(), "DC_1X": object()})
    monkeypatch.setattr(config, "SEUIL_DIVERGENCE_DC", 0.05)
    monkeypatch.setattr(
        nouveau_prediction, "_proba_classe_positive", lambda modele, X: 0.95
    )
    avertissements = []
    monkeypatch.setattr(
        nouveau_prediction,
        "log_warning",
        lambda message, *a, **k: avertissements.append(message),
    )
    resultat = nouveau_prediction.predire_match_v2("A", "B")
    # dc_1x reste dérivé du 1N2 malgré la divergence du modèle DC_1X
    assert abs(resultat["dc_1x"] - 0.8) < 1e-12
    assert avertissements


def test_feature_manquante_renvoie_une_erreur(monkeypatch):
    _preparer(monkeypatch, features=list(FEATS) + ["feature_absente"])
    erreurs = []
    monkeypatch.setattr(
        nouveau_prediction, "log_error", lambda message, *a, **k: erreurs.append(message)
    )
    resultat = nouveau_prediction.predire_match_v2("A", "B")
    assert "erreur" in resultat
    assert erreurs


def test_get_matrice_poisson_cles_stables(monkeypatch):
    monkeypatch.setattr(
        nouveau_prediction, "_get_team_features", lambda h, a: dict(FEATS)
    )
    matrice = nouveau_prediction.get_matrice_poisson("A", "B")
    assert set(matrice) == {
        "lambda_home",
        "lambda_away",
        "top_scores",
        "proba_over_25",
        "proba_btts",
    }
    assert all({"score", "proba"} <= set(score) for score in matrice["top_scores"])
