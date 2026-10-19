"""
Point d'entrée des handlers Telegram.
Ce fichier orchestre l'enregistrement de tous les modules.
"""

# 1. Le Start en PREMIER (pour /start, /help, /langue)
from telegram_bot.handlers.start import enregistrer_start_handlers

# 2. L'Admin ensuite (pour /admin et le panneau)
from telegram_bot.admin_handlers import enregistrer_admin_handlers

# 3. Les modules de fonctionnalités (clés uniques #)
from telegram_bot.handlers.pronostic import enregistrer_pronostic_handlers
from telegram_bot.premium_handlers import enregistrer_premium_handlers
from telegram_bot.handlers.premium_menu import enregistrer_premium_menu_handlers
from telegram_bot.handlers.notifications import enregistrer_notifications_handlers
from telegram_bot.handlers.historique import enregistrer_historique_handlers
from telegram_bot.handlers.statistiques import enregistrer_statistiques_handlers
from telegram_bot.handlers.parrainage import enregistrer_parrainage_handlers

# 4. Les paiements et prédictions (qui gèrent aussi des textes)
from telegram_bot.payment_handlers import enregistrer_payment_handlers
from telegram_bot.prediction_handlers import enregistrer_prediction_handlers

# 5. Le Fallback en TOUT DERNIER (filet de sécurité)
from telegram_bot.handlers.fallback import enregistrer_fallback_handlers


def enregistrer_handlers(bot):
    handlers_modules = [
        # 1. Les commandes de base
        ("Start", enregistrer_start_handlers),
        
        # 2. L'admin (car il a des boutons spécifiques)
        ("Admin", enregistrer_admin_handlers),
        
        # 3. Les fonctionnalités principales (avec clés uniques)
        ("Pronostic", enregistrer_pronostic_handlers),
        ("Premium", enregistrer_premium_handlers),
        ("Premium Menu", enregistrer_premium_menu_handlers),
        ("Notifs", enregistrer_notifications_handlers),
        ("Historique", enregistrer_historique_handlers),
        ("Stats", enregistrer_statistiques_handlers),
        ("Parrainage", enregistrer_parrainage_handlers),
        
        # 4. Paiements et prédictions
        ("Paiement", enregistrer_payment_handlers),
        ("Prédiction", enregistrer_prediction_handlers),
        
        # 5. Le filet de sécurité (TOUJOURS EN DERNIER)
        ("Fallback", enregistrer_fallback_handlers),
    ]

    for nom, enregistrer in handlers_modules:
        try:
            enregistrer(bot)
            print(f"✅ Module {nom} enregistré.")
        except Exception as e:
            print(f"❌ Erreur d'enregistrement du module {nom} : {e}")

    noms = " -> ".join([nom for nom, _ in handlers_modules])
    print(f"✅ Handlers enregistrés dans l'ordre : {noms}")
