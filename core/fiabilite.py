# core/fiabilite.py
"""
Fonctionnalité 455 : Indice de fiabilité par championnat.
Calcule le taux de réussite des pronostics par compétition.
"""

from users.db import db_fetchall
from core.utils.logs import log_info, log_error


def calculer_fiabilite_par_championnat():
    """
    Calcule le taux de réussite des pronostics pour chaque compétition.
    Retourne une liste de dictionnaires triée par taux de réussite décroissant.
    """
    try:
        rows = db_fetchall(
            """
            SELECT competition, 
                   COUNT(*) as total,
                   SUM(CASE WHEN est_gagnant = 1 THEN 1 ELSE 0 END) as gagnes
            FROM resultats_pronostics
            WHERE est_gagnant IS NOT NULL
            GROUP BY competition
            ORDER BY (CAST(SUM(CASE WHEN est_gagnant = 1 THEN 1 ELSE 0 END) AS FLOAT) / COUNT(*)) DESC
            """
        )
    except Exception as e:
        log_error("Erreur calcul fiabilité par championnat", "FIABILITE", exception=e)
        return []

    if not rows:
        return []

    resultats = []
    for row in rows:
        competition, total, gagnes = row
        if total > 0:
            taux = round((gagnes / total) * 100, 1)
            resultats.append({
                "competition": competition,
                "total": total,
                "gagnes": gagnes,
                "taux": taux
            })

    log_info(f"Fiabilité calculée pour {len(resultats)} championnats", "FIABILITE")
    return resultats


def formater_fiabilite(resultats):
    """Formate les résultats en texte lisible pour Telegram."""
    if not resultats:
        return "📊 Aucun résultat disponible pour l'instant."

    texte = "📊 <b>FIABILITÉ PAR CHAMPIONNAT</b>\n"
    texte += "━━━━━━━━━━━━━━━━━━━━\n\n"

    for i, r in enumerate(resultats[:10], 1):  # Top 10
        # Emoji selon le taux
        if r["taux"] >= 70:
            emoji = "🔥"
        elif r["taux"] >= 50:
            emoji = "✅"
        else:
            emoji = "📉"

        texte += f"{i}. {emoji} <b>{r['competition']}</b>\n"
        texte += f"   🎯 {r['taux']}% ({r['gagnes']}/{r['total']})\n\n"

    texte += "━━━━━━━━━━━━━━━━━━━━\n"
    texte += "💡 <i>Choisis les championnats avec le meilleur taux pour maximiser tes chances.</i>\n"
    return texte
