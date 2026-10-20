import telebot
import config

from users import (
    enregistrer_utilisateur, get_langue, set_langue, est_banni,
    get_user_info, est_administrateur, set_parrain, compter_filleuls,
    ajouter_jours_premium, get_palier_atteint, get_statut_label,
    get_compteur_jour, get_limite_jour
)
from core.translations import get_text, LANGUES_DISPONIBLES
from core.ml_model import global_model_data
from core.utils.logs import log_info

BOT_USERNAME = "MonPronosticFootball_bot"


def envoyer_menu_principal(chat_id, user_id, bot):
    langue = get_langue(user_id)
    user_info = get_user_info(user_id)
    nom = user_info['first_name'] if user_info else "Utilisateur"

    # ⚠️ SI LE MODE VITRINE EST ACTIVÉ
    if config.MODE_VITRINE:
        presentation = (
            f"👋 Bienvenue {nom} sur Pronostic Football !\n\n"
            f"🛠️ **Le bot est actuellement en cours d'amélioration technique.**\n\n"
            f"📢 En attendant, toutes les analyses, pronostics et coupons sont publiés **gratuitement** sur notre canal Telegram.\n\n"
            f"👇 Clique sur le bouton ci-dessous pour rejoindre le canal et ne rien rater :"
        )
        
        # On garde uniquement les boutons essentiels
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
        markup.add(
            telebot.types.KeyboardButton("#LANGUE"),
        )
        
        bot.send_message(chat_id, presentation, reply_markup=markup, parse_mode="Markdown")

        # Bouton pour rejoindre le canal
        inline_markup = telebot.types.InlineKeyboardMarkup(row_width=1)
        inline_markup.add(
            telebot.types.InlineKeyboardButton("📢 REJOINDRE LE CANAL (Pronostics Gratuits)", url=config.CANAL_LIEN)
        )
        bot.send_message(chat_id, "👇 Clique ici pour rejoindre :", reply_markup=inline_markup)
        return

    # ⚠️ SINON (MODE NORMAL - ton code habituel)
    statut_label = get_statut_label(user_id)
    prec = global_model_data.get('precision', 0.5)
    compteur = get_compteur_jour(user_id)
    limite = get_limite_jour(user_id)

    presentation = (
        f"👋 Bienvenue {nom} sur Pronostic Football !\n\n"
        f"🤖 Je suis un bot d'Intelligence Artificielle spécialisé dans les pronostics sportifs.\n\n"
        f"📊 Statut : {statut_label}\n"
        f"🎯 Pronostics aujourd'hui : {compteur}/{limite}\n"
        f"⚙️ Précision du modèle : {prec*100:.2f}%\n\n"
        f"👇 Utilise les boutons ci-dessous pour commencer :"
    )

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

    bot.send_message(chat_id, presentation, reply_markup=markup)

    inline_markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    member = bot.get_chat_member(config.CANAL_ID, user_id)
    is_member = member.status in ['member', 'administrator', 'creator']

    if not is_member:
        inline_markup.add(
            telebot.types.InlineKeyboardButton("📢 Rejoindre notre Canal", url=config.CANAL_LIEN)
        )

    if inline_markup.keyboard:
        bot.send_message(chat_id, "👇 Rejoins notre canal pour ne rien rater :", reply_markup=inline_markup)


def enregistrer_start_handlers(bot):

    @bot.message_handler(commands=['start', 'help'])
    def send_welcome(message):
        user = message.from_user
        if est_banni(user.id):
            bot.reply_to(message, get_text("banni", get_langue(user.id)))
            return

        existe_avant = get_user_info(user.id) is not None
        enregistrer_utilisateur(user.id, user.username, user.first_name)

        if not existe_avant:
            parts = message.text.split()
            if len(parts) >= 2 and parts[1].startswith("REF"):
                parrain_id = int(parts[1].replace("REF", ""))
                if parrain_id != user.id and get_user_info(parrain_id):
                    if set_parrain(user.id, parrain_id):
                        ajouter_jours_premium(user.id, 1)
                        ajouter_jours_premium(parrain_id, 1)

        envoyer_menu_principal(message.chat.id, user.id, bot)

    @bot.message_handler(commands=['langue', 'language'])
    @bot.message_handler(func=lambda m: m.text == "#LANGUE")
    def cmd_langue(message):
        user_id = message.from_user.id
        langue = get_langue(user_id)
        markup = telebot.types.InlineKeyboardMarkup(row_width=1)
        for code, nom in LANGUES_DISPONIBLES.items():
            markup.add(telebot.types.InlineKeyboardButton(nom, callback_data=f"lang|{code}"))
        bot.reply_to(message, get_text("choix_langue", langue), reply_markup=markup)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("lang|"))
    def traiter_langue(call):
        user_id = call.from_user.id
        langue = call.data.split("|")[1]
        if set_langue(user_id, langue):
            bot.answer_callback_query(call.id, "OK")
            bot.send_message(call.message.chat.id, get_text("langue_changee", langue))
            envoyer_menu_principal(call.message.chat.id, user_id, bot)
        else:
            bot.answer_callback_query(call.id, "Erreur")
