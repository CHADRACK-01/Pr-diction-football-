"""Fonctionnalités locales d'engagement : XP, bonus quotidien et roue."""

import random

from users.db import db_execute, db_fetchone


_TABLE = """
CREATE TABLE IF NOT EXISTS engagement_utilisateurs (
    user_id INTEGER PRIMARY KEY,
    xp INTEGER NOT NULL DEFAULT 0,
    derniere_connexion TEXT,
    dernier_spin TEXT,
    serie_connexion INTEGER NOT NULL DEFAULT 0
)
"""


def _assurer_table():
    db_execute(_TABLE, db_context={"table": "engagement_utilisateurs", "operation": "create"})


def obtenir_engagement(user_id):
    _assurer_table()
    row = db_fetchone(
        "SELECT xp, derniere_connexion, dernier_spin, serie_connexion FROM engagement_utilisateurs WHERE user_id = ?",
        params=[user_id],
        db_context={"table": "engagement_utilisateurs", "operation": "get"},
    )
    if not row:
        return {"user_id": user_id, "xp": 0, "derniere_connexion": None, "dernier_spin": None, "serie_connexion": 0}
    return {"user_id": user_id, "xp": row[0], "derniere_connexion": row[1], "dernier_spin": row[2], "serie_connexion": row[3]}


def crediter_xp(user_id, points):
    if points < 0:
        raise ValueError("Les points XP ne peuvent pas être négatifs")
    _assurer_table()
    db_execute(
        "INSERT INTO engagement_utilisateurs (user_id, xp) VALUES (?, ?) "
        "ON CONFLICT(user_id) DO UPDATE SET xp = engagement_utilisateurs.xp + excluded.xp",
        params=[user_id, points],
        db_context={"table": "engagement_utilisateurs", "operation": "credit_xp"},
    )
    return obtenir_engagement(user_id)


def bonus_connexion_quotidienne(user_id, date_jour):
    _assurer_table()
    engagement = obtenir_engagement(user_id)
    derniere = engagement["derniere_connexion"]
    if derniere == date_jour:
        return {"attribue": False, "xp": 0, "serie": engagement["serie_connexion"]}

    nouvelle_serie = engagement["serie_connexion"] + 1 if derniere else 1
    xp = min(10 * nouvelle_serie, 70)
    db_execute(
        "INSERT INTO engagement_utilisateurs (user_id, xp, derniere_connexion, serie_connexion) VALUES (?, ?, ?, ?) "
        "ON CONFLICT(user_id) DO UPDATE SET xp = engagement_utilisateurs.xp + excluded.xp, "
        "derniere_connexion = excluded.derniere_connexion, serie_connexion = excluded.serie_connexion",
        params=[user_id, xp, date_jour, nouvelle_serie],
        db_context={"table": "engagement_utilisateurs", "operation": "daily_bonus"},
    )
    return {"attribue": True, "xp": xp, "serie": nouvelle_serie}


def tourner_roue(user_id, date_jour, graine=None):
    engagement = obtenir_engagement(user_id)
    if engagement["dernier_spin"] == date_jour:
        return {"attribue": False, "gain": None}

    rng = random.Random(graine)
    gains = ["10 XP", "25 XP", "Analyse gratuite", "-10% réduction", "50 XP"]
    gain = rng.choice(gains)
    db_execute(
        "INSERT INTO engagement_utilisateurs (user_id, dernier_spin) VALUES (?, ?) "
        "ON CONFLICT(user_id) DO UPDATE SET dernier_spin = excluded.dernier_spin",
        params=[user_id, date_jour],
        db_context={"table": "engagement_utilisateurs", "operation": "daily_spin"},
    )
    return {"attribue": True, "gain": gain}
