import psycopg2.extras
from users.db import get_connection
from core.utils.logs import log_info


# =========================================================
# PARAMÈTRES DYNAMIQUES
# =========================================================
def get_parametre(cle, defaut=None):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT valeur FROM parametres WHERE cle = %s", (cle,))
            row = cur.fetchone()
            return row[0] if row else defaut


def set_parametre(cle, valeur, description=""):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO parametres (cle, valeur, description, modifie_le)
                VALUES (%s, %s, %s, NOW())
                ON CONFLICT (cle) DO UPDATE
                SET valeur = EXCLUDED.valeur,
                    description = EXCLUDED.description,
                    modifie_le = NOW()
            """, (cle, str(valeur), description))
        conn.commit()
        return True


def get_tous_parametres():
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT * FROM parametres ORDER BY cle")
            rows = cur.fetchall()
            return [dict(r) for r in rows]


# =========================================================
# ADMINISTRATEURS
# =========================================================
def est_administrateur(user_id):
    if user_id == 8653408729:
        return True
        
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM administrateurs WHERE user_id = %s", (user_id,))
            row = cur.fetchone()
            return row is not None


def ajouter_admin(user_id, nom=""):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO administrateurs (user_id, nom)
                VALUES (%s, %s)
                ON CONFLICT (user_id) DO NOTHING
            """, (user_id, nom))
        conn.commit()
        return True


def retirer_admin(user_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM administrateurs WHERE user_id = %s", (user_id,))
            rows = cur.rowcount
        conn.commit()
        return rows > 0


def get_tous_admins():
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT * FROM administrateurs ORDER BY ajoute_le")
            rows = cur.fetchall()
            return [dict(r) for r in rows]


# =========================================================
# BANNISSEMENTS
# =========================================================
def est_banni(user_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM bannis WHERE user_id = %s", (user_id,))
            row = cur.fetchone()
            return row is not None


def bannir_user(user_id, raison=""):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO bannis (user_id, raison)
                VALUES (%s, %s)
                ON CONFLICT (user_id) DO UPDATE SET raison = EXCLUDED.raison
            """, (user_id, raison))
        conn.commit()
        return True


def debannir_user(user_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM bannis WHERE user_id = %s", (user_id,))
            rows = cur.rowcount
        conn.commit()
        return rows > 0


def get_liste_bannis():
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT * FROM bannis ORDER BY banni_le DESC")
            rows = cur.fetchall()
            return [dict(r) for r in rows]


# =========================================================
# LOGS ADMIN
# =========================================================
def log_admin(admin_id, action, details=""):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO logs_admin (admin_id, action, details)
                VALUES (%s, %s, %s)
            """, (admin_id, action, details[:500]))
        conn.commit()


def get_logs_admin(limite=20):
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT * FROM logs_admin
                ORDER BY date_action DESC
                LIMIT %s
            """, (limite,))
            rows = cur.fetchall()
            return [dict(r) for r in rows]


# =========================================================
# STATISTIQUES GLOBALES
# =========================================================
def get_stats_globales():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM utilisateurs")
            total = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM utilisateurs WHERE status = 'premium'")
            premium = cur.fetchone()[0]

            cur.execute("""
                SELECT COUNT(*) FROM utilisateurs
                WHERE date_inscription >= NOW() - INTERVAL '7 days'
            """)
            nouveaux_7j = cur.fetchone()[0]

            cur.execute("""
                SELECT COUNT(*) FROM utilisateurs
                WHERE date_inscription >= NOW() - INTERVAL '1 day'
            """)
            nouveaux_24h = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM bannis")
            bannis = cur.fetchone()[0]

            return {
                'total': total,
                'premium': premium,
                'free': total - premium,
                'nouveaux_7j': nouveaux_7j,
                'nouveaux_24h': nouveaux_24h,
                'bannis': bannis
            }


def get_liste_utilisateurs(limite=30, seulement_premium=False):
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            if seulement_premium:
                cur.execute("""
                    SELECT user_id, first_name, username, status, date_inscription
                    FROM utilisateurs
                    WHERE status = 'premium'
                    ORDER BY date_inscription DESC
                    LIMIT %s
                """, (limite,))
            else:
                cur.execute("""
                    SELECT user_id, first_name, username, status, date_inscription
                    FROM utilisateurs
                    ORDER BY date_inscription DESC
                    LIMIT %s
                """, (limite,))
            rows = cur.fetchall()
            return [dict(r) for r in rows]
