# tests/test_config_defauts.py
"""Tests des défauts sûrs de configuration (635).

Sans variables d'environnement optionnelles, ``config`` doit conserver des
valeurs par défaut sûres : l'import réussit et les seuils métier restent
définis.
"""

import os
import sys

DOSSIER_TESTS = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(DOSSIER_TESTS)
for chemin in (RACINE, DOSSIER_TESTS):
    if chemin not in sys.path:
        sys.path.insert(0, chemin)

from conftest import lancer_code_config

# Variables de réglage facultatives : lorsqu'elles sont absentes, ``config``
# doit appliquer ses valeurs par défaut plutôt que d'échouer.
VARIABLES_OPTIONNELLES = (
    "VALUE_BET_MIN_EV",
    "COTE_MIN_RECO",
    "SEUIL_CONF_SUR",
    "SEUIL_CONF_MODERE",
    "SEUIL_CONF_RISQUE",
    "FACTEUR_MT",
    "BANDE_OUTSIDE_MIN",
    "BANDE_OUTSIDE_MAX",
    "SEUIL_DIVERGENCE_DC",
    "COEF_AVANTAGE_TERRAIN",
    "POISSON_MAX_BUTS",
)

CODE_DEFAUTS = (
    "import config\n"
    "for nom in %r:\n"
    "    print(nom + '=' + str(getattr(config, nom)))\n"
) % (list(VARIABLES_OPTIONNELLES),)


def _valeurs_par_defaut():
    resultat = lancer_code_config(
        {nom: None for nom in VARIABLES_OPTIONNELLES}, CODE_DEFAUTS
    )
    assert resultat.returncode == 0, resultat.stderr

    valeurs = {}
    for ligne in resultat.stdout.strip().splitlines():
        nom, _, valeur = ligne.partition("=")
        valeurs[nom] = valeur
    return valeurs


def test_import_sans_variables_optionnelles():
    resultat = lancer_code_config(
        {nom: None for nom in VARIABLES_OPTIONNELLES}, CODE_DEFAUTS
    )
    assert resultat.returncode == 0, resultat.stderr


def test_seuils_metier_definis_par_defaut():
    valeurs = _valeurs_par_defaut()
    for nom in VARIABLES_OPTIONNELLES:
        assert nom in valeurs
        assert valeurs[nom] != "None"


def test_seuils_numeriques_par_defaut():
    valeurs = _valeurs_par_defaut()
    for nom in VARIABLES_OPTIONNELLES:
        float(valeurs[nom])  # lève ValueError si le défaut n'est pas numérique
