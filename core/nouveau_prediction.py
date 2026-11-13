# core/nouveau_prediction.py
"""
Moteur de prédiction V2.
- Traduction des noms d'équipes (Telegram -> Base de données)
- Reconstruit les features (Elo, forme, moyennes de buts)
- Utilise les 6 modèles globaux
"""

import numpy as np
from core.ml_model import global_model_data
from core.utils.logs import log_info, log_error, log_warning
from users.db import db_fetchall

# =========================================================
# DICTIONNAIRE DE CORRESPONDANCE DES NOMS
# =========================================================
NOMS_EQUIPES_MAPPING = {
    # Allemagne
    "FC Bayern München": "Bayern Munich",
    "Bayern München": "Bayern Munich",
    "Borussia Dortmund": "Dortmund",
    "Borussia Mönchengladbach": "M'gladbach",
    "Bayer 04 Leverkusen": "Leverkusen",
    "Eintracht Frankfurt": "Ein Frankfurt",
    "VfB Stuttgart": "Stuttgart",
    "VfL Wolfsburg": "Wolfsburg",
    "1. FC Union Berlin": "Union Berlin",
    "SC Freiburg": "Freiburg",
    "TSG 1899 Hoffenheim": "Hoffenheim",
    "FC Augsburg": "Augsburg",
    "1. FSV Mainz 05": "Mainz",
    "SV Werder Bremen": "Werder Bremen",
    "VfL Bochum 1848": "Bochum",
    "1. FC Köln": "FC Koln",
    "SV Darmstadt 98": "Darmstadt",
    "1. FC Heidenheim 1846": "Heidenheim",
    "FC St. Pauli": "St Pauli",
    "Holstein Kiel": "Holstein Kiel",
    
    # France
    "Paris Saint-Germain FC": "Paris SG",
    "Paris Saint-Germain": "Paris SG",
    "Olympique de Marseille": "Marseille",
    "Olympique Lyonnais": "Lyon",
    "AS Monaco FC": "Monaco",
    "LOSC Lille": "Lille",
    "OGC Nice": "Nice",
    "Stade Rennais FC 1901": "Rennes",
    "Racing Club de Lens": "Lens",
    "Stade de Reims": "Reims",
    "Montpellier HSC": "Montpellier",
    "FC Nantes": "Nantes",
    "Stade Brestois 29": "Brest",
    "RC Strasbourg Alsace": "Strasbourg",
    "Toulouse FC": "Toulouse",
    "FC Metz": "Metz",
    "Le Havre AC": "Le Havre",
    "Clermont Foot 63": "Clermont",
    "FC Lorient": "Lorient",
    "Angers SCO": "Angers",
    "AS Saint-Etienne": "St Etienne",
    "AJ Auxerre": "Auxerre",
    
    # Espagne
    "Real Madrid CF": "Real Madrid",
    "FC Barcelona": "Barcelona",
    "Atletico de Madrid": "Ath Madrid",
    "Atlético Madrid": "Ath Madrid",
    "Athletic Club": "Ath Bilbao",
    "Real Sociedad de Futbol": "Sociedad",
    "Real Betis Balompie": "Betis",
    "Sevilla FC": "Sevilla",
    "Valencia CF": "Valencia",
    "Villarreal CF": "Villarreal",
    "Getafe CF": "Getafe",
    "RCD Espanyol de Barcelona": "Espanol",
    "Rayo Vallecano de Madrid": "Vallecano",
    "RC Celta de Vigo": "Celta",
    "RCD Mallorca": "Mallorca",
    "CA Osasuna": "Osasuna",
    "Granada CF": "Granada",
    "Deportivo Alaves": "Alaves",
    "Cadiz CF": "Cadiz",
    "UD Las Palmas": "Las Palmas",
    "Girona FC": "Girona",
    "Real Valladolid CF": "Valladolid",
    "Levante UD": "Levante",
    "Elche CF": "Elche",
    "CD Leganes": "Leganes",
    "Real Zaragoza": "Zaragoza",
    "Real Oviedo": "Oviedo",
    "Sporting Gijon": "Sp Gijon",
    
    # Angleterre
    "Manchester City FC": "Man City",
    "Manchester United FC": "Man United",
    "Newcastle United FC": "Newcastle",
    "Nottingham Forest FC": "Nott'm Forest",
    "Tottenham Hotspur FC": "Tottenham",
    "Wolverhampton Wanderers FC": "Wolves",
    "Brighton & Hove Albion FC": "Brighton",
    "West Ham United FC": "West Ham",
    
    # Italie
    "AS Roma": "Roma",
    "SS Lazio": "Lazio",
    "Juventus FC": "Juventus",
    "AC Milan": "Milan",
    "FC Internazionale Milano": "Inter",
    "SSC Napoli": "Napoli",
    "ACF Fiorentina": "Fiorentina",
    "Atalanta BC": "Atalanta",
    "Bologna FC 1909": "Bologna",
    "Torino FC": "Torino",
    "Udinese Calcio": "Udinese",
    "US Sassuolo Calcio": "Sassuolo",
    "Empoli FC": "Empoli",
    "US Lecce": "Lecce",
    "Hellas Verona FC": "Verona",
    "Cagliari Calcio": "Cagliari",
    "Genoa CFC": "Genoa",
    "US Salernitana 1919": "Salernitana",
    "Frosinone Calcio": "Frosinone",
    "AC Monza": "Monza",
    "Parma Calcio 1913": "Parma",
    "Como 1907": "Como",
    "Venezia FC": "Venezia"
}


