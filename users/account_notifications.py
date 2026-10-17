from users.db import get_connection
from core.utils.logs import log_error


def activer_notifications(user_id):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            UPDATE utilisateurs
            SET notifications_actives = TRUE
            WHERE user_id = %s
        """, (user_id,))
        conn.commit()
        rows = cur.rowcount
        cur.close()
        conn.close()
        return rows > 0
    except Exception as e:
        log_error(f"Erreur activer_notifications : {e}", "ACCOUNTS")
        return False


def desactiver_notifications(user_id):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            UPDATE utilisateurs
            SET notifications_actives = FALSE
            WHERE user_id = %s
        """, (user_id,))
        conn.commit()
        rows = cur.rowcount
        cur.close()
        conn.close()
        return rows > 0
    except Exception as e:
        log_error(f"Erreur desactiver_notifications : {e}", "ACCOUNTS")
        return False


def get_utilisateurs_notifies():
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT user_id FROM utilisateurs
            WHERE notifications_actives = TRUE
        """)
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return [r[0] for r in rows]
    except Exception as e:
        log_error(f"Erreur get_utilisateurs_notifies : {e}", "ACCOUNTS")
        return []


def get_tous_utilisateurs():
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT user_id FROM utilisateurs")
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return [r[0] for r in rows]
    except Exception as e:
        log_error(f"Erreur get_tous_utilisateurs : {e}", "ACCOUNTS")
        return []
