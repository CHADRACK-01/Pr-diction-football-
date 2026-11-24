"""Tests des services support, litiges et avoir."""

from core import support_extension as module


def test_statut_ticket_invalide(monkeypatch):
    monkeypatch.setattr(module, "db_execute", lambda *args, **kwargs: 1)
    try:
        module.changer_statut_ticket(1, "inconnu")
        assert False
    except ValueError:
        assert True


def test_avoir_refuse_montant_negatif(monkeypatch):
    monkeypatch.setattr(module, "db_execute", lambda *args, **kwargs: 1)
    try:
        module.crediter_avoir(10, -100)
        assert False
    except ValueError:
        assert True
