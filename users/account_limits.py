from datetime import datetime, timedelta
from config import LIMITE_FREE_JOUR, LIMITE_PREMIUM_JOUR
from users.db import get_connection
from users.account_base import est_premium
from core.utils.logs import log_error


def incrementer_compteur(user_id):
    try:
        today = datetime.now().date()
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO compteurs_jour (user_id, date, compteur)
            VALUES (%s, %s, 1)
            ON CONFLICT (user_id, date)
            DO UPDATE SET compteur = compteurs_jour.compteur + 1
        """, (user_id, today))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        log_error(f"Erreur incrementer_compteur : {e}", "ACCOUNTS")


def get_compteur_jour(user_id):
    try:
        today = datetime.now().date()
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT compteur FROM compteurs_jour WHERE user_id = %s AND date = %s",
            (user_id, today)
        )
        result = cur.fetchone()
        cur.close()
        conn.close()
        return result[0] if result else 0
    except Exception as e:
        log_error(f"Erreur get_compteur_jour : {e}", "ACCOUNTS")
        return 0


def get_limite_jour(user_id):
    """Récupère la limite en fonction du statut, avec paramètre dynamique pour le Free."""
    if est_premium(user_id):
        return LIMITE_PREMIUM_JOUR
    
    from users.admin import get_parametre
    try:
        limite_free_bdd = int(get_parametre("limite_free", LIMITE_FREE_JOUR))
        return limite_free_bdd
    except Exception:
        return LIMITE_FREE_JOUR


def peut_faire_pronostic(user_id):
    return get_compteur_jour(user_id) < get_limite_jour(user_id)


def ajouter_jours_premium(user_id, jours):
    """Ajoute X jours de Premium à un utilisateur (cumulable)."""
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT date_expiration, status FROM utilisateurs WHERE user_id = %s", (user_id,))
        row = cur.fetchone()
        if not row:
            cur.close()
            conn.close()
            return False

        expiration_actuelle, status = row

        if status == 'premium' and expiration_actuelle and expiration_actuelle > datetime.now():
            nouvelle_date = expiration_actuelle + timedelta(days=jours)
        else:
            nouvelle_date = datetime.now() + timedelta(days=jours)

        cur.execute("""
            UPDATE utilisateurs
            SET status = 'premium', date_expiration = %s
            WHERE user_id = %s
        """, (nouvelle_date, user_id))
        conn.commit()
        cur.close()
        conn.close()
        print(f"⭐ +{jours}j Premium pour {user_id} (expire {nouvelle_date})")
        return True
    except Exception as e:
        log_error(f"Erreur ajouter_jours_premium : {e}", "ACCOUNTS")
        return False
