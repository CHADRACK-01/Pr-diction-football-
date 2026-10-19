import telebot
from users import get_langue, est_banni, est_administrateur
from core.translations import get_text
from core.keys import KEYS
from core.utils.logs import log_info, log_error

def enregistrer_router_handler(bot):
    
    @bot.message_handler(func=lambda m: m.text and m.text.startswith('#'))
    def router(message):
        """Routeur central : lit la clé et exécute l'action correspondante."""
        user_id = message.from_user.id
        cle = message.text.strip()
        
        log_info(f"Routeur : clé reçue '{cle}' de {user_id}", "ROUTER")
        
        if est_banni(user_id):
            bot.reply_to(message, "Tu es banni.")
            return

        # =========================================================
        # ROUTAGE DES CLÉS
        # =========================================================
        
        if cle == KEYS["MENU_PRONOSTIC"]:
            from telegram_bot.handlers.pronostic import afficher_menu_competitions
            afficher_menu_competitions(bot, message)
            
        elif cle == KEYS["MENU_MATCHS"]:
            from telegram_bot.premium_handlers import handle_matchs_jour
            handle_matchs_jour(bot, message)
            
        elif cle == KEYS["MENU_COUPONS"]:
            from telegram_bot.premium_handlers import handle_coupons
            handle_coupons(bot, message)
            
        elif cle == KEYS["MENU_TOP"]:
            from telegram_bot.premium_handlers import handle_top_affiches
            handle_top_affiches(bot, message)
            
        elif cle == KEYS["MENU_HISTORIQUE"]:
            from telegram_bot.handlers.historique import handle_historique
            handle_historique(bot, message)
            
        elif cle == KEYS["MENU_STATS"]:
            from telegram_bot.handlers.statistiques import handle_statistiques
            handle_statistiques(bot, message)
            
        elif cle == KEYS["MENU_NOTIFS"]:
            from telegram_bot.handlers.notifications import handle_notifications
            handle_notifications(bot, message)
            
        elif cle == KEYS["MENU_PREMIUM"]:
            from telegram_bot.handlers.premium_menu import handle_premium
            handle_premium(bot, message)
            
        elif cle == KEYS["MENU_PARRAINAGE"]:
            from telegram_bot.handlers.parrainage import handle_parrainage
            handle_parrainage(bot, message)
            
        elif cle == KEYS["MENU_LANGUE"]:
            from telegram_bot.handlers.start import cmd_langue
            cmd_langue(bot, message)
            
        elif cle == KEYS["MENU_ADMIN"]:
            if est_administrateur(user_id):
                from telegram_bot.admin_handlers import cmd_admin
                cmd_admin(bot, message)
            else:
                bot.reply_to(message, "Accès refusé.")
        
        # Ajoute ici les autres clés (Admin, Compétitions, etc.)
        
        else:
            log_info(f"Routeur : clé inconnue '{cle}'", "ROUTER")
            bot.reply_to(message, "⚠️ Commande inconnue. Utilise le menu.")
