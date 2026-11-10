from users.db import get_connection
from core.utils.logs import log_info, log_error, log_warning


def set_session_competition(user_id, competition):
    """
    Enregistre la compétition choisie par l'utilisateur en BDD.
    Retourne True si succès, False sinon.
    """
    try:
        conn = get_connection()
        try:
            conn.execute("""
                INSERT INTO sessions_pronostic (user_id, competition)
                VALUES (?, ?)
                ON CONFLICT (user_id) DO UPDATE SET competition = excluded.competition
            """, (user_id, competition))
            conn.commit()
            log_info(f"Session définie pour {user_id} : {competition}", "SESSION")
            return True
        finally:
            try:
                conn.close()
            except Exception as e:
                log_warning(f"Impossible de fermer la connexion pour {user_id} : {e}", "SESSION")
    except Exception as e:
        log_error(f"Impossible d'enregistrer la session de {user_id} ({competition})", "SESSION", exception=e)
        return False


def get_session_competition(user_id):
    """
    Récupère la compétition choisie depuis la BDD.
    Retourne "default" en cas d'erreur ou si aucune session n'existe.
    """
    try:
        conn = get_connection()
        try:
            result = conn.execute(
                "SELECT competition FROM sessions_pronostic WHERE user_id = ?", 
                (user_id,)
            ).fetchone()
            return result[0] if result else "default"
        finally:
            try:
                conn.close()
            except Exception as e:
                log_warning(f"Impossible de fermer la connexion pour {user_id} : {e}", "SESSION")
    except Exception as e:
        log_error(f"Impossible de récupérer la session de {user_id}", "SESSION", exception=e)
        return "default"


def clear_session_competition(user_id):
    """
    Supprime la session après le pronostic.
    Retourne True si succès, False sinon.
    """
    try:
        conn = get_connection()
        try:
            conn.execute("DELETE FROM sessions_pronostic WHERE user_id = ?", (user_id,))
            conn.commit()
            log_info(f"Session supprimée pour {user_id}", "SESSION")
            return True
        finally:
            try:
                conn.close()
            except Exception as e:
                log_warning(f"Impossible de fermer la connexion pour {user_id} : {e}", "SESSION")
    except Exception as e:
        log_error(f"Impossible de supprimer la session de {user_id}", "SESSION", exception=e)
        return False
