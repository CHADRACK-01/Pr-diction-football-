"""
Point d'entrée des handlers Telegram.
Enregistre tous les modules dans le bon ordre.
"""

# ⚠️ L'ADMIN DOIT ÊTRE EN PREMIER
from telegram_bot.admin_handlers import enregistrer_admin_handlers
from telegram_bot.menu_handlers import enregistrer_menu_handlers
from telegram_bot.payment_handlers import enregistrer_payment_handlers
from telegram_bot.prediction_handlers import enregistrer_prediction_handlers
from telegram_bot.premium_handlers import enregistrer_premium_handlers
from telegram_bot.user_handlers import enregistrer_user_handlers


def enregistrer_handlers(bot):
    # Liste ordonnée des modules de handlers (du plus restrictif/prioritaire au fallback)
    handlers_modules = [
        ("Admin", enregistrer_admin_handlers),
        ("Paiement", enregistrer_payment_handlers),
        ("Premium", enregistrer_premium_handlers),
        ("Prédiction", enregistrer_prediction_handlers),
        ("User", enregistrer_user_handlers),
        ("Menu", enregistrer_menu_handlers),  # Fallback en dernier
    ]

    # Enregistrement séquentiel
    for nom, enregistrer in handlers_modules:
        enregistrer(bot)

    # Construction dynamique du message de log
    noms = " -> ".join([nom for nom, _ in handlers_modules])
    print(f"✅ Handlers enregistrés : {noms}")
