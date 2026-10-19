import telebot
from users import get_langue, est_banni, peut_faire_pronostic, get_limite_jour, est_administrateur
from core.translations import get_text
from config import CHAMPIONNATS, INFOS_COMPETITIONS

# Dictionnaire pour stocker la compétition choisie par l'utilisateur
SESSIONS_PRONOSTIC = {}

def creer_clavier_competitions(langue="fr"):
    """Crée le clavier avec toutes les compétitions disponibles (avec clés uniques)."""
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    
    boutons = []
    for code, nom_propre in CHAMPIONNATS.items():
        infos = INFOS_COMPETITIONS.get(nom_propre, {})
        emoji = infos.get("emoji", "🏆")
        # ⚠️ La clé unique est basée sur le code de la compétition
        boutons.append(telebot.types.KeyboardButton(f"#PRONO_{code.upper()} {emoji} {nom_propre}"))
    
    markup.add(*boutons)
    markup.add(telebot.types.KeyboardButton("🔙 Retour Menu"))
    return markup

def afficher_menu_competitions(bot, message):
    """Affiche le menu des compétitions (appelé par le handler #PRONO)."""
    user_id = message.from_user.id
    langue = get_langue(user_id)

    if est_banni(user_id):
        bot.reply_to(message, get_text("banni", langue))
        return

    if not peut_faire_pronostic(user_id):
        bot.reply_to(
            message,
            get_text("limite_atteinte", langue, limite=get_limite_jour(user_id))
        )
        return

    markup = creer_clavier_competitions(langue)
    
    bot.reply_to(
        message,
        "⚽ **Choisis la compétition** pour ton pronostic :\n\n"
        "👇 Utilise les boutons ci-dessous ou clique sur 🔙 Retour Menu.",
        reply_markup=markup,
        parse_mode="Markdown"
    )

def enregistrer_pronostic_handlers(bot):

    @bot.message_handler(func=lambda m: m.text == "#PRONO")
    def handle_pronostic(message):
        afficher_menu_competitions(bot, message)

    @bot.message_handler(func=lambda m: m.text == "🔙 Retour Menu")
    def retour_menu(message):
        user_id = message.from_user.id
        SESSIONS_PRONOSTIC.pop(user_id, None)
        from telegram_bot.handlers.start import envoyer_menu_principal
        envoyer_menu_principal(message.chat.id, user_id, bot)

    @bot.message_handler(func=lambda m: m.text and m.text.startswith("#PRONO_"))
    def handle_choix_competition(message):
        """Gère le clic sur un bouton de compétition (ex: #PRONO_LIGUE_1)."""
        user_id = message.from_user.id
        langue = get_langue(user_id)
        texte_bouton = message.text

        # On extrait le code de la compétition depuis la clé
        # Ex: "#PRONO_LIGUE_1 🇫🇷 Ligue 1" -> "ligue_1"
        try:
            cle = texte_bouton.split(" ")[0]  # Récupère "#PRONO_LIGUE_1"
            comp_code = cle.replace("#PRONO_", "").lower()
        except Exception:
            return

        # On vérifie que la compétition existe bien
        if comp_code not in CHAMPIONNATS:
            return

        nom_propre = CHAMPIONNATS[comp_code]
        SESSIONS_PRONOSTIC[user_id] = comp_code

        # On remet le clavier principal
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        markup.add(
            telebot.types.KeyboardButton("#PRONO"),
            telebot.types.KeyboardButton("#MATCHS"),
            telebot.types.KeyboardButton("#COUPONS"),
            telebot.types.KeyboardButton("#TOP"),
            telebot.types.KeyboardButton("#HISTO"),
            telebot.types.KeyboardButton("#STATS"),
            telebot.types.KeyboardButton("#NOTIFS"),
            telebot.types.KeyboardButton("#PREMIUM"),
            telebot.types.KeyboardButton("#PARRAINAGE"),
            telebot.types.KeyboardButton("#LANGUE"),
        )
        if est_administrateur(user_id):
            markup.add(telebot.types.KeyboardButton("#ADMIN"))
        
        bot.send_message(
            message.chat.id,
            f"⚽ Tu as choisi **{nom_propre}**.\n\n"
            f"Tape maintenant ton pronostic :\n"
            f"Format : `Equipe A vs Equipe B`\n\n"
            f"Exemples :\n"
            f"• `PSG vs Marseille`\n"
            f"• `Real Madrid vs Barcelona`",
            reply_markup=markup,
            parse_mode="Markdown"
        )
