import io
import joblib
from core.ml_model import global_model_data

def charger_modele_universel():
    """
    Charge le modèle depuis la BDD (XGBoost ou RF) et l'injecte dans global_model_data.
    """
    if global_model_data.get('model') is not None:
        return True # Déjà chargé

    from users import charger_modele_cache
    
    cache = charger_modele_cache()
    if not cache:
        print("❌ Aucun modèle en cache.")
        return False

    try:
        modele_bytes, precision, nb_matchs = cache
        buffer = io.BytesIO(modele_bytes)
        donnees = joblib.load(buffer)

        # On met à jour le dictionnaire global
        global_model_data['df'] = donnees.get('df')
        global_model_data['teams'] = donnees.get('teams')
        global_model_data['team_to_code'] = donnees.get('team_to_code')
        global_model_data['team_global_stats'] = donnees.get('team_global_stats')
        global_model_data['precision'] = precision
        global_model_data['model'] = donnees.get('model')
        global_model_data['features'] = donnees.get('features')
        global_model_data['_tables_initialisees'] = True
        
        print(f"✅ Modèle chargé : {type(global_model_data['model']).__name__} (Précision : {round(precision*100, 2)}%)")
        return True
    except Exception as e:
        print(f"⚠️ Erreur chargement modèle : {e}")
        return False
