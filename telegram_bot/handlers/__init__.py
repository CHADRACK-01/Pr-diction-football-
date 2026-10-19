"""
Point d'entrée des handlers Telegram.
"""
from telegram_bot.handlers.start import enregistrer_start_handlers
from telegram_bot.admin_handlers import enregistrer_admin_handlers
from telegram_bot.payment_handlers import enregistrer_payment_handlers
from telegram_bot.premium_handlers import enregistrer_premium_handlers
from telegram_bot.prediction_handlers import enregistrer_prediction_handlers
from telegram_bot.handlers.pronostic import enregistrer_pronostic_handlers
from telegram_bot.handlers.premium_menu import enregistrer_premium_menu_handlers
from telegram_bot.handlers.notifications import enregistrer_notifications_handlers
from telegram_bot.handlers.historique import enregistrer_historique_handlers
from telegram_bot.handlers.statistiques import enregistrer_statistiques_handlers
from telegram_bot.handlers.parrainage import enregistrer_parrainage_handlers
from telegram_bot.handlers.fallback import enregistrer_fallback_handlers

def enregistrer_handlers(bot):
    handlers_modules = [
        ("Start", enregistrer_start_handlers),      # ⚠️ TOUJOURS EN PREMIER
        ("Admin", enregistrer_admin_handlers),      # ⚠️ Ensuite
        ("Paiement", enregistrer_payment_handlers),
        ("Premium", enregistrer_premium_handlers),
        ("Prédiction", enregistrer_prediction_handlers),
        ("Pronostic", enregistrer_pronostic_handlers),
        ("Premium Menu", enregistrer_premium_menu_handlers),
        ("Notifs", enregistrer_notifications_handlers),
        ("Historique", enregistrer_historique_handlers),
        ("Stats", enregistrer_statistiques_handlers),
        ("Parrainage", enregistrer_parrainage_handlers),
        ("Fallback", enregistrer_fallback_handlers), # ⚠️ TOUJOURS EN DERNIER
    ]

    for nom, enregistrer in handlers_modules:
        try:
            enregistrer(bot)
            print(f"✅ Module {nom} enregistré.")
        except Exception as e:
            print(f"❌ Erreur d'enregistrement du module {nom} : {e}")
