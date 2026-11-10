import libsql
from datetime import datetime

from users.db import get_connection
from core.utils.logs import log_info, log_error, log_warning


def utilisateur_existe(user_id):
    """Vérifie si un utilisateur existe (avec gestion d'erreur)."""
    try:
        conn = get_connection()
        result = conn.execute("SELECT 1 FROM utilisateurs WHERE user_id = ?", (user_id,)).fetchone()
        conn.close()
        return result is not None
    except Exception as e:
        log_error(f"Impossible de vérifier l'existence de {user_id}", "ACCOUNTS", exception=e)
        return False


def get_user_info(user_id):
    """Récupère les infos d'un utilisateur (avec gestion d'erreur)."""
    try:
        conn = get_connection()
        cur = conn.execute("SELECT * FROM utilisateurs WHERE user_id = ?", (user_id,))
        row = cur.fetchone()
        if row:
            columns = [desc[0] for desc in cur.description]
            info = dict(zip(columns, row))
            conn.close()
            return info
        conn.close()
        return None
    except Exception as e:
        log_error(f"Impossible de récupérer les infos de {user_id}", "ACCOUNTS", exception=e)
        return None


def get_user_status(user_id):
    """Récupère le statut d'un utilisateur."""
    info = get_user_info(user_id)
    if not info:
        return 'free', None
    return info.get('status', 'free'), info.get('date_expiration')


def enregistrer_utilisateur(user_id, username, first_name):
    """Enregistre un nouvel utilisateur (avec gestion d'erreur)."""
    try:
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
    except Exception as e:
        log_error(f"Impossible d'enregistrer l'utilisateur {user_id}", "ACCOUNTS", exception=e)
        return False


def set_premium(user_id, date_expiration):
    """Passe un utilisateur en Premium (avec gestion d'erreur)."""
    if isinstance(date_expiration, datetime):
        date_expiration = date_expiration.strftime("%Y-%m-%d %H:%M:%S")
    
    try:
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
    except Exception as e:
        log_error(f"Impossible de passer {user_id} en premium", "ACCOUNTS", exception=e)
        return False


def est_premium(user_id):
    """Vérifie si un utilisateur est Premium (avec gestion d'erreur)."""
    status, expiration = get_user_status(user_id)
    if status != 'premium' or not expiration:
        return False
    try:
        if isinstance(expiration, str):
            expiration_dt = datetime.strptime(expiration, "%Y-%m-%d %H:%M:%S")
        else:
            expiration_dt = expiration
        return expiration_dt > datetime.now()
    except Exception as e:
        log_warning(f"Erreur parsing date expiration pour {user_id} : {e}", "ACCOUNTS")
        return False


def get_statut_label(user_id):
    """Retourne le label du statut ('PREMIUM' ou 'FREE')."""
    return "PREMIUM" if est_premium(user_id) else "FREE"


def get_langue(user_id):
    """Récupère la langue d'un utilisateur (avec gestion d'erreur)."""
    try:
        conn = get_connection()
        result = conn.execute("SELECT langue FROM utilisateurs WHERE user_id = ?", (user_id,)).fetchone()
        conn.close()
        return result[0] if result and result[0] else "fr"
    except Exception as e:
        log_error(f"Impossible de récupérer la langue de {user_id}", "ACCOUNTS", exception=e)
        return "fr"


def set_langue(user_id, langue):
    """Change la langue d'un utilisateur (avec gestion d'erreur)."""
    if langue not in ["fr", "en", "ln"]:
        return False
        
    try:
        conn = get_connection()
        conn.execute("""
            UPDATE utilisateurs
            SET langue = ?
            WHERE user_id = ?
        """, (langue, user_id))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        log_error(f"Impossible de changer la langue de {user_id}", "ACCOUNTS", exception=e)
        return False
