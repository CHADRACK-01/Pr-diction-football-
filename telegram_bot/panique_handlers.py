import telebot
from users.admin import est_administrateur
from core.urgence import activer_panique, desactiver_panique, est_en_panique
from core.utils.logs import log_info, log_warning


def enregistrer_panique_handlers(bot):

    @bot.message_handler(commands=['panique'])
    def cmd_panique(message):
        user_id = message.from_user.id
        try:
            if not est_administrateur(user_id):
                log_warning(message="Tentative d'accès à /panique refusée", module="PANIQUE", user_context={"user_id": user_id})
                bot.reply_to(message, "⛔ Commande réservée aux administrateurs.")
                return

            if not est_en_panique():
                activer_panique()
                log_info("Mode panique activé", "PANIQUE", user_context={"user_id": user_id})
                bot.reply_to(message, "🚨 MODE PANIQUE ACTIVÉ. Le bot est en pause.")
            else:
                desactiver_panique()
                log_info("Mode panique désactivé", "PANIQUE", user_context={"user_id": user_id})
                bot.reply_to(message, "✅ MODE PANIQUE DÉSACTIVÉ. Le bot reprend son activité.")
        except Exception as e:
            log_warning(message=f"Erreur commande /panique pour {user_id}", module="PANIQUE", user_context={"user_id": user_id}, exception=e)
