"""Contrats de sécurité du runtime du catalogue complet."""

from core.runtime_700 import executer_fonctionnalite


def test_fonction_connue_retourne_un_contrat():
    resultat = executer_fonctionnalite(31)
    assert resultat["feature_id"] == "31"
    assert resultat["etat"] in {"pret", "provider_disponible", "en_attente_configuration"}


def test_fonction_inconnue_ne_plante_pas():
    resultat = executer_fonctionnalite(9999)
    assert resultat["etat"] == "invalide"


def test_limite_catalogue_est_validee():
    for feature_id in (1, 137, 138, 700):
        resultat = executer_fonctionnalite(feature_id)
        assert resultat["feature_id"] == str(feature_id)
