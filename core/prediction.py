import difflib
import gc
import numpy as np
import pandas as pd
from scipy.stats import poisson

from core.ml_model import global_model_data, charger_modele_competition
from users.db import get_connection
from core.utils.logs import log_info, log_error


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


def predire_match(home_input, away_input, competition="default", cotes_book=None):
    """
    Retourne un dict avec toutes les probabilités.
    ⚠️ Charge le modèle de la compétition à la demande (Lazy Loading).
    """
    if not global_model_data:
        return {"erreur": "Modèle non chargé."}

    # On récupère le modèle spécifique à la compétition
    model = charger_modele_competition(competition)
    
    if not model:
        return {"erreur": f"⚠️ Le modèle pour la compétition '{competition}' n'est pas disponible."}

    # On récupère les données de base pour les équipes
    teams = global_model_data.get('teams', [])
    team_to_code = global_model_data.get('team_to_code', {})
    team_global_stats = global_model_data.get('team_global_stats', {})
    
    # On cherche les noms exacts
    home_team = trouver_nom_exact(home_input, teams)
    away_team = trouver_nom_exact(away_input, teams)

    if home_team not in team_to_code:
        return {"erreur": f"⚠️ Équipe introuvable : **{home_input}**.\n\nLe bot prend en charge 21 compétitions (Premier League, Ligue 1, Champions League, etc.).\n\n(Note : vérifie l'orthographe du nom de l'équipe)."}
        
    if away_team not in team_to_code:
        return {"erreur": f"⚠️ Équipe introuvable : **{away_input}**.\n\nLe bot prend en charge 21 compétitions (Premier League, Ligue 1, Champions League, etc.).\n\n(Note : vérifie l'orthographe du nom de l'équipe)."}

    # =========================================================
    # ⚠️ On utilise les stats de buts (plus simples que les features du modèle)
    # =========================================================
    h_stats = team_global_stats.get(home_team, {})
    a_stats = team_global_stats.get(away_team, {})
    
    h_att = sum(h_stats.get('scored', [1.2])[-10:]) / len(h_stats.get('scored', [1.2])[-10:])
    h_def = sum(h_stats.get('conceded', [1.2])[-10:]) / len(h_stats.get('conceded', [1.2])[-10:])
    a_att = sum(a_stats.get('scored', [1.0])[-10:]) / len(a_stats.get('scored', [1.0])[-10:])
    a_def = sum(a_stats.get('conceded', [1.3])[-10:]) / len(a_stats.get('conceded', [1.3])[-10:])

    lambda_home = max(0.2, (h_att * a_def) / 1.5)
    lambda_away = max(0.2, (a_att * h_def) / 1.2)

    max_goals = 6
    matrix = np.outer(
        [poisson.pmf(i, lambda_home) for i in range(max_goals + 1)],
        [poisson.pmf(j, lambda_away) for j in range(max_goals + 1)]
    )

    p_h = float(np.sum(np.tril(matrix, -1)))
    p_d = float(np.sum(np.diag(matrix)))
    p_a = float(np.sum(np.triu(matrix, 1)))
    total = p_h + p_d + p_a
    p_h, p_d, p_a = p_h/total, p_d/total, p_a/total

    dc_1x = p_h + p_d
    dc_x2 = p_d + p_a
    dc_12 = p_h + p_a

    under_25 = sum(matrix[i, j] for i in range(7) for j in range(7) if i + j < 2.5)
    over_25 = 1 - under_25
    under_15 = sum(matrix[i, j] for i in range(7) for j in range(7) if i + j < 1.5)
    over_15 = 1 - under_15
    under_35 = sum(matrix[i, j] for i in range(7) for j in range(7) if i + j < 3.5)
    over_35 = 1 - under_35

    btts_yes = sum(matrix[i, j] for i in range(1, 7) for j in range(1, 7))

    indices = np.dstack(np.unravel_index(np.argsort(matrix.ravel())[::-1], matrix.shape))[0]
    top_scores = [(int(idx[0]), int(idx[1]), float(matrix[idx[0], idx[1]])) for idx in indices[:5]]

    lh_mt = lambda_home / 2.2
    la_mt = lambda_away / 2.2
    matrix_mt = np.outer(
        [poisson.pmf(i, lh_mt) for i in range(4)],
        [poisson.pmf(j, la_mt) for j in range(4)]
    )
    mt_over_05 = 1 - matrix_mt[0, 0]
    mt_over_15 = 1 - sum(matrix_mt[i, j] for i in range(4) for j in range(4) if i + j < 1.5)
    mt_btts = sum(matrix_mt[i, j] for i in range(1, 4) for j in range(1, 4))

    hcp_home_moins_05 = p_h
    hcp_home_plus_05 = p_h + p_d

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
        "p_h": p_h,
        "p_d": p_d,
        "p_a": p_a,
        "dc_1x": dc_1x,
        "dc_x2": dc_x2,
        "dc_12": dc_12,
        "over_15": over_15,
        "over_25": over_25,
        "over_35": over_35,
        "under_25": under_25,
        "btts_yes": btts_yes,
        "btts_no": 1.0 - btts_yes,
        "best_score": top_scores[0][:2] if top_scores else (0, 0),
        "top_scores": top_scores,
        "mt_over_05": mt_over_05,
        "mt_over_15": mt_over_15,
        "mt_btts": mt_btts,
        "hcp_home_moins_05": hcp_home_moins_05,
        "hcp_home_plus_05": hcp_home_plus_05,
        "fiabilite": fiabilite,
    }
    
    analyse_pari = _calculer_meilleur_pari(prono, cotes_book)
    prono["analyse_pari"] = analyse_pari

    # Libération de la RAM
    del matrix
    del matrix_mt
    gc.collect()

    return prono


def sauvegarder_historique(home_team, away_team, p_h, p_d, p_a, best_i, best_j):
    """Sauvegarde dans Turso et nettoie les données de + de 30 jours."""
    options = [("1X", p_h + p_d), ("X2", p_d + p_a), ("12", p_h + p_a)]
    meilleure = max(options, key=lambda x: x[1])[0]
    score_exact = f"{best_i}-{best_j}"
    
    conn = get_connection()
    conn.execute("""
        INSERT INTO resultats_pronostics (date_match, home_team, away_team, pronostic_reco, score_reel)
        VALUES (date('now'), ?, ?, ?, ?)
    """, (home_team, away_team, meilleure, score_exact))
    
    conn.execute("""
        DELETE FROM resultats_pronostics 
        WHERE date_match < date('now', '-30 days')
    """)
    conn.commit()
    conn.close()
