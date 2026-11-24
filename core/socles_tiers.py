"""Socles prêts pour les fonctionnalités nécessitant des API ou comptes tiers.

Chaque adaptateur doit respecter les contrats ci-dessous. Aucun secret n'est stocké.
"""

from abc import ABC, abstractmethod


class FournisseurPaiement(ABC):
    @abstractmethod
    def verifier_reference(self, operateur, montant, reference, numero_expediteur):
        raise NotImplementedError


class FournisseurContenu(ABC):
    @abstractmethod
    def publier_texte(self, destinataire, texte):
        raise NotImplementedError

    @abstractmethod
    def publier_image(self, destinataire, chemin_image, legende=None):
        raise NotImplementedError


class FournisseurAudio(ABC):
    @abstractmethod
    def generer_audio(self, texte, langue="fr"):
        raise NotImplementedError


class FournisseurCalendrier(ABC):
    @abstractmethod
    def creer_evenement(self, titre, debut, description="", timezone="Africa/Kinshasa"):
        raise NotImplementedError


class AdaptateurIndisponible:
    """Retour sûr : aucune opération externe n'est simulée comme réussie."""

    def verifier_reference(self, *args, **kwargs):
        return False, "Adaptateur tiers non configuré"

    def publier_texte(self, *args, **kwargs):
        return False, "Adaptateur tiers non configuré"

    def publier_image(self, *args, **kwargs):
        return False, "Adaptateur tiers non configuré"

    def generer_audio(self, *args, **kwargs):
        return None, "Adaptateur tiers non configuré"

    def creer_evenement(self, *args, **kwargs):
        return None, "Adaptateur tiers non configuré"
