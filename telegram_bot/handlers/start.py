# telegram_bot/handlers/start.py
"""
Handler /start + menu principal.
- Gestion forcée de la langue après changement
- Parrainage atomique (vérif enregistrement)
- Logs enrichis
- Détection admin pour afficher le clavier admin automatiquement
- BOUTONS_MENU : source unique des libellés de boutons (utilisée par fallback)
- Bouton Devise ajouté au clavier utilisateur (cohérent avec /devise)
"""

import telebot
import config

from users import (
    enregistrer_utilisateur, get_langue, set_langue, est_banni,
    get_user_info, est_administrateur, set_parrain,
    ajouter_jours_premium, get_statut_label,
    get_compteur_jour, get_limite_jour, utilisateur_existe,
)
from core.translations import get_text, LANGUES_DISPONIBLES
from core.utils.logs import log_info, log_error, log_warning

BOT_USERNAME = "MonPronosticFootball_bot"


# =========================================================
# BOUTONS DU MENU (source unique, utilisée par le fallback)
# =========================================================
BOUTONS_MENU = frozenset({
    # Menu utilisateur
    "⚽ Faire un Pronostic", "📅 Matchs du Jour", "🎟️ Coupons",
    "🏆 Top Affiches", "📜 Historique", "📊 Statistiques",
    "🔔 Notifications", "💎 Premium", "🤝 Parrainage",
    "🌍 Langue", "💎 Devise", "👑 Panneau Admin",
    # Menu admin (boutons paramétrés + boutons simples)
    "📊 Fiabilité", "🔍 Comparer", "⚽ Série",
    "💰 Cotes", "📈 Bankroll", "💸 Cash-out", "⚠️ Piège",
    "🌦️ Météo", "🎯 Favoris", "🎟️ Code Promo",
    "📊 Stats Admin", "🚨 Panique", "📸 Preuves",
    "🎟️ Codes", "🔧 Features", "💱 Taux",
    # Navigation
    "↩️ Retour au Menu",
})


def _contexte(user, chat_id=None):
    return {
        "user_id": user.id,
        "user_name": user.first_name or "",
        "username": user.username or "",
        "chat_id": chat_id or user.id,
    }


# Boutons du menu utilisateur, affichés à TOUS (y compris l'admin)
BOUTONS_UTILISATEUR = [
    "⚽ Faire un Pronostic", "📅 Matchs du Jour", "🎟️ Coupons",
    "🏆 Top Affiches", "📜 Historique", "📊 Statistiques",
    "🔔 Notifications", "💎 Premium", "🤝 Parrainage",
    "🌍 Langue", "💎 Devise",
]

# Boutons réservés à l'administrateur, ajoutés sous le menu utilisateur
BOUTONS_ADMIN_SUPPLEMENTAIRES = [
    "📊 Fiabilité", "🔍 Comparer", "⚽ Série", "💰 Cotes",
    "📈 Bankroll", "💸 Cash-out", "⚠️ Piège", "🌦️ Météo",
    "🎯 Favoris", "🎟️ Code Promo", "📊 Stats Admin", "🚨 Panique",
    "📸 Preuves", "🎟️ Codes", "🔧 Features", "💱 Taux",
    "↩️ Retour au Menu",
]


def _creer_clavier_admin():
    """Clavier de l'administrateur : menu utilisateur complet + boutons admin."""
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(*[telebot.types.KeyboardButton(b) for b in BOUTONS_UTILISATEUR])
    markup.add(*[telebot.types.KeyboardButton(b) for b in BOUTONS_ADMIN_SUPPLEMENTAIRES])
    return markup


def _creer_clavier_utilisateur(user_id=None):
    """Clavier normal pour les utilisateurs (+ Panneau Admin pour un admin)."""
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(*[telebot.types.KeyboardButton(b) for b in BOUTONS_UTILISATEUR])
    try:
        if user_id is not None and est_administrateur(user_id):
            markup.add(telebot.types.KeyboardButton("👑 Panneau Admin"))
    except Exception:
        pass
    return markup


