# core/paiement_auto.py
"""
Fonctionnalité 31 : Paiement Auto Airtel / M-Pesa / Orange.
Utilise un endpoint HTTP de l'opérateur lorsqu'il est configuré.
Sans clé ou endpoint, retourne explicitement une demande de vérification manuelle.
"""

import os
import requests
from core.utils.logs import log_info, log_error, log_warning

# Clés API (à remplir si les opérateurs mettent à disposition un endpoint vérifiable).
AIRTEL_API_KEY = os.environ.get("AIRTEL_API_KEY", "")
ORANGE_API_KEY = os.environ.get("ORANGE_API_KEY", "")
MPESA_API_KEY = os.environ.get("MPESA_API_KEY", "")
AIRTEL_API_URL = os.environ.get("AIRTEL_API_URL", "")
ORANGE_API_URL = os.environ.get("ORANGE_API_URL", "")
MPESA_API_URL = os.environ.get("MPESA_API_URL", "")


def verifier_paiement_auto(operateur, numero_expediteur, montant, reference):
    """Vérifie une référence auprès d'un fournisseur Mobile Money configuré."""
    operateur_normalise = str(operateur or "").strip().lower()
    log_info(f"Vérification paiement : {operateur} - {numero_expediteur} - {montant} CDF", "PAIEMENT_AUTO")

    fournisseurs = {
        "airtel": (AIRTEL_API_KEY, AIRTEL_API_URL),
        "orange": (ORANGE_API_KEY, ORANGE_API_URL),
        "m-pesa": (MPESA_API_KEY, MPESA_API_URL),
    }
    fournisseur = fournisseurs.get(operateur_normalise)
    if fournisseur is None:
        return False, "Opérateur de paiement non reconnu."

    cle, url = fournisseur
    if not cle:
        return False, f"Vérification manuelle requise (API {operateur} non configurée)."
    if not url:
        log_warning(f"Endpoint API {operateur} non configuré.", "PAIEMENT_AUTO")
        return False, f"Vérification manuelle requise (endpoint API {operateur} absent)."

    try:
        reponse = requests.post(
            url,
            headers={"Authorization": f"Bearer {cle}", "Accept": "application/json"},
            json={
                "operateur": operateur,
                "numero_expediteur": str(numero_expediteur).strip(),
                "montant": float(montant),
                "reference": str(reference).strip(),
            },
            timeout=15,
        )
        if reponse.status_code not in (200, 201, 202):
            return False, f"Paiement non confirmé par l'opérateur ({reponse.status_code})."

        donnees = reponse.json()
        statut = str(donnees.get("status", "")).strip().upper()
        reference_retournee = str(donnees.get("reference", reference)).strip()
        if statut == "SUCCESS" and reference_retournee == str(reference).strip():
            return True, "Paiement vérifié avec succès par l'opérateur."
        return False, "Paiement non trouvé dans les systèmes de l'opérateur."
    except (requests.exceptions.RequestException, ValueError, TypeError) as e:
        log_error(f"Erreur lors de la vérification API {operateur}", "PAIEMENT_AUTO", exception=e)
        return False, "Erreur technique lors de la vérification automatique."
