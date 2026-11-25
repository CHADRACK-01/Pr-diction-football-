import telebot
from users import get_langue, est_premium, est_banni
from core.translations import get_text
from core.utils.logs import log_info, log_error, log_warning


def enregistrer_premium_menu_handlers(bot):

    @bot.message_handler(func=lambda m: m.text == "💎 Premium")
    def handle_premium(message):
        user_id = message.from_user.id
        log_info(f"Menu Premium demandé par {user_id}", "PREMIUM")

        # 1. Récupérer la langue (avec fallback)
        try:
            langue = get_langue(user_id)
        except Exception as e:
            log_error(f"Impossible de récupérer la langue de {user_id}", "PREMIUM", exception=e)
            langue = "fr"

        # 2. Vérifier si banni
        try:
            if est_banni(user_id):
                bot.reply_to(message, get_text("banni", langue))
                return
        except Exception as e:
            log_error(f"Impossible de vérifier si {user_id} est banni", "PREMIUM", exception=e)
            # Si on ne peut pas vérifier, on refuse par sécurité
            bot.reply_to(message, "❌ Une erreur est survenue. Réessaie dans quelques instants.")
            return

        # 3. Vérifier si déjà Premium
        try:
            is_premium_user = est_premium(user_id)
        except Exception as e:
            log_error(f"Impossible de vérifier si {user_id} est premium", "PREMIUM", exception=e)
            is_premium_user = False  # Par défaut, on affiche le menu

        if is_premium_user:
            bot.reply_to(message, get_text("premium_actif", langue))
            return

        # 4. Afficher le menu des 3 options de paiement
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

        try:
            bot.reply_to(
                message,
                get_text("premium_choix_titre", langue),
                reply_markup=markup
            )
        except Exception as e:
            log_error(f"Impossible d'afficher le menu Premium à {user_id}", "PREMIUM", exception=e)
            # Fallback sans Markdown si l'erreur vient du Markdown
            try:
                bot.reply_to(message, "💎 Choisis ton mode de paiement :", reply_markup=markup)
            except Exception as e2:
                log_error(f"Impossible d'afficher le menu Premium (fallback) à {user_id}", "PREMIUM", exception=e2)
