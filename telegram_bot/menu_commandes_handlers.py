# telegram_bot/menu_commandes_handlers.py
"""
Menu unique pour l'admin : tous les boutons (anciens + nouveaux).
Réservé aux administrateurs pour l'instant.
"""

import telebot
from users import est_administrateur
from core.utils.logs import log_info, log_error


def enregistrer_menu_commandes_handlers(bot):

    @bot.message_handler(commands=['menu'])
    def cmd_menu(message):
        """Affiche le menu admin avec tous les boutons."""
        user_id = message.from_user.id
        
        if not est_administrateur(user_id):
            bot.reply_to(message, "⛔ Commande réservée aux administrateurs.")
            return
        
        markup = telebot.types.InlineKeyboardMarkup(row_width=2)
        
        # --- Boutons des nouvelles fonctionnalités ---
        boutons = [
            ("🌍 Langue", "/langue"),
            ("💎 Devise", "/devise"),
            ("📊 Fiabilité", "/fiabilite"),
            ("🔍 Comparer", "/comparer"),
            ("⚽ Série", "/serie"),
            ("💰 Cotes", "/cotes"),
            ("📈 Bankroll", "/bankroll"),
            ("💸 Cash-out", "/cashout"),
            ("⚠️ Piège", "/piege"),
            ("🌦️ Météo", "/meteo"),
            ("🎯 Favoris", "/favoris"),
            ("🎟️ Code Promo", "/utilisercode"),
        ]
        
        for label, cmd in boutons:
            markup.add(telebot.types.InlineKeyboardButton(label, callback_data=f"cmd|{cmd}"))

        # --- Boutons admin existants ---
        markup.add(telebot.types.InlineKeyboardButton("📊 Stats Admin", callback_data="cmd|/admin"))
        markup.add(telebot.types.InlineKeyboardButton("🚨 Panique", callback_data="cmd|/panique"))
        markup.add(telebot.types.InlineKeyboardButton("📸 Preuves", callback_data="cmd|/preuves"))
        markup.add(telebot.types.InlineKeyboardButton("🎟️ Codes", callback_data="cmd|/codepromo"))
        markup.add(telebot.types.InlineKeyboardButton("🔧 Features", callback_data="cmd|/features"))
        markup.add(telebot.types.InlineKeyboardButton("💱 Taux", callback_data="cmd|/taux"))

        bot.reply_to(
            message,
            "🛠️ <b>MENU ADMIN</b>\n\nClique sur un bouton pour exécuter la commande :",
            reply_markup=markup,
            parse_mode="HTML"
        )

    @bot.callback_query_handler(func=lambda call: call.data.startswith("cmd|"))
    def traiter_clic_bouton(call):
        """Redirige le clic vers la commande correspondante."""
        commande = call.data.split("|", 1)[1]
        
        try:
            bot.answer_callback_query(call.id, f"Exécution de {commande}...")
            
            # On simule l'envoi de la commande par l'utilisateur
            from telebot.types import Message
            fake_message = call.message
            fake_message.text = commande
            fake_message.from_user = call.from_user
            
            # On traite la commande comme si l'utilisateur l'avait tapée
            bot.process_new_messages([fake_message])
            
        except Exception as e:
            log_error(f"Erreur redirection bouton {commande}", "MENU", exception=e)
            bot.send_message(call.message.chat.id, f"❌ Erreur lors de l'exécution de {commande}.")
