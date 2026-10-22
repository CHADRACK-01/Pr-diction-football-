from users.db import get_connection


def set_session_competition(user_id, competition):
    """Enregistre la compétition choisie par l'utilisateur en BDD."""
    conn = get_connection()
    conn.execute("""
        INSERT INTO sessions_pronostic (user_id, competition)
        VALUES (?, ?)
        ON CONFLICT (user_id) DO UPDATE SET competition = excluded.competition
    """, (user_id, competition))
    conn.commit()
    conn.close()


def get_session_competition(user_id):
    """Récupère la compétition choisie depuis la BDD."""
    conn = get_connection()
    result = conn.execute(
        "SELECT competition FROM sessions_pronostic WHERE user_id = ?", 
        (user_id,)
    ).fetchone()
    conn.close()
    return result[0] if result else "default"


def clear_session_competition(user_id):
    """Supprime la session après le pronostic."""
    conn = get_connection()
    conn.execute("DELETE FROM sessions_pronostic WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()
