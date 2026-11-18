# tests/test_determinisme.py
"""Tests de déterminisme (631) : mêmes entrées, mêmes sorties, sans graine."""

import os
import sys

DOSSIER_TESTS = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(DOSSIER_TESTS)
for chemin in (RACINE, DOSSIER_TESTS):
    if chemin not in sys.path:
        sys.path.insert(0, chemin)

from conftest import ENV_VALIDE

# ``core.poisson`` lit quelques seuils dans ``config`` : on garantit un
# environnement minimal valide pour l'import in-process.
for _cle, _valeur in ENV_VALIDE.items():
    os.environ.setdefault(_cle, _valeur)

from core import poisson


def test_sorties_reproductibles():
    """Deux appels identiques donnent exactement le même résultat, sans graine."""
    appels = (
        lambda: poisson.matrice_scores(1.5, 1.2, max_buts=5),
        lambda: poisson.top_scores(1.5, 1.2, max_buts=5, top=5),
        lambda: poisson.proba_over(1.5, 1.2, seuil=2.5, max_buts=5),
        lambda: poisson.proba_btts(1.5, 1.2),
        lambda: poisson.proba_score(1, 2, 1.5, 1.2),
        lambda: poisson.calculer_lambdas(1.5, 1.2, 1.5, 1.2),
    )
    for appel in appels:
        assert appel() == appel()
