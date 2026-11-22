# tests/test_revenus.py
import os, sqlite3, sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core import revenus as rv


def _base():
    cnx = sqlite3.connect(":memory:")
    cnx.execute("""
        CREATE TABLE paiements_attente (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER, abonnement TEXT, montant INTEGER,
            statut TEXT DEFAULT 'en_attente', date_validation TEXT
        )""")
    lignes = [
        (1, "mensuel", 5000, "valide", "2026-11-01 10:00:00"),
        (2, "mensuel", 5000, "valide", "2026-11-01 18:30:00"),
        (3, "hebdo", 2000, "valide", "2026-11-03 09:00:00"),
        (4, "mensuel", 5000, "refuse", "2026-11-03 09:00:00"),
        (5, "mensuel", 5000, "en_attente", None),
        (6, "mensuel", 5000, "valide", "2026-10-31 23:59:00"),
    ]
    cnx.executemany(
        "INSERT INTO paiements_attente (user_id, abonnement, montant, statut, date_validation) "
        "VALUES (?, ?, ?, ?, ?)", lignes)
    cnx.commit()
    return cnx


def test_revenus_par_jour_ignore_refus_et_attente():
    cnx = _base()
    r = rv.revenus_par_jour(date(2026, 11, 1), date(2026, 11, 30), conn=cnx)
    assert r == [
        {"jour": "2026-11-01", "nb_paiements": 2, "total_cdf": 10000},
        {"jour": "2026-11-03", "nb_paiements": 1, "total_cdf": 2000},
    ]


def test_total_revenus():
    cnx = _base()
    assert rv.total_revenus(date(2026, 11, 1), date(2026, 11, 30), conn=cnx) == (3, 12000)


def test_periode_vide_donne_zero_et_pas_d_erreur():
    cnx = _base()
    assert rv.total_revenus(date(2025, 1, 1), date(2025, 1, 31), conn=cnx) == (0, 0)


def test_bornes_incluses():
    cnx = _base()
    # le paiement du 31/10 à 23:59 n'est pas dans novembre
    r = rv.revenus_par_jour(date(2026, 10, 31), date(2026, 10, 31), conn=cnx)
    assert r == [{"jour": "2026-10-31", "nb_paiements": 1, "total_cdf": 5000}]


def test_csv_export_format():
    cnx = _base()
    csv_txt = rv.exporter_revenus_csv(date(2026, 11, 1), date(2026, 11, 30), conn=cnx)
    lignes = csv_txt.strip().splitlines()
    assert lignes[0] == "jour;nb_paiements;total_cdf"
    assert lignes[1] == "2026-11-01;2;10000"
    assert lignes[2] == "2026-11-03;1;2000"


def test_periode_invalide_refusee():
    cnx = _base()
    try:
        rv.revenus_par_jour(date(2026, 11, 30), date(2026, 11, 1), conn=cnx)
        assert False, "aurait dû lever ValueError"
    except ValueError:
        pass
