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

    for t in teams:
        if t.lower() == recherche:
            return t

    initiales_recherche = recherche.replace(" ", "").replace(".", "")
    for t in teams:
        initiales_equipe = "".join(w[0] for w in t.lower().split() if w)
        if initiales_equipe == initiales_recherche:
            return t

    mots_recherche = set(recherche.split())
    for t in teams:
        mots_equipe = set(t.lower().split())
        if mots_recherche and mots_recherche.issubset(mots_equipe):
            return t

    for t in teams:
        if t.lower().startswith(recherche):
            return t

    lower_teams = {t.lower(): t for t in teams}
    matches = difflib.get_close_matches(recherche, lower_teams.keys(), n=1, cutoff=0.6)
    return lower_teams[matches[0]] if matches else nom_partiel


def _calculer_meilleur_pari(prono, cotes_book=None):
    """Calcule la meilleure option de pari en appliquant les règles."""
    options = [
        ("1X", prono['dc_1x']),
        ("X2", prono['dc_x2']),
        ("12", prono['dc_12']),
        ("Over 2.5", prono['over_25']),
        ("BTTS Oui", prono['btts_yes']),
        ("1 (Domicile)", prono['p_h']),
        ("2 (Extérieur)", prono['p_a'])
    ]
    
    options.sort(key=lambda x: x[1], reverse=True)
    
    for label, proba in options:
        cote_bot = round(1 / proba, 2) if proba > 0 else 999
        
        if cote_bot < 1.25:
            continue
            
        cote_book = None
        is_value_bet = False
        
        if cotes_book:
            if label == "1X" and cotes_book.get('h') and cotes_book.get('d'):
                cote_book = round(1 / (1/cotes_book['h'] + 1/cotes_book['d']), 2)
            elif label == "X2" and cotes_book.get('a') and cotes_book.get('d'):
                cote_book = round(1 / (1/cotes_book['a'] + 1/cotes_book['d']), 2)
            elif label == "12" and cotes_book.get('h') and cotes_book.get('a'):
                cote_book = round(1 / (1/cotes_book['h'] + 1/cotes_book['a']), 2)
            elif label == "1 (Domicile)":
                cote_book = cotes_book.get('h')
            elif label == "2 (Extérieur)":
                cote_book = cotes_book.get('a')
                
            if cote_book and cote_bot < cote_book:
                is_value_bet = True

        return {
            "label": label,
            "proba": proba,
            "cote_bot": cote_bot,
            "cote_book": cote_book,
            "is_value": is_value_bet
        }
    
    return None


