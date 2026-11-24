"""Tests minimaux d'enregistrement des commandes Telegram locales."""

from telegram_bot.completions_handlers import enregistrer_completions_handlers


class _BotFactice:
    def __init__(self):
        self.commandes = []

    def message_handler(self, commands=None, **kwargs):
        def decorateur(fonction):
            for commande in commands or []:
                self.commandes.append(commande)
            return fonction
        return decorateur


def test_commandes_locales_sont_enregistrees():
    bot = _BotFactice()
    enregistrer_completions_handlers(bot)
    assert "daily" in bot.commandes
    assert "roue" in bot.commandes
    assert "xp" in bot.commandes
    assert "montecarlo" in bot.commandes
    assert "derby" in bot.commandes
    assert "elo" in bot.commandes
    assert "fatigue" in bot.commandes
    assert "antiperte" in bot.commandes
    assert "cashpartiel" in bot.commandes
