"""Tests unitaires des utilitaires du scheduler."""

from datetime import datetime, timezone

from core.scheduling import cle_intervalle


def test_cle_live_est_indexee_par_creneau_de_cinq_minutes():
    now = datetime(2026, 11, 23, 14, 23, tzinfo=timezone.utc)
    assert cle_intervalle(now, "2026-11-23", 5) == "2026-11-23-14-04"


def test_cle_live_change_a_la_tranche_suivante():
    first = datetime(2026, 11, 23, 14, 24, tzinfo=timezone.utc)
    second = datetime(2026, 11, 23, 14, 25, tzinfo=timezone.utc)
    assert cle_intervalle(first, "2026-11-23", 5) != cle_intervalle(second, "2026-11-23", 5)
