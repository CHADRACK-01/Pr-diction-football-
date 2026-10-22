import difflib
import gc
import numpy as np
import pandas as pd
from scipy.stats import poisson

from users.db import get_connection
from core.ml_model import global_model_data, charger_modele_competition
from core.utils.logs import log_info, log_error


def trouver_nom_exact(nom_partiel, teams):
    """Recherche intelligente d'équipe."""
    recherche = nom_partiel.lower().strip()
    for t in teams:
        if t.lower() == recherche: return t
    initiales_recherche = recherche.replace(" ", "").replace(".", "")
    for t in teams:
        if "".join(w[0] for w in t.lower().split() if w) == initiales_recherche: return t
    mots_recherche = set(recherche.split())
    for t in teams:
        if mots_recherche and mots_recherche.issubset(set(t.lower().split())): return t
    for t in teams:
        if t.lower().startswith(recherche): return t
    lower_teams = {t.lower(): t for t in teams}
    matches = difflib.get_close_matches(recherche, lower_teams.keys(), n=1, cutoff=0.6)
    return lower_teams[matches[0]] if matches else nom_partiel


def _recalculer_toutes_les_features(home_team, away_team, competition):
    """
    Recalcule les 27 features pour un match à venir,
    en utilisant l'historique des matchs dans Turso.
    """
    conn = get_connection()
    
    # On récupère les 20 derniers matchs de chaque équipe dans la compétition
    query = """
        SELECT date, home_team, away_team,
               fthg, ftag, ftr,
               hs, as_shots, hst, ast,
               hc, ac, hf, af,
               hy, ay, hr, ar
        FROM matchs
        WHERE competition = ? AND (home_team = ? OR away_team = ? OR home_team = ? OR away_team = ?)
        ORDER BY date DESC
        LIMIT 40
    """
    rows = conn.execute(query, (competition, home_team, away_team, away_team, home_team)).fetchall()
    conn.close()
    
    if len(rows) < 5:
        return None
    
    df = pd.DataFrame(rows, columns=[
        'Date', 'HomeTeam', 'AwayTeam',
        'FTHG', 'FTAG', 'FTR',
        'HS', 'AS', 'HST', 'AST',
        'HC', 'AC', 'HF', 'AF',
        'HY', 'AY', 'HR', 'AR'
    ])
    df = df.sort_values('Date')
    
    def get_team_stats(team):
        matches = df[(df['HomeTeam'] == team) | (df['AwayTeam'] == team)].tail(10)
        
        scored, conceded, results = [], [], []
        shots, shots_target, corners, fouls, yellows, reds = [], [], [], [], [], []
        
        for _, m in matches.iterrows():
            is_home = (m['HomeTeam'] == team)
            
            # Buts
            scored.append(m['FTHG'] if is_home else m['FTAG'])
            conceded.append(m['FTAG'] if is_home else m['FTHG'])
            
            # Résultat
            if m['FTR'] == 'H': results.append(1.0 if is_home else 0.0)
            elif m['FTR'] == 'D': results.append(0.5)
            else: results.append(1.0 if not is_home else 0.0)
            
            # Stats avancées
            shots.append(m['HS'] if is_home else m['AS'])
            shots_target.append(m['HST'] if is_home else m['AST'])
            corners.append(m['HC'] if is_home else m['AC'])
            fouls.append(m['HF'] if is_home else m['AF'])
            yellows.append(m['HY'] if is_home else m['AY'])
            reds.append(m['HR'] if is_home else m['AR'])
        
        def avg(lst, default=1.2):
            return np.mean(lst) if lst else default
        
        # Forme pondérée
        if len(results) >= 3:
            recent = results[-3:]
            weights = [3, 2, 1]
            weighted_form = sum(w * r for w, r in zip(weights, recent)) / sum(weights)
        elif len(results) > 0:
            weighted_form = np.mean(results)
        else:
            weighted_form = 0.5
        
        return {
            'att': avg(scored), 'def': avg(conceded),
            'weighted_form': weighted_form,
            'shots': avg(shots, 10), 'shots_target': avg(shots_target, 3),
            'corners': avg(corners, 5), 'fouls': avg(fouls, 12),
            'yellows': avg(yellows, 2), 'reds': avg(reds, 0),
        }
    
    h_stats = get_team_stats(home_team)
    a_stats = get_team_stats(away_team)
    
    # Elo approximatif (basé sur la forme)
    base_elo = 1500
    h_elo = base_elo + (h_stats['weighted_form'] - 0.5) * 200
    a_elo = base_elo + (a_stats['weighted_form'] - 0.5) * 200
    
    return {
        'Home_Elo': h_elo, 'Away_Elo': a_elo, 'Elo_Diff': h_elo - a_elo,
        'H_Glob_Sc': h_stats['att'], 'H_Glob_Co': h_stats['def'],
        'A_Glob_Sc': a_stats['att'], 'A_Glob_Co': a_stats['def'],
        'H_Weighted_Form': h_stats['weighted_form'], 'A_Weighted_Form': a_stats['weighted_form'],
        'Delta_Forme': h_stats['weighted_form'] - a_stats['weighted_form'],
        'H_Shots': h_stats['shots'], 'A_Shots': a_stats['shots'],
        'H_Shots_Target': h_stats['shots_target'], 'A_Shots_Target': a_stats['shots_target'],
        'H_Corners': h_stats['corners'], 'A_Corners': a_stats['corners'],
        'H_Fouls': h_stats['fouls'], 'A_Fouls': a_stats['fouls'],
        'H_Yellows': h_stats['yellows'], 'A_Yellows': a_stats['yellows'],
        'H_Reds': h_stats['reds'], 'A_Reds': a_stats['reds'],
    }


