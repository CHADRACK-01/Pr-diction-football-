import psycopg2.extras
from users.db import get_connection
from core.utils.logs import log_error


def get_parrain(user_id):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT parrain_id FROM utilisateurs WHERE user_id = %s", (user_id,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        return row[0] if row and row[0] else None
    except Exception as e:
        log_error(f"Erreur get_parrain : {e}", "ACCOUNTS")
        return None


def set_parrain(user_id, parrain_id):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            UPDATE utilisateurs
            SET parrain_id = %s
            WHERE user_id = %s AND parrain_id IS NULL
        """, (parrain_id, user_id))
        conn.commit()
        rows = cur.rowcount
        cur.close()
        conn.close()
        return rows > 0
    except Exception as e:
        log_error(f"Erreur set_parrain : {e}", "ACCOUNTS")
        return False


def compter_filleuls(user_id):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM utilisateurs WHERE parrain_id = %s", (user_id,))
        result = cur.fetchone()
        cur.close()
        conn.close()
        return result[0] if result else 0
    except Exception as e:
        log_error(f"Erreur compter_filleuls : {e}", "ACCOUNTS")
        return 0


def get_top_parrains(limite=10):
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT 
                p.user_id,
                p.first_name,
                COUNT(f.user_id) as nb_filleuls
            FROM utilisateurs p
            INNER JOIN utilisateurs f ON f.parrain_id = p.user_id
            GROUP BY p.user_id, p.first_name
            ORDER BY nb_filleuls DESC
            LIMIT %s
        """, (limite,))
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return [dict(r) for r in rows]
    except Exception as e:
        log_error(f"Erreur get_top_parrains : {e}", "ACCOUNTS")
        return []


def get_filleuls(user_id, limite=20):
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT user_id, first_name, date_inscription
            FROM utilisateurs
            WHERE parrain_id = %s
            ORDER BY date_inscription DESC
            LIMIT %s
        """, (user_id, limite))
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return [dict(r) for r in rows]
    except Exception as e:
        log_error(f"Erreur get_filleuls : {e}", "ACCOUNTS")
        return []


def get_palier_atteint(nb_filleuls):
    paliers = [
        (50, 30, "Legende"),
        (20, 15, "Or"),
        (10, 10, "Argent"),
        (5, 7, "Bronze"),
    ]
    for seuil, bonus, nom in paliers:
        if nb_filleuls >= seuil:
            return {"seuil": seuil, "bonus": bonus, "nom": nom}
    return None


def get_prochain_palier(nb_filleuls):
    paliers = [
        (5, 7, "Bronze"),
        (10, 10, "Argent"),
        (20, 15, "Or"),
        (50, 30, "Legende"),
    ]
    for seuil, bonus, nom in paliers:
        if nb_filleuls < seuil:
            return {"seuil": seuil, "bonus": bonus, "nom": nom, "restant": seuil - nb_filleuls}
    return None
