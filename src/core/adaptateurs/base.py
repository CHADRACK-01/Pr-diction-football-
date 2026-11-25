# core/adaptateurs/base.py
"""Classes de base et contrats pour tous les adaptateurs tiers.

Convention de retour : ``ResultatAdaptateur`` = namedtuple
``(succes, donnees, erreur)``.

Règle d'or : une dépendance absente ou mal configurée retourne
``succes=False`` avec un message d'erreur explicite. JAMAIS de succès
simulé.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections import namedtuple
from typing import Any


ResultatAdaptateur = namedtuple("ResultatAdaptateur", ["succes", "donnees", "erreur"])


def _resultat(succes: bool, donnees: Any = None, erreur: str | None = None) -> ResultatAdaptateur:
    return ResultatAdaptateur(succes=succes, donnees=donnees, erreur=erreur)


class AdaptateurIndisponible:
    """Adaptateur neutre retourné quand aucune clé API n'est configurée.

    Toutes les méthodes retournent ``(False, None, "Adaptateur tiers non configuré")``.
    """

    def verifier_reference(self, *args, **kwargs) -> ResultatAdaptateur:
        return _resultat(False, None, "Adaptateur tiers non configuré")

    def publier_texte(self, *args, **kwargs) -> ResultatAdaptateur:
        return _resultat(False, None, "Adaptateur tiers non configuré")

    def publier_image(self, *args, **kwargs) -> ResultatAdaptateur:
        return _resultat(False, None, "Adaptateur tiers non configuré")

    def generer_audio(self, *args, **kwargs) -> ResultatAdaptateur:
        return _resultat(False, None, "Adaptateur tiers non configuré")

    def creer_evenement(self, *args, **kwargs) -> ResultatAdaptateur:
        return _resultat(False, None, "Adaptateur tiers non configuré")

    def get_matchs_live(self, *args, **kwargs) -> ResultatAdaptateur:
        return _resultat(False, None, "Adaptateur tiers non configuré")

    def get_cotes(self, *args, **kwargs) -> ResultatAdaptateur:
        return _resultat(False, None, "Adaptateur tiers non configuré")

    def get_meteo(self, *args, **kwargs) -> ResultatAdaptateur:
        return _resultat(False, None, "Adaptateur tiers non configuré")


# =====================================================================
# FOURNISSEURS DE DONNÉES SPORTIVES
# =====================================================================


class FournisseurDonneesSportives(ABC):
    """Contrat pour un fournisseur de données football (matchs, cotes, scores)."""

    @abstractmethod
    def get_matchs_live(self, competition: str | None = None) -> ResultatAdaptateur:
        """Retourne les matchs en direct."""
        ...

    @abstractmethod
    def get_cotes(self, match_id: str) -> ResultatAdaptateur:
        """Retourne les cotes d'un match."""
        ...

    @abstractmethod
    def get_resultat(self, match_id: str) -> ResultatAdaptateur:
        """Retourne le résultat final d'un match."""
        ...

    @abstractmethod
    def get_matchs_du_jour(self, date: str) -> ResultatAdaptateur:
        """Retourne les matchs programmés pour une date."""
        ...


# =====================================================================
# FOURNISSEURS DE PAIEMENT
# =====================================================================


class FournisseurPaiement(ABC):
    """Contrat pour un fournisseur de paiement Mobile Money."""

    @abstractmethod
    def verifier_reference(
        self,
        operateur: str,
        montant: int,
        reference: str,
        numero_expediteur: str,
    ) -> ResultatAdaptateur:
        """Vérifie une référence de paiement."""
        ...

    @abstractmethod
    def generer_code_paiement(
        self,
        operateur: str,
        montant: int,
        numero_client: str,
    ) -> ResultatAdaptateur:
        """Génère une demande de paiement (USSD/API)."""
        ...


# =====================================================================
# FOURNISSEURS DE CONTENU (Réseaux sociaux)
# =====================================================================


class FournisseurContenu(ABC):
    """Contrat pour publier du contenu (texte, image) sur un canal tiers."""

    @abstractmethod
    def publier_texte(self, destinataire: str, texte: str) -> ResultatAdaptateur:
        ...

    @abstractmethod
    def publier_image(self, destinataire: str, chemin_image: str, legende: str | None = None) -> ResultatAdaptateur:
        ...


# =====================================================================
# FOURNISSEURS AUDIO
# =====================================================================


class FournisseurAudio(ABC):
    """Contrat pour la synthèse vocale / génération audio."""

    @abstractmethod
    def generer_audio(self, texte: str, langue: str = "fr") -> ResultatAdaptateur:
        """Génère un fichier audio à partir d'un texte."""
        ...


# =====================================================================
# FOURNISSEURS DE CALENDRIER
# =====================================================================


class FournisseurCalendrier(ABC):
    """Contrat pour créer des événements calendrier."""

    @abstractmethod
    def creer_evenement(
        self,
        titre: str,
        debut: str,
        description: str = "",
        timezone: str = "Africa/Kinshasa",
    ) -> ResultatAdaptateur:
        ...


# =====================================================================
# FOURNISSEURS DE MÉTÉO
# =====================================================================


class FournisseurMeteo(ABC):
    """Contrat pour récupérer les données météo."""

    @abstractmethod
    def get_meteo(self, ville: str) -> ResultatAdaptateur:
        """Retourne les conditions météo actuelles d'une ville."""
        ...
