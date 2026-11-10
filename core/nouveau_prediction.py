import numpy as np
import joblib
import io
import os
import libsql
from core.ml_model import global_model_data
from core.utils.logs import log_info, log_error, log_warning

TURSO_URL = os.environ.get("TURSO_URL", "")
TURSO_TOKEN = os.environ.get("TURSO_TOKEN", "")


def get_connection():
    return libsql.connect(database=TURSO_URL, auth_token=TURSO_TOKEN)


def _charger_modeles():
    """Charge les modèles depuis Turso si pas déjà en mémoire."""
    if global_model_data.get('modeles_par_competition'):
        return global_model_data['modeles_par_competition']
    
    log_info("Chargement des modèles depuis Turso...", "PREDICTION")
    
    try:
        conn = get_connection()
        cur = conn.execute("SELECT data FROM models_cache ORDER BY id DESC LIMIT 1")
        row = cur.fetchone()
        conn.close()
    except Exception as e:
        log_error("Impossible de lire la table models_cache", "PREDICTION", exception=e)
        return None
    
    if not row:
        log_error("Aucun modèle trouvé dans la table models_cache", "PREDICTION")
        return None
    
    try:
        modeles = joblib.load(io.BytesIO(row[0]))
        global_model_data['modeles_par_competition'] = modeles
        log_info(f"{len(modeles)} compétitions chargées.", "PREDICTION")
        return modeles
    except Exception as e:
        log_error("Erreur lors du chargement des modèles (joblib)", "PREDICTION", exception=e)
        return None


def _get_team_stats(competition, team, n=5):
    """Récupère les stats récentes d'une équipe."""
    try:
        conn = get_connection()
        cur = conn.execute("""
            SELECT fthg, ftag, ftr, hthg, htag, htr, home_team, away_team, date
            FROM matchs_features
            WHERE competition = ? AND (home_team = ? OR away_team = ?)
            ORDER BY date DESC LIMIT ?
        """, (competition, team, team, n))
        rows = cur.fetchall()
        conn.close()
    except Exception as e:
        log_error(f"Impossible de récupérer les stats pour l'équipe '{team}' en '{competition}'", "PREDICTION", exception=e)
        return None
    
    if not rows:
        log_warning(f"Aucun historique trouvé pour '{team}' en '{competition}'", "PREDICTION")
        return None
    
    ft_scored, ft_conceded = [], []
    ht_scored, ht_conceded = [], []
    ft_results, ht_results = [], []
    ft_home_scored, ft_away_scored = [], []
    
    for r in rows:
        fthg, ftag, ftr, hthg, htag, htr, home, away, date = r
        is_home = (home == team)
        
        if is_home:
            ft_scored.append(fthg); ft_conceded.append(ftag)
            ht_scored.append(hthg); ht_conceded.append(htag)
            ft_home_scored.append(fthg)
        else:
            ft_scored.append(ftag); ft_conceded.append(fthg)
            ht_scored.append(htag); ht_conceded.append(hthg)
            ft_away_scored.append(ftag)
        
        ft_results.append(1.0 if (ftr == 'H' and is_home) or (ftr == 'A' and not is_home) else (0.5 if ftr == 'D' else 0.0))
        ht_results.append(1.0 if (htr == 'H' and is_home) or (htr == 'A' and not is_home) else (0.5 if htr in ['D','N'] else 0.0))
    
    def wf(res):
        if not res: return 0.5
        r = res[:3]
        w = [3, 2, 1][:len(r)]
        return sum(x*y for x,y in zip(w,r)) / sum(w)
        
    def avg(lst, d=1.0): 
        return np.mean(lst) if lst else d
    
    return {
        'ft_glob_sc': avg(ft_scored, 1.2), 'ft_glob_co': avg(ft_conceded, 1.0),
        'ht_glob_sc': avg(ht_scored, 0.5), 'ht_glob_co': avg(ht_conceded, 0.5),
        'ft_home_sc': avg(ft_home_scored, 1.3), 'ft_away_sc': avg(ft_away_scored, 1.0),
        'ht_home_sc': avg(ht_scored, 0.5), 'ht_away_sc': avg(ht_scored, 0.5),
        'ft_form': wf(ft_results), 'ht_form': wf(ht_results),
    }


def _get_elo(competition, team):
    """Récupère l'Elo actuel d'une équipe."""
    try:
        conn = get_connection()
        cur = conn.execute("""
            SELECT h_elo_ft, a_elo_ft, home_team FROM matchs_features
            WHERE competition = ? AND (home_team = ? OR away_team = ?)
            ORDER BY date DESC LIMIT 1
        """, (competition, team, team))
        row = cur.fetchone()
        conn.close()
    except Exception as e:
        log_error(f"Impossible de récupérer l'Elo pour '{team}' en '{competition}'", "PREDICTION", exception=e)
        return 1500.0
    
    if not row:
        log_warning(f"Aucun Elo trouvé pour '{team}' en '{competition}', on utilise 1500 par défaut", "PREDICTION")
        return 1500.0
    return row[0] if row[2] == team else row[1]


