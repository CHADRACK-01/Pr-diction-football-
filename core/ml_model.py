import os
os.environ['LOKY_MAX_CPU_COUNT'] = '1'

import io
import joblib
import zlib
from datetime import datetime

from users import charger_modele_cache
from core.utils.logs import log_info, log_error

# Dictionnaire global : contiendra les données de base et les modèles
global_model_data = {}

# Cache LRU pour les modèles par compétition (évite de recharger tout le temps)
CACHE_MODELES = {}
TAILLE_MAX_CACHE = 3


def charger_et_entrainer():
    """
    Charge les données de base depuis Turso.
    ⚠️ Le modèle est déjà entraîné et stocké dans Turso.
    ⚠️ Cette fonction ne fait que charger le dictionnaire global.
    """
    global global_model_data

    if global_model_data.get('modeles_par_competition') is not None:
        return True

    cache = charger_modele_cache()
    if not cache:
        log_error("Aucun modèle trouvé dans Turso.", "ML_MODEL")
        return False

    modele_bytes, precision, nb_matchs = cache
    
    log_info(f"Décompression du modèle ({len(modele_bytes) / 1024 / 1024:.2f} MB)...", "ML_MODEL")
    modele_decompresse = zlib.decompress(modele_bytes)
    
    log_info("Chargement en mémoire...", "ML_MODEL")
    buffer = io.BytesIO(modele_decompresse)
    donnees = joblib.load(buffer)

    # On injecte les données dans le dictionnaire global
    global_model_data['modeles_par_competition'] = donnees.get('modeles_par_competition')
    global_model_data['precision_moyenne'] = donnees.get('precision_moyenne', precision)
    global_model_data['total_matchs'] = donnees.get('total_matchs', nb_matchs)
    global_model_data['_tables_initialisees'] = True
    
    log_info(f"Modèle chargé : {len(global_model_data['modeles_par_competition'])} compétitions", "ML_MODEL")
    return True


def charger_modele_competition(competition):
    """
    Charge le modèle d'une compétition spécifique depuis le dictionnaire global.
    Utilise un cache LRU pour ne garder que les 3 derniers modèles en RAM.
    """
    if competition in CACHE_MODELES:
        return CACHE_MODELES[competition]

    modeles = global_model_data.get('modeles_par_competition', {})
    if competition not in modeles:
        log_error(f"Modèle introuvable pour la compétition : {competition}", "ML_MODEL")
        return None
    
    # Gestion du cache LRU
    if len(CACHE_MODELES) >= TAILLE_MAX_CACHE:
        plus_ancien = next(iter(CACHE_MODELES))
        del CACHE_MODELES[plus_ancien]
        log_info(f"Cache plein. Suppression du modèle '{plus_ancien}' de la RAM.", "ML_MODEL")
    
    modele_data = modeles[competition]
    CACHE_MODELES[competition] = modele_data['model']
    
    log_info(f"Modèle '{competition}' chargé en RAM (Précision: {round(modele_data['precision']*100, 2)}%).", "ML_MODEL")
    
    return CACHE_MODELES[competition]
