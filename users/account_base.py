import libsql
from datetime import datetime

from users.db import get_connection
from core.utils.logs import log_info, log_error


def utilisateur_existe(user_id):
    conn = get_connection()
    result = conn.execute("SELECT 1 FROM utilisateurs WHERE user_id = ?", (user_id,)).fetchone()
    conn.close()
    return result is not None


def get_user_info(user_id):
    conn = get_connection()
    # On récupère les noms de colonnes pour construire un dictionnaire
    cur = conn.execute("SELECT * FROM utilisateurs WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    if row:
        # Récupérer les noms des colonnes
        columns = [desc[0] for desc in cur.description]
        info = dict(zip(columns, row))
        conn.close()
        return info
    conn.close()
    return None


def get_user_status(user_id):
    info = get_user_info(user_id)
    if not info:
        return 'free', None
    return info['status'], info['date_expiration']


def enregistrer_utilisateur(user_id, username, first_name):
    if utilisateur_existe(user_id):
        return False
        
    conn = get_connection()
    conn.execute("""
        INSERT INTO utilisateurs (user_id, username, first_name, status)
        VALUES (?, ?, ?, 'free')
        ON CONFLICT (user_id) DO NOTHING
    """, (user_id, username or "", first_name or ""))
    conn.commit()
    conn.close()
    log_info(f"Nouvel utilisateur : {first_name} ({user_id})", "ACCOUNTS")
    return True


def set_premium(user_id, date_expiration):
    # SQLite stocke les dates en TEXT. On s'assure que c'est une chaîne.
    if isinstance(date_expiration, datetime):
        date_expiration = date_expiration.strftime("%Y-%m-%d %H:%M:%S")
        
    conn = get_connection()
    conn.execute("""
        UPDATE utilisateurs
        SET status = 'premium', date_expiration = ?
        WHERE user_id = ?
    """, (date_expiration, user_id))
    conn.commit()
    conn.close()
    
    log_info(f"Utilisateur {user_id} passé en PREMIUM (expire {date_expiration})", "ACCOUNTS")
    return True


def est_premium(user_id):
    status, expiration = get_user_status(user_id)
    if status != 'premium' or not expiration:
        return False
    try:
        # SQLite renvoie la date en string, on la convertit
        if isinstance(expiration, str):
            expiration_dt = datetime.strptime(expiration, "%Y-%m-%d %H:%M:%S")
        else:
            expiration_dt = expiration
        return expiration_dt > datetime.now()
    except Exception as e:
        log_error(f"Erreur parsing date expiration : {e}", "ACCOUNTS")
        return False


def get_statut_label(user_id):
    return "PREMIUM" if est_premium(user_id) else "FREE"


def get_langue(user_id):
    conn = get_connection()
    result = conn.execute("SELECT langue FROM utilisateurs WHERE user_id = ?", (user_id,)).fetchone()
    conn.close()
    return result[0] if result and result[0] else "fr"


def set_langue(user_id, langue):
    if langue not in ["fr", "en", "ln"]:
        return False
        
    conn = get_connection()
    conn.execute("""
        UPDATE utilisateurs
        SET langue = ?
        WHERE user_id = ?
    """, (langue, user_id))
    conn.commit()
    conn.close()
    return True
