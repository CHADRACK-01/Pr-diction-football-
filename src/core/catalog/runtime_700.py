"""Runtime sécurisé du catalogue 1 à 700.

Ce module ne simule jamais un succès métier. Il fournit un contrat commun aux
fonctionnalités locales, partielles ou externes : validation, logs, repli sûr,
registre de provider et statut explicite.
"""

import os
from datetime import datetime

from core.catalog.catalogue_fonctionnalites import obtenir_fonctionnalite
from core.utils.logs import log_error, log_info, log_warning


_PROVIDERS = {
    "Paiement": ("AIRTEL_API_URL", "ORANGE_API_URL", "MPESA_API_URL"),
    "Données": ("FOOTBALL_DATA_KEY", "BZZOIRO_API_KEY", "API_FOOTBALL_KEY_1"),
    "Paris": ("ODDS_API_KEY",),
    "Live": ("API_FOOTBALL_KEY_1",),
    "Contenu": ("GOOGLE_AI_API_KEY", "GROQ_API_KEY"),
    "Distribution": ("TELEGRAM_TOKEN",),
    "Expérience": ("TELEGRAM_TOKEN",),
}


def obtenir_variables_provider(groupe):
    return tuple(_PROVIDERS.get(groupe, ()))


def executer_fonctionnalite(feature_id, payload=None):
    """Exécute un contrat sûr ou retourne un état explicite de préparation."""
    payload = dict(payload or {})
    try:
        item = obtenir_fonctionnalite(feature_id)
        groupe = item["groupe"]
        variables = obtenir_variables_provider(groupe)
        configurées = [variable for variable in variables if os.environ.get(variable, "").strip()] 

        if item["statut"] == "complete":
            log_info(f"Fonction {feature_id} invoquée", "RUNTIME_700", extra={"nom": item["nom"]})
            return {
                "feature_id": str(feature_id),
                "nom": item["nom"],
                "statut": "complete",
                "etat": "pret",
                "message": "Fonctionnalité disponible dans son module local.",
                "horodatage": datetime.now().isoformat(timespec="seconds"),
            }

        if configurées:
            log_info(f"Fournisseur disponible pour la fonction {feature_id}", "RUNTIME_700", extra={"variables": configurées})
            return {
                "feature_id": str(feature_id),
                "nom": item["nom"],
                "statut": item["statut"],
                "etat": "provider_disponible",
                "message": "Intégration prête : adaptation finale du fournisseur requise.",
                "provider": {variable: "configuré" for variable in configurées},
                "horodatage": datetime.now().isoformat(timespec="seconds"),
            }

        log_warning(f"Fonction {feature_id} en attente de configuration", "RUNTIME_700", extra={"groupe": groupe})
        return {
            "feature_id": str(feature_id),
            "nom": item["nom"],
            "statut": item["statut"],
            "etat": "en_attente_configuration",
            "message": "Fonction ajoutée au runtime ; fournisseur humain/externe à configurer.",
            "variables_requises": list(variables),
            "horodatage": datetime.now().isoformat(timespec="seconds"),
        }
    except KeyError as e:
        log_warning("Identifiant de fonctionnalité inconnu", "RUNTIME_700", extra={"feature_id": str(feature_id)})
        return {"feature_id": str(feature_id), "etat": "invalide", "message": "Fonctionnalité inconnue."}
    except Exception as e:
        log_error("Erreur du runtime des 700 fonctionnalités", "RUNTIME_700", extra={"feature_id": str(feature_id)}, exception=e)
        return {"feature_id": str(feature_id), "etat": "erreur_sure", "message": "Erreur capturée : aucune action réelle n'a été exécutée."}
