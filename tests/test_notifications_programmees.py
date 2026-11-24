"""Tests du formatage des notifications planifiées."""

from datetime import datetime, timezone

from core.notifications import formater_conseils_matchs


def test_notification_retourne_aucun_texte_sans_match():
    assert formater_conseils_matchs([]) is None


def test_notification_trie_et_formate_trois_matchs():
    matchs = [
        {"home": "A", "away": "B", "dc_label": "1X", "dc_pct": 0.70},
        {"home": "C", "away": "D", "dc_label": "X2", "dc_pct": 0.80},
        {"home": "E", "away": "F", "dc_label": "X", "dc_pct": 0.75},
        {"home": "G", "away": "H", "dc_label": "1X", "dc_pct": 0.60},
    ]
    texte = formater_conseils_matchs(matchs, datetime(2026, 11, 23, tzinfo=timezone.utc))
    assert "C vs D" in texte
    assert "E vs F" in texte
    assert "A vs B" in texte
    assert "G vs H" not in texte
