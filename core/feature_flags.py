# core/feature_flags.py
from users.db import db_execute, db_fetchone, db_fetchall

def est_active(feature_id):
    """Vérifie si une fonctionnalité est active (par défaut : False)."""
    row = db_fetchone(
        "SELECT actif FROM fonctionnalites_actives WHERE feature_id = ?",
        params=[str(feature_id)]
    )
    return bool(row[0]) if row else False

def activer_feature(feature_id):
    """Active une fonctionnalité."""
    db_execute(
        "INSERT OR REPLACE INTO fonctionnalites_actives (feature_id, actif) VALUES (?, 1)",
        params=[str(feature_id)]
    )

def desactiver_feature(feature_id):
    """Désactive une fonctionnalité."""
    db_execute(
        "INSERT OR REPLACE INTO fonctionnalites_actives (feature_id, actif) VALUES (?, 0)",
        params=[str(feature_id)]
    )

def lister_features():
    """Retourne la liste de toutes les fonctionnalités et leur état."""
    rows = db_fetchall("SELECT feature_id, actif FROM fonctionnalites_actives")
    return {row[0]: bool(row[1]) for row in rows}
