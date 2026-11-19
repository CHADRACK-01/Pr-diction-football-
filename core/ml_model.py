# core/ml_model.py
"""
Chargement du modèle IA depuis models_cache.

Le bundle doit respecter le contrat défini dans core/contrat_modele.py.
Un bundle non conforme est refusé et journalisé : le bot affiche alors
« modèle indisponible » plutôt que de produire des pronostics faux.
"""
import threading
from datetime import datetime, timezone, timedelta

from core.utils.logs import log_info, log_error
from core.contrat_modele import decoder_bundle, ContratInvalide, FEATURE_NAMES
from core.features import EtatEquipes
from users.db import db_fetchone

TZ_KINSHASA = timezone(timedelta(hours=1))

global_model_data = {
    "models": None,
    "features": None,
    "metrics": None,
    "precision_moyenne": None,
    "total_matchs": None,
    "date_chargement": None,
    "etat": None,              # EtatEquipes, avancé au fil des nouveaux matchs
    "date_max_donnees": None,
}

_model_lock = threading.Lock()
_is_loading = False


def charger_et_entrainer():
    """Charge le dernier bundle valide depuis models_cache.

    Le nom est conservé pour compatibilité avec les appels existants.
    Cette fonction ne ré-entraîne pas le modèle : l'entraînement se fait
    hors du bot (voir entrainement/).
    """
    global _is_loading

    with _model_lock:
        if _is_loading:
            return False
        _is_loading = True

    try:
        log_info("Chargement du modèle IA depuis Turso...", "ML_MODEL")

        row = db_fetchone(
            "SELECT data FROM models_cache ORDER BY id DESC LIMIT 1",
            db_context={"table": "models_cache", "operation": "load"},
        )
        if not row or not row[0]:
            log_error("Aucun modèle trouvé dans models_cache", "ML_MODEL")
            return False

        try:
            bundle = decoder_bundle(row[0])
        except ContratInvalide as e:
            log_error(f"Modèle refusé (contrat non respecté) : {e}", "ML_MODEL")
            return False

        global_model_data["models"] = bundle["models"]
        global_model_data["features"] = list(FEATURE_NAMES)
        global_model_data["metrics"] = bundle["metrics"]
        global_model_data["etat"] = EtatEquipes.depuis_dict(bundle["etat"])
        global_model_data["date_max_donnees"] = bundle["date_max_donnees"]
        global_model_data["date_chargement"] = datetime.now(TZ_KINSHASA).strftime("%Y-%m-%d %H:%M:%S")

        metrics_1n2 = bundle["metrics"].get("1N2", {})
        global_model_data["precision_moyenne"] = metrics_1n2.get("accuracy")
        global_model_data["total_matchs"] = bundle.get("total_matchs")

        log_info(
            f"✅ Modèle chargé (données jusqu'au {bundle['date_max_donnees']}) : "
            f"{len(bundle['models'])} marché(s).",
            "ML_MODEL",
        )
        return True

    except Exception as e:
        log_error("Erreur critique lors du chargement du modèle", "ML_MODEL", exception=e)
        return False
    finally:
        _is_loading = False


def get_modeles():
    return global_model_data.get("models")
    
