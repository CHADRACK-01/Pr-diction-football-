# core/consultation.py
"""
Module fusionné regroupant trois fonctionnalités core :
- 455 : Indice de fiabilité par championnat.
- 22 : Détecteur de Série / Momentum.
- 8 : Filtre Anti-Piège.
"""

from users.db import db_fetchall
from core.utils.logs import log_info, log_error

# Liste des derbys connus (à enrichir)
DERBYS_CONNUS = [
    ("Real Madrid", "Barcelona"),
    ("Manchester United", "Manchester City"),
    ("PSG", "Marseille"),
    ("Bayern Munich", "Dortmund"),
    ("Inter", "Milan"),
    ("Roma", "Lazio"),
    ("Arsenal", "Tottenham"),
    ("Liverpool", "Everton"),
    ("Mazembe", "Vita Club"),
]


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


def detecter_piege(home_team, away_team):
    """
    Détecte si un match est un 'piège' potentiel.
    Retourne un dictionnaire avec :
    - est_piege : booléen
    - raison : texte explicatif
    """
    raisons = []

    # 1. Vérifier si c'est un derby connu
    for equipe1, equipe2 in DERBYS_CONNUS:
        if (equipe1 in home_team and equipe2 in away_team) or \
           (equipe2 in home_team and equipe1 in away_team):
            raisons.append("🔥 Derby / Rivalité historique")
            break

    # 2. Vérifier l'historique de cartons (basé sur les 5 derniers matchs des deux équipes)
    try:
        cartons_home = _compter_cartons_equipe(home_team)
        cartons_away = _compter_cartons_equipe(away_team)
        moyenne_cartons = (cartons_home + cartons_away) / 2

        if moyenne_cartons > 4:
            raisons.append(f"🟨 Match à cartons ({moyenne_cartons:.1f} cartons/match en moyenne)")
    except Exception as e:
        log_error(f"Erreur analyse cartons pour {home_team} vs {away_team}", "PIEGES", exception=e)

    # 3. Vérifier si les deux équipes sont en mauvaise forme
    try:
        forme_home = _forme_recente(home_team)
        forme_away = _forme_recente(away_team)
        if forme_home < 0.3 and forme_away < 0.3:
            raisons.append("📉 Les deux équipes sont en mauvaise forme")
    except Exception as e:
        log_error(f"Erreur analyse forme pour {home_team} vs {away_team}", "PIEGES", exception=e)

    return {
        "est_piege": len(raisons) > 0,
        "raison": " | ".join(raisons) if raisons else ""
    }


def _compter_cartons_equipe(nom_equipe, nb_matchs=5):
    """Compte la moyenne de cartons d'une équipe sur ses X derniers matchs."""
    try:
        rows = db_fetchall(
            """
            SELECT home_team, away_team, hy, ay
            FROM matchs
            WHERE (home_team = ? OR away_team = ?) AND hy IS NOT NULL AND ay IS NOT NULL
            ORDER BY date DESC
            LIMIT ?
            """,
            params=[nom_equipe, nom_equipe, nb_matchs],
        )
    except Exception:
        return 0

    if not rows:
        return 0

    total_cartons = 0
    for row in rows:
        home, away, hy, ay = row
        if home == nom_equipe:
            total_cartons += hy
        else:
            total_cartons += ay

    return total_cartons / len(rows)


def _forme_recente(nom_equipe, nb_matchs=5):
    """Calcule la forme récente (0 à 1) d'une équipe."""
    try:
        rows = db_fetchall(
            """
            SELECT home_team, away_team, ftr
            FROM matchs
            WHERE (home_team = ? OR away_team = ?) AND ftr IS NOT NULL
            ORDER BY date DESC
            LIMIT ?
            """,
            params=[nom_equipe, nom_equipe, nb_matchs],
        )
    except Exception:
        return 0.5

    if not rows:
        return 0.5

    points = 0
    for row in rows:
        home, away, ftr = row
        if home == nom_equipe:
            if ftr == "H": points += 1
            elif ftr == "D": points += 0.5
        else:
            if ftr == "A": points += 1
            elif ftr == "D": points += 0.5

    return points / len(rows)


def formater_alerte_piege(home_team, away_team):
    """Retourne un texte d'alerte si le match est un piège."""
    resultat = detecter_piege(home_team, away_team)
    if resultat["est_piege"]:
        return f"⚠️ <b>ATTENTION : MATCH PIÈGE</b>\n{resultat['raison']}"
    return ""
