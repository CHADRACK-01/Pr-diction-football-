# core/cotes_historiques.py
"""
Historique horodaté des cotes, pour mesurer la valeur réelle des estimations.

Chaque observation est enregistrée avec sa date de capture. On ne réécrit
jamais une observation : les cotes passées restent telles qu'elles étaient.
Une seule observation par match, par bookmaker et par heure.
"""
import datetime as _dt
from core.data.equipes import cle_canonique
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


def lire_dernieres_cotes(home, away, bookmaker, limite=2):
    """
    Retourne les dernières observations d'un match pour un bookmaker,
    la plus récente en premier : [(date_capture, cote_h, cote_d, cote_a), ...].
    Retourne une liste vide en cas d'erreur ou d'absence de données.
    """
    try:
        from users.db import db_fetchall
        cle_match = f"{cle_canonique(home)}|{cle_canonique(away)}"
        lignes = db_fetchall(
            "SELECT date_capture, cote_h, cote_d, cote_a FROM cotes_snapshots "
            "WHERE cle_match = ? AND bookmaker = ? ORDER BY date_capture DESC LIMIT ?",
            params=[cle_match, str(bookmaker), int(limite)],
            db_context={"table": "cotes_snapshots", "operation": "select"},
        )
        return list(lignes or [])
    except Exception as e:
        log_error("Lecture des cotes historiques impossible", "COTES", exception=e)
        return []


def detecter_chute(home, away, bookmaker, seuil=0.05):
    """
    Compare la dernière observation à la précédente pour un même bookmaker.
    Une cote « chute » si elle a baissé d'au moins `seuil` (5 % par défaut)
    en valeur relative. Retourne None s'il n'y a pas deux observations.
    Sinon retourne {"variations": {issue: var}, "chutes": [issue, ...]},
    où var = (ancienne - nouvelle) / ancienne et issue ∈ {home, draw, away}.
    """
    obs = lire_dernieres_cotes(home, away, bookmaker, limite=2)
    if len(obs) < 2:
        return None
    _, rec_h, rec_d, rec_a = obs[0]
    _, anc_h, anc_d, anc_a = obs[1]
    variations = {}
    for issue, ancienne, recente in (("home", anc_h, rec_h), ("draw", anc_d, rec_d), ("away", anc_a, rec_a)):
        if not all(_valide(c) for c in (ancienne, recente)):
            return None
        variations[issue] = (float(ancienne) - float(recente)) / float(ancienne)
    chutes = [issue for issue, var in variations.items() if var >= seuil]
    return {"variations": variations, "chutes": chutes}
