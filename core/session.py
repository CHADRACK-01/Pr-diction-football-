from users.db import get_connection
from core.utils.logs import log_info


def set_session_competition(user_id, competition):
    """Enregistre la compétition choisie par l'utilisateur en BDD."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO sessions_pronostic (user_id, competition)
                VALUES (%s, %s)
                ON CONFLICT (user_id) DO UPDATE SET competition = EXCLUDED.competition
            """, (user_id, competition))
        conn.commit()


def get_session_competition(user_id):
    """Récupère la compétition choisie depuis la BDD."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT competition FROM sessions_pronostic WHERE user_id = %s", (user_id,))
            row = cur.fetchone()
            return row[0] if row else "default"


def clear_session_competition(user_id):
    """Supprime la session après le pronostic."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM sessions_pronostic WHERE user_id = %s", (user_id,))
        conn.commit()
