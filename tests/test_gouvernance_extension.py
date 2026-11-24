"""Tests des concours, tirages transparents et audit local."""

from core import gouvernance_extension as module


def test_tirage_retourne_un_participant(monkeypatch):
    monkeypatch.setattr(module, "db_execute", lambda *args, **kwargs: 1)
    resultat = module.tirer_gagnant(1, [10, 20, 30])
    assert resultat["gagnant_id"] in {10, 20, 30}
    assert len(resultat["empreinte"]) == 64


def test_tirage_refuse_participants_vides(monkeypatch):
    monkeypatch.setattr(module, "db_execute", lambda *args, **kwargs: 1)
    try:
        module.tirer_gagnant(1, [])
        assert False
    except ValueError:
        assert True
