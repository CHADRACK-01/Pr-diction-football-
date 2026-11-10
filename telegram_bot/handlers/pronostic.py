import telebot
import re

from users import get_langue, est_banni, peut_faire_pronostic, get_limite_jour, est_administrateur
from core.translations import get_text
from config import CHAMPIONNATS, INFOS_COMPETITIONS, MAPPING_COMPETITIONS
from core.session import set_session_competition, clear_session_competition
from core.utils.logs import log_info, log_error, log_warning


def _extraire_competition_du_texte(texte_bouton):
    """
    Extrait le code de la compétition à partir du texte du bouton.
    Ex: "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League" -> "premier_league"
    Retourne (code, nom_propre) ou (None, None) si non trouvé.
    """
    for code, nom_propre in CHAMPIONNATS.items():
        # On vérifie que le texte contient le nom propre, en tant que mot complet
        # (pour éviter que "Ligue 1" matche "Ligue 12" par exemple)
        if re.search(rf'\b{re.escape(nom_propre)}\b', texte_bouton):
            return code, nom_propre
    return None, None


def creer_clavier_competitions():
    """Crée le clavier des compétitions avec des boutons propres."""
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    boutons = []
    for code, nom_propre in CHAMPIONNATS.items():
        infos = INFOS_COMPETITIONS.get(nom_propre, {})
        emoji = infos.get("emoji", "🏆")
        boutons.append(telebot.types.KeyboardButton(f"{emoji} {nom_propre}"))
    markup.add(*boutons)
    markup.add(telebot.types.KeyboardButton("↩️ Retour au Menu"))
    return markup


def _creer_clavier_principal(user_id):
    """Recrée le clavier principal (après choix de compétition)."""
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
        log_warning(f"Impossible de vérifier le statut admin pour {user_id} : {e}", "PRONOSTIC")
    return markup


def afficher_menu_competitions(bot, message):
    user_id = message.from_user.id
    langue = get_langue(user_id)

    try:
        if est_banni(user_id):
            bot.reply_to(message, get_text("banni", langue))
            return
    except Exception as e:
        log_error(f"Impossible de vérifier si {user_id} est banni", "PRONOSTIC", exception=e)
        return

    try:
        if not peut_faire_pronostic(user_id):
            limite = get_limite_jour(user_id)
            bot.reply_to(message, get_text("limite_atteinte", langue, limite=limite))
            return
    except Exception as e:
        log_error(f"Impossible de vérifier la limite de {user_id}", "PRONOSTIC", exception=e)
        bot.reply_to(message, "❌ Une erreur est survenue lors de la vérification de tes limites. Réessaie plus tard.")
        return

    markup = creer_clavier_competitions()
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
        try:
            clear_session_competition(user_id)
        except Exception as e:
            log_error(f"Impossible de supprimer la session de {user_id}", "PRONOSTIC", exception=e)
        from telegram_bot.handlers.start import envoyer_menu_principal
        envoyer_menu_principal(message.chat.id, user_id, bot)

    @bot.message_handler(func=lambda m: m.text and any(nom in m.text for nom in CHAMPIONNATS.values()))
    def handle_choix_competition(message):
        user_id = message.from_user.id
        langue = get_langue(user_id)
        texte_bouton = message.text

        # Extraction sécurisée du code de la compétition
        comp_code, nom_propre = _extraire_competition_du_texte(texte_bouton)
        if not comp_code:
            log_warning(f"Texte de compétition non reconnu : '{texte_bouton}' de {user_id}", "PRONOSTIC")
            return

        # Sauvegarde de la compétition dans la BDD
        try:
            set_session_competition(user_id, comp_code)
        except Exception as e:
            log_error(f"Impossible de sauvegarder la compétition {comp_code} pour {user_id}", "PRONOSTIC", exception=e)
            bot.reply_to(message, "❌ Impossible de sauvegarder ta compétition. Réessaie.")
            return

        # On remet le clavier principal
        markup = _creer_clavier_principal(user_id)
        
        bot.send_message(
            message.chat.id,
            f"⚽ Tu as choisi **{nom_propre}**.\n\nTape maintenant ton pronostic :\nFormat : `Equipe A vs Equipe B`\nExemple : `Paris SG vs Marseille`",
            reply_markup=markup,
            parse_mode="Markdown"
        )
        
        log_info(f"Compétition choisie par {user_id} : {nom_propre}", "PRONOSTIC")