def _get_team_features(home_team, away_team):
    """
    Calcule les features pour un match en interrogeant l'historique.
    """
    rows = db_fetchall(
        """
        SELECT date, home_team, away_team, fthg, ftag, ftr
        FROM matchs
        WHERE (home_team = ? OR away_team = ?) AND fthg IS NOT NULL
        ORDER BY date DESC LIMIT 50
        """,
        params=[home_team, home_team],
        db_context={"table": "matchs", "operation": "get_features_home"},
    )
    
    rows_away = db_fetchall(
        """
        SELECT date, home_team, away_team, fthg, ftag, ftr
        FROM matchs
        WHERE (home_team = ? OR away_team = ?) AND fthg IS NOT NULL
        ORDER BY date DESC LIMIT 50
        """,
        params=[away_team, away_team],
        db_context={"table": "matchs", "operation": "get_features_away"},
    )

    if not rows or not rows_away:
        return None

    # --- Calcul des stats Home ---
    bm_h, be_h, forme_h = [], [], []
    for r in rows:
        h, a, fthg, ftag, ftr = r[1], r[2], r[3], r[4], r[5]
        if h == home_team:
            bm_h.append(fthg); be_h.append(ftag)
            forme_h.append(1 if ftr == 'H' else 0.5 if ftr == 'D' else 0)
        else:
            bm_h.append(ftag); be_h.append(fthg)
            forme_h.append(1 if ftr == 'A' else 0.5 if ftr == 'D' else 0)

    # --- Calcul des stats Away ---
    bm_a, be_a, forme_a = [], [], []
    for r in rows_away:
        h, a, fthg, ftag, ftr = r[1], r[2], r[3], r[4], r[5]
        if h == away_team:
            bm_a.append(fthg); be_a.append(ftag)
            forme_a.append(1 if ftr == 'H' else 0.5 if ftr == 'D' else 0)
        else:
            bm_a.append(ftag); be_a.append(fthg)
            forme_a.append(1 if ftr == 'A' else 0.5 if ftr == 'D' else 0)

    # Approximation de l'Elo basée sur les points (0 à 2000)
    elo_home = 1500 + (sum(forme_h) / len(forme_h)) * 200 if forme_h else 1500
    elo_away = 1500 + (sum(forme_a) / len(forme_a)) * 200 if forme_a else 1500

    features = {
        "elo_home": elo_home,
        "elo_away": elo_away,
        "elo_diff": elo_home - elo_away,
        "forme_h": sum(forme_h) / len(forme_h) if forme_h else 0.5,
        "forme_a": sum(forme_a) / len(forme_a) if forme_a else 0.5,
        "forme_diff": (sum(forme_h) / len(forme_h) if forme_h else 0.5) - (sum(forme_a) / len(forme_a) if forme_a else 0.5),
        "bm_h": sum(bm_h) / len(bm_h) if bm_h else 1.3,
        "be_h": sum(be_h) / len(be_h) if be_h else 1.3,
        "bm_a": sum(bm_a) / len(bm_a) if bm_a else 1.1,
        "be_a": sum(be_a) / len(be_a) if be_a else 1.4,
        "diff_attaque": (sum(bm_h)/len(bm_h) if bm_h else 1.3) - (sum(bm_a)/len(bm_a) if bm_a else 1.1),
        "diff_defense": (sum(be_a)/len(be_a) if be_a else 1.4) - (sum(be_h)/len(be_h) if be_h else 1.3),
        "h2h_goals_home": 0, "h2h_goals_away": 0, "h2h_n": 0,
        "repos_h": 7, "repos_a": 7,
        "home_adv_ratio": 0.45,
    }
    return features


