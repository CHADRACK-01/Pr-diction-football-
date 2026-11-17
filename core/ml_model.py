# core/ml_model.py
import base64
import zlib
import pickle
import threading
from datetime import datetime, timezone, timedelta

from core.utils.logs import log_info, log_error, log_warning
from users.db import db_fetchone

TZ_KINSHASA = timezone(timedelta(hours=1))

global_model_data = {
    "models": None,
    "features": None,
    "metrics": None,
    "precision_moyenne": None,
    "total_matchs": None,
    "date_chargement": None,
}

_model_lock = threading.Lock()
_is_loading = False

def charger_et_entrainer():
    global _is_loading
    
    with _model_lock:
        if _is_loading:
            return False
        _is_loading = True

    try:
        log_info("Chargement du modèle IA depuis Turso...", "ML_MODEL")

        # On lit juste la colonne 'data'
        row = db_fetchone(
            "SELECT data FROM models_cache ORDER BY id DESC LIMIT 1",
            db_context={"table": "models_cache", "operation": "load"},
        )

        if not row or not row[0]:
            log_error("Aucun modèle trouvé dans models_cache", "ML_MODEL")
            _is_loading = False
            return False

        b64_data = row[0]

        try:
            compressed_data = base64.b64decode(b64_data)
            bundle_bytes = zlib.decompress(compressed_data)
            bundle = pickle.loads(bundle_bytes)
        except Exception as e:
            log_error("Erreur de décodage/décompression du modèle", "ML_MODEL", exception=e)
            _is_loading = False
            return False

        global_model_data["models"] = bundle.get("models", {})
        global_model_data["features"] = bundle.get("features", [])
        global_model_data["metrics"] = bundle.get("metrics", {})
        global_model_data["date_chargement"] = datetime.now(TZ_KINSHASA).strftime("%Y-%m-%d %H:%M:%S")
        
        metrics = global_model_data["metrics"]
        if "DC_1X" in metrics:
            global_model_data["precision_moyenne"] = metrics["DC_1X"].get("accuracy")
        elif "1N2" in metrics:
            global_model_data["precision_moyenne"] = metrics["1N2"].get("accuracy")

        nb_modeles = len(global_model_data["models"])
        log_info(f"✅ Modèle chargé : {nb_modeles} marchés disponibles.", "ML_MODEL")

        modele_1n2 = global_model_data["models"].get("1N2")
        if modele_1n2 is not None and hasattr(modele_1n2, "classes_"):
            log_info(f"Classes 1N2 : {list(modele_1n2.classes_)}", "ML_MODEL")

        _is_loading = False
        return True

    except Exception as e:
        log_error("Erreur critique lors du chargement du modèle", "ML_MODEL", exception=e)
        _is_loading = False
        return False

def get_modeles():
    return global_model_data.get("models")
