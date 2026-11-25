# core/adaptateurs/factory.py
"""
Factory pour instancier les adaptateurs selon la configuration.

L'utilisateur configure ses clés dans ``core/config_adaptateurs.py`` (ou
directement via les variables d'environnement). Cette factory centralise
la création et permet de mocker facilement en tests.
"""

from __future__ import annotations

from typing import Any

from core.adaptateurs.api_football import AdaptateurApiFootball
from core.adaptateurs.base import (
    AdaptateurIndisponible,
    FournisseurCalendrier,
    FournisseurContenu,
    FournisseurDonneesSportives,
    FournisseurMeteo,
    FournisseurPaiement,
)
from core.adaptateurs.paiements import AdaptateurPaiementMobileMoney
from core.adaptateurs.reseaux_sociaux import AdaptateurReseauxSociaux
from core.adaptateurs.audio import AdaptateurAudio
from core.adaptateurs.calendrier import AdaptateurCalendrier
from core.adaptateurs.meteo import AdaptateurMeteo


# Instances singleton (créées une seule fois)
_sportif: FournisseurDonneesSportives | None = None
_paiement: FournisseurPaiement | None = None
_contenu: FournisseurContenu | None = None
_audio: Any | None = None
_calendrier: FournisseurCalendrier | None = None
_meteo: FournisseurMeteo | None = None


def creer_adaptateur_sportif() -> FournisseurDonneesSportives:
    """Retourne l'instance singleton du fournisseur de données sportives."""
    global _sportif
    if _sportif is None:
        _sportif = AdaptateurApiFootball()
    return _sportif


def creer_adaptateur_paiement() -> FournisseurPaiement:
    """Retourne l'instance singleton du fournisseur de paiement."""
    global _paiement
    if _paiement is None:
        _paiement = AdaptateurPaiementMobileMoney()
    return _paiement


def creer_adaptateur_contenu() -> FournisseurContenu:
    """Retourne l'instance singleton du fournisseur de contenu (réseaux sociaux)."""
    global _contenu
    if _contenu is None:
        _contenu = AdaptateurReseauxSociaux()
    return _contenu


def creer_adaptateur_audio() -> Any:
    """Retourne l'instance singleton du fournisseur audio."""
    global _audio
    if _audio is None:
        _audio = AdaptateurAudio()
    return _audio


def creer_adaptateur_calendrier() -> FournisseurCalendrier:
    """Retourne l'instance singleton du fournisseur de calendrier."""
    global _calendrier
    if _calendrier is None:
        _calendrier = AdaptateurCalendrier()
    return _calendrier


def creer_adaptateur_meteo() -> FournisseurMeteo:
    """Retourne l'instance singleton du fournisseur météo."""
    global _meteo
    if _meteo is None:
        _meteo = AdaptateurMeteo()
    return _meteo


def reinitialiser_instances() -> None:
    """Réinitialise toutes les instances (tests uniquement)."""
    global _sportif, _paiement, _contenu, _audio, _calendrier, _meteo
    _sportif = None
    _paiement = None
    _contenu = None
    _audio = None
    _calendrier = None
    _meteo = None
