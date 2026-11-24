"""Compatibilité historique : importez depuis core.scheduling."""

from core.scheduling.scheduler import SchedulerState, cle_intervalle, lancer_scheduler

__all__ = ["SchedulerState", "cle_intervalle", "lancer_scheduler"]
