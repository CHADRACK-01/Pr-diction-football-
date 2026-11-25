from users.database import get_connection
from core.utils.logs import log_info, log_error, log_warning


def get_parrain(user_id):
    """Récupère l'ID du parrain d'un utilisateur."""
    try:
        conn = get_connection()
        result = conn.execute(
            "SELECT parrain_id FROM utilisateurs WHERE user_id = ?", 
            (user_id,)
        ).fetchone()
        conn.close()
        return result[0] if result and result[0] else None
    except Exception as e:
        log_error(f"Impossible de récupérer le parrain de {user_id}", "ACCOUNTS", exception=e)
        return None


def set_parrain(user_id, parrain_id):
    """Définit le parrain d'un utilisateur (si pas déjà défini)."""
    try:
        conn = get_connection()
        existing = conn.execute(
            "SELECT parrain_id FROM utilisateurs WHERE user_id = ?", 
            (user_id,)
        ).fetchone()
        
        if existing and existing[0] is not None:
            conn.close()
            return False
        
        conn.execute("""
            UPDATE utilisateurs
            SET parrain_id = ?
            WHERE user_id = ? AND parrain_id IS NULL
        """, (parrain_id, user_id))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        log_error(f"Impossible de définir le parrain de {user_id}", "ACCOUNTS", exception=e)
        return False


def compter_filleuls(user_id):
    """Compte le nombre de filleuls d'un utilisateur."""
    try:
        conn = get_connection()
        result = conn.execute(
            "SELECT COUNT(*) FROM utilisateurs WHERE parrain_id = ?", 
            (user_id,)
        ).fetchone()
        conn.close()
        return result[0] if result else 0
    except Exception as e:
        log_error(f"Impossible de compter les filleuls de {user_id}", "ACCOUNTS", exception=e)
        return 0


def get_top_parrains(limite=10):
    """Retourne le classement des meilleurs parrains."""
    try:
        conn = get_connection()
        cur = conn.execute("""
            SELECT 
                p.user_id,
                p.first_name,
                COUNT(f.user_id) as nb_filleuls
            FROM utilisateurs p
            INNER JOIN utilisateurs f ON f.parrain_id = p.user_id
            GROUP BY p.user_id, p.first_name
            ORDER BY nb_filleuls DESC
            LIMIT ?
        """, (limite,))
        rows = cur.fetchall()
        columns = [desc[0] for desc in cur.description]
        conn.close()
        return [dict(zip(columns, row)) for row in rows]
    except Exception as e:
        log_error("Impossible de récupérer le classement des parrains", "ACCOUNTS", exception=e)
        return []


def get_filleuls(user_id, limite=20):
    """Retourne la liste des filleuls d'un utilisateur."""
    try:
        conn = get_connection()
        cur = conn.execute("""
            SELECT user_id, first_name, date_inscription
            FROM utilisateurs
            WHERE parrain_id = ?
            ORDER BY date_inscription DESC
            LIMIT ?
        """, (user_id, limite))
        rows = cur.fetchall()
        columns = [desc[0] for desc in cur.description]
        conn.close()
        return [dict(zip(columns, row)) for row in rows]
    except Exception as e:
        log_error(f"Impossible de récupérer les filleuls de {user_id}", "ACCOUNTS", exception=e)
        return []


def get_palier_atteint(nb_filleuls):
    """Retourne le palier atteint en fonction du nombre de filleuls."""
    paliers = [
        (50, 30, "Legende"),
        (20, 15, "Or"),
        (10, 10, "Argent"),
        (5, 7, "Bronze"),
    ]
    for seuil, bonus, nom in paliers:
        if nb_filleuls >= seuil:
            return {"seuil": seuil, "bonus": bonus, "nom": nom}
    return None


def get_prochain_palier(nb_filleuls):
    """Retourne le prochain palier à atteindre."""
    paliers = [
        (5, 7, "Bronze"),
        (10, 10, "Argent"),
        (20, 15, "Or"),
        (50, 30, "Legende"),
    ]
    for seuil, bonus, nom in paliers:
        if nb_filleuls < seuil:
            return {"seuil": seuil, "bonus": bonus, "nom": nom, "restant": seuil - nb_filleuls}
    return None
