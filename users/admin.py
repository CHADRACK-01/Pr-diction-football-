import psycopg2.extras
from users.db import get_connection
from core.utils.logs import log_error


# =========================================================
# PARAMÈTRES DYNAMIQUES
# =========================================================
def get_parametre(cle, defaut=None):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT valeur FROM parametres WHERE cle = %s", (cle,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        return row[0] if row else defaut
    except Exception as e:
        log_error(f"Erreur get_parametre : {e}", "ADMIN")
        return defaut


def set_parametre(cle, valeur, description=""):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO parametres (cle, valeur, description, modifie_le)
            VALUES (%s, %s, %s, NOW())
            ON CONFLICT (cle) DO UPDATE
            SET valeur = EXCLUDED.valeur,
                description = EXCLUDED.description,
                modifie_le = NOW()
        """, (cle, str(valeur), description))
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        log_error(f"Erreur set_parametre : {e}", "ADMIN")
        return False


def get_tous_parametres():
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM parametres ORDER BY cle")
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return [dict(r) for r in rows]
    except Exception as e:
        log_error(f"Erreur get_tous_parametres : {e}", "ADMIN")
        return []


# =========================================================
# ADMINISTRATEURS
# =========================================================
def est_administrateur(user_id):
    if user_id == 8653408729:
        return True
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM administrateurs WHERE user_id = %s", (user_id,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        return row is not None
    except Exception as e:
        log_error(f"Erreur est_administrateur : {e}", "ADMIN")
        return False


def ajouter_admin(user_id, nom=""):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO administrateurs (user_id, nom)
            VALUES (%s, %s)
            ON CONFLICT (user_id) DO NOTHING
        """, (user_id, nom))
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        log_error(f"Erreur ajouter_admin : {e}", "ADMIN")
        return False


def retirer_admin(user_id):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM administrateurs WHERE user_id = %s", (user_id,))
        conn.commit()
        rows = cur.rowcount
        cur.close()
        conn.close()
        return rows > 0
    except Exception as e:
        log_error(f"Erreur retirer_admin : {e}", "ADMIN")
        return False


def get_tous_admins():
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM administrateurs ORDER BY ajoute_le")
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return [dict(r) for r in rows]
    except Exception as e:
        log_error(f"Erreur get_tous_admins : {e}", "ADMIN")
        return []


# =========================================================
# BANNISSEMENTS
# =========================================================
def est_banni(user_id):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM bannis WHERE user_id = %s", (user_id,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        return row is not None
    except Exception as e:
        log_error(f"Erreur est_banni : {e}", "ADMIN")
        return False


def bannir_user(user_id, raison=""):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO bannis (user_id, raison)
            VALUES (%s, %s)
            ON CONFLICT (user_id) DO UPDATE SET raison = EXCLUDED.raison
        """, (user_id, raison))
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        log_error(f"Erreur bannir_user : {e}", "ADMIN")
        return False


def debannir_user(user_id):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM bannis WHERE user_id = %s", (user_id,))
        conn.commit()
        rows = cur.rowcount
        cur.close()
        conn.close()
        return rows > 0
    except Exception as e:
        log_error(f"Erreur debannir_user : {e}", "ADMIN")
        return False


def get_liste_bannis():
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM bannis ORDER BY banni_le DESC")
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return [dict(r) for r in rows]
    except Exception as e:
        log_error(f"Erreur get_liste_bannis : {e}", "ADMIN")
        return []


# =========================================================
# LOGS ADMIN
# =========================================================
def log_admin(admin_id, action, details=""):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO logs_admin (admin_id, action, details)
            VALUES (%s, %s, %s)
        """, (admin_id, action, details[:500]))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        log_error(f"Erreur log_admin : {e}", "ADMIN")


def get_logs_admin(limite=20):
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT * FROM logs_admin
            ORDER BY date_action DESC
            LIMIT %s
        """, (limite,))
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return [dict(r) for r in rows]
    except Exception as e:
        log_error(f"Erreur get_logs_admin : {e}", "ADMIN")
        return []


# =========================================================
# STATISTIQUES GLOBALES
# =========================================================
def get_stats_globales():
    try:
        conn = get_connection()
        cur = conn.cursor()

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

        cur.close()
        conn.close()

        return {
            'total': total,
            'premium': premium,
            'free': total - premium,
            'nouveaux_7j': nouveaux_7j,
            'nouveaux_24h': nouveaux_24h,
            'bannis': bannis
        }
    except Exception as e:
        log_error(f"Erreur get_stats_globales : {e}", "ADMIN")
        return {}


def get_liste_utilisateurs(limite=30, seulement_premium=False):
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
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
        cur.close()
        conn.close()
        return [dict(r) for r in rows]
    except Exception as e:
        log_error(f"Erreur get_liste_utilisateurs : {e}", "ADMIN")
        return []