def predire_match_v2(home_team, away_team, competition, cotes_book=None):
    """
    Fait une prédiction en utilisant nos 5 modèles LightGBM.
    """
    modeles = _charger_modeles()
    if not modeles:
        return {"erreur": "Modèle non chargé."}
    
    if competition not in modeles:
        log_error(f"Compétition '{competition}' non supportée par le modèle", "PREDICTION")
        return {"erreur": f"⚠️ Compétition '{competition}' non supportée."}
    
    h_feat = _get_team_stats(competition, home_team)
    a_feat = _get_team_stats(competition, away_team)
    if not h_feat or not a_feat:
        return {"erreur": f"⚠️ Données insuffisantes pour {home_team} ou {away_team}."}
    
    h_elo = _get_elo(competition, home_team)
    a_elo = _get_elo(competition, away_team)
    
    # Normalisation des cotes bookmaker
    p_h, p_d, p_a = 1/3, 1/3, 1/3
    if cotes_book and all(cotes_book.get(k) for k in ['h','d','a']):
        try:
            s = sum(1/cotes_book[k] for k in ['h','d','a'])
            p_h, p_d, p_a = (1/cotes_book['h'])/s, (1/cotes_book['d'])/s, (1/cotes_book['a'])/s
        except ZeroDivisionError as e:
            log_error("Cotes bookmaker invalides (division par zéro)", "PREDICTION", exception=e)
    
    ft_f = np.array([[
        h_elo, a_elo, h_elo - a_elo,
        h_feat['ft_glob_sc'], h_feat['ft_glob_co'], a_feat['ft_glob_sc'], a_feat['ft_glob_co'],
        h_feat['ft_home_sc'], a_feat['ft_away_sc'],
        h_feat['ft_form'], a_feat['ft_form'],
        p_h, p_d, p_a
    ]])
    ht_f = np.array([[
        h_elo, a_elo, h_elo - a_elo,
        h_feat['ht_glob_sc'], h_feat['ht_glob_co'], a_feat['ht_glob_sc'], a_feat['ht_glob_co'],
        h_feat['ht_home_sc'], a_feat['ht_away_sc'],
        h_feat['ht_form'], a_feat['ht_form'],
        p_h, p_d, p_a
    ]])
    
    preds = {}
    for nom, info in modeles[competition].items():
        try:
            is_ft = any('ft' in str(f) for f in info['features'])
            X = ft_f if is_ft else ht_f
            X_scaled = info['scaler'].transform(X)
            proba = info['model'].predict_proba(X_scaled)[0]
            preds[nom] = proba
        except Exception as e:
            log_error(f"Erreur de prédiction pour le marché '{nom}'", "PREDICTION", exception=e)
            preds[nom] = None
    
    res = {
        "home_team": home_team, 
        "away_team": away_team,
        "p_h": float(preds['DC_1X'][1] * 0.6) if preds.get('DC_1X') is not None else 0.33,
        "p_d": 0.33, 
        "p_a": 0.33,
        "dc_1x": float(preds['DC_1X'][1]) if preds.get('DC_1X') is not None else 0.5,
        "dc_x2": 1.0 - float(preds['DC_1X'][1]) if preds.get('DC_1X') is not None else 0.5,
        "dc_12": 0.5,
        "over_25": float(preds['Over25'][1]) if preds.get('Over25') is not None else 0.5,
        "under_25": 1.0 - float(preds['Over25'][1]) if preds.get('Over25') is not None else 0.5,
        "btts_yes": float(preds['BTTS'][1]) if preds.get('BTTS') is not None else 0.5,
        "btts_no": 1.0 - float(preds['BTTS'][1]) if preds.get('BTTS') is not None else 0.5,
        "best_score": (1, 1), 
        "top_scores": [(1,1,0.1), (2,1,0.08), (1,2,0.07)],
        "fiabilite": "⚖️ CONFIANCE MODÉRÉE",
        "ht_prolific": {
            "1ere_mt": float(preds['HT_Prolific'][1]) if preds.get('HT_Prolific') is not None else 0.33,
            "2eme_mt": float(preds['HT_Prolific'][2]) if preds.get('HT_Prolific') is not None else 0.33,
            "egalite": float(preds['HT_Prolific'][0]) if preds.get('HT_Prolific') is not None else 0.33,
        },
        "htr": {
            "1": float(preds['HTR'][0]) if preds.get('HTR') is not None else 0.33,
            "N": float(preds['HTR'][1]) if preds.get('HTR') is not None else 0.33,
            "2": float(preds['HTR'][2]) if preds.get('HTR') is not None else 0.33,
        },
        "analyse_pari": None,
    }
    
    if preds.get('DC_1X') is not None:
        meilleure_dc = max([("1X", res['dc_1x']), ("X2", res['dc_x2']), ("12", res['dc_12'])], key=lambda x: x[1])
        cote_bot = round(1/meilleure_dc[1], 2) if meilleure_dc[1] > 0 else 999
        
        cote_book = None
        if cotes_book:
            if meilleure_dc[0] == "1X": cote_book = cotes_book.get('h')
            elif meilleure_dc[0] == "12": cote_book = cotes_book.get('a')
            elif meilleure_dc[0] == "X2": cote_book = cotes_book.get('d')
        
        is_value = False
        if cote_book and cote_book > cote_bot:
            is_value = True
        
        res['analyse_pari'] = {
            'label': meilleure_dc[0],
            'proba': meilleure_dc[1],
            'cote_bot': cote_bot,
            'cote_book': cote_book,
            'is_value': is_value,
        }
    
    return res
