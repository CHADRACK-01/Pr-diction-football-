"""Tests du menu Telegram du catalogue complet."""

from telegram_bot.completions_handlers import creer_menu_catalogue, creer_menu_groupe


class _BoutonsFake:
    pass


def test_creation_du_menu_catalogue_sans_exception():
    markup = creer_menu_catalogue()
    assert markup is not None


def test_creation_d_un_groupe_avec_statuts():
    markup = creer_menu_groupe("Paris", page=0)
    assert markup is not None
