"""Tests de validation des registres sportifs locaux."""

from core import registre_sportif


def test_enregistrement_blessure_fake_db(monkeypatch):
    monkeypatch.setattr(registre_sportif, "db_execute", lambda *args, **kwargs: 1)
    assert registre_sportif.enregistrer_blessure("A", "Mazembe", "Genou", "blesse", "source-test") == {
        "joueur": "A", "equipe": "Mazembe", "statut": "blesse"
    }
