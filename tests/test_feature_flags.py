# tests/test_feature_flags.py
"""Tests du catalogue et de l'historique des interrupteurs de fonctionnalités."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from core import feature_flags
from users import db as users_db


class _FakeDB:
    """Petite base en mémoire imitant les tables utilisées par feature_flags."""

    def __init__(self):
        self.features = {}
        self.historique = []

    def execute(self, query, params=None):
        params = list(params or [])
        q = " ".join(query.split()).lower()
        if "insert into fonctionnalites_actives" in q:
            fid = str(params[0])
            precedent = self.features.get(fid, {})
            libelle = params[2] if len(params) > 2 else None
            categorie = params[3] if len(params) > 3 else None
            proprietaire = params[4] if len(params) > 4 else None
            self.features[fid] = {
                "feature_id": fid,
                "actif": int(params[1]),
                "libelle": libelle if libelle is not None else precedent.get("libelle"),
                "categorie": categorie if categorie is not None else precedent.get("categorie"),
                "proprietaire": proprietaire if proprietaire is not None else precedent.get("proprietaire"),
                "priorite": precedent.get("priorite"),
                "date_creation": precedent.get("date_creation"),
                "date_expiration": precedent.get("date_expiration"),
            }
        elif "insert into historique_features" in q:
            self.historique.append(
                {
                    "feature_id": str(params[0]),
                    "actif": int(params[1]),
                    "auteur_id": params[2] if len(params) > 2 else None,
                }
            )
        else:
            raise AssertionError(f"Requête non gérée : {query}")

    def fetchone(self, query, params=None):
        params = list(params or [])
        q = " ".join(query.split()).lower()
        if "from fonctionnalites_actives" in q and "where feature_id" in q:
            ligne = self.features.get(str(params[0]))
            return None if ligne is None else (ligne["actif"],)
        raise AssertionError(f"Requête non gérée : {query}")

    def fetchall(self, query, params=None):
        q = " ".join(query.split()).lower()
        if "from fonctionnalites_actives" in q:
            return [
                (
                    ligne["feature_id"],
                    ligne["actif"],
                    ligne["libelle"],
                    ligne["categorie"],
                    ligne["priorite"],
                    ligne["proprietaire"],
                    ligne["date_creation"],
                    ligne["date_expiration"],
                )
                for ligne in self.features.values()
            ]
        raise AssertionError(f"Requête non gérée : {query}")


@pytest.fixture(autouse=True)
def _silence_logs(monkeypatch):
    """Neutralise l'envoi Telegram déclenché par log_error."""
    monkeypatch.setattr(feature_flags, "log_error", lambda *a, **k: None, raising=False)


@pytest.fixture
def fake_db(monkeypatch):
    base = _FakeDB()
    for nom in ("db_execute", "db_fetchone", "db_fetchall"):
        methode = getattr(base, nom.replace("db_", ""))
        monkeypatch.setattr(users_db, nom, methode)
        monkeypatch.setattr(feature_flags, nom, methode)
    return base


def test_est_active_par_defaut_false(fake_db):
    assert feature_flags.est_active("647") is False


def test_activation_idempotente(fake_db):
    feature_flags.activer_feature("647")
    feature_flags.activer_feature("647")
    assert feature_flags.lister_features() == {"647": True}
    assert feature_flags.est_active("647") is True


def test_lister_features_forme_inchangee(fake_db):
    feature_flags.activer_feature("647")
    feature_flags.desactiver_feature("648")
    resultat = feature_flags.lister_features()
    assert resultat == {"647": True, "648": False}
    assert all(isinstance(valeur, bool) for valeur in resultat.values())


def test_metadonnees_optionnelles_enregistrees(fake_db):
    feature_flags.activer_feature(
        "647", libelle="Catalogue", categorie="Gouvernance", proprietaire="admin"
    )
    infos = feature_flags.lister_catalogue()["647"]
    assert infos["libelle"] == "Catalogue"
    assert infos["categorie"] == "Gouvernance"
    assert infos["proprietaire"] == "admin"
    assert infos["actif"] is True


def test_libelle_par_defaut_si_metadonnee_absente(fake_db):
    feature_flags.activer_feature("649")
    catalogue = feature_flags.lister_catalogue()
    assert catalogue["649"]["libelle"] == "649"
    assert catalogue["649"]["categorie"] is None


def test_une_ligne_historique_par_bascule(fake_db):
    feature_flags.activer_feature("647", auteur_id=42)
    feature_flags.desactiver_feature("647", auteur_id=42)
    assert fake_db.historique == [
        {"feature_id": "647", "actif": 1, "auteur_id": 42},
        {"feature_id": "647", "actif": 0, "auteur_id": 42},
    ]


def test_appel_sans_metadonnee_sans_exception(fake_db):
    feature_flags.activer_feature("649")
    feature_flags.desactiver_feature("649")
    assert fake_db.historique[-1]["auteur_id"] is None


def test_bascule_non_bloquante_si_historique_echoue(fake_db, monkeypatch):
    def _execute_qui_echoue(query, params=None):
        if "historique_features" in query:
            raise RuntimeError("table historique absente")
        return fake_db.execute(query, params=params)

    monkeypatch.setattr(feature_flags, "db_execute", _execute_qui_echoue)
    feature_flags.activer_feature("649")
    assert feature_flags.est_active("649") is True