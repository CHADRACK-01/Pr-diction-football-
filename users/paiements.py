import psycopg2.extras
import random
import string
from datetime import datetime

from users.db import get_connection
from core.utils.logs import log_info


# =========================================================
# DEMANDES DE PAIEMENT EN ATTENTE
# =========================================================
def creer_demande_paiement(user_id, abonnement, montant, preuve_photo_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO paiements_attente (user_id, abonnement, montant, preuve_photo_id)
                VALUES (%s, %s, %s, %s)
                RETURNING id
            """, (user_id, abonnement, montant, preuve_photo_id))
            demande_id = cur.fetchone()[0]
        conn.commit()
        
    log_info(f"Demande paiement #{demande_id} créée par {user_id}", "PAIEMENTS")
    return demande_id


def get_demande(demande_id):
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT * FROM paiements_attente WHERE id = %s", (demande_id,))
            row = cur.fetchone()
            return dict(row) if row else None


def get_demandes_en_attente(limite=20):
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT * FROM paiements_attente
                WHERE statut = 'en_attente'
                ORDER BY date_demande DESC
                LIMIT %s
            """, (limite,))
            rows = cur.fetchall()
            return [dict(r) for r in rows]


def valider_demande(demande_id, admin_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE paiements_attente
                SET statut = 'valide', date_validation = NOW(), admin_id = %s
                WHERE id = %s
            """, (admin_id, demande_id))
            rows = cur.rowcount
        conn.commit()
        return rows > 0


def refuser_demande(demande_id, admin_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE paiements_attente
                SET statut = 'refuse', date_validation = NOW(), admin_id = %s
                WHERE id = %s
            """, (admin_id, demande_id))
            rows = cur.rowcount
        conn.commit()
        return rows > 0


def compter_demandes_en_attente():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM paiements_attente WHERE statut = 'en_attente'")
            result = cur.fetchone()
            return result[0] if result else 0


# =========================================================
# CODES PREMIUM
# =========================================================
def generer_code(jours, prefix="PREM"):
    with get_connection() as conn:
        with conn.cursor() as cur:
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
        return code


def generer_lot_codes(jours, quantite):
    codes = []
    for _ in range(quantite):
        code = generer_code(jours)
        if code:
            codes.append(code)
    return codes


def utiliser_code(code, user_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT jours, utilise FROM codes_premium WHERE code = %s", (code,))
            row = cur.fetchone()

            if not row:
                return {"erreur": "Code introuvable"}

            jours, utilise = row

            if utilise:
                return {"erreur": "Code déjà utilisé"}

            cur.execute("""
                UPDATE codes_premium
                SET utilise = TRUE, utilise_par = %s, date_utilisation = NOW()
                WHERE code = %s
            """, (user_id, code))
        conn.commit()
        return {"jours": jours}


def get_codes_disponibles(limite=50):
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT * FROM codes_premium
                WHERE utilise = FALSE
                ORDER BY date_creation DESC
                LIMIT %s
            """, (limite,))
            rows = cur.fetchall()
            return [dict(r) for r in rows]


def get_codes_utilises(limite=50):
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT * FROM codes_premium
                WHERE utilise = TRUE
                ORDER BY date_utilisation DESC
                LIMIT %s
            """, (limite,))
            rows = cur.fetchall()
            return [dict(r) for r in rows]


def compter_codes_disponibles():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM codes_premium WHERE utilise = FALSE")
            result = cur.fetchone()
            return result[0] if result else 0
