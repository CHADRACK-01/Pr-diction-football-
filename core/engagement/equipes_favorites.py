# core/equipes_favorites.py
"""
Fonctionnalité 10 : Calendrier Perso "Mes Équipes".
Permet à l'utilisateur de choisir jusqu'à 5 équipes favorites.
"""

from users.db import db_execute, db_fetchone, db_fetchall
from core.utils.logs import log_info, log_error


def _assurer_table_favoris():
    """Crée la table des équipes favorites si elle n'existe pas."""
    db_execute(
        """
        CREATE TABLE IF NOT EXISTS equipes_favorites (
            user_id INTEGER,
            equipe TEXT,
            date_ajout TEXT DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, equipe)
        )
        """,
        db_context={"table": "equipes_favorites", "operation": "create"}
    )


def ajouter_favori(user_id, equipe):
    """Ajoute une équipe aux favoris d'un utilisateur (max 5)."""
    _assurer_table_favoris()

    # Vérifier la limite de 5
    rows = db_fetchall(
        "SELECT equipe FROM equipes_favorites WHERE user_id = ?",
        params=[user_id],
        db_context={"table": "equipes_favorites", "operation": "count"}
    )
    
    if len(rows) >= 5:
        return False, "Tu as déjà 5 équipes favorites. Supprime-en une pour en ajouter une nouvelle."

    equipe = equipe.strip()
    if not equipe:
        return False, "Nom d'équipe invalide."

    rowcount = db_execute(
        "INSERT OR IGNORE INTO equipes_favorites (user_id, equipe) VALUES (?, ?)",
        params=[user_id, equipe],
        db_context={"table": "equipes_favorites", "operation": "insert"}
    )

    if rowcount is None:
        return False, "Erreur lors de l'ajout."

    log_info(f"Équipe {equipe} ajoutée aux favoris de {user_id}", "FAVORIS")
    return True, f"✅ {equipe} ajoutée à tes favoris !"


def supprimer_favori(user_id, equipe):
    """Supprime une équipe des favoris d'un utilisateur."""
    _assurer_table_favoris()

    rowcount = db_execute(
        "DELETE FROM equipes_favorites WHERE user_id = ? AND equipe = ?",
        params=[user_id, equipe.strip()],
        db_context={"table": "equipes_favorites", "operation": "delete"}
    )

    if rowcount is None or rowcount == 0:
        return False, "Cette équipe n'est pas dans tes favoris."

    return True, f"✅ {equipe} retirée de tes favoris."


def lister_favoris(user_id):
    """Liste les équipes favorites d'un utilisateur."""
    _assurer_table_favoris()

    rows = db_fetchall(
        "SELECT equipe FROM equipes_favorites WHERE user_id = ?",
        params=[user_id],
        db_context={"table": "equipes_favorites", "operation": "list"}
    )
    return [row[0] for row in rows] if rows else []


def get_matchs_favoris(user_id, matchs_du_jour):
    """Filtre les matchs du jour pour ne garder que ceux des équipes favorites."""
    favoris = lister_favoris(user_id)
    if not favoris:
        return matchs_du_jour

    matchs_filtres = []
    for match in matchs_du_jour:
        if match.get("home") in favoris or match.get("away") in favoris:
            matchs_filtres.append(match)

    return matchs_filtres
