import os
import libsql
from datetime import datetime

from core.nouveau_prediction import predire_match_v2
from core.utils.logs import log_info, log_error

TURSO_URL = os.environ.get("TURSO_URL", "")
TURSO_TOKEN = os.environ.get("TURSO_TOKEN", "")

def get_connection():
    return libsql.connect(database=TURSO_URL, auth_token=TURSO_TOKEN)

def predire_match(home_input, away_input, competition="default", cotes_book=None):
    """
    Wrapper : appelle la nouvelle fonction de prédiction (5 modèles LightGBM).
    """
    log_info(f"Prédiction demandée : {home_input} vs {away_input} ({competition})", "PREDICTION")
    
    # Appel de la nouvelle fonction
    resultat = predire_match_v2(
        home_team=home_input, 
        away_team=away_input, 
        competition=competition, 
        cotes_book=cotes_book
    )
    
    return resultat


def sauvegarder_historique(home_team, away_team, p_h, p_d, p_a, best_i, best_j):
    """
    Sauvegarde le pronostic dans l'historique (table resultats_pronostics).
    """
    options = [("1X", p_h + p_d), ("X2", p_d + p_a), ("12", p_h + p_a)]
    meilleure = max(options, key=lambda x: x[1])[0]
    score_exact = f"{best_i}-{best_j}"
    
    try:
        conn = get_connection()
        conn.execute("""
            INSERT INTO resultats_pronostics (date_match, home_team, away_team, pronostic_reco, score_reel)
            VALUES (date('now'), ?, ?, ?, ?)
        """, (home_team, away_team, meilleure, score_exact))
        
        # Nettoyage des vieux historiques (garde 30 jours)
        conn.execute("DELETE FROM resultats_pronostics WHERE date_match < date('now', '-30 days')")
        conn.commit()
        conn.close()
        
        log_info(f"Historique sauvegardé : {home_team} vs {away_team} ({meilleure})", "PREDICTION")
    except Exception as e:
        log_error(f"Erreur sauvegarde historique : {e}", "PREDICTION")
