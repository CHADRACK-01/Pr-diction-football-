from users.db import get_connection
from core.utils.logs import log_info


def activer_notifications(user_id):
    """Active les notifications pour un utilisateur."""
    conn = get_connection()
    conn.execute("""
        UPDATE utilisateurs
        SET notifications_actives = 1
        WHERE user_id = ?
    """, (user_id,))
    conn.commit()
    conn.close()
    return True


def desactiver_notifications(user_id):
    """Désactive les notifications pour un utilisateur."""
    conn = get_connection()
    conn.execute("""
        UPDATE utilisateurs
        SET notifications_actives = 0
        WHERE user_id = ?
    """, (user_id,))
    conn.commit()
    conn.close()
    return True


def get_utilisateurs_notifies():
    """Retourne la liste des utilisateurs qui ont activé les notifications."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT user_id FROM utilisateurs
        WHERE notifications_actives = 1
    """).fetchall()
    conn.close()
    return [r[0] for r in rows]


def get_tous_utilisateurs():
    """Retourne la liste de tous les utilisateurs enregistrés."""
    conn = get_connection()
    rows = conn.execute("SELECT user_id FROM utilisateurs").fetchall()
    conn.close()
    return [r[0] for r in rows]