def predire_match(home_input, away_input, cotes_book=None):
    if not global_model_data:
        return {"erreur": "Modèle non chargé. Réessaie plus tard."}

    teams = global_model_data['teams']
    team_to_code = global_model_data['team_to_code']
    team_global_stats = global_model_data.get('team_global_stats', {})
    team_xg_stats = global_model_data.get('team_xg_stats', {})
    df = global_model_data['df']

    home_team = trouver_nom_exact(home_input, teams)
    away_team = trouver_nom_exact(away_input, teams)

    # ⚠️ GESTION INTELLIGENTE DES ERREURS D'ÉQUIPES
    if home_team not in team_to_code:
        return {"erreur": f"⚠️ Équipe introuvable : **{home_input}**.\n\nLe bot prend en charge : Premier League, Championship, LaLiga, Ligue 1, Bundesliga, Serie A.\n\n(Note : les équipes reléguées dans les divisions inférieures ne sont plus analysées)."}
        
    if away_team not in team_to_code:
        return {"erreur": f"⚠️ Équipe introuvable : **{away_input}**.\n\nLe bot prend en charge : Premier League, Championship, LaLiga, Ligue 1, Bundesliga, Serie A.\n\n(Note : les équipes reléguées dans les divisions inférieures ne sont plus analysées)."}

    # Calculs xG avec fallback
    h_xg_hist = team_xg_stats.get(home_team, {}).get('xg_for', [])
    h_xga_hist = team_xg_stats.get(home_team, {}).get('xg_against', [])
    a_xg_hist = team_xg_stats.get(away_team, {}).get('xg_for', [])
    a_xga_hist = team_xg_stats.get(away_team, {}).get('xg_against', [])

    if h_xg_hist and a_xg_hist:
        h_att = sum(h_xg_hist[-5:]) / len(h_xg_hist[-5:])
        h_def = sum(h_xga_hist[-5:]) / len(h_xga_hist[-5:])
        a_att = sum(a_xg_hist[-5:]) / len(a_xg_hist[-5:])
        a_def = sum(a_xga_hist[-5:]) / len(a_xga_hist[-5:])
    else:
        h_g_hist = team_global_stats.get(home_team, {}).get('scored', [])
        h_g_cond = team_global_stats.get(home_team, {}).get('conceded', [])
        a_g_hist = team_global_stats.get(away_team, {}).get('scored', [])
        a_g_cond = team_global_stats.get(away_team, {}).get('conceded', [])
        
        h_att = sum(h_g_hist) / len(h_g_hist) if h_g_hist else 1.2
        h_def = sum(h_g_cond) / len(h_g_cond) if h_g_cond else 1.2
        a_att = sum(a_g_hist) / len(a_g_hist) if a_g_hist else 1.0
        a_def = sum(a_g_cond) / len(a_g_cond) if a_g_cond else 1.3

    league_avg_home = df['FTHG'].mean() if 'FTHG' in df else 1.5
    league_avg_away = df['FTAG'].mean() if 'FTAG' in df else 1.2

    lambda_home = max(0.2, (h_att * a_def) / league_avg_home)
    lambda_away = max(0.2, (a_att * h_def) / league_avg_away)

    max_goals = 5
    score_matrix = np.outer(
        [poisson.pmf(i, lambda_home) for i in range(max_goals + 1)],
        [poisson.pmf(j, lambda_away) for j in range(max_goals + 1)]
    )

    prob_home_win = float(np.sum(np.tril(score_matrix, -1)))
    prob_draw = float(np.sum(np.diag(score_matrix)))
    prob_away_win = float(np.sum(np.triu(score_matrix, 1)))
    total_prob = prob_home_win + prob_draw + prob_away_win

    p_h = prob_home_win / total_prob
    p_d = prob_draw / total_prob
    p_a = prob_away_win / total_prob

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

    best_i, best_j = np.unravel_index(np.argmax(score_matrix), score_matrix.shape)
    best_i, best_j = int(best_i), int(best_j)

    indices = np.dstack(np.unravel_index(np.argsort(score_matrix.ravel())[::-1], score_matrix.shape))[0]
    top_scores = []
    for idx in indices[:3]:
        i, j = int(idx[0]), int(idx[1])
        proba = float(score_matrix[i, j])
        top_scores.append((i, j, proba))

    max_prob = float(max(p_h, p_d, p_a))
    if max_prob >= 0.55:
        fiabilite = "🔥 CONFIANCE ÉLEVÉE"
    elif max_prob >= 0.45:
        fiabilite = "⚖️ CONFIANCE MODÉRÉE"
    else:
        fiabilite = "⚠️ MATCH INCERTAIN / RISQUÉ"

    dc_1x = float(p_h + p_d)
    dc_x2 = float(p_d + p_a)
    dc_12 = float(p_h + p_a)

    prono = {
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
    
    analyse_pari = _calculer_meilleur_pari(prono, cotes_book)
    prono["analyse_pari"] = analyse_pari

    return prono


def sauvegarder_historique(home_team, away_team, p_h, p_d, p_a, best_i, best_j):
    try:
        options = [("1X", p_h + p_d), ("X2", p_d + p_a), ("12", p_h + p_a)]
        meilleure = max(options, key=lambda x: x[1])[0]
        score_exact = f"{best_i}-{best_j}"
        
        conn = get_connection()
        cur = conn.cursor()
        
        cur.execute("""
            INSERT INTO resultats_pronostics (date_match, home_team, away_team, pronostic_reco, score_reel)
            VALUES (CURRENT_DATE, %s, %s, %s, %s)
        """, (home_team, away_team, meilleure, score_exact))
        
        cur.execute("""
            DELETE FROM resultats_pronostics 
            WHERE date_match < CURRENT_DATE - INTERVAL '30 days'
        """)
        
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"⚠️ Erreur sauvegarde historique BDD : {e}")
