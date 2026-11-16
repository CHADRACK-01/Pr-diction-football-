# core/paiement_auto.py
"""
Fonctionnalité 31 : Paiement Auto Airtel / M-Pesa / Orange.
Architecture prête pour l'intégration des APIs.
Pour l'instant, utilise un système de vérification simplifié.
"""

import os
from core.utils.logs import log_info, log_error, log_warning

# Clés API (à remplir plus tard si tu as les accès)
AIRTEL_API_KEY = os.environ.get("AIRTEL_API_KEY", "")
ORANGE_API_KEY = os.environ.get("ORANGE_API_KEY", "")
MPESA_API_KEY = os.environ.get("MPESA_API_KEY", "")

def verifier_paiement_auto(operateur, numero_expediteur, montant, reference):
    """
    Vérifie automatiquement un paiement.
    Retourne (succes: bool, message: str).
    """
    log_info(f"Vérification paiement : {operateur} - {numero_expediteur} - {montant} CDF", "PAIEMENT_AUTO")

    # Si les APIs ne sont pas configurées, on utilise le mode manuel
    if operateur == "Airtel" and not AIRTEL_API_KEY:
        return False, "Vérification manuelle requise (API Airtel non configurée)."
    if operateur == "Orange" and not ORANGE_API_KEY:
        return False, "Vérification manuelle requise (API Orange non configurée)."
    if operateur == "M-Pesa" and not MPESA_API_KEY:
        return False, "Vérification manuelle requise (API M-Pesa non configurée)."

    # --- Logique d'appel API (à activer quand tu auras les clés) ---
    try:
        if operateur == "Airtel":
            # Exemple d'appel API Airtel (à remplacer par la vraie doc)
            # res = requests.get(f"https://api.airtel.com/check?ref={reference}", headers={"Authorization": f"Bearer {AIRTEL_API_KEY}"})
            # if res.json().get("status") == "SUCCESS":
            #     return True, "Paiement vérifié avec succès."
            pass
        elif operateur == "Orange":
            # Idem pour Orange
            pass
        elif operateur == "M-Pesa":
            # Idem pour M-Pesa
            pass

        # Si on arrive ici, l'API n'a pas confirmé
        return False, "Paiement non trouvé dans les systèmes de l'opérateur."

    except Exception as e:
        log_error(f"Erreur lors de la vérification API {operateur}", "PAIEMENT_AUTO", exception=e)
        return False, f"Erreur technique : {str(e)}"
