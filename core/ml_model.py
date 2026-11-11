# core/ml_model.py
"""
Chargement des modèles IA depuis Turso.
- Plus de valeurs en dur (precision, total_matchs lus depuis le BLOB)
- Cache LRU thread-safe
- Logs enrichis
"""

import os
os.environ["LOKY_MAX_CPU_COUNT"] = "1"

import io
import threading
import joblib

from core.utils.logs import log_info, log_error, log_warning

# État global
global_model_data = {}

# Cache LRU thread-safe
CACHE_MODELES = {}
TAILLE_MAX_CACHE = 3
_CACHE_LOCK = threading.Lock()


def charger_et_entrainer():
    """
    Charge les modèles depuis Turso (table models_cache).
    ⚠️ Le nom est conservé pour compatibilité, mais ne fait QUE charger.
    Retourne True si succès, False sinon.
    """
    if global_model_data.get("modeles_par_competition") is not None:
        return True

    from users.db import db_fetchone

    log_info("Chargement des modèles depuis Turso...", "ML_MODEL")

    row = db_fetchone(
        "SELECT data FROM models_cache ORDER BY id DESC LIMIT 1",
        db_context={"table": "models_cache", "operation": "load"},
    )

    if not row or not row[0]:
        log_error(
            message="Aucun modèle trouvé dans models_cache",
            module="ML_MODEL",
            db_context={"table": "models_cache"},
        )
        return False

    try:
        payload = joblib.load(io.BytesIO(row[0]))
    except Exception as e:
        log_error(
            message="Le fichier modèle est corrompu ou illisible",
            module="ML_MODEL",
            exception=e,
        )
        return False

    # Le payload est soit un dict {comp: {marché: data}}, soit un dict enrichi
    # {modeles: {...}, precision: X, total_matchs: Y}
    if isinstance(payload, dict) and "modeles" in payload:
        modeles = payload["modeles"]
        precision = payload.get("precision_moyenne")
        total = payload.get("total_matchs")
    else:
        # Ancien format : juste {comp: {marché: data}}
        modeles = payload
        precision = None
        total = None

    if not isinstance(modeles, dict) or not modeles:
        log_error(
            message="Le BLOB modèle ne contient pas de dictionnaire valide",
            module="ML_MODEL",
            extra={"type_recu": type(modeles).__name__},
        )
        return False

    global_model_data["modeles_par_competition"] = modeles
    global_model_data["precision_moyenne"] = precision  # peut être None
    global_model_data["total_matchs"] = total  # peut être None
    global_model_data["_tables_initialisees"] = True

    log_info(
        f"Modèle chargé : {len(modeles)} compétitions"
        + (f", précision {precision * 100:.1f}%" if precision else "")
        + (f", {total} matchs" if total else ""),
        "ML_MODEL",
        extra={
            "nb_competitions": len(modeles),
            "precision": precision,
            "total_matchs": total,
        },
    )
    return True


def charger_modele_competition(competition):
    """
    Charge le modèle d'une compétition (cache LRU thread-safe).
    Retourne None si introuvable.
    """
    with _CACHE_LOCK:
        if competition in CACHE_MODELES:
            return CACHE_MODELES[competition]

        modeles = global_model_data.get("modeles_par_competition", {})
        if competition not in modeles:
            log_warning(
                message=f"Modèle introuvable pour la compétition '{competition}'",
                module="ML_MODEL",
                extra={"competition": competition},
            )
            return None

        # LRU : supprimer le plus ancien si plein
        if len(CACHE_MODELES) >= TAILLE_MAX_CACHE:
            plus_ancien = next(iter(CACHE_MODELES))
            del CACHE_MODELES[plus_ancien]
            log_info(
                f"Cache plein, suppression du modèle '{plus_ancien}'",
                "ML_MODEL",
            )

        CACHE_MODELES[competition] = modeles[competition]
        log_info(f"Modèle '{competition}' chargé en RAM", "ML_MODEL")

    return CACHE_MODELES[competition]
