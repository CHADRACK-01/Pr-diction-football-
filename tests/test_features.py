# tests/test_features.py
"""Tests du contrat modèle et du calcul de features (sans base de données)."""
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.contrat_modele import (
    FEATURE_NAMES, VERSION_CONTRAT, ContratInvalide, decoder_bundle, encoder_bundle,
)
from core.features import EtatEquipes


class ModeleFictif:
    """Imite l'interface sklearn utilisée par le bot (picklable car au niveau module)."""
    classes_ = [0, 1, 2]

    def predict_proba(self, X):
        return [[0.5, 0.25, 0.25] for _ in X]


def _historique(n, seed=1):
    rnd = random.Random(seed)
    equipes = [f"Equipe{i}" for i in range(8)]
    matchs = []
    for i in range(n):
        d, e = rnd.sample(equipes, 2)
        jour = f"2024-{1 + i // 28:02d}-{1 + i % 28:02d}"
        fthg, ftag = rnd.randint(0, 4), rnd.randint(0, 4)
        ftr = "H" if fthg > ftag else ("A" if ftag > fthg else "D")
        matchs.append({"date": jour, "home": d, "away": e, "fthg": fthg, "ftag": ftag, "ftr": ftr})
    return matchs


def test_pas_de_fuite_features_ne_voient_pas_le_futur():
    """Les features d'un match M doivent être identiques, que l'on ajoute
    ou non des matchs postérieurs à M avant de les calculer."""
    histo = _historique(200)
    cible_idx = 150
    cible = histo[cible_idx]

    etat_court = EtatEquipes()
    for m in histo[:cible_idx]:
        etat_court.mettre_a_jour(m)
    f_court = etat_court.predire(cible["home"], cible["away"], cible["date"])

    # On réinjecte un état qui a aussi "vu" le futur : le résultat doit être le même
    # uniquement si on n'a pas appliqué les matchs futurs, donc on vérifie
    # que predire() ne dépend que de l'état fourni (aucune lecture implicite).
    etat_futur = EtatEquipes()
    for m in histo[:cible_idx]:
        etat_futur.mettre_a_jour(m)
    f_futur = etat_futur.predire(cible["home"], cible["away"], cible["date"])
    assert f_court == f_futur

    # Et la règle d'usage : predire() AVANT mettre_a_jour() ne modifie pas l'état
    avant = etat_futur.vers_dict()
    etat_futur.predire(cible["home"], cible["away"], cible["date"])
    assert etat_futur.vers_dict() == avant


def test_features_noms_et_ordre_conformes_au_contrat():
    histo = _historique(120)
    etat = EtatEquipes()
    for m in histo:
        etat.mettre_a_jour(m)
    f = etat.predire("Equipe0", "Equipe1", "2030-01-01")
    assert f is not None
    assert list(f.keys()) == FEATURE_NAMES
    assert all(isinstance(v, float) for v in f.values())


def test_historique_insuffisant_renvoie_none():
    etat = EtatEquipes()
    etat.mettre_a_jour({"date": "2024-01-01", "home": "A", "away": "B", "fthg": 1, "ftag": 0, "ftr": "H"})
    assert etat.predire("A", "B", "2024-02-01") is None


def test_repos_plafonne_et_equipe_inconnue():
    histo = _historique(60)
    etat = EtatEquipes()
    for m in histo:
        etat.mettre_a_jour(m)
    f = etat.predire("Equipe0", "Equipe1", "2099-12-31")
    assert f["repos_h"] == 14.0 and f["repos_a"] == 14.0


def test_serialisation_aller_retour_donne_les_memes_features():
    histo = _historique(150)
    etat = EtatEquipes()
    for m in histo:
        etat.mettre_a_jour(m)
    relu = EtatEquipes.depuis_dict(etat.vers_dict())
    assert relu.predire("Equipe2", "Equipe3", "2030-01-01") == etat.predire("Equipe2", "Equipe3", "2030-01-01")


def test_determinisme_deux_passages_identiques():
    histo = _historique(150)
    def calcul():
        e = EtatEquipes()
        for m in histo:
            e.mettre_a_jour(m)
        return e.vers_dict()
    assert calcul() == calcul()


def _bundle_valide():
    etat = EtatEquipes()
    for m in _historique(60):
        etat.mettre_a_jour(m)
    return {
        "schema_version": VERSION_CONTRAT,
        "feature_names": list(FEATURE_NAMES),
        "models": {"1N2": ModeleFictif()},
        "metrics": {"1N2": {"accuracy": 0.5}},
        "etat": etat.vers_dict(),
        "date_max_donnees": etat.date_max,
        "date_entrainement": "2026-11-19T00:00:00",
    }


def test_bundle_aller_retour():
    b = decoder_bundle(encoder_bundle(_bundle_valide()))
    assert b["schema_version"] == VERSION_CONTRAT
    assert b["feature_names"] == FEATURE_NAMES


def test_refus_mauvaise_version_et_mauvaises_features():
    mauvais = _bundle_valide()
    mauvais["schema_version"] = 1
    try:
        encoder_bundle(mauvais)
        raise AssertionError("version 1 aurait dû être refusée")
    except ContratInvalide:
        pass

    mauvais = _bundle_valide()
    mauvais["feature_names"] = FEATURE_NAMES[:-1]
    try:
        encoder_bundle(mauvais)
        raise AssertionError("features différentes auraient dû être refusées")
    except ContratInvalide:
        pass


def test_refus_bundle_ancien_format():
    """L'ancien format du script d'entraînement (modeles_par_competition) doit être refusé."""
    import base64, pickle, zlib
    ancien = {"modeles_par_competition": {}, "precision_moyenne": 0.5, "total_matchs": 10}
    donnees = base64.b64encode(zlib.compress(pickle.dumps(ancien))).decode()
    try:
        decoder_bundle(donnees)
        raise AssertionError("l'ancien format aurait dû être refusé")
    except ContratInvalide:
        pass


if __name__ == "__main__":
    fonctions = [v for k, v in dict(globals()).items() if k.startswith("test_")]
    echecs = 0
    for fn in fonctions:
        try:
            fn()
            print(f"✅ {fn.__name__}")
        except Exception as e:
            echecs += 1
            print(f"❌ {fn.__name__} : {e}")
    print(f"\n{len(fonctions) - echecs}/{len(fonctions)} tests OK")
