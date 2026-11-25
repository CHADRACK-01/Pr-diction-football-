# core/adaptateurs/__init__.py
"""
Package d'adaptateurs tiers pour le bot de pronostics football.

Tous les adaptateurs héritent des classes de base définies dans
``core.adaptateurs.base`` et retournent un résultat typé :
``(succes: bool, donnees: Any, erreur: str | None)``.

Aucune opération externe n'est simulée comme réussie : si un adaptateur
n'est pas configuré (clé API manquante), il retourne
``(False, None, "Adaptateur non configuré")``.

L'utilisateur final ne doit modifier que ``core/config_adaptateurs.py``
pour activer ses clés API (2-3 lignes maximum).
"""

from core.adaptateurs.base import (
    FournisseurDonneesSportives,
    FournisseurPaiement,
    FournisseurContenu,
    FournisseurAudio,
    FournisseurCalendrier,
    FournisseurMeteo,
    ResultatAdaptateur,
    AdaptateurIndisponible,
)
from core.adaptateurs.factory import creer_adaptateur_sportif, creer_adaptateur_paiement
from core.adaptateurs.api_football import AdaptateurApiFootball
from core.adaptateurs.paiements import AdaptateurPaiementMobileMoney
from core.adaptateurs.reseaux_sociaux import AdaptateurReseauxSociaux
from core.adaptateurs.audio import AdaptateurAudio
from core.adaptateurs.calendrier import AdaptateurCalendrier
from core.adaptateurs.meteo import AdaptateurMeteo

__all__ = [
    "FournisseurDonneesSportives",
    "FournisseurPaiement",
    "FournisseurContenu",
    "FournisseurAudio",
    "FournisseurCalendrier",
    "FournisseurMeteo",
    "ResultatAdaptateur",
    "AdaptateurIndisponible",
    "creer_adaptateur_sportif",
    "creer_adaptateur_paiement",
    "AdaptateurApiFootball",
    "AdaptateurPaiementMobileMoney",
    "AdaptateurReseauxSociaux",
    "AdaptateurAudio",
    "AdaptateurCalendrier",
    "AdaptateurMeteo",
]
