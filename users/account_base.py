import psycopg2.extras
from datetime import datetime

from users.db import get_connection
from core.utils.logs import log_error


def utilisateur_existe(user_id):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM utilisateurs WHERE user_id = %s", (user_id,))
        result = cur.fetchone()
        cur.close()
        conn.close()
        return result is not None
    except Exception as e:
        log_error(f"Erreur utilisateur_existe : {e}", "ACCOUNTS")
        return False


def get_user_info(user_id):
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM utilisateurs WHERE user_id = %s", (user_id,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        return dict(row) if row else None
    except Exception as e:
        log_error(f"Erreur get_user_info : {e}", "ACCOUNTS")
        return None


def get_user_status(user_id):
    info = get_user_info(user_id)
    if not info:
        return 'free', None
    return info['status'], info['date_expiration']


def enregistrer_utilisateur(user_id, username, first_name):
    try:
        if utilisateur_existe(user_id):
            return False
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO utilisateurs (user_id, username, first_name, status)
            VALUES (%s, %s, %s, 'free')
            ON CONFLICT (user_id) DO NOTHING
        """, (user_id, username or "", first_name or ""))
        conn.commit()
        cur.close()
        conn.close()
        print(f"👤 Nouvel utilisateur : {first_name} ({user_id})")
        return True
    except Exception as e:
        log_error(f"Erreur enregistrer_utilisateur : {e}", "ACCOUNTS")
        return False


def set_premium(user_id, date_expiration):
    try:
        if isinstance(date_expiration, str):
            date_expiration = datetime.strptime(date_expiration, "%Y-%m-%d %H:%M")
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            UPDATE utilisateurs
            SET status = 'premium', date_expiration = %s
            WHERE user_id = %s
        """, (date_expiration, user_id))
        conn.commit()
        rows = cur.rowcount
        cur.close()
        conn.close()
        if rows == 0:
            return False
        print(f"⭐ Utilisateur {user_id} passé en PREMIUM")
        return True
    except Exception as e:
        log_error(f"Erreur set_premium : {e}", "ACCOUNTS")
        return False


def est_premium(user_id):
    status, expiration = get_user_status(user_id)
    if status != 'premium' or not expiration:
        return False
    try:
        return expiration > datetime.now()
    except Exception:
        return False


def get_statut_label(user_id):
    return "PREMIUM" if est_premium(user_id) else "FREE"


def get_langue(user_id):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT langue FROM utilisateurs WHERE user_id = %s", (user_id,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        return row[0] if row and row[0] else "fr"
    except Exception as e:
        log_error(f"Erreur get_langue : {e}", "ACCOUNTS")
        return "fr"


def set_langue(user_id, langue):
    try:
        if langue not in ["fr", "en", "ln"]:
            return False
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            UPDATE utilisateurs
            SET langue = %s
            WHERE user_id = %s
        """, (langue, user_id))
        conn.commit()
        rows = cur.rowcount
        cur.close()
        conn.close()
        return rows > 0
    except Exception as e:
        log_error(f"Erreur set_langue : {e}", "ACCOUNTS")
        return False
