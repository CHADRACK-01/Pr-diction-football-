"""Compatibilité historique : importez depuis core.scheduling.jobs."""

from core.scheduling.jobs import (
    mettre_a_jour_resultats,
    telecharger_matchs,
    nettoyer_matchs_anciens,
)

__all__ = ["mettre_a_jour_resultats", "telecharger_matchs", "nettoyer_matchs_anciens"]