def envoyer_menu_principal(chat_id, user_id, bot, force_langue=None):
    """Affiche le menu principal (normal ou vitrine).

    Pour un administrateur, affiche directement le clavier admin complet.
    """
    try:
        langue = force_langue if force_langue else get_langue(user_id)
        user_info = get_user_info(user_id)
        nom = user_info["first_name"] if user_info else "Utilisateur"
    except Exception as e:
        log_error(
            message="Impossible de récupérer les infos utilisateur",
            module="START",
            user_context={"user_id": user_id, "chat_id": chat_id},
            exception=e,
        )
        nom = "Utilisateur"
        langue = "fr"

    # MODE VITRINE
    if config.MODE_VITRINE:
        presentation = (
            f"👋 Bienvenue sur mon bot auto-évolutif !\n\n"
            f"🛠️ **Le bot est actuellement en maintenance.**\n\n"
            f"📢 Les analyses et pronostics sont publiés **gratuitement** "
            f"sur notre canal Telegram.\n\n"
            f"👇 Clique sur le bouton ci-dessous :"
        )
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
        markup.add(telebot.types.KeyboardButton("🌍 Langue"))
        try:
            bot.send_message(chat_id, presentation, reply_markup=markup, parse_mode="Markdown")
            inline = telebot.types.InlineKeyboardMarkup(row_width=1)
            inline.add(telebot.types.InlineKeyboardButton(
                "📢 REJOINDRE LE CANAL", url=config.CANAL_LIEN,
            ))
            bot.send_message(chat_id, "👇 Clique ici :", reply_markup=inline)
        except Exception as e:
            log_error(
                message="Impossible d'envoyer le menu vitrine",
                module="START",
                user_context={"user_id": user_id, "chat_id": chat_id},
                exception=e,
            )
        return

    # MODE NORMAL
    try:
        statut_label = get_statut_label(user_id)
        compteur = get_compteur_jour(user_id)
        limite = get_limite_jour(user_id)
    except Exception as e:
        log_error(
            message="Impossible de récupérer le statut",
            module="START",
            user_context={"user_id": user_id},
            exception=e,
        )
        statut_label, compteur, limite = "FREE", 0, 3

    presentation = (
        f"👋 Bienvenue sur mon bot auto-évolutif !\n\n"
        f"🤖 Je suis un bot d'IA spécialisé dans les pronostics sportifs.\n\n"
        f"📊 Statut : {statut_label}\n"
        f"🎯 Pronostics aujourd'hui : {compteur}/{limite}\n\n"
        f"👇 Utilise les boutons ci-dessous :"
    )

    # Détection admin : clavier admin complet ou clavier utilisateur
    try:
        est_admin = est_administrateur(user_id)
    except Exception:
        est_admin = False

    if est_admin:
        markup = _creer_clavier_admin()
    else:
        markup = _creer_clavier_utilisateur(user_id)

    try:
        bot.send_message(chat_id, presentation, reply_markup=markup)
    except Exception as e:
        log_error(
            message="Impossible d'envoyer le menu principal",
            module="START",
            user_context={"user_id": user_id, "chat_id": chat_id},
            exception=e,
        )
        return

    # Vérification abonnement canal
    try:
        member = bot.get_chat_member(config.CANAL_ID, user_id)
        is_member = member.status in ("member", "administrator", "creator")
    except Exception as e:
        log_warning(
            message="Impossible de vérifier l'abonnement au canal",
            module="START",
            user_context={"user_id": user_id, "chat_id": chat_id},
            exception=e,
        )
        is_member = True

    if not is_member:
        inline = telebot.types.InlineKeyboardMarkup(row_width=1)
        inline.add(telebot.types.InlineKeyboardButton(
            "📢 Rejoindre notre Canal", url=config.CANAL_LIEN,
        ))
        try:
            bot.send_message(chat_id, "👇 Rejoins notre canal :", reply_markup=inline)
        except Exception as e:
            log_warning(
                message="Impossible d'envoyer le bouton canal",
                module="START",
                user_context={"user_id": user_id, "chat_id": chat_id},
                exception=e,
            )


