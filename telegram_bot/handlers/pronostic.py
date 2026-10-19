import telebot
from users import get_langue, est_banni, peut_faire_pronostic, get_limite_jour
from core.translations import get_text
from config import CHAMPIONNATS, INFOS_COMPETITIONS

# Dictionnaire pour stocker la compétition choisie par l'utilisateur
SESSIONS_PRONOSTIC = {}

def creer_clavier_competitions(langue="fr"):
    """Crée le clavier avec toutes les compétitions disponibles."""
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    
    boutons = []
    for code, nom_propre in CHAMPIONNATS.items():
        infos = INFOS_COMPETITIONS.get(nom_propre, {})
        emoji = infos.get("emoji", "🏆")
        boutons.append(telebot.types.KeyboardButton(f"{emoji} {nom_propre}"))
    
    # On ajoute les boutons par 2 par ligne
    markup.add(*boutons)
    
    # On ajoute le bouton Retour à la fin
    markup.add(telebot.types.KeyboardButton("🔙 Retour Menu"))
    return markup

def enregistrer_pronostic_handlers(bot):

    @bot.message_handler(func=lambda m: m.from_user and m.text in [
        "Faire un Pronostic", "Make a Prediction", "Sala Bokano"
    ])
    def handle_pronostic(message):
        print(f"[PRONOSTIC] Bouton cliqué par {message.from_user.id}")
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

        # ⚠️ NOUVEAU : On affiche le clavier des compétitions
        markup = creer_clavier_competitions(langue)
        
        bot.reply_to(
            message,
            "⚽ **Choisis la compétition** pour ton pronostic :\n\n"
            "👇 Utilise les boutons ci-dessous ou clique sur 🔙 Retour Menu.",
            reply_markup=markup,
            parse_mode="Markdown"
        )

    @bot.message_handler(func=lambda m: m.text == "🔙 Retour Menu")
    def retour_menu(message):
        """Gère le retour au menu principal depuis le clavier des compétitions."""
        user_id = message.from_user.id
        # On supprime la session pour que le prochain pronostic redemande une compétition
        SESSIONS_PRONOSTIC.pop(user_id, None)
        
        # On réaffiche le menu principal
        from telegram_bot.handlers.start import envoyer_menu_principal
        envoyer_menu_principal(message.chat.id, user_id, bot)

    @bot.message_handler(func=lambda m: m.text and any(m.text.endswith(nom) for nom in CHAMPIONNATS.values()))
    def handle_choix_competition(message):
        """Gère le clic sur un bouton de compétition."""
        user_id = message.from_user.id
        langue = get_langue(user_id)
        texte_bouton = message.text

        # On retrouve le code de la compétition à partir du texte du bouton
        comp_code = None
        nom_propre = None
        for code, nom in CHAMPIONNATS.items():
            infos = INFOS_COMPETITIONS.get(nom, {})
            emoji = infos.get("emoji", "🏆")
            if texte_bouton == f"{emoji} {nom}":
                comp_code = code
                nom_propre = nom
                break

        if not comp_code:
            return # Ce n'est pas un bouton de compétition

        # On sauvegarde la compétition choisie
        SESSIONS_PRONOSTIC[user_id] = comp_code

        # On remet le clavier principal pour que l'utilisateur puisse taper son match
        from telegram_bot.handlers.start import envoyer_menu_principal
        # On envoie juste un message avec le clavier normal (sans le texte de bienvenue)
        from telegram_bot.handlers.start import get_text
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        markup.add(
            telebot.types.KeyboardButton(get_text("btn_pronostic", langue)),
            telebot.types.KeyboardButton(get_text("btn_matchs_jour", langue)),
            telebot.types.KeyboardButton(get_text("btn_coupons", langue)),
            telebot.types.KeyboardButton(get_text("btn_top_affiches", langue)),
            telebot.types.KeyboardButton(get_text("btn_historique", langue)),
            telebot.types.KeyboardButton(get_text("btn_stats", langue)),
            telebot.types.KeyboardButton(get_text("btn_notifs", langue)),
            telebot.types.KeyboardButton(get_text("btn_premium", langue)),
            telebot.types.KeyboardButton(get_text("btn_parrainage", langue)),
            telebot.types.KeyboardButton(get_text("btn_langue", langue)),
        )
        
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
