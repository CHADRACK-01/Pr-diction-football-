# tests/test_migrations.py
"""Tests des migrations (634) : ``initialiser_tables`` est idempotente."""

import os
import sqlite3
import sys

DOSSIER_TESTS = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(DOSSIER_TESTS)
for chemin in (RACINE, DOSSIER_TESTS):
    if chemin not in sys.path:
        sys.path.insert(0, chemin)

from conftest import ENV_VALIDE

# ``users.db`` lit ``config`` : on garantit un environnement minimal valide.
for _cle, _valeur in ENV_VALIDE.items():
    os.environ.setdefault(_cle, _valeur)

from users import db as users_db


def _neutraliser_journalisation(monkeypatch):
    """Évite tout envoi réseau déclenché par la journalisation."""
    for nom in ("log_info", "log_warning", "log_error"):
        monkeypatch.setattr(users_db, nom, lambda *a, **k: None, raising=False)


def _brancher_base_temporaire(monkeypatch, chemin):
    """Fait pointer ``users.db.get_connection`` vers une base sqlite locale."""
    def _get_connection():
        return sqlite3.connect(chemin)

    monkeypatch.setattr(users_db, "get_connection", _get_connection, raising=False)


def test_initialiser_tables_idempotente(monkeypatch, tmp_path):
    chemin = str(tmp_path / "migration.db")
    _neutraliser_journalisation(monkeypatch)
    _brancher_base_temporaire(monkeypatch, chemin)

    users_db.initialiser_tables()
    users_db.initialiser_tables()

    conn = sqlite3.connect(chemin)
    try:
        tables = {
            ligne[0]
            for ligne in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        colonnes_matchs = {
            ligne[1]
            for ligne in conn.execute("PRAGMA table_info(matchs)").fetchall()
        }
    finally:
        conn.close()

    assert {"utilisateurs", "matchs", "fonctionnalites_actives"} <= tables
    assert {"hs", "as_shots", "b365h"} <= colonnes_matchs


def test_ajouter_colonnes_manquantes_conserve_les_donnees(monkeypatch, tmp_path):
    chemin = str(tmp_path / "donnees.db")
    _neutraliser_journalisation(monkeypatch)
    _brancher_base_temporaire(monkeypatch, chemin)

    users_db.initialiser_tables()

    conn = sqlite3.connect(chemin)
    conn.execute(
        "INSERT INTO utilisateurs (user_id, username) VALUES (?, ?)", (1, "alice")
    )
    conn.commit()
    conn.close()

    # Rappeler la migration ne doit ni échouer ni perdre les données.
    users_db.initialiser_tables()

    conn = sqlite3.connect(chemin)
    try:
        users_db._ajouter_colonnes_manquantes(
            conn, "utilisateurs", {"nouvelle_colonne": "TEXT"}
        )
        # Deuxième passage : la colonne existe déjà, aucun doublon.
        users_db._ajouter_colonnes_manquantes(
            conn, "utilisateurs", {"nouvelle_colonne": "TEXT"}
        )
        lignes = conn.execute(
            "SELECT user_id, username FROM utilisateurs"
        ).fetchall()
        colonnes = {
            ligne[1]
            for ligne in conn.execute("PRAGMA table_info(utilisateurs)").fetchall()
        }
    finally:
        conn.close()

    assert lignes == [(1, "alice")]
    assert "nouvelle_colonne" in colonnes
