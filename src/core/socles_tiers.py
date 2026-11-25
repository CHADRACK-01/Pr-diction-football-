# core/socles_tiers.py
"""
Shim de compatibilité historique.

Tous les contrats d'adaptateurs tiers vivent désormais dans
``core.adaptateurs.base``.
Ce module ré-exporte les symboles historiques pour ne pas casser les
imports existants.
"""

from core.adaptateurs.base import (  # noqa: F401
    AdaptateurIndisponible,
    FournisseurAudio,
    FournisseurCalendrier,
    FournisseurContenu,
    FournisseurPaiement,
)

__all__ = [
    "AdaptateurIndisponible",
    "FournisseurAudio",
    "FournisseurCalendrier",
    "FournisseurContenu",
    "FournisseurPaiement",
]
