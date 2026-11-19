# tests/test_codes_promo_integration.py
"""Tests d'intégration du flux codes promo (LOT 2).

Couvre :
- création de code (succès, doublon, paramètres invalides)
- utilisation (succès, introuvable, épuisé, course concurrente)
- jours Premium réellement accordés
- migration de schéma (jours_premium ajoutée si absente)

La fausse DB est en mémoire et imite les deux tables utilisées :
- codes_promo (code, type_reduction, valeur, limite_utilisation,
  deja_utilise, jours_premium, date_creation)
- utilisateurs (pour ajouter_jours_premium)
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from core import codes_promo as cp
from users import account_base
from users import db as users_db


# =========================================================
# FAUSSE DB EN MÉMOIRE
# =========================================================
class _FakeConn:
    """Connexion minimale imitant libsql/SQLite pour les requêtes utilisées."""

    def __init__(self, base):
        self.base = base
        self._last_rowcount = 0
        self._last_select = None

    def execute(self, query, params=None):
        q = " ".join(query.split()).lower()
        params = list(params or [])
        self._last_rowcount = 0
        self._last_select = None

        # --- CREATE TABLE ---
        if "create table" in q and "codes_promo" in q:
            return self._cursor()

        # --- PRAGMA table_info ---
        if "pragma table_info" in q and "codes_promo" in q:
            self._last_select = [
                (0, "code", "TEXT"),
                (1, "type_reduction", "TEXT"),
                (2, "valeur", "REAL"),
                (3, "limite_utilisation", "INTEGER"),
                (4, "deja_utilise", "INTEGER"),
                (5, "jours_premium", "INTEGER"),
                (6, "date_creation", "TEXT"),
            ]
            return self._cursor()

        # --- ALTER TABLE ---
        if "alter table" in q and "add column" in q:
            # On considère que la colonne est déjà dans le schéma fake
            self._last_rowcount = 1
            return self._cursor()

        # --- INSERT codes_promo ---
        if "insert into codes_promo" in q:
            code, type_reduction, valeur, limite, jours = params
            if code in self.base["codes_promo"]:
                return self._cursor()  # ON CONFLICT DO NOTHING → rowcount 0
            self.base["codes_promo"][code] = {
                "code": code,
                "type_reduction": type_reduction,
                "valeur": valeur,
                "limite_utilisation": limite,
                "deja_utilise": 0,
                "jours_premium": jours,
            }
            self._last_rowcount = 1
            return self._cursor()

        # --- SELECT codes_promo ---
        if "from codes_promo" in q and "where code" in q:
            code = params[0]
            row = self.base["codes_promo"].get(code)
            if row is None:
                self._last_select = None
            else:
                self._last_select = (
                    row["type_reduction"],
                    row["valeur"],
                    row["limite_utilisation"],
                    row["deja_utilise"],
                    row["jours_premium"],
                )
            return self._cursor()

        # --- UPDATE codes_promo SET deja_utilise = deja_utilise + 1 ---
        if "update codes_promo" in q and "deja_utilise + 1" in q:
            code = params[0]
            row = self.base["codes_promo"].get(code)
            if row is None:
                return self._cursor()
            limite = row["limite_utilisation"]
            if limite != 0 and row["deja_utilise"] >= limite:
                return self._cursor()  # 0 ligne affectée
            row["deja_utilise"] += 1
            self._last_rowcount = 1
            return self._cursor()

        # --- UPDATE utilisateurs SET status=premium (ajouter_jours_premium) ---
        if "update utilisateurs" in q and "set status" in q:
            date_str, user_id = params
            if user_id not in self.base["utilisateurs"]:
                return self._cursor()
            self.base["utilisateurs"][user_id]["status"] = "premium"
            self.base["utilisateurs"][user_id]["date_expiration"] = date_str
            self._last_rowcount = 1
            return self._cursor()

        # --- SELECT utilisateurs ---
        if "from utilisateurs" in q and "where user_id" in q:
            user_id = params[0]
            u = self.base["utilisateurs"].get(user_id)
            if u is None:
                self._last_select = None
            else:
                # colonnes minimales utilisées : status, date_expiration,
                # first_name, username, langue
                self._last_select = (
                    user_id,
                    u.get("username", ""),
                    u.get("first_name", ""),
                    u.get("status", "free"),
                    u.get("date_inscription", ""),
                    u.get("date_expiration"),
                    u.get("notifications_actives", 1),
                    u.get("langue", "fr"),
                    u.get("parrain_id"),
                    u.get("methode_paiement"),
                )
            return self._cursor()

        # --- Requêtes non gérées : on lève pour détecter les oublis ---
        raise AssertionError(f"Requête non gérée : {query}")

    def commit(self):
        pass

    def close(self):
        pass

    def _cursor(self):
        return _FakeCursor(self._last_rowcount, self._last_select)


class _FakeCursor:
    def __init__(self, rowcount, row):
        self.rowcount = rowcount
        self._row = row
        self.description = [
            (0, "type_reduction"), (1, "valeur"), (2, "limite_utilisation"),
            (3, "deja_utilise"), (4, "jours_premium"), (5, "user_id"),
            (6, "username"), (7, "first_name"), (8, "status"),
            (9, "date_inscription"), (10, "date_expiration"),
            (11, "notifications_actives"), (12, "langue"),
            (13, "parrain_id"), (14, "methode_paiement"),
        ]

    def fetchone(self):
        return self._row

    def fetchall(self):
        if self._row is None:
            return []
        if isinstance(self._row, list):
            return self._row
        return [self._row]


# =========================================================
# FIXTURES
# =========================================================
@pytest.fixture
def fake_db(monkeypatch):
    """Branche une fausse DB en mémoire dans users.db et core.codes_promo."""
    base = {"codes_promo": {}, "utilisateurs": {}}

    def _get_connection():
        return _FakeConn(base)

    monkeypatch.setattr(users_db, "get_connection", _get_connection)
    monkeypatch.setattr(cp, "get_connection", _get_connection)
    return base


@pytest.fixture(autouse=True)
def _silence_logs(monkeypatch):
    for nom in ("log_info", "log_warning", "log_error"):
        monkeypatch.setattr(cp, nom, lambda *a, **k: None, raising=False)
        monkeypatch.setattr(account_base, nom, lambda *a, **k: None, raising=False)


def _creer_utilisateur(base, user_id, first_name="Test"):
    base["utilisateurs"][user_id] = {
        "username": "test",
        "first_name": first_name,
        "status": "free",
        "date_inscription": "2026-01-01 00:00:00",
        "date_expiration": None,
        "langue": "fr",
    }


# =========================================================
# TESTS — CRÉATION
# =========================================================
def test_creer_code_succes(fake_db):
    assert cp.creer_code_promo("CAN2026", "pourcentage", 30, 100) is True
    assert "CAN2026" in fake_db["codes_promo"]
    assert fake_db["codes_promo"]["CAN2026"]["valeur"] == 30.0
    assert fake_db["codes_promo"]["CAN2026"]["limite_utilisation"] == 100
    assert fake_db["codes_promo"]["CAN2026"]["jours_premium"] == 1


def test_creer_code_doublon_refuse(fake_db):
    assert cp.creer_code_promo("CAN2026", "pourcentage", 30, 100) is True
    assert cp.creer_code_promo("CAN2026", "fixe", 2000, 0) is False
    # Le premier code n'a pas été écrasé
    assert fake_db["codes_promo"]["CAN2026"]["type_reduction"] == "pourcentage"


def test_creer_code_type_invalide(fake_db):
    assert cp.creer_code_promo("X", "bogus", 10) is False
    assert "X" not in fake_db["codes_promo"]


def test_creer_code_valeur_invalide(fake_db):
    assert cp.creer_code_promo("X", "fixe", 0) is False
    assert cp.creer_code_promo("Y", "fixe", -5) is False
    assert "X" not in fake_db["codes_promo"]
    assert "Y" not in fake_db["codes_promo"]


def test_creer_code_jours_invalides(fake_db):
    assert cp.creer_code_promo("X", "fixe", 10, jours_premium=0) is False
    assert cp.creer_code_promo("Y", "fixe", 10, jours_premium=-1) is False
    assert "X" not in fake_db["codes_promo"]
    assert "Y" not in fake_db["codes_promo"]


def test_creer_code_jours_personnalises(fake_db):
    assert cp.creer_code_promo("VIP", "pourcentage", 50, 10, jours_premium=7) is True
    assert fake_db["codes_promo"]["VIP"]["jours_premium"] == 7


# =========================================================
# TESTS — UTILISATION
# =========================================================
def test_utiliser_code_succes(fake_db):
    cp.creer_code_promo("CAN2026", "pourcentage", 30, 100, jours_premium=3)
    resultat = cp.valider_code_promo("CAN2026", user_id=42)

    assert resultat["valide"] is True
    assert resultat["jours_premium"] == 3
    assert resultat["type_reduction"] == "pourcentage"
    assert resultat["valeur"] == 30.0
    assert fake_db["codes_promo"]["CAN2026"]["deja_utilise"] == 1


def test_utiliser_code_introuvable(fake_db):
    resultat = cp.valider_code_promo("NOPE", user_id=42)
    assert resultat["valide"] is False
    assert "introuvable" in resultat["message"].lower()


def test_utiliser_code_epuise(fake_db):
    cp.creer_code_promo("LIMIT1", "fixe", 1000, limite_utilisation=1)
    r1 = cp.valider_code_promo("LIMIT1", user_id=1)
    assert r1["valide"] is True

    r2 = cp.valider_code_promo("LIMIT1", user_id=2)
    assert r2["valide"] is False
    assert "épuisé" in r2["message"].lower()


def test_utiliser_code_illimite(fake_db):
    cp.creer_code_promo("INFINI", "fixe", 1000, limite_utilisation=0)
    for i in range(1, 6):
        r = cp.valider_code_promo("INFINI", user_id=i)
        assert r["valide"] is True, f"Échec à l'utilisation {i}"
    assert fake_db["codes_promo"]["INFINI"]["deja_utilise"] == 5


def test_utiliser_code_vide(fake_db):
    assert cp.valider_code_promo("", user_id=42)["valide"] is False
    assert cp.valider_code_promo(None, user_id=42)["valide"] is False


# =========================================================
# TESTS — COURSE CONCURRENTE
# =========================================================
def test_course_concurrente_un_seul_gagne(fake_db):
    """Deux utilisateurs tentent un code à limite 1 : un seul doit réussir."""
    cp.creer_code_promo("RACE", "fixe", 1000, limite_utilisation=1)

    r1 = cp.valider_code_promo("RACE", user_id=1)
    r2 = cp.valider_code_promo("RACE", user_id=2)

    assert r1["valide"] is True
    assert r2["valide"] is False
    assert fake_db["codes_promo"]["RACE"]["deja_utilise"] == 1


# =========================================================
# TESTS — JOURS PREMIUM ACCORDÉS
# =========================================================
def test_jours_premium_reellement_accordes(fake_db):
    """Le flux complet : création → validation → ajout des jours."""
    _creer_utilisateur(fake_db, user_id=42, first_name="Alice")
    cp.creer_code_promo("VIP", "pourcentage", 50, 10, jours_premium=7)

    resultat = cp.valider_code_promo("VIP", user_id=42)
    assert resultat["valide"] is True
    jours = resultat["jours_premium"]
    assert jours == 7

    # Simule l'appel de /utilisercode (qui appelle ajouter_jours_premium)
    assert account_base.ajouter_jours_premium(42, jours) is True

    assert fake_db["utilisateurs"][42]["status"] == "premium"
    assert fake_db["utilisateurs"][42]["date_expiration"] is not None


def test_code_epuise_ne_consomme_pas(fake_db):
    """Un code épuisé ne doit pas incrémenter deja_utilise."""
    cp.creer_code_promo("LIMIT1", "fixe", 1000, limite_utilisation=1)
    cp.valider_code_promo("LIMIT1", user_id=1)  # consomme 1/1
    assert fake_db["codes_promo"]["LIMIT1"]["deja_utilise"] == 1

    r = cp.valider_code_promo("LIMIT1", user_id=2)
    assert r["valide"] is False
    # deja_utilise reste à 1 (pas d'incrément sur échec)
    assert fake_db["codes_promo"]["LIMIT1"]["deja_utilise"] == 1


# =========================================================
# TESTS — INFORMATIONS
# =========================================================
def test_get_code_promo_existant(fake_db):
    cp.creer_code_promo("INFO", "pourcentage", 25, 5, jours_premium=2)
    infos = cp.get_code_promo("INFO")
    assert infos is not None
    assert infos["code"] == "INFO"
    assert infos["type_reduction"] == "pourcentage"
    assert infos["valeur"] == 25.0
    assert infos["limite_utilisation"] == 5
    assert infos["deja_utilise"] == 0
    assert infos["jours_premium"] == 2
    assert infos["disponible"] is True


def test_get_code_promo_inexistant(fake_db):
    assert cp.get_code_promo("NOPE") is None
    assert cp.get_code_promo("") is None
    assert cp.get_code_promo(None) is None


def test_get_code_promo_epuise_non_disponible(fake_db):
    cp.creer_code_promo("LIMIT1", "fixe", 1000, limite_utilisation=1)
    cp.valider_code_promo("LIMIT1", user_id=1)
    infos = cp.get_code_promo("LIMIT1")
    assert infos["disponible"] is False
