"""Gouvernance avancée des modèles : versions, shadow, dérive et rollback."""

from datetime import datetime

from users.database import db_execute, db_fetchall, db_fetchone


def _assurer_table():
    db_execute(
        """CREATE TABLE IF NOT EXISTS model_versions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            version TEXT NOT NULL,
            statut TEXT NOT NULL DEFAULT 'shadow',
            empreinte TEXT,
            metriques TEXT,
            cree_le TEXT DEFAULT CURRENT_TIMESTAMP,
            active_le TEXT
        )""",
        db_context={"table": "model_versions", "operation": "create"},
    )


def enregistrer_modele(version, empreinte=None, metriques=None):
    _assurer_table()
    import json
    db_execute(
        "INSERT INTO model_versions (version,statut,empreinte,metriques) VALUES (?,?,?,?)",
        params=[str(version), "shadow", empreinte, json.dumps(metriques or {}, ensure_ascii=False)],
        db_context={"table": "model_versions", "operation": "insert"},
    )
    return {"version": str(version), "statut": "shadow"}


def promouvoir_modele(version):
    _assurer_table()
    db_execute(
        "UPDATE model_versions SET statut='archive' WHERE statut='production'",
        db_context={"table": "model_versions", "operation": "archive"},
    )
    db_execute(
        "UPDATE model_versions SET statut='production',active_le=? WHERE version=?",
        params=[datetime.now().isoformat(timespec="seconds"), str(version)],
        db_context={"table": "model_versions", "operation": "promote"},
    )
    return get_modele_production()


def get_modele_production():
    _assurer_table()
    row = db_fetchone(
        "SELECT version,empreinte,metriques,active_le FROM model_versions WHERE statut='production' ORDER BY id DESC LIMIT 1",
        db_context={"table": "model_versions", "operation": "get"},
    )
    if not row:
        return None
    import json
    try:
        metriques = json.loads(row[2] or "{}")
    except Exception:
        metriques = {}
    return {"version": row[0], "empreinte": row[1], "metriques": metriques, "active_le": row[3]}


def lister_versions(limite=20):
    _assurer_table()
    rows = db_fetchall(
        "SELECT version,statut,empreinte,metriques,cree_le,active_le FROM model_versions ORDER BY id DESC LIMIT ?",
        params=[limite],
        db_context={"table": "model_versions", "operation": "list"},
    )
    import json
    return [
        {"version": r[0], "statut": r[1], "empreinte": r[2], "metriques": json.loads(r[3] or "{}"), "cree_le": r[4], "active_le": r[5]}
        for r in rows
    ]


def detecter_drift(metric_avant, metric_apres, tolerance=0.05):
    if not 0 <= tolerance:
        raise ValueError("La tolérance doit être positive")
    ecart_relatif = abs(float(metric_apres) - float(metric_avant)) / max(abs(float(metric_avant)), 1e-12)
    return {"drift": ecart_relatif > tolerance, "ecart_relatif": round(ecart_relatif, 6), "tolerance": tolerance}


def rollback_modele(version):
    _assurer_table()
    db_execute(
        "UPDATE model_versions SET statut='archive' WHERE statut='production'",
        db_context={"table": "model_versions", "operation": "archive"},
    )
    db_execute(
        "UPDATE model_versions SET statut='production',active_le=? WHERE version=?",
        params=[datetime.now().isoformat(timespec="seconds"), str(version)],
        db_context={"table": "model_versions", "operation": "rollback"},
    )
    return get_modele_production()
