"""Tests des fonctionnalités P0/P1 prioritaires."""

from core.services_prioritaires import demarrer_essai_premium, construire_dashboard_admin


def test_essai_premium_n_est_pas_reattribue(monkeypatch):
    appels = []
    monkeypatch.setattr("core.services_prioritaires.ajouter_jours_premium", lambda uid, jours: appels.append((uid, jours)) or True)
    assert demarrer_essai_premium(7) is True
    assert demarrer_essai_premium(7) is False


def test_dashboard_admin_retourne_des_compteurs(monkeypatch):
    monkeypatch.setattr("core.services_prioritaires.get_stats_globales", lambda: {"total": 10, "premium": 4, "free": 6})
    dashboard = construire_dashboard_admin()
    assert dashboard["utilisateurs"]["total"] == 10
    assert dashboard["utilisateurs"]["premium"] == 4
