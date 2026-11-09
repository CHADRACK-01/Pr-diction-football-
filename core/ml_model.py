import os
os.environ['LOKY_MAX_CPU_COUNT'] = '1'

import io
import joblib
from core.utils.logs import log_info, log_error

# Dictionnaire global : contiendra les données de base et les modèles
global_model_data = {}

# Cache LRU pour les modèles par compétition (évite de recharger tout le temps)
CACHE_MODELES = {}
TAILLE_MAX_CACHE = 3


def charger_et_entrainer():
    """
    Charge les modèles depuis Turso (table models_cache).
    ⚠️ Les modèles sont déjà entraînés et stockés.
    """
    global global_model_data

    if global_model_data.get('modeles_par_competition') is not None:
        return True

    from users.db import get_connection
    
    log_info("Chargement des modèles depuis Turso...", "ML_MODEL")
    
    conn = get_connection()
    cur = conn.cursor()
    # On prend le dernier modèle sauvegardé
    cur.execute("SELECT data FROM models_cache ORDER BY id DESC LIMIT 1")
    row = cur.fetchone()
    conn.close()

    if not row or not row[0]:
        log_error("Aucun modèle trouvé dans Turso.", "ML_MODEL")
        return False

    try:
        modeles = joblib.load(io.BytesIO(row[0]))
    except Exception as e:
        log_error(f"Erreur lors du chargement du modèle : {e}", "ML_MODEL")
        return False

    # On injecte les données dans le dictionnaire global
    global_model_data['modeles_par_competition'] = modeles
    global_model_data['precision_moyenne'] = 0.58  # Valeur par défaut
    global_model_data['total_matchs'] = 24804
    global_model_data['_tables_initialisees'] = True
    
    log_info(f"Modèle chargé : {len(modeles)} compétitions", "ML_MODEL")
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
    CACHE_MODELES[competition] = modele_data
    
    log_info(f"Modèle '{competition}' chargé en RAM.", "ML_MODEL")
    
    return CACHE_MODELES[competition]
