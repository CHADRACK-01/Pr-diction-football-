import difflib
import gc
import numpy as np
import pandas as pd
from users.db import get_connection
from core.ml_model import global_model_data, charger_modele_competition
from core.utils.logs import log_info, log_error


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


def _recalculer_features(home_team, away_team, competition):
    """
    Recalcule les features pour un match à venir en utilisant 
    les données historiques de Turso.
    """
    conn = get_connection()
    
    # On récupère les 10 derniers matchs de chaque équipe dans cette compétition
    query = """
        SELECT date, home_team, away_team, fthg, ftag, ftr
        FROM matchs
        WHERE competition = ? AND (home_team = ? OR away_team = ? OR home_team = ? OR away_team = ?)
        ORDER BY date DESC
        LIMIT 20
    """
    rows = conn.execute(query, (competition, home_team, away_team, away_team, home_team)).fetchall()
    conn.close()
    
    if not rows:
        return None
    
    df = pd.DataFrame(rows, columns=['Date', 'HomeTeam', 'AwayTeam', 'FTHG', 'FTAG', 'FTR'])
    
    # Calcul des stats pour l'équipe à domicile
    h_matches = df[(df['HomeTeam'] == home_team) | (df['AwayTeam'] == home_team)].head(10)
    a_matches = df[(df['HomeTeam'] == away_team) | (df['AwayTeam'] == away_team)].head(10)
    
    def get_stats(matches, team):
        scored = []
        conceded = []
        for _, m in matches.iterrows():
            if m['HomeTeam'] == team:
                scored.append(m['FTHG'])
                conceded.append(m['FTAG'])
            else:
                scored.append(m['FTAG'])
                conceded.append(m['FTHG'])
        return scored, conceded
    
    h_scored, h_conceded = get_stats(h_matches, home_team)
    a_scored, a_conceded = get_stats(a_matches, away_team)
    
    # Moyennes
    h_att = np.mean(h_scored) if h_scored else 1.2
    h_def = np.mean(h_conceded) if h_conceded else 1.2
    a_att = np.mean(a_scored) if a_scored else 1.0
    a_def = np.mean(a_conceded) if a_conceded else 1.3
    
    return {
        'h_att': h_att, 'h_def': h_def,
        'a_att': a_att, 'a_def': a_def,
        'h_scored': h_scored, 'h_conceded': h_conceded,
        'a_scored': a_scored, 'a_conceded': a_conceded
    }


def predire_match(home_input, away_input, competition="default", cotes_book=None):
    """
    Fait une prédiction en utilisant le modèle Stacking spécifique à la compétition.
    """
    if not global_model_data:
        return {"erreur": "Modèle non chargé."}

    # On récupère le modèle de la compétition
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

    # On recalcule les features à la volée
    stats = _recalculer_features(home_team, away_team, competition)
    if not stats:
        return {"erreur": "⚠️ Pas assez de données historiques pour ces équipes dans cette compétition."}

    # Construction du vecteur de features (doit correspondre à l'ordre d'entraînement)
    # ⚠️ L'ordre dépend de ton script d'entraînement
    features_vector = np.array([[
        team_to_code.get(home_team, 0),
        team_to_code.get(away_team, 0),
        stats['h_att'], stats['h_def'],
        stats['a_att'], stats['a_def'],
    ]])
    
    # On applique le scaler (stocké dans le modèle)
    scaler = model_data['scaler']
    features_scaled = scaler.transform(features_vector)
    
    # Prédiction
    model = model_data['model']
    proba = model.predict_proba(features_scaled)[0]
    
    p_h, p_d, p_a = float(proba[0]), float(proba[1]), float(proba[2])
    
    dc_1x = p_h + p_d
    dc_x2 = p_d + p_a
    dc_12 = p_h + p_a

    # Calculs supplémentaires (Poisson pour Over/Under, BTTS, scores exacts)
    lambda_home = max(0.2, (stats['h_att'] * stats['a_def']) / 1.5)
    lambda_away = max(0.2, (stats['a_att'] * stats['h_def']) / 1.2)
    
    from scipy.stats import poisson
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
        "home_team": home_team,
        "away_team": away_team,
        "p_h": p_h, "p_d": p_d, "p_a": p_a,
        "dc_1x": dc_1x, "dc_x2": dc_x2, "dc_12": dc_12,
        "over_25": over_25,
        "under_25": under_25,
        "btts_yes": btts_yes,
        "btts_no": 1.0 - btts_yes,
        "best_score": top_scores[0][:2] if top_scores else (0, 0),
        "top_scores": top_scores,
        "fiabilite": fiabilite,
    }
    
    # Libération de la RAM
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
