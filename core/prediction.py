import difflib
from datetime import datetime
import pandas as pd
import numpy as np
from scipy.stats import poisson

from config import FICHIER_HISTORIQUE
from core.ml_model import global_model_data


def predire_match(home_input, away_input):
    """Retourne un dict avec toutes les probas. Aucun appel Telegram ici."""
    if not global_model_data:
        return {"erreur": "Modèle non chargé."}

    teams = global_model_data['teams']
    team_to_code = global_model_data['team_to_code']
    team_global_stats = global_model_data['team_global_stats']
    df = global_model_data['df']

    def trouver_nom_exact(nom_partiel):
        lower_teams = {t.lower(): t for t in teams}
        matches = difflib.get_close_matches(nom_partiel.lower(), lower_teams.keys(), n=1, cutoff=0.4)
        return lower_teams[matches[0]] if matches else nom_partiel

    home_team = trouver_nom_exact(home_input)
    away_team = trouver_nom_exact(away_input)

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

    prob_home_win = np.sum(np.tril(score_matrix, -1))
    prob_draw = np.sum(np.diag(score_matrix))
    prob_away_win = np.sum(np.triu(score_matrix, 1))
    total_prob = prob_home_win + prob_draw + prob_away_win

    p_h = prob_home_win / total_prob
    p_d = prob_draw / total_prob
    p_a = prob_away_win / total_prob

    under_25 = np.sum([score_matrix[i, j] for i in range(max_goals + 1) for j in range(max_goals + 1) if i + j < 2.5])
    over_25 = 1.0 - under_25
    btts_yes = np.sum([score_matrix[i, j] for i in range(1, max_goals + 1) for j in range(1, max_goals + 1)])
    best_i, best_j = np.unravel_index(np.argmax(score_matrix), score_matrix.shape)

    max_prob = max(p_h, p_d, p_a)
    if max_prob >= 0.50:
        fiabilite = "🔥 CONFIANCE ÉLEVÉE"
    elif max_prob < 0.40:
        fiabilite = "⚠️ MATCH INCERTAIN / RISQUÉ"
    else:
        fiabilite = "⚖️ CONFIANCE MODÉRÉE"

    return {
        "home_team": home_team,
        "away_team": away_team,
        "p_h": p_h,
        "p_d": p_d,
        "p_a": p_a,
        "over_25": over_25,
        "btts_yes": btts_yes,
        "best_score": (int(best_i), int(best_j)),
        "fiabilite": fiabilite
    }


def sauvegarder_historique(home_team, away_team, p_h, p_d, p_a, best_i, best_j):
    record = {
        "Date_Consultation": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "Match": f"{home_team} vs {away_team}",
        "Pronostic_1N2": f"1:{round(p_h * 100, 1)}% N:{round(p_d * 100, 1)}% 2:{round(p_a * 100, 1)}%",
        "Score_Exact": f"{best_i}-{best_j}"
    }
    hist_df = pd.DataFrame([record])
    try:
        existing = pd.read_csv(FICHIER_HISTORIQUE)
        updated = pd.concat([existing, hist_df], ignore_index=True)
        updated.to_csv(FICHIER_HISTORIQUE, index=False)
    except FileNotFoundError:
        hist_df.to_csv(FICHIER_HISTORIQUE, index=False)
