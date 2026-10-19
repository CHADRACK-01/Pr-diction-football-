from users.db import get_connection
from core.utils.logs import log_info


def activer_notifications(user_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE utilisateurs
                SET notifications_actives = TRUE
                WHERE user_id = %s
            """, (user_id,))
            rows = cur.rowcount
        conn.commit()
        return rows > 0


def desactiver_notifications(user_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE utilisateurs
                SET notifications_actives = FALSE
                WHERE user_id = %s
            """, (user_id,))
            rows = cur.rowcount
        conn.commit()
        return rows > 0


def get_utilisateurs_notifies():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT user_id FROM utilisateurs
                WHERE notifications_actives = TRUE
            """)
            rows = cur.fetchall()
            return [r[0] for r in rows]


def get_tous_utilisateurs():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT user_id FROM utilisateurs")
            rows = cur.fetchall()
            return [r[0] for r in rows]
