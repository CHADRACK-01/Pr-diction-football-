# tests/test_menu_admin_selection.py
"""Tests des sous-claviers de sélection des boutons admin paramétrés."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from config import CHAMPIONNATS
from telegram_bot.admin import selection
from telegram_bot.admin.menus import menu_admin_bas


COMPETITION = next(iter(CHAMPIONNATS.values()))


class _FakeUser:
    def __init__(self, user_id):
        self.id = user_id


class _FakeChat:
    def __init__(self, chat_id):
        self.id = chat_id


class _FakeMessage:
    def __init__(self, user_id, text, chat_id=None):
        self.from_user = _FakeUser(user_id)
        self.chat = _FakeChat(chat_id if chat_id is not None else user_id)
        self.text = text


class _FakeBot:
    """Bot minimal qui enregistre les messages émis."""

    def __init__(self):
        self.messages = []
        self.replies = []
        self.processed = []

    def send_message(self, chat_id, text, **kwargs):
        self.messages.append((chat_id, text, kwargs))

    def reply_to(self, message, text, **kwargs):
        self.replies.append((message, text, kwargs))

    def process_new_messages(self, messages):
        self.processed.append(list(messages))


def _textes(markup):
    textes = []
    for ligne in markup.keyboard:
        for bouton in ligne:
            if isinstance(bouton, dict):
                textes.append(bouton.get("text"))
            else:
                textes.append(bouton.text)
    return textes


@pytest.fixture(autouse=True)
def _silence_logs(monkeypatch):
    monkeypatch.setattr(selection, "log_info", lambda *a, **k: None, raising=False)
    monkeypatch.setattr(selection, "log_error", lambda *a, **k: None, raising=False)


@pytest.fixture(autouse=True)
def _nettoyer_etat():
    selection.ADMIN_SELECTIONS.clear()
    yield
    selection.ADMIN_SELECTIONS.clear()


@pytest.fixture
def bot():
    return _FakeBot()


@pytest.fixture
def equipes(monkeypatch):
    valeurs = ["PSG", "OM", "Lyon"]
    monkeypatch.setattr(selection, "get_equipes_saison_en_cours", lambda comp: list(valeurs))
    return valeurs


def _derouler(bot, bouton, choix_equipes=(), texte=None):
    commande, type_param = selection.COMMANDES_PARAMETREES[bouton]
    selection.demarrer_selection(7, commande, type_param, bot=bot, chat_id=70)
    if type_param != "texte":
        selection.traiter_message_selection(_FakeMessage(7, f"🏆 {COMPETITION}"), bot)
    for equipe in choix_equipes:
        selection.traiter_message_selection(_FakeMessage(7, equipe), bot)
    if texte is not None:
        selection.traiter_message_selection(_FakeMessage(7, texte), bot)
    if not bot.processed:
        return None
    return bot.processed[-1][0].text


def test_mapping_bouton_vers_type_parametre():
    assert selection.COMMANDES_PARAMETREES == {
        "🔍 Comparer": ("/comparer", "equipe"),
        "⚽ Série": ("/serie", "equipe"),
        "💰 Cotes": ("/cotes", "equipe"),
        "🎯 Favoris": ("/favoris", "equipe"),
        "🌦️ Météo": ("/meteo", "deux_equipes"),
        "⚠️ Piège": ("/piege", "deux_equipes"),
        "💸 Cash-out": ("/cashout", "cashout"),
        "📈 Bankroll": ("/bankroll", "texte"),
        "🎟️ Code Promo": ("/utilisercode", "texte"),
    }


def test_demarrer_selection_affiche_les_competitions(bot):
    markup = selection.demarrer_selection(7, "/comparer", "equipe", bot=bot, chat_id=70)
    etat = selection.ADMIN_SELECTIONS[7]
    assert etat["commande"] == "/comparer"
    assert etat["type_param"] == "equipe"
    assert etat["etape"] == "competition"
    assert selection.BOUTON_ANNULER in _textes(markup)
    assert bot.messages


def test_succession_competition_puis_equipes(bot, equipes):
    selection.demarrer_selection(7, "/comparer", "equipe", bot=bot, chat_id=70)
    etat = selection.ADMIN_SELECTIONS[7]
    assert etat["etape"] == "competition"

    resultat = selection.traiter_message_selection(_FakeMessage(7, f"🏆 {COMPETITION}"), bot)
    assert resultat is True
    assert etat["etape"] == "equipes"
    assert etat["equipes"] == equipes
    assert "PSG" in _textes(bot.messages[-1][2]["reply_markup"])


@pytest.mark.parametrize("bouton,choix,texte,attendu", [
    ("🔍 Comparer", ["PSG"], None, "/comparer PSG"),
    ("⚽ Série", ["PSG"], None, "/serie PSG"),
    ("💰 Cotes", ["PSG"], None, "/cotes PSG"),
    ("🎯 Favoris", ["PSG"], None, "/favoris ajouter PSG"),
    ("🌦️ Météo", ["PSG", "OM"], None, "/meteo PSG vs OM"),
    ("⚠️ Piège", ["PSG", "OM"], None, "/piege PSG vs OM"),
    ("💸 Cash-out", ["PSG", "OM"], "10 2.5", "/cashout PSG vs OM 10 2.5"),
    ("📈 Bankroll", [], "250", "/bankroll 250"),
    ("🎟️ Code Promo", [], "PROMO2024", "/utilisercode PROMO2024"),
])
def test_commandes_des_neuf_boutons(bouton, choix, texte, attendu, bot, equipes):
    assert _derouler(bot, bouton, choix, texte) == attendu


def test_etat_purge_apres_execution(bot, equipes):
    _derouler(bot, "🔍 Comparer", ["PSG"])
    assert 7 not in selection.ADMIN_SELECTIONS


def test_deux_equipes_redemande_la_seconde(bot, equipes):
    selection.demarrer_selection(7, "/meteo", "deux_equipes", bot=bot, chat_id=70)
    selection.traiter_message_selection(_FakeMessage(7, f"🏆 {COMPETITION}"), bot)
    selection.traiter_message_selection(_FakeMessage(7, "PSG"), bot)

    assert selection.ADMIN_SELECTIONS[7]["params"] == ["PSG"]
    assert not bot.processed
    assert "OM" in _textes(bot.messages[-1][2]["reply_markup"])


def test_cashout_passe_en_attente_texte(bot, equipes):
    selection.demarrer_selection(7, "/cashout", "cashout", bot=bot, chat_id=70)
    selection.traiter_message_selection(_FakeMessage(7, f"🏆 {COMPETITION}"), bot)
    selection.traiter_message_selection(_FakeMessage(7, "PSG"), bot)
    selection.traiter_message_selection(_FakeMessage(7, "OM"), bot)

    assert selection.ADMIN_SELECTIONS[7]["etape"] == "attente_texte"
    assert not bot.processed

    selection.traiter_message_selection(_FakeMessage(7, "10 2.5"), bot)
    assert bot.processed[-1][0].text == "/cashout PSG vs OM 10 2.5"


def test_code_promo_demarre_en_attente_texte(bot):
    selection.demarrer_selection(7, "/utilisercode", "texte", bot=bot, chat_id=70)
    assert selection.ADMIN_SELECTIONS[7]["etape"] == "attente_texte"

    selection.traiter_message_selection(_FakeMessage(7, "PROMO2024"), bot)
    assert bot.processed[-1][0].text == "/utilisercode PROMO2024"


def test_annuler_purge_et_renvoie_menu_admin(bot, equipes):
    selection.demarrer_selection(7, "/comparer", "equipe", bot=bot, chat_id=70)
    resultat = selection.traiter_message_selection(
        _FakeMessage(7, selection.BOUTON_ANNULER), bot
    )

    assert resultat is True
    assert 7 not in selection.ADMIN_SELECTIONS
    markup = bot.messages[-1][2]["reply_markup"]
    assert "🔍 Comparer" in _textes(markup)


def test_retour_menu_purge_etat(bot, equipes):
    selection.demarrer_selection(7, "/comparer", "equipe", bot=bot, chat_id=70)
    resultat = selection.traiter_message_selection(_FakeMessage(7, "↩️ Retour au Menu"), bot)
    assert resultat is True
    assert 7 not in selection.ADMIN_SELECTIONS


def test_message_hors_selection_non_consomme(bot):
    assert selection.traiter_message_selection(_FakeMessage(99, f"🏆 {COMPETITION}"), bot) is None
    assert not bot.messages


def test_menu_admin_bas_contient_les_boutons_parametres():
    textes = _textes(menu_admin_bas())
    for bouton in selection.COMMANDES_PARAMETREES:
        assert bouton in textes
    # Les boutons initiaux restent présents.
    assert "📊 Stats" in textes
    assert "🔙 Quitter Admin" in textes


def test_clavier_utilisateur_ajoute_panneau_admin(monkeypatch):
    from telegram_bot.handlers import start

    monkeypatch.setattr(start, "est_administrateur", lambda user_id: True)
    markup = start._creer_clavier_utilisateur(42)
    assert "👑 Panneau Admin" in _textes(markup)

    monkeypatch.setattr(start, "est_administrateur", lambda user_id: False)
    markup = start._creer_clavier_utilisateur(42)
    assert "👑 Panneau Admin" not in _textes(markup)
