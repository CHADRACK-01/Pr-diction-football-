# core/ml_model.py
"""
Chargement et gestion du modèle IA (LightGBM).
- Charge le bundle Base64 depuis Turso.
- Décompresse avec zlib et désérialise avec pickle.
- Cache en mémoire (global_model_data).
- Anti-corruption : ne fait plus de concaténation BLOB.
"""

import base64
import zlib
import pickle
import threading
from datetime import datetime, timezone, timedelta

from core.utils.logs import log_info, log_error, log_warning
from users.db import db_fetchone

TZ_KINSHASA = timezone(timedelta(hours=1))

# Cache global en mémoire
global_model_data = {
    "modeles_par_competition": None,
    "features": None,
    "metrics": None,
    "precision_moyenne": None,
    "total_matchs": None,
    "date_chargement": None,
    "version": None,
}

_model_lock = threading.Lock()
_is_loading = False


def charger_et_entrainer():
    """
    Charge le modèle depuis Turso (models_cache).
    Nom conservé pour compatibilité avec app.py et daily_matches.py.
    """
    global _is_loading
    
    with _model_lock:
        if _is_loading:
            log_warning(
                message="Chargement du modèle déjà en cours, attente...",
                module="ML_MODEL",
            )
            return False
        _is_loading = True

    try:
        log_info("Tentative de chargement du modèle depuis Turso...", "ML_MODEL")

        # 1. Récupération du BLOB Base64
        row = db_fetchone(
            "SELECT data, date_creation FROM models_cache WHERE id = 1",
            db_context={"table": "models_cache", "operation": "load"},
        )

        if not row or not row[0]:
            log_error(
                message="Aucun modèle trouvé dans models_cache (table vide)",
                module="ML_MODEL",
            )
            _is_loading = False
            return False

        b64_data = row[0]
        date_creation = row[1] if len(row) > 1 else "Inconnue"

        log_info(
            f"Modèle récupéré de la base (Taille B64: {len(b64_data)} chars, créé le: {date_creation})",
            "ML_MODEL",
        )

        # 2. Décodage Base64 -> zlib -> pickle
        try:
            compressed_data = base64.b64decode(b64_data)
            bundle_bytes = zlib.decompress(compressed_data)
            bundle = pickle.loads(bundle_bytes)
        except Exception as e:
            log_error(
                message="Erreur de décodage/décompression du modèle",
                module="ML_MODEL",
                exception=e,
            )
            _is_loading = False
            return False

        # 3. Extraction des données du bundle
        if not isinstance(bundle, dict) or "models" not in bundle:
            log_error(
                message="Format du bundle invalide (clé 'models' manquante)",
                module="ML_MODEL",
                extra={"type_bundle": str(type(bundle))},
            )
            _is_loading = False
            return False

        # 4. Mise à jour du cache global
        global_model_data["modeles_par_competition"] = bundle.get("models", {})
        global_model_data["features"] = bundle.get("features", [])
        global_model_data["metrics"] = bundle.get("metrics", {})
        global_model_data["date_chargement"] = datetime.now(TZ_KINSHASA).strftime("%Y-%m-%d %H:%M:%S")
        global_model_data["version"] = bundle.get("trained_at", "Inconnue")
        global_model_data["total_matchs"] = (
            bundle.get("n_train", 0) + bundle.get("n_val", 0) + bundle.get("n_test", 0)
        )

        # Calcul approximatif de la précision (basé sur les métriques du bundle)
        metrics = global_model_data["metrics"]
        if "DC_1X" in metrics:
            global_model_data["precision_moyenne"] = metrics["DC_1X"].get("accuracy")
        elif "1N2" in metrics:
            global_model_data["precision_moyenne"] = metrics["1N2"].get("accuracy")

        nb_modeles = len(global_model_data["modeles_par_competition"])
        log_info(
            f"✅ Modèle chargé avec succès : {nb_modeles} marchés disponibles.",
            "ML_MODEL",
            extra={"marchés": list(global_model_data['modeles_par_competition'].keys())},
        )

        _is_loading = False
        return True

    except Exception as e:
        log_error(
            message="Erreur critique lors du chargement du modèle",
            module="ML_MODEL",
            exception=e,
        )
        _is_loading = False
        return False


def get_modele_actif():
    """
    Retourne le dictionnaire des modèles actifs en mémoire, ou None.
    """
    return global_model_data.get("modeles_par_competition")


def get_features():
    """Retourne la liste des features utilisées pour l'entraînement."""
    return global_model_data.get("features", [])


def verifier_sante_modele():
    """
    Vérifie si le modèle est chargé et prêt à l'emploi.
    Retourne un dict avec l'état.
    """
    modeles = global_model_data.get("modeles_par_competition")
    if not modeles:
        return {"ok": False, "raison": "Modèle non chargé en mémoire"}

    return {
        "ok": True,
        "nb_marches": len(modeles),
        "marches": list(modeles.keys()),
        "date_chargement": global_model_data.get("date_chargement"),
        "version_entrainement": global_model_data.get("version"),
        "total_matchs_entrainement": global_model_data.get("total_matchs"),
        }
