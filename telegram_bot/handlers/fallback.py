import telebot
import config
from users import get_langue, est_banni
from core.translations import get_text
from core.utils.logs import log_info, log_error, log_warning


# Liste des anciens boutons (#PRONO, #MATCHS, etc.) qui pourraient traîner
ANCIENS_BOUTONS = [
    "#PRONO", "#MATCHS", "#COUPONS", "#TOP",
    "#HISTO", "#STATS", "#NOTIFS", "#PREMIUM",
    "#PARRAINAGE", "#LANGUE", "#ADMIN"
]


def enregistrer_fallback_handlers(bot):
    
    # ⚠️ Le fallback ne s'active que si le message n'est pas une commande (/),
    # n'est pas un ancien bouton (#) et n'est pas un nouveau bouton connu
    @bot.message_handler(func=lambda message: (
        message.text 
        and not message.text.startswith('/') 
        and not message.text.startswith('#')
        and message.text not in ["↩️ Retour au Menu", "🌍 Langue", "👑 Panneau Admin"]
    ))
    def handle_menu_fallback(message):
        user_id = message.from_user.id
        
        try:
            langue = get_langue(user_id)
        except Exception as e:
            log_error(f"Impossible de récupérer la langue de {user_id} dans le fallback", "FALLBACK", exception=e)
            langue = "fr"

        try:
            if est_banni(user_id):
                bot.reply_to(message, get_text("banni", langue))
                return
        except Exception as e:
            log_error(f"Impossible de vérifier si {user_id} est banni dans le fallback", "FALLBACK", exception=e)
            return

        # On ignore si l'utilisateur est en session admin (pour ne pas interrompre)
        try:
            from telegram_bot.admin.actions import ADMIN_SESSIONS
            if user_id in ADMIN_SESSIONS:
                return
        except Exception as e:
            log_warning(f"Impossible de vérifier les sessions admin : {e}", "FALLBACK")

        # ⚠️ SI MODE VITRINE, on redirige vers le message de maintenance
        try:
            if config.MODE_VITRINE:
                from telegram_bot.handlers.start import envoyer_menu_principal
                envoyer_menu_principal(message.chat.id, user_id, bot)
                return
        except Exception as e:
            log_error(f"Impossible de rediriger en mode vitrine pour {user_id}", "FALLBACK", exception=e)

        # Log du message inconnu
        log_info(f"[FALLBACK] Message inconnu de {user_id} : '{message.text}'", "FALLBACK")

        # Message de secours
        try:
            bot.reply_to(message, get_text("fallback", langue))
            from telegram_bot.handlers.start import envoyer_menu_principal
            envoyer_menu_principal(message.chat.id, user_id, bot)
        except Exception as e:
            log_error(f"Impossible d'envoyer le menu principal à {user_id} dans le fallback", "FALLBACK", exception=e)

    # ⚠️ Gestion des anciennes clés (#PRONO, #MATCHS...) pour rediriger vers le menu
    @bot.message_handler(func=lambda message: (
        message.text 
        and message.text.startswith('#') 
        and message.text not in ["#LANGUE", "#ADMIN"]
    ))
    def handle_anciens_boutons(message):
        user_id = message.from_user.id
        
        try:
            langue = get_langue(user_id)
        except Exception as e:
            log_error(f"Impossible de récupérer la langue de {user_id}", "FALLBACK", exception=e)
            langue = "fr"

        log_info(f"[FALLBACK] Ancien bouton '{message.text}' utilisé par {user_id}", "FALLBACK")

        try:
            bot.reply_to(message, "🔄 Ce menu a été mis à jour. Voici le nouveau :")
            from telegram_bot.handlers.start import envoyer_menu_principal
            envoyer_menu_principal(message.chat.id, user_id, bot)
        except Exception as e:
            log_error(f"Impossible de rediriger {user_id} vers le nouveau menu", "FALLBACK", exception=e)