def predire_match(home_input, away_input, competition="default", cotes_book=None):
    """
    Fait une prédiction en utilisant le modèle Stacking (27 features).
    """
    if not global_model_data:
        return {"erreur": "Modèle non chargé."}

    model_data = charger_modele_competition(competition)
    if not model_data:
        return {"erreur": f"⚠️ Le modèle pour la compétition '{competition}' n'est pas disponible."}

    teams = global_model_data.get('teams', [])
    team_to_code = global_model_data.get('team_to_code', {})
    
    home_team = trouver_nom_exact(home_input, teams)
    away_team = trouver_nom_exact(away_input, teams)

    if home_team not in team_to_code:
        return {"erreur": f"⚠️ Équipe introuvable : **{home_input}**."}
    if away_team not in team_to_code:
        return {"erreur": f"⚠️ Équipe introuvable : **{away_input}**."}

    # Recalcul des features
    features_dict = _recalculer_toutes_les_features(home_team, away_team, competition)
    if not features_dict:
        return {"erreur": "⚠️ Pas assez de données historiques pour ces équipes."}

    # ⚠️ ORDRE EXACT DES 27 FEATURES
    features_order = [
        'HomeTeam_Encoded', 'AwayTeam_Encoded',
        'Home_Elo', 'Away_Elo', 'Elo_Diff',
        'H_Glob_Sc', 'H_Glob_Co', 'A_Glob_Sc', 'A_Glob_Co',
        'H_Weighted_Form', 'A_Weighted_Form', 'Delta_Forme',
        'H_Shots', 'A_Shots', 'H_Shots_Target', 'A_Shots_Target',
        'H_Corners', 'A_Corners', 'H_Fouls', 'A_Fouls',
        'H_Yellows', 'A_Yellows', 'H_Reds', 'A_Reds',
        'B365H', 'B365D', 'B365A'
    ]
    
    # Construction du vecteur
    features_vector = []
    for f in features_order:
        if f == 'HomeTeam_Encoded':
            features_vector.append(team_to_code.get(home_team, 0))
        elif f == 'AwayTeam_Encoded':
            features_vector.append(team_to_code.get(away_team, 0))
        elif f in ['B365H', 'B365D', 'B365A']:
            val = cotes_book.get({'B365H': 'h', 'B365D': 'd', 'B365A': 'a'}[f]) if cotes_book else 0
            features_vector.append(val if val else 0)
        else:
            features_vector.append(features_dict.get(f, 0))
    
    features_vector = np.array([features_vector], dtype=float)
    
    # Application du scaler
    scaler = model_data['scaler']
    features_scaled = scaler.transform(features_vector)
    
    # Prédiction
    model = model_data['model']
    proba = model.predict_proba(features_scaled)[0]
    
    p_h, p_d, p_a = float(proba[0]), float(proba[1]), float(proba[2])
    
    dc_1x = p_h + p_d
    dc_x2 = p_d + p_a
    dc_12 = p_h + p_a

    # Poisson pour Over/Under et scores
    lambda_home = max(0.2, (features_dict['H_Glob_Sc'] * features_dict['A_Glob_Co']) / 1.5)
    lambda_away = max(0.2, (features_dict['A_Glob_Sc'] * features_dict['H_Glob_Co']) / 1.2)
    
    max_goals = 6
    matrix = np.outer(
        [poisson.pmf(i, lambda_home) for i in range(max_goals + 1)],
        [poisson.pmf(j, lambda_away) for j in range(max_goals + 1)]
    )
    
    under_25 = sum(matrix[i, j] for i in range(7) for j in range(7) if i + j < 2.5)
    over_25 = 1 - under_25
    btts_yes = sum(matrix[i, j] for i in range(1, 7) for j in range(1, 7))
    
    indices = np.dstack(np.unravel_index(np.argsort(matrix.ravel())[::-1], matrix.shape))[0]
    top_scores = [(int(idx[0]), int(idx[1]), float(matrix[idx[0], idx[1]])) for idx in indices[:5]]

    max_prob = float(max(p_h, p_d, p_a))
    if max_prob >= 0.55:
        fiabilite = "🔥 CONFIANCE ÉLEVÉE"
    elif max_prob >= 0.45:
        fiabilite = "⚖️ CONFIANCE MODÉRÉE"
    else:
        fiabilite = "⚠️ MATCH INCERTAIN / RISQUÉ"

    prono = {
        "home_team": home_team, "away_team": away_team,
        "p_h": p_h, "p_d": p_d, "p_a": p_a,
        "dc_1x": dc_1x, "dc_x2": dc_x2, "dc_12": dc_12,
        "over_25": over_25, "under_25": under_25,
        "btts_yes": btts_yes, "btts_no": 1.0 - btts_yes,
        "best_score": top_scores[0][:2] if top_scores else (0, 0),
        "top_scores": top_scores,
        "fiabilite": fiabilite,
    }
    
    del matrix
    gc.collect()

    return prono


def sauvegarder_historique(home_team, away_team, p_h, p_d, p_a, best_i, best_j):
    """Sauvegarde dans Turso."""
    options = [("1X", p_h + p_d), ("X2", p_d + p_a), ("12", p_h + p_a)]
    meilleure = max(options, key=lambda x: x[1])[0]
    score_exact = f"{best_i}-{best_j}"
    
    conn = get_connection()
    conn.execute("""
        INSERT INTO resultats_pronostics (date_match, home_team, away_team, pronostic_reco, score_reel)
        VALUES (date('now'), ?, ?, ?, ?)
    """, (home_team, away_team, meilleure, score_exact))
    
    conn.execute("DELETE FROM resultats_pronostics WHERE date_match < date('now', '-30 days')")
    conn.commit()
    conn.close()
