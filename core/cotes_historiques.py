# core/cotes_historiques.py
"""
Historique horodaté des cotes, pour mesurer la valeur réelle des estimations.

Chaque observation est enregistrée avec sa date de capture. On ne réécrit
jamais une observation : les cotes passées restent telles qu'elles étaient.
Une seule observation par match, par bookmaker et par heure.
"""
import datetime as _dt
from core.equipes import cle_canonique
from core.utils.logs import log_error

_TABLE_SQL = """
    CREATE TABLE IF NOT EXISTS cotes_snapshots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cle_observation TEXT UNIQUE NOT NULL,
        cle_match TEXT NOT NULL,
        date_capture TEXT NOT NULL,
        bookmaker TEXT NOT NULL,
        cote_h REAL NOT NULL,
        cote_d REAL NOT NULL,
        cote_a REAL NOT NULL
    )
"""


def _valide(c):
    """Une cote valide est un nombre strictement supérieur à 1."""
    try:
        return float(c) > 1.0
    except (TypeError, ValueError):
        return False


def proba_marche(cote_h, cote_d, cote_a):
    """Probabilités implicites d'une ligne de cotes, marge retirée (somme = 1)."""
    if not all(_valide(c) for c in (cote_h, cote_d, cote_a)):
        return None
    brut = [1 / float(cote_h), 1 / float(cote_d), 1 / float(cote_a)]
    total = sum(brut)
    return tuple(p / total for p in brut)


def enregistrer_snapshot(home, away, resultats, maintenant=None):
    """Enregistre les cotes observées. Retourne le nombre d'observations ajoutées."""
    try:
        from users.db import db_execute
        db_execute(_TABLE_SQL, db_context={"table": "cotes_snapshots", "operation": "create"})
        maintenant = maintenant or _dt.datetime.now(_dt.timezone.utc)
        heure = maintenant.strftime("%Y-%m-%d %H:00")
        cle_match = f"{cle_canonique(home)}|{cle_canonique(away)}"
        ajoutees = 0
        for r in resultats or []:
            if not all(_valide(r.get(k)) for k in ("cote_home", "cote_draw", "cote_away")):
                continue
            bk = str(r.get("bookmaker", "inconnu"))
            cle_obs = f"{cle_match}|{bk}|{heure}"
            n = db_execute(
                "INSERT INTO cotes_snapshots (cle_observation, cle_match, date_capture, bookmaker, "
                "cote_h, cote_d, cote_a) VALUES (?, ?, ?, ?, ?, ?, ?) ON CONFLICT(cle_observation) DO NOTHING",
                params=[cle_obs, cle_match, maintenant.isoformat(timespec="seconds"), bk,
                        float(r["cote_home"]), float(r["cote_draw"]), float(r["cote_away"])],
                db_context={"table": "cotes_snapshots", "operation": "insert"},
            )
            if n == 1:
                ajoutees += 1
        return ajoutees
    except Exception as e:
        log_error("Enregistrement des cotes historiques impossible", "COTES", exception=e)
        return 0
