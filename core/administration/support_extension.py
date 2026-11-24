"""Support, litiges, blacklist et crédits locaux pour les extensions du catalogue."""

from datetime import datetime

from users.database import db_execute, db_fetchall, db_fetchone


def _assurer_tables():
    db_execute("CREATE TABLE IF NOT EXISTS tickets_support (id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER,sujet TEXT,statut TEXT DEFAULT 'nouveau',assigne_a INTEGER,details TEXT,cree_le TEXT DEFAULT CURRENT_TIMESTAMP)", db_context={"table":"tickets_support","operation":"create"})
    db_execute("CREATE TABLE IF NOT EXISTS litiges_paiement (id INTEGER PRIMARY KEY AUTOINCREMENT,paiement_id INTEGER,user_id INTEGER,statut TEXT DEFAULT 'en_attente',motif TEXT,resolu_le TEXT)", db_context={"table":"litiges_paiement","operation":"create"})
    db_execute("CREATE TABLE IF NOT EXISTS blacklist_utilisateurs (user_id INTEGER PRIMARY KEY,numero TEXT,appareil TEXT,motif TEXT,cree_le TEXT DEFAULT CURRENT_TIMESTAMP)", db_context={"table":"blacklist_utilisateurs","operation":"create"})
    db_execute("CREATE TABLE IF NOT EXISTS avoirs_utilisateurs (user_id INTEGER PRIMARY KEY,montant REAL DEFAULT 0,modifie_le TEXT DEFAULT CURRENT_TIMESTAMP)", db_context={"table":"avoirs_utilisateurs","operation":"create"})


def creer_ticket(user_id, sujet, details=None):
    _assurer_tables()
    db_execute("INSERT INTO tickets_support (user_id,sujet,details) VALUES (?,?,?)", params=[user_id,sujet,details], db_context={"table":"tickets_support","operation":"insert"})
    rows = db_fetchall("SELECT id FROM tickets_support WHERE user_id=? ORDER BY id DESC LIMIT 1", params=[user_id])
    return {"ticket_id": rows[0][0] if rows else None, "statut": "nouveau"}


def changer_statut_ticket(ticket_id, statut, assigne_a=None):
    _assurer_tables()
    if statut not in {"nouveau", "en_cours", "resolu", "ferme"}:
        raise ValueError("Statut de ticket invalide")
    db_execute("UPDATE tickets_support SET statut=?,assigne_a=? WHERE id=?", params=[statut,assigne_a,ticket_id], db_context={"table":"tickets_support","operation":"update"})
    return True


def creer_litige(paiement_id, user_id, motif):
    _assurer_tables()
    db_execute("INSERT INTO litiges_paiement (paiement_id,user_id,motif) VALUES (?,?,?)", params=[paiement_id,user_id,motif], db_context={"table":"litiges_paiement","operation":"insert"})
    return {"paiement_id": paiement_id, "statut": "en_attente"}


def resoudre_litige(litige_id, statut):
    _assurer_tables()
    if statut not in {"resolu", "contesté", "echoue", "rembourse"}:
        raise ValueError("Statut de litige invalide")
    db_execute("UPDATE litiges_paiement SET statut=?,resolu_le=? WHERE id=?", params=[statut,datetime.now().isoformat(timespec="seconds"),litige_id], db_context={"table":"litiges_paiement","operation":"update"})
    return True


def blacklister(user_id, numero=None, appareil=None, motif=None):
    _assurer_tables()
    db_execute("INSERT INTO blacklist_utilisateurs (user_id,numero,appareil,motif) VALUES (?,?,?,?) ON CONFLICT(user_id) DO UPDATE SET numero=excluded.numero,appareil=excluded.appareil,motif=excluded.motif", params=[user_id,numero,appareil,motif], db_context={"table":"blacklist_utilisateurs","operation":"upsert"})
    return True


def est_blackliste(user_id=None, numero=None, appareil=None):
    _assurer_tables()
    if user_id is not None:
        row = db_fetchone("SELECT 1 FROM blacklist_utilisateurs WHERE user_id=?", params=[user_id])
        if row:
            return True
    if numero:
        row = db_fetchone("SELECT 1 FROM blacklist_utilisateurs WHERE numero=?", params=[numero])
        if row:
            return True
    if appareil:
        row = db_fetchone("SELECT 1 FROM blacklist_utilisateurs WHERE appareil=?", params=[appareil])
        if row:
            return True
    return False


def crediter_avoir(user_id, montant):
    _assurer_tables()
    if montant < 0:
        raise ValueError("L'avoir ne peut pas être négatif")
    db_execute("INSERT INTO avoirs_utilisateurs (user_id,montant) VALUES (?,?) ON CONFLICT(user_id) DO UPDATE SET montant=avoirs_utilisateurs.montant+excluded.montant,modifie_le=CURRENT_TIMESTAMP", params=[user_id,montant], db_context={"table":"avoirs_utilisateurs","operation":"upsert"})
    row = db_fetchone("SELECT montant FROM avoirs_utilisateurs WHERE user_id=?", params=[user_id])
    return float(row[0]) if row else 0.0
