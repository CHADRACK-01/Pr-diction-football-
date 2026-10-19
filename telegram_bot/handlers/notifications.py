import telebot
from users import get_langue, activer_notifications, desactiver_notifications
from core.translations import get_text

def enregistrer_notifications_handlers(bot):

    @bot.message_handler(func=lambda m: m.text == "#NOTIFS")
    def handle_notifications(message):
        print(f"[NOTIFS] Bouton cliqué par {message.from_user.id}")
        user_id = message.from_user.id
        langue = get_langue(user_id)

        markup = telebot.types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            telebot.types.InlineKeyboardButton(
                get_text("bouton_activer", langue),
                callback_data="notif|on"
            ),
            telebot.types.InlineKeyboardButton(
                get_text("bouton_desactiver", langue),
                callback_data="notif|off"
            ),
        )
        bot.reply_to(
            message,
            get_text("notifs_titre", langue),
            reply_markup=markup
        )

    @bot.message_handler(commands=['notif_on'])
    def cmd_notif_on(message):
        user_id = message.from_user.id
        langue = get_langue(user_id)
        if activer_notifications(user_id):
            bot.reply_to(message, get_text("notifs_activees", langue))

    @bot.message_handler(commands=['notif_off'])
    def cmd_notif_off(message):
        user_id = message.from_user.id
        langue = get_langue(user_id)
        if desactiver_notifications(user_id):
            bot.reply_to(message, get_text("notifs_desactivees", langue))

    @bot.callback_query_handler(func=lambda call: call.data.startswith("notif|"))
    def traiter_notif_callback(call):
        user_id = call.from_user.id
        langue = get_langue(user_id)
        action = call.data.split("|")[1]

        if action == "on":
            if activer_notifications(user_id):
                bot.answer_callback_query(call.id, "OK")
                bot.send_message(call.message.chat.id, get_text("notifs_activees", langue))
        elif action == "off":
            if desactiver_notifications(user_id):
                bot.answer_callback_query(call.id, "OK")
                bot.send_message(call.message.chat.id, get_text("notifs_desactivees", langue))
