import psycopg2.extras
from datetime import datetime

from users.db import get_connection
from core.utils.logs import log_error


# =========================================================
# DEMANDES DE PAIEMENT EN ATTENTE
# =========================================================
def creer_demande_paiement(user_id, abonnement, montant, preuve_photo_id):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO paiements_attente (user_id, abonnement, montant, preuve_photo_id)
            VALUES (%s, %s, %s, %s)
            RETURNING id
        """, (user_id, abonnement, montant, preuve_photo_id))
        demande_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        print(f"💳 Demande paiement #{demande_id} créée par {user_id}")
        return demande_id
    except Exception as e:
        log_error(f"Erreur creer_demande_paiement : {e}", "PAIEMENTS")
        return None


def get_demande(demande_id):
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM paiements_attente WHERE id = %s", (demande_id,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        return dict(row) if row else None
    except Exception as e:
        log_error(f"Erreur get_demande : {e}", "PAIEMENTS")
        return None


def get_demandes_en_attente(limite=20):
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT * FROM paiements_attente
            WHERE statut = 'en_attente'
            ORDER BY date_demande DESC
            LIMIT %s
        """, (limite,))
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return [dict(r) for r in rows]
    except Exception as e:
        log_error(f"Erreur get_demandes_en_attente : {e}", "PAIEMENTS")
        return []


def valider_demande(demande_id, admin_id):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            UPDATE paiements_attente
            SET statut = 'valide', date_validation = NOW(), admin_id = %s
            WHERE id = %s
        """, (admin_id, demande_id))
        conn.commit()
        rows = cur.rowcount
        cur.close()
        conn.close()
        return rows > 0
    except Exception as e:
        log_error(f"Erreur valider_demande : {e}", "PAIEMENTS")
        return False


def refuser_demande(demande_id, admin_id):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            UPDATE paiements_attente
            SET statut = 'refuse', date_validation = NOW(), admin_id = %s
            WHERE id = %s
        """, (admin_id, demande_id))
        conn.commit()
        rows = cur.rowcount
        cur.close()
        conn.close()
        return rows > 0
    except Exception as e:
        log_error(f"Erreur refuser_demande : {e}", "PAIEMENTS")
        return False


def compter_demandes_en_attente():
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM paiements_attente WHERE statut = 'en_attente'")
        result = cur.fetchone()
        cur.close()
        conn.close()
        return result[0] if result else 0
    except Exception as e:
        log_error(f"Erreur compter_demandes_en_attente : {e}", "PAIEMENTS")
        return 0


# =========================================================
# CODES PREMIUM
# =========================================================
def generer_code(jours, prefix="PREM"):
    import random
    import string
    try:
        conn = get_connection()
        cur = conn.cursor()

        while True:
            code = f"{prefix}-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
            cur.execute("SELECT 1 FROM codes_premium WHERE code = %s", (code,))
            if not cur.fetchone():
                break

        cur.execute("""
            INSERT INTO codes_premium (code, jours)
            VALUES (%s, %s)
        """, (code, jours))
        conn.commit()
        cur.close()
        conn.close()
        return code
    except Exception as e:
        log_error(f"Erreur generer_code : {e}", "PAIEMENTS")
        return None


def generer_lot_codes(jours, quantite):
    codes = []
    for _ in range(quantite):
        code = generer_code(jours)
        if code:
            codes.append(code)
    return codes


def utiliser_code(code, user_id):
    try:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("SELECT jours, utilise FROM codes_premium WHERE code = %s", (code,))
        row = cur.fetchone()

        if not row:
            cur.close()
            conn.close()
            return {"erreur": "Code introuvable"}

        jours, utilise = row

        if utilise:
            cur.close()
            conn.close()
            return {"erreur": "Code déjà utilisé"}

        cur.execute("""
            UPDATE codes_premium
            SET utilise = TRUE, utilise_par = %s, date_utilisation = NOW()
            WHERE code = %s
        """, (user_id, code))
        conn.commit()
        cur.close()
        conn.close()
        return {"jours": jours}
    except Exception as e:
        log_error(f"Erreur utiliser_code : {e}", "PAIEMENTS")
        return {"erreur": str(e)}


def get_codes_disponibles(limite=50):
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT * FROM codes_premium
            WHERE utilise = FALSE
            ORDER BY date_creation DESC
            LIMIT %s
        """, (limite,))
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return [dict(r) for r in rows]
    except Exception as e:
        log_error(f"Erreur get_codes_disponibles : {e}", "PAIEMENTS")
        return []


def get_codes_utilises(limite=50):
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT * FROM codes_premium
            WHERE utilise = TRUE
            ORDER BY date_utilisation DESC
            LIMIT %s
        """, (limite,))
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return [dict(r) for r in rows]
    except Exception as e:
        log_error(f"Erreur get_codes_utilises : {e}", "PAIEMENTS")
        return []


def compter_codes_disponibles():
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM codes_premium WHERE utilise = FALSE")
        result = cur.fetchone()
        cur.close()
        conn.close()
        return result[0] if result else 0
    except Exception as e:
        log_error(f"Erreur compter_codes_disponibles : {e}", "PAIEMENTS")
        return 0
