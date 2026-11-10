import random
import string
from datetime import datetime

from users.db import get_connection
from core.utils.logs import log_info, log_error, log_warning


# =========================================================
# DEMANDES DE PAIEMENT EN ATTENTE
# =========================================================
def creer_demande_paiement(user_id, abonnement, montant, preuve_photo_id):
    """Crée une demande de paiement en attente de validation."""
    try:
        conn = get_connection()
        conn.execute("""
            INSERT INTO paiements_attente (user_id, abonnement, montant, preuve_photo_id)
            VALUES (?, ?, ?, ?)
        """, (user_id, abonnement, montant, preuve_photo_id))
        conn.commit()
        
        result = conn.execute("SELECT last_insert_rowid()").fetchone()
        demande_id = result[0] if result else None
        conn.close()
        
        log_info(f"Demande paiement #{demande_id} créée par {user_id}", "PAIEMENTS")
        return demande_id
    except Exception as e:
        log_error(f"Impossible de créer la demande de paiement pour {user_id}", "PAIEMENTS", exception=e)
        return None


def get_demande(demande_id):
    """Récupère une demande de paiement par son ID."""
    try:
        conn = get_connection()
        cur = conn.execute("SELECT * FROM paiements_attente WHERE id = ?", (demande_id,))
        row = cur.fetchone()
        
        if row:
            columns = [desc[0] for desc in cur.description]
            demande = dict(zip(columns, row))
            conn.close()
            return demande
        conn.close()
        return None
    except Exception as e:
        log_error(f"Impossible de récupérer la demande {demande_id}", "PAIEMENTS", exception=e)
        return None


def get_demandes_en_attente(limite=20):
    """Récupère les demandes de paiement en attente."""
    try:
        conn = get_connection()
        cur = conn.execute("""
            SELECT * FROM paiements_attente
            WHERE statut = 'en_attente'
            ORDER BY date_demande DESC
            LIMIT ?
        """, (limite,))
        rows = cur.fetchall()
        columns = [desc[0] for desc in cur.description]
        conn.close()
        return [dict(zip(columns, row)) for row in rows]
    except Exception as e:
        log_error("Impossible de récupérer les paiements en attente", "PAIEMENTS", exception=e)
        return []


def valider_demande(demande_id, admin_id):
    """Valide une demande de paiement."""
    try:
        conn = get_connection()
        conn.execute("""
            UPDATE paiements_attente
            SET statut = 'valide', date_validation = CURRENT_TIMESTAMP, admin_id = ?
            WHERE id = ?
        """, (admin_id, demande_id))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        log_error(f"Impossible de valider la demande {demande_id}", "PAIEMENTS", exception=e)
        return False


def refuser_demande(demande_id, admin_id):
    """Refuse une demande de paiement."""
    try:
        conn = get_connection()
        conn.execute("""
            UPDATE paiements_attente
            SET statut = 'refuse', date_validation = CURRENT_TIMESTAMP, admin_id = ?
            WHERE id = ?
        """, (admin_id, demande_id))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        log_error(f"Impossible de refuser la demande {demande_id}", "PAIEMENTS", exception=e)
        return False


def compter_demandes_en_attente():
    """Compte le nombre de demandes en attente."""
    try:
        conn = get_connection()
        result = conn.execute("SELECT COUNT(*) FROM paiements_attente WHERE statut = 'en_attente'").fetchone()
        conn.close()
        return result[0] if result else 0
    except Exception as e:
        log_error("Impossible de compter les demandes en attente", "PAIEMENTS", exception=e)
        return 0


# =========================================================
# CODES PREMIUM
# =========================================================
def generer_code(jours, prefix="PREM"):
    """Génère un code Premium unique."""
    try:
        conn = get_connection()
        
        # On boucle jusqu'à trouver un code unique (max 10 tentatives)
        for _ in range(10):
            code = f"{prefix}-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
            existing = conn.execute("SELECT 1 FROM codes_premium WHERE code = ?", (code,)).fetchone()
            if not existing:
                conn.execute("""
                    INSERT INTO codes_premium (code, jours)
                    VALUES (?, ?)
                """, (code, jours))
                conn.commit()
                conn.close()
                return code
        
        conn.close()
        log_error("Impossible de générer un code unique (10 tentatives épuisées)", "PAIEMENTS")
        return None
    except Exception as e:
        log_error("Impossible de générer un code Premium", "PAIEMENTS", exception=e)
        return None


def generer_lot_codes(jours, quantite):
    """Génère un lot de codes Premium."""
    codes = []
    for _ in range(quantite):
        code = generer_code(jours)
        if code:
            codes.append(code)
    return codes


def utiliser_code(code, user_id):
    """Utilise un code Premium pour un utilisateur."""
    try:
        conn = get_connection()
        result = conn.execute("SELECT jours, utilise FROM codes_premium WHERE code = ?", (code,)).fetchone()

        if not result:
            conn.close()
            return {"erreur": "Code introuvable"}

        jours, utilise = result

        if utilise:
            conn.close()
            return {"erreur": "Code déjà utilisé"}

        conn.execute("""
            UPDATE codes_premium
            SET utilise = 1, utilise_par = ?, date_utilisation = CURRENT_TIMESTAMP
            WHERE code = ?
        """, (user_id, code))
        conn.commit()
        conn.close()
        return {"jours": jours}
    except Exception as e:
        log_error(f"Impossible d'utiliser le code {code} pour {user_id}", "PAIEMENTS", exception=e)
        return {"erreur": "Erreur interne. L'admin a été prévenu."}


def get_codes_disponibles(limite=50):
    """Récupère les codes Premium non utilisés."""
    try:
        conn = get_connection()
        cur = conn.execute("""
            SELECT * FROM codes_premium
            WHERE utilise = 0
            ORDER BY date_creation DESC
            LIMIT ?
        """, (limite,))
        rows = cur.fetchall()
        columns = [desc[0] for desc in cur.description]
        conn.close()
        return [dict(zip(columns, row)) for row in rows]
    except Exception as e:
        log_error("Impossible de récupérer les codes disponibles", "PAIEMENTS", exception=e)
        return []


def get_codes_utilises(limite=50):
    """Récupère les codes Premium utilisés."""
    try:
        conn = get_connection()
        cur = conn.execute("""
            SELECT * FROM codes_premium
            WHERE utilise = 1
            ORDER BY date_utilisation DESC
            LIMIT ?
        """, (limite,))
        rows = cur.fetchall()
        columns = [desc[0] for desc in cur.description]
        conn.close()
        return [dict(zip(columns, row)) for row in rows]
    except Exception as e:
        log_error("Impossible de récupérer les codes utilisés", "PAIEMENTS", exception=e)
        return []


def compter_codes_disponibles():
    """Compte le nombre de codes Premium disponibles."""
    try:
        conn = get_connection()
        result = conn.execute("SELECT COUNT(*) FROM codes_premium WHERE utilise = 0").fetchone()
        conn.close()
        return result[0] if result else 0
    except Exception as e:
        log_error("Impossible de compter les codes disponibles", "PAIEMENTS", exception=e)
        return 0
