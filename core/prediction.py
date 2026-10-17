import difflib
from datetime import datetime
import pandas as pd
import numpy as np
from scipy.stats import poisson

from core.ml_model import global_model_data
from users.db import get_connection


def trouver_nom_exact(nom_partiel, teams):
    """Recherche intelligente d'équipe : priorité aux initiales (PSG → Paris SG)."""
    recherche = nom_partiel.lower().strip()

    # 1. Correspondance exacte
    for t in teams:
        if t.lower() == recherche:
            return t

    # 2. Correspondance par initiales (PSG → Paris SG)
    initiales_recherche = recherche.replace(" ", "").replace(".", "")
    for t in teams:
        initiales_equipe = "".join(w[0] for w in t.lower().split() if w)
        if initiales_equipe == initiales_recherche:
            return t

    # 3. Correspondance de mots-clés
    mots_recherche = set(recherche.split())
    for t in teams:
        mots_equipe = set(t.lower().split())
        if mots_recherche and mots_recherche.issubset(mots_equipe):
            return t

    # 4. Préfixe
    for t in teams:
        if t.lower().startswith(recherche):
            return t

    # 5. Fallback difflib
    lower_teams = {t.lower(): t for t in teams}
    matches = difflib.get_close_matches(recherche, lower_teams.keys(), n=1, cutoff=0.6)
    return lower_teams[matches[0]] if matches else nom_partiel


def predire_match(home_input, away_input):
    """Retourne un dict avec toutes les probabilités."""
    if not global_model_data:
        return {"erreur": "Modèle non chargé."}

    teams = global_model_data['teams']
    team_to_code = global_model_data['team_to_code']
    team_global_stats = global_model_data['team_global_stats']
    df = global_model_data['df']

    home_team = trouver_nom_exact(home_input, teams)
    away_team = trouver_nom_exact(away_input, teams)

    if home_team not in team_to_code or away_team not in team_to_code:
        return {"erreur": f"Équipe introuvable : '{home_input}' ou '{away_input}'"}

    h_g_hist = team_global_stats[home_team]['scored']
    h_g_cond = team_global_stats[home_team]['conceded']
    a_g_hist = team_global_stats[away_team]['scored']
    a_g_cond = team_global_stats[away_team]['conceded']

    league_avg_home = df['FTHG'].mean()
    league_avg_away = df['FTAG'].mean()

    h_att = (sum(h_g_hist) / len(h_g_hist)) if h_g_hist else league_avg_home
    h_def = (sum(h_g_cond) / len(h_g_cond)) if h_g_cond else league_avg_away
    a_att = (sum(a_g_hist) / len(a_g_hist)) if a_g_hist else league_avg_away
    a_def = (sum(a_g_cond) / len(a_g_cond)) if a_g_cond else league_avg_home

    lambda_home = max(0.2, (h_att * a_def) / league_avg_home)
    lambda_away = max(0.2, (a_att * h_def) / league_avg_away)

    max_goals = 5
    score_matrix = np.outer(
        [poisson.pmf(i, lambda_home) for i in range(max_goals + 1)],
        [poisson.pmf(j, lambda_away) for j in range(max_goals + 1)]
    )

    # ✅ Convertir tous les np.sum() en float
    prob_home_win = float(np.sum(np.tril(score_matrix, -1)))
    prob_draw = float(np.sum(np.diag(score_matrix)))
    prob_away_win = float(np.sum(np.triu(score_matrix, 1)))
    total_prob = prob_home_win + prob_draw + prob_away_win

    p_h = prob_home_win / total_prob
    p_d = prob_draw / total_prob
    p_a = prob_away_win / total_prob

    # ✅ Convertir en float
    under_25 = float(np.sum([
        score_matrix[i, j]
        for i in range(max_goals + 1)
        for j in range(max_goals + 1)
        if i + j < 2.5
    ]))
    over_25 = 1.0 - under_25

    btts_yes = float(np.sum([
        score_matrix[i, j]
        for i in range(1, max_goals + 1)
        for j in range(1, max_goals + 1)
    ]))

    # Meilleur score
    best_i, best_j = np.unravel_index(np.argmax(score_matrix), score_matrix.shape)
    best_i, best_j = int(best_i), int(best_j)

    # Top 3 scores
    indices = np.dstack(np.unravel_index(np.argsort(score_matrix.ravel())[::-1], score_matrix.shape))[0]
    top_scores = []
    for idx in indices[:3]:
        i, j = int(idx[0]), int(idx[1])
        proba = float(score_matrix[i, j])
        top_scores.append((i, j, proba))

    # ✅ Convertir max en float
    max_prob = float(max(p_h, p_d, p_a))
    if max_prob >= 0.55:
        fiabilite = "🔥 CONFIANCE ÉLEVÉE"
    elif max_prob >= 0.45:
        fiabilite = "⚖️ CONFIANCE MODÉRÉE"
    else:
        fiabilite = "⚠️ MATCH INCERTAIN / RISQUÉ"

    # ✅ Convertir Double Chance en float
    dc_1x = float(p_h + p_d)
    dc_x2 = float(p_d + p_a)
    dc_12 = float(p_h + p_a)

    return {
        "home_team": home_team,
        "away_team": away_team,
        "p_h": float(p_h),
        "p_d": float(p_d),
        "p_a": float(p_a),
        "dc_1x": dc_1x,
        "dc_x2": dc_x2,
        "dc_12": dc_12,
        "over_25": over_25,
        "under_25": under_25,
        "btts_yes": btts_yes,
        "btts_no": float(1.0 - btts_yes),
        "best_score": (best_i, best_j),
        "top_scores": top_scores,
        "fiabilite": fiabilite,
    }


def sauvegarder_historique(home_team, away_team, p_h, p_d, p_a, best_i, best_j):
    """Sauvegarde dans PostgreSQL et nettoie les données de + de 30 jours."""
    try:
        # Déterminer la recommandation principale
        options = [("1X", p_h + p_d), ("X2", p_d + p_a), ("12", p_h + p_a)]
        meilleure = max(options, key=lambda x: x[1])[0]
        score_exact = f"{best_i}-{best_j}"
        
        conn = get_connection()
        cur = conn.cursor()
        
        # 1. On enregistre le nouveau pronostic
        cur.execute("""
            INSERT INTO resultats_pronostics (date_match, home_team, away_team, pronostic_reco, score_reel)
            VALUES (CURRENT_DATE, %s, %s, %s, %s)
        """, (home_team, away_team, meilleure, score_exact))
        
        # 2. 🧹 NETTOYAGE AUTOMATIQUE : On supprime les pronostics de plus de 30 jours
        # (Sauf ceux qui n'ont pas encore de résultat pour le bilan de la veille)
        cur.execute("""
            DELETE FROM resultats_pronostics 
            WHERE date_match < CURRENT_DATE - INTERVAL '30 days'
        """)
        
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"⚠️ Erreur sauvegarde historique BDD : {e}")
