import telebot
import config
from users import get_langue, est_banni
from core.translations import get_text
from telegram_bot.handlers.start import envoyer_menu_principal


def enregistrer_fallback_handlers(bot):
    
    @bot.message_handler(func=lambda message: not message.text.startswith('/') and not message.text.startswith('#'))
    def handle_menu_fallback(message):
        user_id = message.from_user.id
        langue = get_langue(user_id)

        if est_banni(user_id):
            bot.reply_to(message, get_text("banni", langue))
            return

        if message.text == "🔙 Retour Menu":
            return

        from telegram_bot.admin.actions import ADMIN_SESSIONS
        if user_id in ADMIN_SESSIONS:
            return

        # ⚠️ SI MODE VITRINE, on redirige vers le message de maintenance
        if config.MODE_VITRINE:
            envoyer_menu_principal(message.chat.id, user_id, bot)
            return

        print(f"[FALLBACK] Message inconnu : {message.text}")
        bot.reply_to(message, get_text("fallback", langue))
        envoyer_menu_principal(message.chat.id, user_id, bot)


    # ⚠️ NOUVEAU : Gestion des anciennes clés # en mode vitrine
    @bot.message_handler(func=lambda message: message.text and message.text.startswith('#') and message.text != "#LANGUE" and message.text != "#ADMIN")
    def handle_vitrine_keys(message):
        if config.MODE_VITRINE:
            envoyer_menu_principal(message.chat.id, message.from_user.id, bot)
