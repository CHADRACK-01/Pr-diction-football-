# core/bilans.py
"""
Bilans vérifiables : chaque estimation est enregistrée AVANT le match,
puis comparée au résultat réel. Un bilan ne porte que sur ces enregistrements.

Garanties :
- une estimation n'est enregistrée que si le match n'a pas encore de résultat ;
- une même estimation (même match, même jour) n'est enregistrée qu'une fois ;
- les bilans ne sont calculés qu'à partir des enregistrements, jamais à partir
  de prédictions recalculées après coup.
"""
import math
import datetime as _dt
from core.utils.logs import log_error, log_info

_TABLE_SQL = """
    CREATE TABLE IF NOT EXISTS estimations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cle TEXT UNIQUE NOT NULL,
        date_enregistrement TEXT NOT NULL,
        competition TEXT,
        home TEXT NOT NULL,
        away TEXT NOT NULL,
        p_h REAL NOT NULL,
        p_d REAL NOT NULL,
        p_a REAL NOT NULL,
        pick TEXT NOT NULL,
        resolu INTEGER NOT NULL DEFAULT 0,
        resultat TEXT,
        date_resultat TEXT
    )
"""

_ISSUE = {"H": 0, "D": 1, "A": 2}


def _db():
    from users.db import db_execute, db_fetchone, db_fetchall
    return db_execute, db_fetchone, db_fetchall


def _assurer_table():
    db_execute, _, _ = _db()
    db_execute(_TABLE_SQL, db_context={"table": "estimations", "operation": "create"})


def _aujourdhui():
    from core.ml_model import TZ_KINSHASA
    return datetime_now().strftime("%Y-%m-%d")


def datetime_now():
    from core.ml_model import TZ_KINSHASA
    return _dt.datetime.now(TZ_KINSHASA)


def _match_deja_joue(home, away, depuis):
    """True si ce match a déjà un résultat à partir de la date donnée."""
    _, db_fetchone, _ = _db()
    row = db_fetchone(
        "SELECT 1 FROM matchs WHERE home_team = ? AND away_team = ? "
        "AND date >= ? AND fthg IS NOT NULL LIMIT 1",
        params=[home, away, depuis],
        db_context={"table": "matchs", "operation": "deja_joue"},
    )
    return row is not None


def _nom_base(nom):
    """Convertit le nom saisi en nom utilisé dans la table matchs (même règle que le bot)."""
    try:
        from core.nouveau_prediction import NOMS_EQUIPES_MAPPING
        return NOMS_EQUIPES_MAPPING.get(nom, nom)
    except Exception:
        return nom


def enregistrer_estimation(home, away, p_h, p_d, p_a, competition=None):
    """Enregistre une estimation avant match. Retourne True si enregistrée maintenant.

    Refuse si le match a déjà un résultat, ou si l'estimation existe déjà pour aujourd'hui.
    """
    try:
        if None in (p_h, p_d, p_a):
            return False
        home, away = _nom_base(home), _nom_base(away)
        _assurer_table()
        jour = _aujourdhui()
        if _match_deja_joue(home, away, jour):
            return False
        pick = max((("H", p_h), ("D", p_d), ("A", p_a)), key=lambda x: x[1])[0]
        cle = f"{home}|{away}|{jour}"
        db_execute, _, _ = _db()
        rowcount = db_execute(
            "INSERT INTO estimations (cle, date_enregistrement, competition, home, away, "
            "p_h, p_d, p_a, pick) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?) "
            "ON CONFLICT(cle) DO NOTHING",
            params=[cle, datetime_now().isoformat(timespec="seconds"), competition,
                    home, away, float(p_h), float(p_d), float(p_a), pick],
            db_context={"table": "estimations", "operation": "insert"},
        )
        return rowcount == 1
    except Exception as e:
        log_error("Enregistrement de l'estimation impossible", "BILANS", exception=e)
        return False


def resoudre_estimations():
    """Relie les estimations non résolues à leur résultat réel, quand il existe."""
    db_execute, db_fetchone, db_fetchall = _db()
    _assurer_table()
    lignes = db_fetchall(
        "SELECT id, home, away, date_enregistrement FROM estimations WHERE resolu = 0",
        db_context={"table": "estimations", "operation": "a_resoudre"},
    )
    n = 0
    for est_id, home, away, date_enr in lignes:
        jour = str(date_enr)[:10]
        row = db_fetchone(
            "SELECT date, fthg, ftag, ftr FROM matchs WHERE home_team = ? AND away_team = ? "
            "AND date >= ? AND fthg IS NOT NULL ORDER BY date LIMIT 1",
            params=[home, away, jour],
            db_context={"table": "matchs", "operation": "resultat"},
        )
        if not row:
            continue
        db_execute(
            "UPDATE estimations SET resolu = 1, resultat = ?, date_resultat = ? WHERE id = ?",
            params=[row[3], str(row[0])[:10], est_id],
            db_context={"table": "estimations", "operation": "resoudre"},
        )
        n += 1
    if n:
        log_info(f"{n} estimation(s) résolue(s)", "BILANS")
    return n


def statistiques():
    """Bilan calculé uniquement sur les estimations résolues."""
    _assurer_table()
    _, _, db_fetchall = _db()
    lignes = db_fetchall(
        "SELECT p_h, p_d, p_a, pick, resultat FROM estimations WHERE resolu = 1",
        db_context={"table": "estimations", "operation": "stats"},
    )
    total_enregistrees = _db()[1]("SELECT COUNT(*) FROM estimations", db_context={"table": "estimations", "operation": "count"})[0]
    n = len(lignes)
    if n == 0:
        return {"enregistrees": total_enregistrees, "resolues": 0}

    bonnes = sum(1 for r in lignes if r[3] == r[4])
    ll = 0.0
    for p_h, p_d, p_a, _, resultat in lignes:
        p = {"H": p_h, "D": p_d, "A": p_a}[resultat]
        ll -= math.log(max(p, 1e-9))
    return {
        "enregistrees": total_enregistrees,
        "resolues": n,
        "precision": bonnes / n,
        "log_loss": ll / n,
    }
