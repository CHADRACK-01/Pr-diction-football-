import telebot
from users import get_langue, activer_notifications, desactiver_notifications
from core.translations import get_text
from core.utils.logs import log_info, log_error, log_warning


def enregistrer_notifications_handlers(bot):

    @bot.message_handler(func=lambda m: m.text == "🔔 Notifications")
    def handle_notifications(message):
        user_id = message.from_user.id
        log_info(f"Menu notifications demandé par {user_id}", "NOTIFS")
        
        try:
            langue = get_langue(user_id)
        except Exception as e:
            log_error(f"Impossible de récupérer la langue de {user_id}", "NOTIFS", exception=e)
            langue = "fr"

        markup = telebot.types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            telebot.types.InlineKeyboardButton(
                "✅ Activer",
                callback_data="notif|on"
            ),
            telebot.types.InlineKeyboardButton(
                "❌ Désactiver",
                callback_data="notif|off"
            ),
        )
        
        try:
            bot.reply_to(
                message,
                get_text("notifs_titre", langue),
                reply_markup=markup
            )
        except Exception as e:
            log_error(f"Impossible d'afficher le menu notifications à {user_id}", "NOTIFS", exception=e)

    @bot.message_handler(commands=['notif_on'])
    def cmd_notif_on(message):
        user_id = message.from_user.id
        try:
            langue = get_langue(user_id)
            if activer_notifications(user_id):
                bot.reply_to(message, get_text("notifs_activees", langue))
            else:
                bot.reply_to(message, "❌ Impossible d'activer les notifications. Réessaie.")
        except Exception as e:
            log_error(f"Impossible d'activer les notifications pour {user_id}", "NOTIFS", exception=e)
            bot.reply_to(message, "❌ Erreur lors de l'activation. L'admin a été prévenu.")

    @bot.message_handler(commands=['notif_off'])
    def cmd_notif_off(message):
        user_id = message.from_user.id
        try:
            langue = get_langue(user_id)
            if desactiver_notifications(user_id):
                bot.reply_to(message, get_text("notifs_desactivees", langue))
            else:
                bot.reply_to(message, "❌ Impossible de désactiver les notifications. Réessaie.")
        except Exception as e:
            log_error(f"Impossible de désactiver les notifications pour {user_id}", "NOTIFS", exception=e)
            bot.reply_to(message, "❌ Erreur lors de la désactivation. L'admin a été prévenu.")

    @bot.callback_query_handler(func=lambda call: call.data.startswith("notif|"))
    def traiter_notif_callback(call):
        user_id = call.from_user.id
        action = call.data.split("|")[1]
        
        try:
            langue = get_langue(user_id)
        except Exception as e:
            log_error(f"Impossible de récupérer la langue de {user_id}", "NOTIFS", exception=e)
            langue = "fr"

        try:
            if action == "on":
                if activer_notifications(user_id):
                    bot.answer_callback_query(call.id, "✅ Activé")
                    bot.send_message(call.message.chat.id, get_text("notifs_activees", langue))
                else:
                    bot.answer_callback_query(call.id, "❌ Échec")
            elif action == "off":
                if desactiver_notifications(user_id):
                    bot.answer_callback_query(call.id, "❌ Désactivé")
                    bot.send_message(call.message.chat.id, get_text("notifs_desactivees", langue))
                else:
                    bot.answer_callback_query(call.id, "❌ Échec")
        except Exception as e:
            log_error(f"Erreur callback notifications pour {user_id} (action={action})", "NOTIFS", exception=e)
            try:
                bot.answer_callback_query(call.id, "❌ Erreur")
            except Exception:
                pass
