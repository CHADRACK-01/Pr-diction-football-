# tests/test_config.py
"""Tests de sécurité de la configuration : aucun identifiant en dur."""

import os
import sys

DOSSIER_TESTS = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(DOSSIER_TESTS)
for chemin in (RACINE, DOSSIER_TESTS):
    if chemin not in sys.path:
        sys.path.insert(0, chemin)

from conftest import lancer_code_config, lancer_import_config


def test_admin_id_absent_bloque_le_demarrage():
    resultat = lancer_import_config({"ADMIN_ID": None})
    assert resultat.returncode != 0
    assert "ADMIN_ID" in resultat.stderr


def test_admin_id_non_numerique_bloque_le_demarrage():
    resultat = lancer_import_config({"ADMIN_ID": "abc"})
    assert resultat.returncode != 0
    assert "ADMIN_ID" in resultat.stderr


def test_admin_id_valide_est_conserve():
    resultat = lancer_code_config(
        {"ADMIN_ID": "123456789"}, "import config; print(config.ADMIN_ID)"
    )
    assert resultat.returncode == 0
    assert resultat.stdout.strip() == "123456789"


def test_canal_id_absent_bloque_le_demarrage():
    resultat = lancer_import_config({"CANAL_ID": None})
    assert resultat.returncode != 0
    assert "CANAL_ID" in resultat.stderr


def test_canal_id_username_conserve_en_chaine():
    resultat = lancer_code_config(
        {"CANAL_ID": "@canal"}, "import config; print(config.CANAL_ID)"
    )
    assert resultat.returncode == 0
    assert resultat.stdout.strip() == "@canal"


def test_canal_id_numerique_converti_en_entier():
    resultat = lancer_code_config(
        {"CANAL_ID": "-100123"}, "import config; print(config.CANAL_ID)"
    )
    assert resultat.returncode == 0
    assert resultat.stdout.strip() == "-100123"


def test_telegram_token_vide_bloque_le_demarrage():
    resultat = lancer_import_config({"TELEGRAM_TOKEN": ""})
    assert resultat.returncode != 0
    assert "TELEGRAM_TOKEN" in resultat.stderr


def test_turso_vide_bloque_le_demarrage():
    for variable in ("TURSO_URL", "TURSO_TOKEN"):
        resultat = lancer_import_config({variable: ""})
        assert resultat.returncode != 0
        assert variable in resultat.stderr


def test_aucun_identifiant_en_dur_dans_config():
    with open(os.path.join(RACINE, "config.py"), encoding="utf-8") as fichier:
        source = fichier.read()
    assert "8653408729" not in source
    assert "-1003999473611" not in source