def predire_match_v2(home_team, away_team, competition="default", cotes_book=None):
    """Fonction principale de prédiction."""
    
    # --- TRADUCTION DES NOMS ---
    home_team_db = NOMS_EQUIPES_MAPPING.get(home_team, home_team)
    away_team_db = NOMS_EQUIPES_MAPPING.get(away_team, away_team)
    # ---------------------------

    models = global_model_data.get("models")
    if not models:
        return {"erreur": "Modèle IA non chargé. Réessaie dans un instant."}

    feats = _get_team_features(home_team_db, away_team_db)
    if not feats:
        return {"erreur": f"Pas assez d'historique pour {home_team} vs {away_team}."}

    # Construire le vecteur X dans l'ordre exact des features
    feature_names = global_model_data.get("features", [])
    X = np.array([[feats.get(f, 0) for f in feature_names]])

    try:
        result = {"home_team": home_team, "away_team": away_team, "competition": competition}

        # 1N2
        if "1N2" in models:
            p = models["1N2"].predict_proba(X)[0]
            result["p_h"], result["p_d"], result["p_a"] = float(p[0]), float(p[1]), float(p[2])
        else:
            result["p_h"], result["p_d"], result["p_a"] = 0.33, 0.33, 0.33

        # DC_1X
        if "DC_1X" in models:
            p_dc = models["DC_1X"].predict_proba(X)[0]
            result["dc_1x"] = float(p_dc[1])
            result["dc_x2"] = float(1 - result["p_h"])
            result["dc_12"] = float(1 - result["p_d"])
        else:
            result["dc_1x"] = result["p_h"] + result["p_d"]
            result["dc_x2"] = result["p_d"] + result["p_a"]
            result["dc_12"] = result["p_h"] + result["p_a"]

        # Over 2.5 & BTTS
        result["over_25"] = float(models["Over25"].predict_proba(X)[0][1]) if "Over25" in models else 0.5
        result["btts_yes"] = float(models["BTTS"].predict_proba(X)[0][1]) if "BTTS" in models else 0.5

        # HT
        result["ht_prolific"] = {"1ere_mt": 0.33, "2eme_mt": 0.33, "egalite": 0.34}
        if "HT_Prolific" in models:
            p_ht = models["HT_Prolific"].predict_proba(X)[0]
            result["ht_prolific"]["1ere_mt"] = float(p_ht[0])
            result["ht_prolific"]["2eme_mt"] = float(p_ht[1])

        result["htr"] = {"1": 0.33, "N": 0.33, "2": 0.33}
        if "HTR" in models:
            p_htr = models["HTR"].predict_proba(X)[0]
            result["htr"] = {"1": float(p_htr[0]), "N": float(p_htr[1]), "2": float(p_htr[2])}

        # Score exact (approximation basique)
        result["best_score"] = (2, 1) if result["p_h"] > result["p_a"] else (1, 2)

        # Analyse Value Bet
        result["analyse_pari"] = None
        if cotes_book and "h" in cotes_book:
            proba_book = 1 / cotes_book["h"]
            if result["p_h"] > proba_book + 0.05:
                result["analyse_pari"] = {
                    "label": "1 (Domicile)",
                    "proba": result["p_h"],
                    "cote_bot": round(1 / result["p_h"], 2),
                    "cote_book": cotes_book["h"],
                    "is_value": True
                }

        return result

    except Exception as e:
        log_error("Erreur de prédiction", "PREDICTION", extra={"home": home_team, "away": away_team}, exception=e)
        return {"erreur": "Erreur de calcul. L'admin a été prévenu."}
