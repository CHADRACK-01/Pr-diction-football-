from datetime import datetime, timedelta
from config import LIMITE_FREE_JOUR, LIMITE_PREMIUM_JOUR
from users.db import get_connection
from users.account_base import est_premium
from core.utils.logs import log_info, log_error, log_warning


def incrementer_compteur(user_id):
    """Incrémente le compteur de pronostics du jour (avec gestion d'erreur)."""
    today = datetime.now().strftime("%Y-%m-%d")
    try:
        conn = get_connection()
        conn.execute("""
            INSERT INTO compteurs_jour (user_id, date, compteur)
            VALUES (?, ?, 1)
            ON CONFLICT (user_id, date)
            DO UPDATE SET compteur = compteurs_jour.compteur + 1
        """, (user_id, today))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        log_error(f"Impossible d'incrémenter le compteur de {user_id}", "ACCOUNTS", exception=e)
        return False


def get_compteur_jour(user_id):
    """Récupère le nombre de pronostics effectués aujourd'hui."""
    today = datetime.now().strftime("%Y-%m-%d")
    try:
        conn = get_connection()
        result = conn.execute(
            "SELECT compteur FROM compteurs_jour WHERE user_id = ? AND date = ?",
            (user_id, today)
        ).fetchone()
        conn.close()
        return result[0] if result else 0
    except Exception as e:
        log_error(f"Impossible de récupérer le compteur de {user_id}", "ACCOUNTS", exception=e)
        return 0


def get_limite_jour(user_id):
    """Récupère la limite en fonction du statut (Free ou Premium)."""
    try:
        if est_premium(user_id):
            return LIMITE_PREMIUM_JOUR
    except Exception as e:
        log_warning(f"Impossible de vérifier le statut de {user_id} : {e}", "ACCOUNTS")
    
    from users.admin import get_parametre
    limite_free_bdd = get_parametre("limite_free", LIMITE_FREE_JOUR)
    
    try:
        return int(limite_free_bdd)
    except (ValueError, TypeError):
        return LIMITE_FREE_JOUR


def peut_faire_pronostic(user_id):
    """Vérifie si l'utilisateur peut encore faire un pronostic aujourd'hui."""
    try:
        return get_compteur_jour(user_id) < get_limite_jour(user_id)
    except Exception as e:
        log_error(f"Impossible de vérifier la limite de {user_id}", "ACCOUNTS", exception=e)
        return False


def ajouter_jours_premium(user_id, jours):
    """Ajoute X jours de Premium à un utilisateur (cumulable)."""
    try:
        conn = get_connection()
        row = conn.execute(
            "SELECT date_expiration, status FROM utilisateurs WHERE user_id = ?",
            (user_id,)
        ).fetchone()
        
        if not row:
            conn.close()
            log_warning(f"Utilisateur {user_id} introuvable pour ajout premium", "ACCOUNTS")
            return False

        expiration_actuelle, status = row
        maintenant = datetime.now()
        
        if status == 'premium' and expiration_actuelle:
            try:
                expiration_dt = datetime.strptime(expiration_actuelle, "%Y-%m-%d %H:%M:%S")
                if expiration_dt > maintenant:
                    nouvelle_date = expiration_dt + timedelta(days=jours)
                else:
                    nouvelle_date = maintenant + timedelta(days=jours)
            except Exception:
                nouvelle_date = maintenant + timedelta(days=jours)
        else:
            nouvelle_date = maintenant + timedelta(days=jours)

        nouvelle_date_str = nouvelle_date.strftime("%Y-%m-%d %H:%M:%S")
        conn.execute("""
            UPDATE utilisateurs
            SET status = 'premium', date_expiration = ?
            WHERE user_id = ?
        """, (nouvelle_date_str, user_id))
        conn.commit()
        conn.close()
        
        log_info(f"+{jours}j Premium pour {user_id} (expire {nouvelle_date_str})", "ACCOUNTS")
        return True
    except Exception as e:
        log_error(f"Impossible d'ajouter {jours}j premium à {user_id}", "ACCOUNTS", exception=e)
        return False
