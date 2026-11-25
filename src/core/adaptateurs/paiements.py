# core/adaptateurs/paiements.py
"""
Adaptateurs de paiement Mobile Money (Airtel, M-Pesa, Orange Money).

Configuration requise :
  - AIRTEL_API_KEY, AIRTEL_API_URL
  - MPESA_API_KEY, MPESA_API_URL
  - ORANGE_API_KEY, ORANGE_API_URL

Aucun paiement n'est simulé comme réussi si le fournisseur n'est pas configuré.
"""

from __future__ import annotations

import os
from typing import Any

import requests

from core.adaptateurs.base import FournisseurPaiement, ResultatAdaptateur, _resultat

TIMEOUT_SEC = 10


class AdaptateurPaiementMobileMoney(FournisseurPaiement):
    """Adaptateur unifié pour les opérateurs Mobile Money RDC.

    Supporte : Airtel Money, M-Pesa, Orange Money.
    Chaque opérateur est configuré indépendamment via ses propres variables d'env.
    """

    def __init__(self):
        self._config = {
            "airtel": {
                "cle": os.environ.get("AIRTEL_API_KEY", ""),
                "url": os.environ.get("AIRTEL_API_URL", ""),
            },
            "m-pesa": {
                "cle": os.environ.get("MPESA_API_KEY", ""),
                "url": os.environ.get("MPESA_API_URL", ""),
            },
            "orange": {
                "cle": os.environ.get("ORANGE_API_KEY", ""),
                "url": os.environ.get("ORANGE_API_URL", ""),
            },
        }

    def _config_operateur(self, operateur: str) -> dict[str, str] | None:
        cfg = self._config.get(operateur.lower())
        if not cfg or not cfg["cle"] or not cfg["url"]:
            return None
        return cfg

    def verifier_reference(
        self,
        operateur: str,
        montant: int,
        reference: str,
        numero_expediteur: str,
    ) -> ResultatAdaptateur:
        """Vérifie qu'une référence de paiement a été validée par l'opérateur."""
        cfg = self._config_operateur(operateur)
        if not cfg:
            return _resultat(False, None, f"Opérateur {operateur} non configuré (clé/URL manquante)")
        try:
            resp = requests.post(
                f"{cfg['url']}/verify",
                json={"montant": montant, "reference": reference, "numero": numero_expediteur},
                headers={"Authorization": f"Bearer {cfg['cle']}"},
                timeout=TIMEOUT_SEC,
            )
            if resp.status_code != 200:
                return _resultat(False, None, f"Erreur HTTP {resp.status_code} lors de la vérification")
            donnees = resp.json()
            valide = donnees.get("statut") == "succes" or donnees.get("success") is True
            return _resultat(valide, donnees, None if valide else "Paiement non confirmé")
        except requests.RequestException as e:
            return _resultat(False, None, f"Erreur réseau {operateur} : {type(e).__name__}")
        except (ValueError, KeyError) as e:
            return _resultat(False, None, f"Erreur de parsing {operateur} : {type(e).__name__}")

    def generer_code_paiement(
        self,
        operateur: str,
        montant: int,
        numero_client: str,
    ) -> ResultatAdaptateur:
        """Génère une demande de paiement (push USSD / API) vers le client."""
        cfg = self._config_operateur(operateur)
        if not cfg:
            return _resultat(False, None, f"Opérateur {operateur} non configuré (clé/URL manquante)")
        try:
            resp = requests.post(
                f"{cfg['url']}/payment",
                json={"montant": montant, "numero": numero_client},
                headers={"Authorization": f"Bearer {cfg['cle']}"},
                timeout=TIMEOUT_SEC,
            )
            if resp.status_code != 200:
                return _resultat(False, None, f"Erreur HTTP {resp.status_code} lors du paiement")
            donnees = resp.json()
            ref = donnees.get("reference") or donnees.get("transaction_id")
            if not ref:
                return _resultat(False, None, "Aucune référence de paiement retournée")
            return _resultat(True, {"reference": ref, "operateur": operateur, "montant": montant}, None)
        except requests.RequestException as e:
            return _resultat(False, None, f"Erreur réseau {operateur} : {type(e).__name__}")
        except (ValueError, KeyError) as e:
            return _resultat(False, None, f"Erreur de parsing {operateur} : {type(e).__name__}")
