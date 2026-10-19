import psycopg2.extras
from users.db import get_connection


def get_parrain(user_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT parrain_id FROM utilisateurs WHERE user_id = %s", (user_id,))
            row = cur.fetchone()
            return row[0] if row and row[0] else None


def set_parrain(user_id, parrain_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE utilisateurs
                SET parrain_id = %s
                WHERE user_id = %s AND parrain_id IS NULL
            """, (parrain_id, user_id))
            rows = cur.rowcount
        conn.commit()
        return rows > 0


def compter_filleuls(user_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM utilisateurs WHERE parrain_id = %s", (user_id,))
            result = cur.fetchone()
            return result[0] if result else 0


def get_top_parrains(limite=10):
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
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
            return [dict(r) for r in rows]


def get_filleuls(user_id, limite=20):
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT user_id, first_name, date_inscription
                FROM utilisateurs
                WHERE parrain_id = %s
                ORDER BY date_inscription DESC
                LIMIT %s
            """, (user_id, limite))
            rows = cur.fetchall()
            return [dict(r) for r in rows]


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
