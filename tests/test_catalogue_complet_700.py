"""Tests de cohérence du catalogue complet 1 à 700."""

from core.catalogue_fonctionnalites import obtenir_catalogue
from core.catalogue_extensions import charger_extensions


def test_catalogue_etend_jusqu_a_700():
    catalogue = obtenir_catalogue()
    assert len(catalogue) >= 700
    assert "138" in catalogue
    assert "700" in catalogue


def test_extensions_restent_dans_la_bonne_bande():
    extensions = charger_extensions()
    numeros = {int(numero) for numero in extensions}
    assert all(138 <= numero <= 700 for numero in numeros)


def test_aucune_fonctionnalite_1_a_700_est_sans_nom():
    catalogue = obtenir_catalogue()
    for numero in range(1, 701):
        item = catalogue.get(str(numero))
        assert item is not None
        assert item["nom"].strip()
