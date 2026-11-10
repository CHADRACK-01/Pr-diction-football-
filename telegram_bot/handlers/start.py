import telebot
import config

from users import (
    enregistrer_utilisateur, get_langue, set_langue, est_banni,
    get_user_info, est_administrateur, set_parrain,
    ajouter_jours_premium, get_statut_label,
    get_compteur_jour, get_limite_jour
)
from core.translations import get_text, LANGUES_DISPONIBLES
from core.utils.logs import log_info, log_error, log_warning

BOT_USERNAME = "MonPronosticFootball_bot"


def envoyer_menu_principal(chat_id, user_id, bot):
    """Affiche le menu principal (mode normal ou mode vitrine)."""
    try:
        langue = get_langue(user_id)
        user_info = get_user_info(user_id)
        nom = user_info['first_name'] if user_info else "Utilisateur"
    except Exception as e:
        log_error(f"Impossible de récupérer les infos de l'utilisateur {user_id}", "START", exception=e)
        nom = "Utilisateur"

    # ⚠️ SI LE MODE VITRINE EST ACTIVÉ
    if config.MODE_VITRINE:
        presentation = (
            f"👋 Bienvenue {nom} sur Pronostic Football !\n\n"
            f"🛠️ **Le bot est actuellement en cours d'amélioration technique.**\n\n"
            f"📢 En attendant, toutes les analyses, pronostics et coupons sont publiés **gratuitement** sur notre canal Telegram.\n\n"
            f"👇 Clique sur le bouton ci-dessous pour rejoindre le canal et ne rien rater :"
        )
        
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
        markup.add(telebot.types.KeyboardButton("🌍 Langue"))
        
        bot.send_message(chat_id, presentation, reply_markup=markup, parse_mode="Markdown")

        inline_markup = telebot.types.InlineKeyboardMarkup(row_width=1)
        inline_markup.add(
            telebot.types.InlineKeyboardButton("📢 REJOINDRE LE CANAL (Pronostics Gratuits)", url=config.CANAL_LIEN)
        )
        bot.send_message(chat_id, "👇 Clique ici pour rejoindre :", reply_markup=inline_markup)
        return

    # ⚠️ MODE NORMAL
    try:
        statut_label = get_statut_label(user_id)
        compteur = get_compteur_jour(user_id)
        limite = get_limite_jour(user_id)
    except Exception as e:
        log_error(f"Impossible de récupérer le statut de l'utilisateur {user_id}", "START", exception=e)
        statut_label, compteur, limite = "FREE", 0, 3

    presentation = (
        f"👋 Bienvenue {nom} sur Pronostic Football !\n\n"
        f"🤖 Je suis un bot d'Intelligence Artificielle spécialisé dans les pronostics sportifs.\n\n"
        f"📊 Statut : {statut_label}\n"
        f"🎯 Pronostics aujourd'hui : {compteur}/{limite}\n\n"
        f"👇 Utilise les boutons ci-dessous pour commencer :"
    )

    # ⚠️ LE MENU AVEC LES BOUTONS PRO
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
    
    try:
        if est_administrateur(user_id):
            markup.add(telebot.types.KeyboardButton("👑 Panneau Admin"))
    except Exception as e:
        log_warning(f"Impossible de vérifier si {user_id} est admin : {e}", "START")

    try:
        bot.send_message(chat_id, presentation, reply_markup=markup)
    except Exception as e:
        log_error(f"Impossible d'envoyer le menu à {user_id}", "START", exception=e)
        return

    # Vérification de l'abonnement au canal
    inline_markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    try:
        member = bot.get_chat_member(config.CANAL_ID, user_id)
        is_member = member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        # Si on ne peut pas vérifier (canal supprimé, bot pas admin...), on ne bloque pas
        log_warning(f"Impossible de vérifier l'abonnement au canal pour {user_id} : {e}", "START")
        is_member = True

    if not is_member:
        inline_markup.add(
            telebot.types.InlineKeyboardButton("📢 Rejoindre notre Canal", url=config.CANAL_LIEN)
        )

    if inline_markup.keyboard:
        try:
            bot.send_message(chat_id, "👇 Rejoins notre canal pour ne rien rater :", reply_markup=inline_markup)
        except Exception as e:
            log_warning(f"Impossible d'envoyer le bouton canal à {user_id} : {e}", "START")


def enregistrer_start_handlers(bot):

    @bot.message_handler(commands=['start', 'help'])
    def send_welcome(message):
        user = message.from_user
        try:
            if est_banni(user.id):
                bot.reply_to(message, get_text("banni", get_langue(user.id)))
                return
        except Exception as e:
            log_error(f"Impossible de vérifier si {user.id} est banni", "START", exception=e)
            # En cas de doute, on refuse (par sécurité)
            return

        try:
            existe_avant = get_user_info(user.id) is not None
            enregistrer_utilisateur(user.id, user.username, user.first_name)
        except Exception as e:
            log_error(f"Impossible d'enregistrer l'utilisateur {user.id}", "START", exception=e)
            return

        if not existe_avant:
            parts = message.text.split()
            if len(parts) >= 2 and parts[1].startswith("REF"):
                try:
                    parrain_id = int(parts[1].replace("REF", ""))
                    if parrain_id != user.id and get_user_info(parrain_id):
                        if set_parrain(user.id, parrain_id):
                            ajouter_jours_premium(user.id, 1)
                            ajouter_jours_premium(parrain_id, 1)
                            log_info(f"Nouveau parrainage : {user.id} par {parrain_id}", "START")
                except ValueError:
                    log_warning(f"Code parrainage invalide dans le message de {user.id}", "START")
                except Exception as e:
                    log_error(f"Erreur lors du parrainage de {user.id}", "START", exception=e)

        envoyer_menu_principal(message.chat.id, user.id, bot)

    @bot.message_handler(commands=['langue', 'language'])
    @bot.message_handler(func=lambda m: m.text == "🌍 Langue")
    def cmd_langue(message):
        user_id = message.from_user.id
        try:
            langue = get_langue(user_id)
            markup = telebot.types.InlineKeyboardMarkup(row_width=1)
            for code, nom in LANGUES_DISPONIBLES.items():
                markup.add(telebot.types.InlineKeyboardButton(nom, callback_data=f"lang|{code}"))
            bot.reply_to(message, get_text("choix_langue", langue), reply_markup=markup)
        except Exception as e:
            log_error(f"Impossible d'afficher le menu des langues pour {user_id}", "START", exception=e)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("lang|"))
    def traiter_langue(call):
        user_id = call.from_user.id
        try:
            langue = call.data.split("|")[1]
            if set_langue(user_id, langue):
                bot.answer_callback_query(call.id, "OK")
                bot.send_message(call.message.chat.id, get_text("langue_changee", langue))
                envoyer_menu_principal(call.message.chat.id, user_id, bot)
            else:
                log_warning(f"Langue '{langue}' invalide pour {user_id}", "START")
                bot.answer_callback_query(call.id, "Langue non supportée")
        except Exception as e:
            log_error(f"Erreur de traitement de la langue pour {user_id}", "START", exception=e)
