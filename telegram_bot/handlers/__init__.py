"""
Point d'entrée des handlers Telegram.
Ce fichier est le "cerveau" qui orchestre tous les modules.
"""

# =========================================================
# 1. IMPORTS
# =========================================================
# ⚠️ Le Start DOIT être importé et enregistré en premier
from telegram_bot.handlers.start import enregistrer_start_handlers

# L'Admin ensuite
from telegram_bot.admin_handlers import enregistrer_admin_handlers

# Les autres modules
from telegram_bot.payment_handlers import enregistrer_payment_handlers
from telegram_bot.premium_handlers import enregistrer_premium_handlers
from telegram_bot.prediction_handlers import enregistrer_prediction_handlers
from telegram_bot.handlers.pronostic import enregistrer_pronostic_handlers
from telegram_bot.handlers.premium_menu import enregistrer_premium_menu_handlers
from telegram_bot.handlers.notifications import enregistrer_notifications_handlers
from telegram_bot.handlers.historique import enregistrer_historique_handlers
from telegram_bot.handlers.statistiques import enregistrer_statistiques_handlers
from telegram_bot.handlers.parrainage import enregistrer_parrainage_handlers

# ⚠️ Le Fallback DOIT être importé et enregistré en TOUT DERNIER
from telegram_bot.handlers.fallback import enregistrer_fallback_handlers


def enregistrer_handlers(bot):
    """
    Enregistre tous les handlers dans le bon ordre.
    L'ordre est CRUCIAL pour que les commandes (comme /start) 
    ne soient pas bloquées par d'autres handlers.
    """
    handlers_modules = [
        # 1. Le Start en PREMIER (pour /start, /help, /langue)
        ("Start", enregistrer_start_handlers),
        
        # 2. L'Admin ensuite (pour /admin et les boutons du panneau)
        ("Admin", enregistrer_admin_handlers),
        
        # 3. Les autres modules utilisateurs
        ("Paiement", enregistrer_payment_handlers),
        ("Premium", enregistrer_premium_handlers),
        ("Prédiction", enregistrer_prediction_handlers),
        ("Pronostic", enregistrer_pronostic_handlers),
        ("Premium Menu", enregistrer_premium_menu_handlers),
        ("Notifs", enregistrer_notifications_handlers),
        ("Historique", enregistrer_historique_handlers),
        ("Stats", enregistrer_statistiques_handlers),
        ("Parrainage", enregistrer_parrainage_handlers),
        
        # 4. Le Fallback en TOUT DERNIER (filet de sécurité)
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
