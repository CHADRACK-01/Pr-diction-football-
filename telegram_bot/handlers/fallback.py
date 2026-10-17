import telebot
from users import get_langue, est_banni
from core.translations import get_text
from telegram_bot.handlers.start import envoyer_menu_principal

def enregistrer_fallback_handlers(bot):
    @bot.message_handler(func=lambda message: not message.text.startswith('/'))
    def handle_menu_fallback(message):
        user_id = message.from_user.id
        langue = get_langue(user_id)

        if est_banni(user_id):
            bot.reply_to(message, get_text("banni", langue))
            return

        # Vérifie si l'utilisateur est en session admin (pour ne pas interrompre)
        from telegram_bot.admin.actions import ADMIN_SESSIONS
        if user_id in ADMIN_SESSIONS:
            return

        # Si c'est un message inconnu, on renvoie le menu
        bot.reply_to(message, get_text("fallback", langue))
        envoyer_menu_principal(message.chat.id, user_id, bot)
