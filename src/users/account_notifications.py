from users.database import get_connection
from core.utils.logs import log_info, log_error


def activer_notifications(user_id):
    """Active les notifications pour un utilisateur."""
    try:
        conn = get_connection()
        conn.execute("""
            UPDATE utilisateurs
            SET notifications_actives = 1
            WHERE user_id = ?
        """, (user_id,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        log_error(f"Impossible d'activer les notifications de {user_id}", "ACCOUNTS", exception=e)
        return False


def desactiver_notifications(user_id):
    """Désactive les notifications pour un utilisateur."""
    try:
        conn = get_connection()
        conn.execute("""
            UPDATE utilisateurs
            SET notifications_actives = 0
            WHERE user_id = ?
        """, (user_id,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        log_error(f"Impossible de désactiver les notifications de {user_id}", "ACCOUNTS", exception=e)
        return False


def get_utilisateurs_notifies():
    """Retourne la liste des utilisateurs qui ont activé les notifications."""
    try:
        conn = get_connection()
        rows = conn.execute("""
            SELECT user_id FROM utilisateurs
            WHERE notifications_actives = 1
        """).fetchall()
        conn.close()
        return [r[0] for r in rows]
    except Exception as e:
        log_error("Impossible de récupérer les utilisateurs notifiés", "ACCOUNTS", exception=e)
        return []


def get_tous_utilisateurs():
    """Retourne la liste de tous les utilisateurs enregistrés."""
    try:
        conn = get_connection()
        rows = conn.execute("SELECT user_id FROM utilisateurs").fetchall()
        conn.close()
        return [r[0] for r in rows]
    except Exception as e:
        log_error("Impossible de récupérer tous les utilisateurs", "ACCOUNTS", exception=e)
        return []
