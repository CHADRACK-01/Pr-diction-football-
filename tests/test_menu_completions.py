"""Tests des boutons Telegram des complétions locales."""

from telegram_bot.handlers.start import BOUTONS_MENU, BOUTONS_UTILISATEUR


def test_nouveaux_boutons_sont_presents_dans_le_menu():
    attendus = {
        "🎁 Bonus Quotidien",
        "🎡 Roue",
        "⭐ Mes XP",
        "🎲 Monte Carlo",
        "🔴 Derby",
        "📈 Elo Live",
        "📅 Fatigue",
        "🛡️ Anti-perte",
        "💸 Cash-out Partiel",
    }
    assert attendus.issubset(BOUTONS_MENU)
    assert attendus.issubset(set(BOUTONS_UTILISATEUR))
