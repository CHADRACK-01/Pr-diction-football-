"""Registres sportifs locaux : blessures, suspensions, arbitres et qualité."""

from datetime import datetime

from users.db import db_execute, db_fetchall, db_fetchone


def _assurer_tables():
    db_execute(
        """CREATE TABLE IF NOT EXISTS blessures_joueurs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            joueur TEXT NOT NULL,
            equipe TEXT,
            type_blessure TEXT,
            statut TEXT DEFAULT 'incertain',
            date_statut TEXT,
            source TEXT,
            modifie_le TEXT DEFAULT CURRENT_TIMESTAMP
        )""",
        db_context={"table": "blessures_joueurs", "operation": "create"},
    )
    db_execute(
        """CREATE TABLE IF NOT EXISTS suspensions_joueurs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            joueur TEXT NOT NULL,
            equipe TEXT,
            motif TEXT,
            date_retour TEXT,
            active INTEGER DEFAULT 1,
            modifie_le TEXT DEFAULT CURRENT_TIMESTAMP
        )""",
        db_context={"table": "suspensions_joueurs", "operation": "create"},
    )
    db_execute(
        """CREATE TABLE IF NOT EXISTS profils_arbitres (
            arbitre TEXT PRIMARY KEY,
            cartons_moyens REAL DEFAULT 0,
            penalties_moyens REAL DEFAULT 0,
            fautes_moyennes REAL DEFAULT 0,
            temps_additionnel_moyen REAL DEFAULT 0,
            var_moyenne REAL DEFAULT 0,
            modifie_le TEXT DEFAULT CURRENT_TIMESTAMP
        )""",
        db_context={"table": "profils_arbitres", "operation": "create"},
    )


def enregistrer_blessure(joueur, equipe=None, type_blessure=None, statut="incertain", source=None):
    _assurer_tables()
    db_execute(
        "INSERT INTO blessures_joueurs (joueur,equipe,type_blessure,statut,date_statut,source) VALUES (?,?,?,?,?,?)",
        params=[joueur, equipe, type_blessure, statut, datetime.now().isoformat(timespec="seconds"), source],
        db_context={"table": "blessures_joueurs", "operation": "insert"},
    )
    return {"joueur": joueur, "equipe": equipe, "statut": statut}


def lister_blessures(equipe=None):
    _assurer_tables()
    if equipe:
        rows = db_fetchall(
            "SELECT joueur,equipe,type_blessure,statut,date_statut,source FROM blessures_joueurs WHERE equipe=? ORDER BY modifie_le DESC",
            params=[equipe],
            db_context={"table": "blessures_joueurs", "operation": "list"},
        )
    else:
        rows = db_fetchall(
            "SELECT joueur,equipe,type_blessure,statut,date_statut,source FROM blessures_joueurs ORDER BY modifie_le DESC",
            db_context={"table": "blessures_joueurs", "operation": "list"},
        )
    return [{"joueur": r[0], "equipe": r[1], "type_blessure": r[2], "statut": r[3], "date_statut": r[4], "source": r[5]} for r in rows]


def enregistrer_suspension(joueur, equipe=None, motif=None, date_retour=None):
    _assurer_tables()
    db_execute(
        "INSERT INTO suspensions_joueurs (joueur,equipe,motif,date_retour) VALUES (?,?,?,?)",
        params=[joueur, equipe, motif, date_retour],
        db_context={"table": "suspensions_joueurs", "operation": "insert"},
    )
    return {"joueur": joueur, "equipe": equipe, "date_retour": date_retour}


def enregistrer_arbitre(arbitre, cartons_moyens=0, penalties_moyens=0, fautes_moyennes=0, temps_additionnel_moyen=0, var_moyenne=0):
    _assurer_tables()
    db_execute(
        """INSERT INTO profils_arbitres
        (arbitre,cartons_moyens,penalties_moyens,fautes_moyennes,temps_additionnel_moyen,var_moyenne)
        VALUES (?,?,?,?,?,?)
        ON CONFLICT(arbitre) DO UPDATE SET
        cartons_moyens=excluded.cartons_moyens,
        penalties_moyens=excluded.penalties_moyens,
        fautes_moyennes=excluded.fautes_moyennes,
        temps_additionnel_moyen=excluded.temps_additionnel_moyen,
        var_moyenne=excluded.var_moyenne,
        modifie_le=CURRENT_TIMESTAMP""",
        params=[arbitre, cartons_moyens, penalties_moyens, fautes_moyennes, temps_additionnel_moyen, var_moyenne],
        db_context={"table": "profils_arbitres", "operation": "upsert"},
    )
    return {"arbitre": arbitre, "cartons_moyens": cartons_moyens}


def get_profil_arbitre(arbitre):
    _assurer_tables()
    row = db_fetchone(
        "SELECT cartons_moyens,penalties_moyens,fautes_moyennes,temps_additionnel_moyen,var_moyenne FROM profils_arbitres WHERE arbitre=?",
        params=[arbitre],
        db_context={"table": "profils_arbitres", "operation": "get"},
    )
    if not row:
        return None
    return {"arbitre": arbitre, "cartons_moyens": row[0], "penalties_moyens": row[1], "fautes_moyennes": row[2], "temps_additionnel_moyen": row[3], "var_moyenne": row[4]}
