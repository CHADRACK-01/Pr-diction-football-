"""Tests du catalogue complet des fonctionnalités 1 à 137."""

from core.catalogue_fonctionnalites import (
    obtenir_catalogue,
    obtenir_fonctionnalite,
    lister_par_statut,
)


def test_catalogue_contient_les_137_fonctionnalites():
    catalogue = obtenir_catalogue()
    assert len(catalogue) == 137
    assert set(catalogue) == {str(numero) for numero in range(1, 138)}


def test_fonctionnalites_requises_sont_documentees():
    for numero in range(1, 138):
        item = obtenir_fonctionnalite(numero)
        assert item["nom"]
        assert item["groupe"]
        assert item["statut"] in {"complete", "partielle", "a_implanter"}


def test_filtrage_du_catalogue_par_statut():
    catalogue = lister_par_statut("complete")
    assert catalogue
    assert all(item["statut"] == "complete" for item in catalogue)
