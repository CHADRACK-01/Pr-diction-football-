import telebot
from users import est_administrateur
from core.canal_manager import (
    publier_matchs_sur_canal,
    publier_coupons_sur_canal
)


def _menu_test_canal():
    """Menu interne pour les tests du canal."""
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        telebot.types.InlineKeyboardButton("👁️ Dry Run : Matchs du jour", callback_data="dryrun_matchs"),
        telebot.types.InlineKeyboardButton("👁️ Dry Run : Coupons", callback_data="dryrun_coupons"),
        telebot.types.InlineKeyboardButton("🚀 ENVOI RÉEL : Matchs du jour", callback_data="send_matchs"),
        telebot.types.InlineKeyboardButton("🚀 ENVOI RÉEL : Coupons", callback_data="send_coupons"),
        telebot.types.InlineKeyboardButton("🔙 Retour Admin", callback_data="admin_back")
    )
    return markup


def enregistrer_tests_handlers(bot):
    """Enregistre les handlers pour le module de test du canal."""

    @bot.callback_query_handler(func=lambda call: call.data.startswith(("dryrun_", "send_", "admin_test_menu")))
    def handle_test_canal_callbacks(call):
        if not est_administrateur(call.from_user.id):
            bot.answer_callback_query(call.id, "Acces refuse")
            return

        data = call.data
        user_id = call.from_user.id
        bot.answer_callback_query(call.id)

        # Affichage du menu de test
        if data == "admin_test_menu":
            bot.edit_message_text(
                "🧪 **TESTS DU CANAL**\n\nChoisis une action :",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=_menu_test_canal(),
                parse_mode="Markdown"
            )
            return

        # --- Dry Run : Matchs ---
        if data == "dryrun_matchs":
            bot.send_message(call.message.chat.id, "⏳ Préparation du message (Dry Run)...")
            publier_matchs_sur_canal(bot, dry_run=True, chat_debug=call.message.chat.id)
            
        # --- Dry Run : Coupons ---
        elif data == "dryrun_coupons":
            bot.send_message(call.message.chat.id, "⏳ Préparation du coupon (Dry Run)...")
            publier_coupons_sur_canal(bot, dry_run=True, chat_debug=call.message.chat.id)

        # --- Envoi Réel : Matchs ---
        elif data == "send_matchs":
            bot.send_message(call.message.chat.id, "🚀 Envoi réel des matchs sur le canal...")
            publier_matchs_sur_canal(bot, dry_run=False, chat_debug=call.message.chat.id)

        # --- Envoi Réel : Coupons ---
        elif data == "send_coupons":
            bot.send_message(call.message.chat.id, "🚀 Envoi réel des coupons sur le canal...")
            publier_coupons_sur_canal(bot, dry_run=False, chat_debug=call.message.chat.id)
