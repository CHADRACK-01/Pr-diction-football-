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
            from telegram_bot.premium_handlers import enregistrer_premium_handlers
            # On ne peut pas appeler directement, on déclenche le handler correspondant
            bot.process_new_messages([message])
            
        elif cle == KEYS["MENU_COUPONS"]:
            bot.process_new_messages([message])
            
        elif cle == KEYS["MENU_TOP"]:
            bot.process_new_messages([message])
            
        elif cle == KEYS["MENU_HISTORIQUE"]:
            bot.process_new_messages([message])
            
        elif cle == KEYS["MENU_STATS"]:
            bot.process_new_messages([message])
            
        elif cle == KEYS["MENU_NOTIFS"]:
            bot.process_new_messages([message])
            
        elif cle == KEYS["MENU_PREMIUM"]:
            bot.process_new_messages([message])
            
        elif cle == KEYS["MENU_PARRAINAGE"]:
            bot.process_new_messages([message])
            
        elif cle == KEYS["MENU_LANGUE"]:
            from telegram_bot.handlers.start import cmd_langue
            cmd_langue(bot, message)
            
        elif cle == KEYS["MENU_ADMIN"]:
            if est_administrateur(user_id):
                from telegram_bot.admin_handlers import cmd_admin
                cmd_admin(bot, message)
            else:
                bot.reply_to(message, "Accès refusé.")
        
        else:
            log_info(f"Routeur : clé inconnue '{cle}'", "ROUTER")
            bot.reply_to(message, "⚠️ Commande inconnue. Utilise le menu.")