def enregistrer_start_handlers(bot):

    @bot.message_handler(commands=["start", "help"])
    def send_welcome(message):
        user = message.from_user
        user_id = user.id
        ctx = _contexte(user, message.chat.id)
        ctx["command"] = message.text or "/start"

        try:
            if est_banni(user_id):
                bot.reply_to(message, get_text("banni", get_langue(user_id)))
                return
        except Exception as e:
            log_error(
                message="Impossible de vérifier le bannissement",
                module="START",
                user_context=ctx,
                exception=e,
            )
            return

        # Enregistrement
        try:
            existe_avant = utilisateur_existe(user_id)
            cree = enregistrer_utilisateur(user_id, user.username, user.first_name)
        except Exception as e:
            log_error(
                message="Impossible d'enregistrer l'utilisateur",
                module="START",
                user_context=ctx,
                exception=e,
            )
            return

        # Parrainage (seulement pour les nouveaux)
        if cree and not existe_avant:
            parts = (message.text or "").split()
            if len(parts) >= 2 and parts[1].startswith("REF"):
                try:
                    parrain_id = int(parts[1].replace("REF", ""))
                    if parrain_id != user_id and get_user_info(parrain_id):
                        if set_parrain(user_id, parrain_id):
                            if utilisateur_existe(user_id):
                                ajouter_jours_premium(user_id, 1)
                                ajouter_jours_premium(parrain_id, 1)
                                log_info(
                                    f"Parrainage appliqué : {user_id} par {parrain_id}",
                                    module="START",
                                    user_context=ctx,
                                    extra={"parrain_id": parrain_id},
                                )
                except ValueError:
                    log_warning(
                        message="Code parrainage invalide",
                        module="START",
                        user_context=ctx,
                        extra={"code": parts[1][:20]},
                    )
                except Exception as e:
                    log_error(
                        message="Erreur lors du parrainage",
                        module="START",
                        user_context=ctx,
                        exception=e,
                    )

        envoyer_menu_principal(message.chat.id, user_id, bot)

    @bot.message_handler(commands=["langue", "language"])
    @bot.message_handler(func=lambda m: m.text == "🌍 Langue")
    def cmd_langue(message):
        user = message.from_user
        ctx = _contexte(user, message.chat.id)
        try:
            langue = get_langue(user.id)
            markup = telebot.types.InlineKeyboardMarkup(row_width=1)
            for code, nom in LANGUES_DISPONIBLES.items():
                markup.add(telebot.types.InlineKeyboardButton(nom, callback_data=f"lang|{code}"))
            bot.reply_to(message, get_text("choix_langue", langue), reply_markup=markup)
        except Exception as e:
            log_error(
                message="Impossible d'afficher le menu des langues",
                module="START",
                user_context=ctx,
                exception=e,
            )

    @bot.callback_query_handler(func=lambda call: call.data.startswith("lang|"))
    def traiter_langue(call):
        user = call.from_user
        ctx = _contexte(user, call.message.chat.id)
        try:
            langue = call.data.split("|", 1)[1]
            if set_langue(user.id, langue):
                bot.answer_callback_query(call.id, "OK")

                # On force la relecture de la langue depuis la BDD
                nouvelle_langue = get_langue(user.id)

                bot.send_message(call.message.chat.id, get_text("langue_changee", nouvelle_langue))

                # On passe la nouvelle langue au menu pour qu'il s'affiche correctement
                envoyer_menu_principal(call.message.chat.id, user.id, bot, force_langue=nouvelle_langue)
            else:
                bot.answer_callback_query(call.id, "Langue non supportée")
        except Exception as e:
            log_error(
                message="Erreur traitement langue",
                module="START",
                user_context=ctx,
                exception=e,
            )
