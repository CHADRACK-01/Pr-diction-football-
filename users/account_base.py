import psycopg2.extras
from datetime import datetime

from users.db import get_connection
from core.utils.logs import log_info, log_error


def utilisateur_existe(user_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM utilisateurs WHERE user_id = %s", (user_id,))
            result = cur.fetchone()
            return result is not None


def get_user_info(user_id):
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT * FROM utilisateurs WHERE user_id = %s", (user_id,))
            row = cur.fetchone()
            return dict(row) if row else None


def get_user_status(user_id):
    info = get_user_info(user_id)
    if not info:
        return 'free', None
    return info['status'], info['date_expiration']


def enregistrer_utilisateur(user_id, username, first_name):
    if utilisateur_existe(user_id):
        return False
        
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO utilisateurs (user_id, username, first_name, status)
                VALUES (%s, %s, %s, 'free')
                ON CONFLICT (user_id) DO NOTHING
            """, (user_id, username or "", first_name or ""))
        conn.commit()
        log_info(f"Nouvel utilisateur : {first_name} ({user_id})", "ACCOUNTS")
        return True


def set_premium(user_id, date_expiration):
    if isinstance(date_expiration, str):
        date_expiration = datetime.strptime(date_expiration, "%Y-%m-%d %H:%M")
        
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE utilisateurs
                SET status = 'premium', date_expiration = %s
                WHERE user_id = %s
            """, (date_expiration, user_id))
            rows = cur.rowcount
        conn.commit()
        
        if rows == 0:
            return False
            
        log_info(f"Utilisateur {user_id} passé en PREMIUM", "ACCOUNTS")
        return True


def est_premium(user_id):
    status, expiration = get_user_status(user_id)
    if status != 'premium' or not expiration:
        return False
    return expiration > datetime.now()


def get_statut_label(user_id):
    return "PREMIUM" if est_premium(user_id) else "FREE"


def get_langue(user_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT langue FROM utilisateurs WHERE user_id = %s", (user_id,))
            row = cur.fetchone()
            return row[0] if row and row[0] else "fr"


def set_langue(user_id, langue):
    if langue not in ["fr", "en", "ln"]:
        return False
        
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE utilisateurs
                SET langue = %s
                WHERE user_id = %s
            """, (langue, user_id))
            rows = cur.rowcount
        conn.commit()
        return rows > 0
