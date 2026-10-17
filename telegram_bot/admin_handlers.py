import telebot
from users import est_administrateur, compter_codes_disponibles

from telegram_bot.admin.menus import (
    menu_principal_admin, menu_premium, menu_codes,
    menu_parametres, menu_bdd
)
from telegram_bot.admin.actions import executer_action, ADMIN_SESSIONS


def enregistrer_admin_handlers(bot):

    # =========================================================
    # COMMANDE /admin (SECOURS)
    # =========================================================
    @bot.message_handler(commands=['admin'])
    def cmd_admin(message):
        if not est_administrateur(message.from_user.id):
            return
        bot.send_message(message.chat.id, "🎛️ PANNEAU ADMIN\n\nChoisis une action :", reply_markup=menu_principal_admin())

    # =========================================================
    # BOUTON TEXTE "Panneau Admin" (depuis le clavier en bas)
    # =========================================================
    @bot.message_handler(func=lambda m: m.text == "Panneau Admin" and est_administrateur(m.from_user.id))
    def handle_panneau_admin_text(message):
        bot.send_message(message.chat.id, "🎛️ PANNEAU ADMIN\n\nChoisis une action :", reply_markup=menu_principal_admin())

    # =========================================================
    # OUVERTURE DU PANNEAU (Bouton Inline)
    # =========================================================
    @bot.callback_query_handler(func=lambda call: call.data == "open_admin_panel")
    def open_admin_panel_callback(call):
        if not est_administrateur(call.from_user.id):
            bot.answer_callback_query(call.id, "Accès refusé")
            return
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "🎛️ PANNEAU ADMIN\n\nChoisis une action :", reply_markup=menu_principal_admin())

    # =========================================================
    # GESTIONNAIRE DES BOUTONS ADMIN
    # =========================================================
    @bot.callback_query_handler(func=lambda call: call.data.startswith(("admin_", "param_", "bcast_")))
    def handle_admin_callbacks(call):
        if not est_administrateur(call.from_user.id):
            bot.answer_callback_query(call.id, "Accès refusé")
            return
            
        data = call.data
        user_id = call.from_user.id
        bot.answer_callback_query(call.id)

        # Navigation
        if data == "admin_back":
            ADMIN_SESSIONS.pop(user_id, None)
            try:
                bot.edit_message_text("🎛️ PANNEAU ADMIN\n\nChoisis une action :", call.message.chat.id, call.message.message_id, reply_markup=menu_principal_admin())
            except Exception:
                bot.send_message(call.message.chat.id, "🎛️ PANNEAU ADMIN", reply_markup=menu_principal_admin())
        elif data == "admin_close":
            ADMIN_SESSIONS.pop(user_id, None)
            try:
                bot.delete_message(call.message.chat.id, call.message.message_id)
            except Exception:
                pass
        elif data == "admin_premium":
            ADMIN_SESSIONS.pop(user_id, None)
            bot.edit_message_text("💎 GESTION PREMIUM", call.message.chat.id, call.message.message_id, reply_markup=menu_premium())
        elif data == "admin_codes":
            ADMIN_SESSIONS.pop(user_id, None)
            dispo = compter_codes_disponibles()
            bot.edit_message_text(f"🎟️ CODES PREMIUM\n\nCodes disponibles : {dispo}", call.message.chat.id, call.message.message_id, reply_markup=menu_codes())
        elif data == "admin_bdd":
            ADMIN_SESSIONS.pop(user_id, None)
            bot.edit_message_text("🗄️ BASE DE DONNÉES", call.message.chat.id, call.message.message_id, reply_markup=menu_bdd())
        elif data == "admin_params":
            ADMIN_SESSIONS.pop(user_id, None)
            bot.edit_message_text("⚙️ PARAMÈTRES", call.message.chat.id, call.message.message_id, reply_markup=menu_parametres())
        else:
            # Délégation au module actions.py
            executer_action(bot, call, data, user_id)

    # =========================================================
    # COMMANDE /annuler
    # =========================================================
    @bot.message_handler(commands=['annuler'])
    def cmd_annuler(message):
        if not est_administrateur(message.from_user.id): 
            return
        ADMIN_SESSIONS.pop(message.from_user.id, None)
        bot.reply_to(message, "Action annulée.")
