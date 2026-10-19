import telebot
from users import get_langue, est_premium, est_banni
from core.translations import get_text


def enregistrer_premium_menu_handlers(bot):

    @bot.message_handler(func=lambda m: m.text == "#PREMIUM")
    def handle_premium(message):
        print(f"[PREMIUM MENU] Bouton cliqué par {message.from_user.id}")
        user_id = message.from_user.id
        langue = get_langue(user_id)

        if est_banni(user_id):
            bot.reply_to(message, get_text("banni", langue))
            return

        if est_premium(user_id):
            bot.reply_to(message, get_text("premium_actif", langue))
            return

        # 3 choix de paiement
        markup = telebot.types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            telebot.types.InlineKeyboardButton(
                get_text("btn_pay_stars", langue),
                callback_data="pay|stars"
            ),
            telebot.types.InlineKeyboardButton(
                get_text("btn_pay_mobile", langue),
                callback_data="pay|mobile"
            ),
            telebot.types.InlineKeyboardButton(
                get_text("btn_pay_code", langue),
                callback_data="pay|code"
            ),
        )

        bot.reply_to(
            message,
            get_text("premium_choix_titre", langue),
            reply_markup=markup
        )
