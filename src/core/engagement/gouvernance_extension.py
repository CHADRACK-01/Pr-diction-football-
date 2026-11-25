"""Fonctionnalités locales de gouvernance pour l'extension 138 à 700."""

import hashlib
import secrets
from datetime import datetime

from users.db import db_execute, db_fetchall


def _assurer_tables():
    db_execute(
        """CREATE TABLE IF NOT EXISTS concours (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL,
            regle TEXT,
            actif INTEGER DEFAULT 1,
            cree_le TEXT DEFAULT CURRENT_TIMESTAMP
        )""",
        db_context={"table": "concours", "operation": "create"},
    )
    db_execute(
        """CREATE TABLE IF NOT EXISTS tirages_concours (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            concours_id INTEGER,
            gagnant_id INTEGER,
            graine TEXT,
            empreinte TEXT,
            tire_le TEXT DEFAULT CURRENT_TIMESTAMP
        )""",
        db_context={"table": "tirages_concours", "operation": "create"},
    )
    db_execute(
        """CREATE TABLE IF NOT EXISTS audit_evenements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            acteur_id INTEGER,
            action TEXT NOT NULL,
            cible TEXT,
            details TEXT,
            date_evenement TEXT DEFAULT CURRENT_TIMESTAMP
        )""",
        db_context={"table": "audit_evenements", "operation": "create"},
    )


def creer_concours(nom, regle="invite_5"):
    _assurer_tables()
    db_execute(
        "INSERT INTO concours (nom,regle) VALUES (?,?)",
        params=[nom, regle],
        db_context={"table": "concours", "operation": "insert"},
    )
    return {"nom": nom, "regle": regle, "actif": True}


def tirer_gagnant(concours_id, participants):
    _assurer_tables()
    participants = sorted(set(int(p) for p in participants))
    if not participants:
        raise ValueError("La liste des participants ne peut pas être vide")
    graine = secrets.token_hex(16)
    empreinte = hashlib.sha256(graine.encode()).hexdigest()
    index = int(empreinte[:8], 16) % len(participants)
    gagnant = participants[index]
    db_execute(
        "INSERT INTO tirages_concours (concours_id,gagnant_id,graine,empreinte) VALUES (?,?,?,?)",
        params=[concours_id, gagnant, graine, empreinte],
        db_context={"table": "tirages_concours", "operation": "insert"},
    )
    return {"gagnant_id": gagnant, "empreinte": empreinte, "nb_participants": len(participants)}


def journaliser_evenement(acteur_id, action, cible=None, details=None):
    _assurer_tables()
    db_execute(
        "INSERT INTO audit_evenements (acteur_id,action,cible,details) VALUES (?,?,?,?)",
        params=[acteur_id, action, cible, details],
        db_context={"table": "audit_evenements", "operation": "insert"},
    )


def lire_audit(limite=50):
    _assurer_tables()
    rows = db_fetchall(
        "SELECT acteur_id,action,cible,details,date_evenement FROM audit_evenements ORDER BY id DESC LIMIT ?",
        params=[limite],
        db_context={"table": "audit_evenements", "operation": "list"},
    )
    return [{"acteur_id": r[0], "action": r[1], "cible": r[2], "details": r[3], "date": r[4]} for r in rows]


def rate_limiter_clic(cle_utilisateur, fenetre_secondes=10, limite=5, maintenant=None):
    maintenant = maintenant or datetime.now().timestamp()
    if fenetre_secondes <= 0 or limite <= 0:
        raise ValueError("Les limites doivent être positives")
    empreinte = hashlib.sha256(f"{cle_utilisateur}:{int(maintenant)}".encode()).hexdigest()
    # Fenêtre logique sans état partagé : la persistance doit être ajoutée par l'appelant.
    return {"autorise": True, "fenetre_secondes": fenetre_secondes, "limite": limite, "empreinte": empreinte}
