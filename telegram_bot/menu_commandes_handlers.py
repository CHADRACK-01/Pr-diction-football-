# telegram_bot/menu_commandes_handlers.py
"""
Clavier admin avec tous les boutons.
Réservé aux administrateurs pour l'instant.
"""

import telebot
from users import est_administrateur
from core.utils.logs import log_info, log_error


def enregistrer_menu_commandes_handlers(bot):

    @bot.message_handler(commands=['menu'])
    def cmd_menu(message):
        """Affiche le clavier admin avec tous les boutons."""
        user_id = message.from_user.id
        
        if not est_administrateur(user_id):
            bot.reply_to(message, "⛔ Commande réservée aux administrateurs.")
            return
        
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        
        # --- Boutons des nouvelles fonctionnalités ---
        markup.add(
            telebot.types.KeyboardButton("🌍 Langue"),
            telebot.types.KeyboardButton("💎 Devise"),
            telebot.types.KeyboardButton("📊 Fiabilité"),
            telebot.types.KeyboardButton("🔍 Comparer"),
            telebot.types.KeyboardButton("⚽ Série"),
            telebot.types.KeyboardButton("💰 Cotes"),
            telebot.types.KeyboardButton("📈 Bankroll"),
            telebot.types.KeyboardButton("💸 Cash-out"),
            telebot.types.KeyboardButton("⚠️ Piège"),
            telebot.types.KeyboardButton("🌦️ Météo"),
            telebot.types.KeyboardButton("🎯 Favoris"),
            telebot.types.KeyboardButton("🎟️ Code Promo"),
        )
        
        # --- Boutons admin existants ---
        markup.add(
            telebot.types.KeyboardButton("📊 Stats Admin"),
            telebot.types.KeyboardButton("🚨 Panique"),
            telebot.types.KeyboardButton("📸 Preuves"),
            telebot.types.KeyboardButton("🎟️ Codes"),
            telebot.types.KeyboardButton("🔧 Features"),
            telebot.types.KeyboardButton("💱 Taux"),
        )
        
        # --- Bouton retour ---
        markup.add(telebot.types.KeyboardButton("↩️ Retour au Menu"))

        bot.reply_to(
            message,
            "🛠️ <b>MENU ADMIN</b>\n\nChoisis une commande :",
            reply_markup=markup,
            parse_mode="HTML"
        )

    # =========================================================
    # GESTION DES CLICS SUR LES BOUTONS
    # =========================================================
    @bot.message_handler(func=lambda m: m.text in [
        "🌍 Langue", "💎 Devise", "📊 Fiabilité", "🔍 Comparer",
        "⚽ Série", "💰 Cotes", "📈 Bankroll", "💸 Cash-out",
        "⚠️ Piège", "🌦️ Météo", "🎯 Favoris", "🎟️ Code Promo",
        "📊 Stats Admin", "🚨 Panique", "📸 Preuves",
        "🎟️ Codes", "🔧 Features", "💱 Taux"
    ])
    def handle_admin_buttons(message):
        """Traite les clics sur les boutons admin."""
        text = message.text
        user_id = message.from_user.id
        
        if not est_administrateur(user_id):
            bot.reply_to(message, "⛔ Commande réservée aux administrateurs.")
            return
        
        # Mapping bouton -> commande
        mapping = {
            "🌍 Langue": "/langue",
            "💎 Devise": "/devise",
            "📊 Fiabilité": "/fiabilite",
            "🔍 Comparer": "/comparer",
            "⚽ Série": "/serie",
            "💰 Cotes": "/cotes",
            "📈 Bankroll": "/bankroll",
            "💸 Cash-out": "/cashout",
            "⚠️ Piège": "/piege",
            "🌦️ Météo": "/meteo",
            "🎯 Favoris": "/favoris",
            "🎟️ Code Promo": "/utilisercode",
            "📊 Stats Admin": "/admin",
            "🚨 Panique": "/panique",
            "📸 Preuves": "/preuves",
            "🎟️ Codes": "/codepromo",
            "🔧 Features": "/features",
            "💱 Taux": "/taux",
        }
        
        commande = mapping.get(text)
        if commande:
            try:
                from telebot.types import Message
                fake_message = message
                fake_message.text = commande
                bot.process_new_messages([fake_message])
            except Exception as e:
                log_error(f"Erreur redirection bouton {text}", "MENU", exception=e)
                bot.reply_to(message, f"❌ Erreur lors de l'exécution de {commande}.")
