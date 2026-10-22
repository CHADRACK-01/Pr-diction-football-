from users.db import get_connection
from core.utils.logs import log_info


# =========================================================
# PARAMÈTRES DYNAMIQUES
# =========================================================
def get_parametre(cle, defaut=None):
    """Récupère un paramètre par sa clé."""
    conn = get_connection()
    result = conn.execute("SELECT valeur FROM parametres WHERE cle = ?", (cle,)).fetchone()
    conn.close()
    return result[0] if result else defaut


def set_parametre(cle, valeur, description=""):
    """Définit ou met à jour un paramètre."""
    conn = get_connection()
    conn.execute("""
        INSERT INTO parametres (cle, valeur, description, modifie_le)
        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT (cle) DO UPDATE
        SET valeur = excluded.valeur,
            description = excluded.description,
            modifie_le = CURRENT_TIMESTAMP
    """, (cle, str(valeur), description))
    conn.commit()
    conn.close()
    return True


def get_tous_parametres():
    """Récupère tous les paramètres."""
    conn = get_connection()
    cur = conn.execute("SELECT * FROM parametres ORDER BY cle")
    rows = cur.fetchall()
    columns = [desc[0] for desc in cur.description]
    conn.close()
    return [dict(zip(columns, row)) for row in rows]


# =========================================================
# ADMINISTRATEURS
# =========================================================
def est_administrateur(user_id):
    """Vérifie si un utilisateur est administrateur."""
    if user_id == 8653408729:
        return True
        
    conn = get_connection()
    result = conn.execute("SELECT 1 FROM administrateurs WHERE user_id = ?", (user_id,)).fetchone()
    conn.close()
    return result is not None


def ajouter_admin(user_id, nom=""):
    """Ajoute un administrateur."""
    conn = get_connection()
    conn.execute("""
        INSERT INTO administrateurs (user_id, nom)
        VALUES (?, ?)
        ON CONFLICT (user_id) DO NOTHING
    """, (user_id, nom))
    conn.commit()
    conn.close()
    return True


def retirer_admin(user_id):
    """Retire un administrateur."""
    conn = get_connection()
    conn.execute("DELETE FROM administrateurs WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()
    return True


def get_tous_admins():
    """Récupère tous les administrateurs."""
    conn = get_connection()
    cur = conn.execute("SELECT * FROM administrateurs ORDER BY ajoute_le")
    rows = cur.fetchall()
    columns = [desc[0] for desc in cur.description]
    conn.close()
    return [dict(zip(columns, row)) for row in rows]


# =========================================================
# BANNISSEMENTS
# =========================================================
def est_banni(user_id):
    """Vérifie si un utilisateur est banni."""
    conn = get_connection()
    result = conn.execute("SELECT 1 FROM bannis WHERE user_id = ?", (user_id,)).fetchone()
    conn.close()
    return result is not None


def bannir_user(user_id, raison=""):
    """Bannit un utilisateur."""
    conn = get_connection()
    conn.execute("""
        INSERT INTO bannis (user_id, raison)
        VALUES (?, ?)
        ON CONFLICT (user_id) DO UPDATE SET raison = excluded.raison
    """, (user_id, raison))
    conn.commit()
    conn.close()
    return True


def debannir_user(user_id):
    """Débannit un utilisateur."""
    conn = get_connection()
    conn.execute("DELETE FROM bannis WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()
    return True


def get_liste_bannis():
    """Récupère la liste des utilisateurs bannis."""
    conn = get_connection()
    cur = conn.execute("SELECT * FROM bannis ORDER BY banni_le DESC")
    rows = cur.fetchall()
    columns = [desc[0] for desc in cur.description]
    conn.close()
    return [dict(zip(columns, row)) for row in rows]


# =========================================================
# LOGS ADMIN
# =========================================================
def log_admin(admin_id, action, details=""):
    """Enregistre une action d'administrateur."""
    conn = get_connection()
    conn.execute("""
        INSERT INTO logs_admin (admin_id, action, details)
        VALUES (?, ?, ?)
    """, (admin_id, action, details[:500]))
    conn.commit()
    conn.close()


def get_logs_admin(limite=20):
    """Récupère les derniers logs administrateur."""
    conn = get_connection()
    cur = conn.execute("""
        SELECT * FROM logs_admin
        ORDER BY date_action DESC
        LIMIT ?
    """, (limite,))
    rows = cur.fetchall()
    columns = [desc[0] for desc in cur.description]
    conn.close()
    return [dict(zip(columns, row)) for row in rows]


# =========================================================
# STATISTIQUES GLOBALES
# =========================================================
def get_stats_globales():
    """Récupère les statistiques globales du bot."""
    conn = get_connection()

    total = conn.execute("SELECT COUNT(*) FROM utilisateurs").fetchone()[0]
    premium = conn.execute("SELECT COUNT(*) FROM utilisateurs WHERE status = 'premium'").fetchone()[0]
    nouveaux_7j = conn.execute("""
        SELECT COUNT(*) FROM utilisateurs
        WHERE date_inscription >= datetime('now', '-7 days')
    """).fetchone()[0]
    nouveaux_24h = conn.execute("""
        SELECT COUNT(*) FROM utilisateurs
        WHERE date_inscription >= datetime('now', '-1 day')
    """).fetchone()[0]
    bannis = conn.execute("SELECT COUNT(*) FROM bannis").fetchone()[0]

    conn.close()

    return {
        'total': total,
        'premium': premium,
        'free': total - premium,
        'nouveaux_7j': nouveaux_7j,
        'nouveaux_24h': nouveaux_24h,
        'bannis': bannis
    }


def get_liste_utilisateurs(limite=30, seulement_premium=False):
    """Récupère la liste des utilisateurs récents."""
    conn = get_connection()
    
    if seulement_premium:
        cur = conn.execute("""
            SELECT user_id, first_name, username, status, date_inscription
            FROM utilisateurs
            WHERE status = 'premium'
            ORDER BY date_inscription DESC
            LIMIT ?
        """, (limite,))
    else:
        cur = conn.execute("""
            SELECT user_id, first_name, username, status, date_inscription
            FROM utilisateurs
            ORDER BY date_inscription DESC
            LIMIT ?
        """, (limite,))
    
    rows = cur.fetchall()
    columns = [desc[0] for desc in cur.description]
    conn.close()
    return [dict(zip(columns, row)) for row in rows]
