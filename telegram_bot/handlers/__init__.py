"""
Point d'entrée des handlers Telegram.
Ce fichier est le "cerveau" qui orchestre tous les modules.
"""

from telegram_bot.admin_handlers import enregistrer_admin_handlers
from telegram_bot.handlers.start import enregistrer_start_handlers
from telegram_bot.handlers.notifications import enregistrer_notifications_handlers
from telegram_bot.handlers.historique import enregistrer_historique_handlers
from telegram_bot.handlers.statistiques import enregistrer_statistiques_handlers
from telegram_bot.handlers.parrainage import enregistrer_parrainage_handlers
from telegram_bot.handlers.pronostic import enregistrer_pronostic_handlers  # ⚠️ NOUVEAU

# Importation des modules existants
from telegram_bot.payment_handlers import enregistrer_payment_handlers
from telegram_bot.premium_handlers import enregistrer_premium_handlers
from telegram_bot.prediction_handlers import enregistrer_prediction_handlers

# ⚠️ Le fallback est importé mais on l'enregistre EN DERNIER
from telegram_bot.handlers.fallback import enregistrer_fallback_handlers


def enregistrer_handlers(bot):
    """
    Enregistre tous les handlers dans un ordre strict.
    L'ordre est CRUCIAL pour éviter les conflits de callbacks.
    """
    handlers_modules = [
        # 1. ADMIN EN PREMIER (Priorité absolue sur les callbacks admin_)
        ("Admin", enregistrer_admin_handlers),
        
        # 2. Paiement (callbacks pay|, buy|)
        ("Paiement", enregistrer_payment_handlers),
        
        # 3. Premium (Coupons et Top affiches)
        ("Premium", enregistrer_premium_handlers),
        
        # 4. Prédiction manuelle (PSG vs Marseille)
        ("Prédiction", enregistrer_prediction_handlers),

        # 5. Le bouton "Faire un Pronostic" qui affiche les instructions
        ("Pronostic", enregistrer_pronostic_handlers),  # ⚠️ NOUVEAU
        
        # 6. Utilisateurs - Start & Langue
        ("Start", enregistrer_start_handlers),
        
        # 7. Utilisateurs - Notifications
        ("Notifs", enregistrer_notifications_handlers),
        
        # 8. Utilisateurs - Historique
        ("Historique", enregistrer_historique_handlers),
        
        # 9. Utilisateurs - Statistiques
        ("Stats", enregistrer_statistiques_handlers),
        
        # 10. Utilisateurs - Parrainage
        ("Parrainage", enregistrer_parrainage_handlers),
        
        # 11. Fallback (EN DERNIER, attrape tout ce qui n'a pas matché)
        ("Fallback", enregistrer_fallback_handlers),
    ]

    for nom, enregistrer in handlers_modules:
        try:
            enregistrer(bot)
        except Exception as e:
            print(f"❌ Erreur d'enregistrement du module {nom} : {e}")

    noms = " -> ".join([nom for nom, _ in handlers_modules])
    print(f"✅ Handlers enregistrés dans l'ordre : {noms}")
