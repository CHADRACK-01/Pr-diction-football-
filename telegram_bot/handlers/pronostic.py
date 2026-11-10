import telebot
from users import get_langue, est_banni, peut_faire_pronostic, get_limite_jour, est_administrateur
from core.translations import get_text
from config import CHAMPIONNATS, INFOS_COMPETITIONS, MAPPING_COMPETITIONS
from core.session import set_session_competition, clear_session_competition


def creer_clavier_competitions(langue="fr"):
    """Crée le clavier des compétitions avec des boutons propres."""
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    boutons = []
    for code, nom_propre in CHAMPIONNATS.items():
        infos = INFOS_COMPETITIONS.get(nom_propre, {})
        emoji = infos.get("emoji", "🏆")
        # On affiche "🏆 Ligue 1" au lieu de "#PRONO_LIGUE_1"
        boutons.append(telebot.types.KeyboardButton(f"{emoji} {nom_propre}"))
    markup.add(*boutons)
    markup.add(telebot.types.KeyboardButton("↩️ Retour au Menu"))
    return markup


def afficher_menu_competitions(bot, message):
    user_id = message.from_user.id
    langue = get_langue(user_id)

    if est_banni(user_id):
        bot.reply_to(message, get_text("banni", langue))
        return

    if not peut_faire_pronostic(user_id):
        bot.reply_to(message, get_text("limite_atteinte", langue, limite=get_limite_jour(user_id)))
        return

    markup = creer_clavier_competitions(langue)
    bot.reply_to(
        message,
        "⚽ **Choisis la compétition** pour ton pronostic :\n\n👇 Utilise les boutons ci-dessous ou clique sur ↩️ Retour au Menu.",
        reply_markup=markup,
        parse_mode="Markdown"
    )


def enregistrer_pronostic_handlers(bot):

    @bot.message_handler(func=lambda m: m.text == "⚽ Faire un Pronostic")
    def handle_pronostic(message):
        afficher_menu_competitions(bot, message)

    @bot.message_handler(func=lambda m: m.text == "↩️ Retour au Menu")
    def retour_menu(message):
        user_id = message.from_user.id
        clear_session_competition(user_id)
        from telegram_bot.handlers.start import envoyer_menu_principal
        envoyer_menu_principal(message.chat.id, user_id, bot)

    @bot.message_handler(func=lambda m: m.text and any(nom in m.text for nom in CHAMPIONNATS.values()))
    def handle_choix_competition(message):
        user_id = message.from_user.id
        langue = get_langue(user_id)
        texte_bouton = message.text

        # On cherche à quelle compétition correspond le texte du bouton
        comp_code_trouve = None
        nom_propre_trouve = None
        
        for code, nom_propre in CHAMPIONNATS.items():
            # Le texte du bouton est de la forme "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League"
            if nom_propre in texte_bouton:
                comp_code_trouve = code
                nom_propre_trouve = nom_propre
                break

        if not comp_code_trouve:
            return

        # On sauvegarde la compétition dans la BDD
        set_session_competition(user_id, comp_code_trouve)

        # On remet le clavier principal (pour que l'utilisateur puisse taper le match)
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        markup.add(
            telebot.types.KeyboardButton("⚽ Faire un Pronostic"),
            telebot.types.KeyboardButton("📅 Matchs du Jour"),
            telebot.types.KeyboardButton("🎟️ Coupons"),
            telebot.types.KeyboardButton("🏆 Top Affiches"),
            telebot.types.KeyboardButton("📜 Historique"),
            telebot.types.KeyboardButton("📊 Statistiques"),
            telebot.types.KeyboardButton("🔔 Notifications"),
            telebot.types.KeyboardButton("💎 Premium"),
            telebot.types.KeyboardButton("🤝 Parrainage"),
            telebot.types.KeyboardButton("🌍 Langue"),
        )
        if est_administrateur(user_id):
            markup.add(telebot.types.KeyboardButton("👑 Panneau Admin"))
        
        bot.send_message(
            message.chat.id,
            f"⚽ Tu as choisi **{nom_propre_trouve}**.\n\nTape maintenant ton pronostic :\nFormat : `Equipe A vs Equipe B`\nExemple : `Paris SG vs Marseille`",
            reply_markup=markup,
            parse_mode="Markdown"
        )
