# core/momentum.py
"""
Fonctionnalité 22 : Détecteur de Série / Momentum.
Analyse les derniers matchs d'une équipe pour détecter les séries.
"""

from users.db import db_fetchall
from core.utils.logs import log_info, log_error


def calculer_serie_equipe(nom_equipe, nb_matchs=5):
    """
    Calcule la série actuelle d'une équipe sur ses X derniers matchs.
    Retourne un dictionnaire avec :
    - serie : nombre de victoires consécutives (ou défaites si négatif)
    - type : 'victoire', 'defaite', 'nul', ou 'aucune'
    - details : liste des résultats
    """
    try:
        rows = db_fetchall(
            """
            SELECT home_team, away_team, fthg, ftag, ftr
            FROM matchs
            WHERE (home_team = ? OR away_team = ?) AND fthg IS NOT NULL
            ORDER BY date DESC
            LIMIT ?
            """,
            params=[nom_equipe, nom_equipe, nb_matchs],
        )
    except Exception as e:
        log_error(f"Erreur récupération matchs pour {nom_equipe}", "MOMENTUM", exception=e)
        return None

    if not rows:
        return {"serie": 0, "type": "aucune", "details": []}

    details = []
    serie = 0
    type_serie = "aucune"

    for row in rows:
        home, away, fthg, ftag, ftr = row

        # Déterminer si l'équipe a gagné, perdu ou fait nul
        if home == nom_equipe:
            if fthg > ftag:
                resultat = "V"
            elif fthg < ftag:
                resultat = "D"
            else:
                resultat = "N"
        else:
            if ftag > fthg:
                resultat = "V"
            elif ftag < fthg:
                resultat = "D"
            else:
                resultat = "N"

        details.append(resultat)

        # Calcul de la série
        if resultat == "V":
            if serie >= 0:
                serie += 1
            else:
                break
        elif resultat == "D":
            if serie <= 0:
                serie -= 1
            else:
                break
        else:  # Nul
            break

    if serie > 0:
        type_serie = "victoire"
    elif serie < 0:
        type_serie = "defaite"

    return {
        "serie": abs(serie),
        "type": type_serie,
        "details": details
    }


def formater_serie(nom_equipe, resultat):
    """Formate la série en texte lisible."""
    if not resultat or resultat["type"] == "aucune":
        return f"📊 {nom_equipe} : Pas de série significative."

    if resultat["type"] == "victoire":
        return f"🔥 {nom_equipe} : {resultat['serie']} victoire(s) d'affilée !"
    elif resultat["type"] == "defaite":
        return f"❄️ {nom_equipe} : {resultat['serie']} défaite(s) d'affilée."

    return f"📊 {nom_equipe} : Série en cours ({''.join(resultat['details'])})."
