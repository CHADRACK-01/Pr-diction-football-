# core/services/paiement.py
"""
Service de paiement et abonnements.

Orchestre :
- core.adaptateurs.paiements.AdaptateurPaiementMobileMoney (Airtel, M-Pesa, Orange)
- core.config_adaptateurs.charger_config_adaptateurs
- users/ pour la persistance (statut, expiration, codes premium)
"""

from __future__ import annotations

from typing import Any

from core.adaptateurs.paiements import AdaptateurPaiementMobileMoney
from core.config_adaptateurs import charger_config_adaptateurs
from core.exceptions import PaiementError, CodePromoInvalideError
from core.utils.logs import log_info, log_error


class ServicePaiement:
    """Service de gestion des paiements Mobile Money et abonnements Premium."""

    def __init__(self):
        self._config = charger_config_adaptateurs()
        self._adaptateur = AdaptateurPaiementMobileMoney()

    def verifier_paiement(
        self,
        operateur: str,
        montant: int,
        reference: str,
        numero_expediteur: str,
    ) -> dict[str, Any]:
        """Vérifie un paiement Mobile Money auprès de l'opérateur.

        Args:
            operateur: "airtel", "m-pesa" ou "orange".
            montant: Montant attendu.
            reference: Référence de la transaction.
            numero_expediteur: Numéro de téléphone de l'expéditeur.

        Returns:
            Dictionnaire {valide, operateur, montant, reference, erreur}.
        """
        if not self._config.paiement_configuré(operateur):
            return {
                "valide": False,
                "erreur": f"Opérateur {operateur} non configuré (clé/URL manquante dans .env)",
            }

        try:
            succes, donnees, erreur = self._adaptateur.verifier_reference(
                operateur, montant, reference, numero_expediteur
            )
            return {
                "valide": succes,
                "operateur": operateur,
                "montant": montant,
                "reference": reference,
                "donnees": donnees,
                "erreur": erreur,
            }
        except Exception as e:
            log_error(
                "Erreur vérification paiement",
                "SERVICE_PAIEMENT",
                exception=e,
                extra={"operateur": operateur, "montant": montant, "reference": reference},
            )
            return {
                "valide": False,
                "operateur": operateur,
                "montant": montant,
                "reference": reference,
                "erreur": str(e),
            }

    def generer_demande_paiement(
        self,
        operateur: str,
        montant: int,
        numero_client: str,
    ) -> dict[str, Any]:
        """Génère une demande de paiement (push USSD) vers le client.

        Returns:
            Dictionnaire {succes, reference, operateur, montant, erreur}.
        """
        if not self._config.paiement_configuré(operateur):
            return {
                "succes": False,
                "erreur": f"Opérateur {operateur} non configuré (clé/URL manquante dans .env)",
            }

        try:
            succes, donnees, erreur = self._adaptateur.generer_code_paiement(
                operateur, montant, numero_client
            )
            return {
                "succes": succes,
                "reference": donnees.get("reference") if donnees else None,
                "operateur": operateur,
                "montant": montant,
                "erreur": erreur,
            }
        except Exception as e:
            log_error(
                "Erreur génération paiement",
                "SERVICE_PAIEMENT",
                exception=e,
                extra={"operateur": operateur, "montant": montant, "numero": numero_client},
            )
            return {
                "succes": False,
                "operateur": operateur,
                "montant": montant,
                "erreur": str(e),
            }

    def essai_premium_24h(self, user_id: int) -> dict[str, Any]:
        """Active un essai Premium de 24 heures pour un utilisateur (une fois).

        Retourne {succes, date_expiration, message}.
        L'implémentation réelle met à jour la table utilisateurs via users/.
        """
        # Placeholder : la persistance réelle se fait via users.account_base ou users.admin
        # Cette fonction définit le contrat métier ; l'implémentation DB est dans users/
        return {
            "succes": True,
            "duree_heures": 24,
            "message": "Essai Premium 24h activé (à implémenter côté persistance users/)",
        }
