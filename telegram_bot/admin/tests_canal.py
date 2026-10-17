import telebot
from users import est_administrateur
from core.canal_manager import publier_matchs_sur_canal, publier_coupons_sur_canal
from telegram_bot.admin.menus import menu_test_canal

def enregistrer_tests_handlers(bot):
    @bot.callback_query_handler(func=lambda call: call.data.startswith(("dryrun_", "send_", "admin_test_menu")))
    def handle_test_canal_callbacks(call):
        if not est_administrateur(call.from_user.id):
            bot.answer_callback_query(call.id, "Acces refuse")
            return

        data = call.data
        bot.answer_callback_query(call.id)

        if data == "admin_test_menu":
            bot.edit_message_text(
                "🧪 **TESTS DU CANAL**\n\nChoisis une action :",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=menu_test_canal(),
                parse_mode="Markdown"
            )
            return

        if data == "dryrun_matchs":
            bot.send_message(call.message.chat.id, "⏳ Préparation du message (Dry Run)...")
            publier_matchs_sur_canal(bot, dry_run=True, chat_debug=call.message.chat.id)
        elif data == "dryrun_coupons":
            bot.send_message(call.message.chat.id, "⏳ Préparation du coupon (Dry Run)...")
            publier_coupons_sur_canal(bot, dry_run=True, chat_debug=call.message.chat.id)
        elif data == "send_matchs":
            bot.send_message(call.message.chat.id, "🚀 Envoi réel des matchs sur le canal...")
            publier_matchs_sur_canal(bot, dry_run=False, chat_debug=call.message.chat.id)
        elif data == "send_coupons":
            bot.send_message(call.message.chat.id, "🚀 Envoi réel des coupons sur le canal...")
            publier_coupons_sur_canal(bot, dry_run=False, chat_debug=call.message.chat.id)
