"""
Point d'entrée des handlers Telegram.
Enregistre tous les modules dans le bon ordre.
"""

from telegram_bot.admin_handlers import enregistrer_admin_handlers
from telegram_bot.menu_handlers import enregistrer_menu_handlers
from telegram_bot.payment_handlers import enregistrer_payment_handlers
from telegram_bot.prediction_handlers import enregistrer_prediction_handlers
from telegram_bot.premium_handlers import enregistrer_premium_handlers
from telegram_bot.user_handlers import enregistrer_user_handlers


def enregistrer_handlers(bot):
    # Liste ordonnée : Admin en premier (priorité absolue sur les callbacks)
    handlers_modules = [
        ("Admin", enregistrer_admin_handlers),
        ("Paiement", enregistrer_payment_handlers),
        ("Premium", enregistrer_premium_handlers),
        ("Prédiction", enregistrer_prediction_handlers),
        ("User", enregistrer_user_handlers),
        ("Menu", enregistrer_menu_handlers),  # Fallback en dernier
    ]

    for nom, enregistrer in handlers_modules:
        enregistrer(bot)

    noms = " -> ".join([nom for nom, _ in handlers_modules])
    print(f"✅ Handlers enregistrés : {noms}")
