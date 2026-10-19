import telebot
from users import est_administrateur, compter_codes_disponibles

from telegram_bot.admin.menus import (
    menu_principal_admin, menu_premium, menu_codes,
    menu_parametres, menu_bdd,
    menu_admin_bas, menu_premium_bas, menu_codes_bas,
    menu_parametres_bas, menu_bdd_bas
)
from telegram_bot.admin.actions import executer_action, executer_action_bas, ADMIN_SESSIONS


def enregistrer_admin_handlers(bot):

    # =========================================================
    # OUVERTURE DU PANNEAU (Clé #ADMIN et commande /admin)
    # =========================================================
    @bot.message_handler(commands=['admin'])
    @bot.message_handler(func=lambda m: m.text == "#ADMIN" and est_administrateur(m.from_user.id))
    def cmd_admin(message):
        if not est_administrateur(message.from_user.id):
            bot.reply_to(message, "Accès refusé.")
            return
        bot.send_message(
            message.chat.id, 
            "🎛️ PANNEAU ADMIN\n\nChoisis une action :", 
            reply_markup=menu_admin_bas()
        )

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
    # GESTIONNAIRE DES BOUTONS INLINE
    # =========================================================
    @bot.callback_query_handler(func=lambda call: call.data.startswith(("admin_", "param_", "bcast_")))
    def handle_admin_callbacks(call):
        if not est_administrateur(call.from_user.id):
            bot.answer_callback_query(call.id, "Accès refusé")
            return
            
        data = call.data
        user_id = call.from_user.id
        bot.answer_callback_query(call.id)

        if data == "admin_back":
            ADMIN_SESSIONS.pop(user_id, None)
            bot.edit_message_text("🎛️ PANNEAU ADMIN\n\nChoisis une action :", call.message.chat.id, call.message.message_id, reply_markup=menu_principal_admin())
        elif data == "admin_close":
            ADMIN_SESSIONS.pop(user_id, None)
            bot.delete_message(call.message.chat.id, call.message.message_id)
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
            executer_action(bot, call, data, user_id)

    # =========================================================
    # GESTIONNAIRE DES BOUTONS DU CLAVIER ADMIN (Texte)
    # =========================================================
    @bot.message_handler(func=lambda m: est_administrateur(m.from_user.id) and m.text in [
        "📊 Stats", "👥 Utilisateurs", "💳 Paiements", "🎟️ Codes Premium",
        "🗄️ Base de données", "👑 Admins", "⚙️ Paramètres", "📝 Logs",
        "🚫 Bannis", "📢 Broadcast", "💎 Premium", "🔙 Quitter Admin",
        "🔍 Lancer l'Audit",
        "➕ Ajouter Premium", "➖ Retirer Premium", "🔙 Retour Admin",
        "Gen 10 jours", "Gen 30 jours", "Gen 90 jours", "Gen custom", "👁️ Voir codes dispo",
        "Heure notifs", "Limite Free", "Prix Stars", "Message accueil", "Mode maintenance", "👁️ Voir parametres",
        "Taille BDD", "Detail tables", "🧹 Nettoyer"
    ])
    def handle_admin_buttons_text(message):
        text = message.text
        user_id = message.from_user.id

        # --- Quitter Admin ---
        if text == "🔙 Quitter Admin":
            from telegram_bot.handlers.start import envoyer_menu_principal
            envoyer_menu_principal(message.chat.id, user_id, bot)
            return

        # --- Retour Admin ---
        if text == "🔙 Retour Admin":
            bot.send_message(message.chat.id, "🎛️ PANNEAU ADMIN", reply_markup=menu_admin_bas())
            return

        # --- Audit (SÉCURISÉ) ---
        if text == "🔍 Lancer l'Audit":
            bot.send_message(message.chat.id, "⏳ Lancement de l'audit en arrière-plan... Regarde les logs Render.")
            
            import threading
            def run_audit():
                from core.audit import lancer_audit_complet
                lancer_audit_complet()
                bot.send_message(message.chat.id, "✅ Audit terminé ! Regarde les logs Render pour les détails.")
                    
            threading.Thread(target=run_audit, daemon=True).start()
            return

        # --- Navigation vers les sous-menus (Bascule de clavier) ---
        if text == "⚙️ Paramètres":
            bot.send_message(message.chat.id, "⚙️ PARAMÈTRES", reply_markup=menu_parametres_bas())
            return
        if text == "🎟️ Codes Premium":
            dispo = compter_codes_disponibles()
            bot.send_message(message.chat.id, f"🎟️ CODES PREMIUM (Dispo : {dispo})", reply_markup=menu_codes_bas())
            return
        if text == "🗄️ Base de données":
            bot.send_message(message.chat.id, "🗄️ BASE DE DONNÉES", reply_markup=menu_bdd_bas())
            return
        if text == "💎 Premium":
            bot.send_message(message.chat.id, "💎 GESTION PREMIUM", reply_markup=menu_premium_bas())
            return

        # --- Exécution des actions ---
        executer_action_bas(bot, message, text, user_id)

    # =========================================================
    # COMMANDE /annuler
    # =========================================================
    @bot.message_handler(commands=['annuler'])
    def cmd_annuler(message):
        if not est_administrateur(message.from_user.id): 
            return
        ADMIN_SESSIONS.pop(message.from_user.id, None)
        bot.reply_to(message, "Action annulée.")
