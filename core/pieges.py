# core/pieges.py
"""
Fonctionnalité 8 : Filtre Anti-Piège.
Détecte les matchs dangereux (derbys, historiques de cartons, etc.).
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
