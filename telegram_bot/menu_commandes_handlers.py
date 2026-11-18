# telegram_bot/menu_commandes_handlers.py
"""
Clavier admin avec tous les boutons.
Réservé aux administrateurs pour l'instant.
"""

from users import est_administrateur
from core.utils.logs import log_info, log_error
from telegram_bot.handlers.start import envoyer_menu_principal, _creer_clavier_admin


def enregistrer_menu_commandes_handlers(bot):
    from telegram_bot.admin.selection import (
        ADMIN_SELECTIONS,
        COMMANDES_PARAMETREES,
        demarrer_selection,
        traiter_message_selection,
    )

    # =========================================================
    # ROUTAGE DES SÉLECTIONS ADMIN (avant le traitement habituel)
    # =========================================================
    @bot.message_handler(func=lambda m: m.from_user.id in ADMIN_SELECTIONS)
    def handle_admin_selection(message):
        """Route un message vers une sélection admin en cours."""
        return traiter_message_selection(message, bot)

    @bot.message_handler(commands=['menu'])
    def cmd_menu(message):
        """Affiche le clavier admin avec tous les boutons."""
        user_id = message.from_user.id

        if not est_administrateur(user_id):
            bot.reply_to(message, "⛔ Commande réservée aux administrateurs.")
            return

        markup = _creer_clavier_admin()

        bot.reply_to(
            message,
            "🛠️ <b>MENU ADMIN</b>\n\nChoisis une commande :",
            reply_markup=markup,
            parse_mode="HTML"
        )

    @bot.message_handler(func=lambda m: m.text == "↩️ Retour au Menu")
    def retour_menu_admin(message):
        """Retourne au menu principal (réservé aux administrateurs)."""
        user_id = message.from_user.id

        if not est_administrateur(user_id):
            bot.reply_to(message, "⛔ Commande réservée aux administrateurs.")
            return

        envoyer_menu_principal(message.chat.id, user_id, bot)

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

        # Boutons paramétrés : on collecte d'abord le paramètre manquant.
        if text in COMMANDES_PARAMETREES:
            commande, type_param = COMMANDES_PARAMETREES[text]
            demarrer_selection(
                user_id, commande, type_param,
                bot=bot, chat_id=message.chat.id,
            )
            return

        # Mapping bouton -> commande (boutons sans paramètre)
        mapping = {
            "🌍 Langue": "/langue",
            "💎 Devise": "/devise",
            "📊 Fiabilité": "/fiabilite",
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
                fake_message = message
                fake_message.text = commande
                bot.process_new_messages([fake_message])
            except Exception as e:
                log_error(f"Erreur redirection bouton {text}", "MENU", exception=e)
                bot.reply_to(message, f"❌ Erreur lors de l'exécution de {commande}.")
