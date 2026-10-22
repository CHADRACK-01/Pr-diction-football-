import io
import joblib
import zlib
from core.ml_model import global_model_data
from core.utils.logs import log_info, log_error


def charger_modele_universel():
    """
    Charge le modèle depuis Turso (via model_cache.py) et l'injecte dans global_model_data.
    """
    # Si le modèle est déjà chargé en mémoire, on ne fait rien
    if global_model_data.get('modeles_par_competition') is not None:
        return True

    from users import charger_modele_cache
    
    cache = charger_modele_cache()
    if not cache:
        log_error("Aucun modèle en cache dans Turso.", "MODEL_LOADER")
        return False

    modele_bytes, precision, nb_matchs = cache
    
    log_info(f"Décompression du modèle ({len(modele_bytes) / 1024 / 1024:.2f} MB)...", "MODEL_LOADER")
    modele_decompresse = zlib.decompress(modele_bytes)
    
    log_info("Chargement en mémoire (patientez quelques secondes)...", "MODEL_LOADER")
    buffer = io.BytesIO(modele_decompresse)
    donnees = joblib.load(buffer)

    # On injecte les données dans le dictionnaire global
    global_model_data['modeles_par_competition'] = donnees.get('modeles_par_competition')
    global_model_data['precision_moyenne'] = donnees.get('precision_moyenne', precision)
    global_model_data['total_matchs'] = donnees.get('total_matchs', nb_matchs)
    global_model_data['_tables_initialisees'] = True
    
    log_info(f"Modèle chargé : {len(global_model_data['modeles_par_competition'])} compétitions (Précision: {round(precision*100, 2)}%)", "MODEL_LOADER")
    return True
