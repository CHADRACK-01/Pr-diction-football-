# telegram_bot/admin/selection.py
"""Sous-claviers de sélection pour les boutons admin paramétrés.

L'état ADMIN_SELECTIONS est calqué sur ADMIN_SESSIONS (admin/actions.py) et
non sur core.session, qui reste réservé au parcours de pronostic.
"""

import telebot

from users.matchs import get_equipes_saison_en_cours
from core.utils.logs import log_info, log_error

from telegram_bot.admin.menus import menu_admin_bas
from telegram_bot.handlers.pronostic import (
    _creer_clavier_competitions,
    _creer_clavier_equipes,
    _detecter_competition,
)


ADMIN_SELECTIONS = {}

BOUTON_ANNULER = "❌ Annuler"
BOUTON_RETOUR = "↩️ Retour au Menu"

# Bouton admin -> (commande, type de paramètre à collecter)
COMMANDES_PARAMETREES = {
    "🔍 Comparer": ("/comparer", "equipe"),
    "⚽ Série": ("/serie", "equipe"),
    "💰 Cotes": ("/cotes", "equipe"),
    "🎯 Favoris": ("/favoris", "equipe"),
    "🌦️ Météo": ("/meteo", "deux_equipes"),
    "⚠️ Piège": ("/piege", "deux_equipes"),
    "💸 Cash-out": ("/cashout", "cashout"),
    "📈 Bankroll": ("/bankroll", "texte"),
    "🎟️ Code Promo": ("/utilisercode", "texte"),
}

QUESTIONS_TEXTE = {
    "/cashout": "💸 Saisis la mise et la cote (ex : 10 2.5) :",
    "/bankroll": "📈 Saisis le montant :",
    "/utilisercode": "🎟️ Saisis le code promo :",
}


def _creer_clavier_competitions_selection():
    markup = _creer_clavier_competitions()
    markup.add(telebot.types.KeyboardButton(BOUTON_ANNULER))
    return markup


def _creer_clavier_equipes_selection(equipes):
    markup = _creer_clavier_equipes(equipes)
    markup.add(telebot.types.KeyboardButton(BOUTON_ANNULER))
    return markup


def _creer_clavier_annuler():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    markup.add(telebot.types.KeyboardButton(BOUTON_ANNULER))
    return markup


def demarrer_selection(user_id, commande, type_param, bot=None, chat_id=None):
    """Initialise l'état de sélection puis affiche le clavier adéquat."""
    ADMIN_SELECTIONS[user_id] = {
        "commande": commande,
        "type_param": type_param,
        "equipes": [],
        "params": [],
        "etape": "attente_texte" if type_param == "texte" else "competition",
    }
    log_info(f"Démarrage sélection admin {commande}", "ADMIN")

    if type_param == "texte":
        markup = _creer_clavier_annuler()
        texte = QUESTIONS_TEXTE.get(commande, "✍️ Saisis la valeur :")
        if bot is not None and chat_id is not None:
            bot.send_message(chat_id, texte, reply_markup=markup)
        return markup

    markup = _creer_clavier_competitions_selection()
    if bot is not None and chat_id is not None:
        bot.send_message(
            chat_id,
            "🏆 <b>Choisis la compétition</b> :",
            reply_markup=markup,
            parse_mode="HTML",
        )
    return markup


def annuler_selection(user_id, bot, chat_id):
    """Purge l'état de sélection et renvoie le menu admin du bas."""
    ADMIN_SELECTIONS.pop(user_id, None)
    markup = menu_admin_bas()
    if bot is not None and chat_id is not None:
        bot.send_message(chat_id, "❌ Sélection annulée.", reply_markup=markup)
    return markup


def traiter_message_selection(message, bot):
    """Traite un message destiné à une sélection admin en cours.

    Retourne True quand le message a été consommé, None sinon, afin de laisser
    les handlers habituels (parcours pronostic) traiter le message.
    """
    user_id = message.from_user.id
    etat = ADMIN_SELECTIONS.get(user_id)
    if not etat:
        return None

    texte = (message.text or "").strip()

    if texte in (BOUTON_ANNULER, BOUTON_RETOUR):
        annuler_selection(user_id, bot, message.chat.id)
        return True

    etape = etat.get("etape")
    if etape == "competition":
        return _traiter_competition(message, bot, etat)
    if etape == "equipes":
        return _traiter_equipe(message, bot, etat)
    if etape == "attente_texte":
        return _traiter_texte(message, bot, etat)
    return None


def _traiter_competition(message, bot, etat):
    comp_code, nom_propre = _detecter_competition(message.text or "")
    if not comp_code:
        return None

    try:
        equipes = get_equipes_saison_en_cours(nom_propre)
    except Exception as e:
        log_error("Erreur récupération équipes sélection admin", "ADMIN", exception=e)
        bot.send_message(message.chat.id, "❌ Erreur lors de la récupération des équipes.")
        return True

    if not equipes:
        bot.send_message(
            message.chat.id,
            f"⚠️ Aucune équipe trouvée pour <b>{nom_propre}</b> cette saison.",
            parse_mode="HTML",
        )
        return True

    etat["equipes"] = list(equipes)
    etat["params"] = []
    etat["etape"] = "equipes"
    bot.send_message(
        message.chat.id,
        "🏠 Sélectionne l'équipe :",
        reply_markup=_creer_clavier_equipes_selection(equipes),
        parse_mode="HTML",
    )
    return True


def _traiter_equipe(message, bot, etat):
    equipe = (message.text or "").strip()
    if equipe not in etat.get("equipes", []):
        return None

    etat["params"].append(equipe)
    type_param = etat.get("type_param")

    if type_param == "equipe":
        return _executer_selection(message, bot, etat)

    if type_param in ("deux_equipes", "cashout"):
        if len(etat["params"]) < 2:
            restantes = [e for e in etat["equipes"] if e not in etat["params"]]
            bot.send_message(
                message.chat.id,
                f"🏠 <b>{etat['params'][0]}</b>\n\n✈️ Sélectionne la seconde équipe :",
                reply_markup=_creer_clavier_equipes_selection(restantes),
                parse_mode="HTML",
            )
            return True
        if type_param == "cashout":
            etat["etape"] = "attente_texte"
            bot.send_message(
                message.chat.id,
                QUESTIONS_TEXTE.get(etat.get("commande"), "✍️ Saisis la valeur :"),
                reply_markup=_creer_clavier_annuler(),
            )
            return True
        return _executer_selection(message, bot, etat)

    return None


def _traiter_texte(message, bot, etat):
    valeur = (message.text or "").strip()
    if not valeur:
        return None
    etat["params"].append(valeur)
    return _executer_selection(message, bot, etat)


def _construire_commande(commande, type_param, params):
    if type_param == "equipe":
        if not params:
            return None
        if commande == "/favoris":
            return f"/favoris ajouter {params[0]}"
        return f"{commande} {params[0]}"
    if type_param == "deux_equipes":
        if len(params) < 2:
            return None
        return f"{commande} {params[0]} vs {params[1]}"
    if type_param == "cashout":
        if len(params) < 3:
            return None
        return f"/cashout {params[0]} vs {params[1]} {params[2]}"
    if type_param == "texte":
        if not params:
            return None
        return f"{commande} {params[0]}"
    return None


def _executer_selection(message, bot, etat):
    user_id = message.from_user.id
    commande = etat.get("commande")
    texte_commande = _construire_commande(
        commande, etat.get("type_param"), etat.get("params", [])
    )
    if not texte_commande:
        return None

    ADMIN_SELECTIONS.pop(user_id, None)

    try:
        fake_message = message
        fake_message.text = texte_commande
        bot.process_new_messages([fake_message])
    except Exception as e:
        log_error(f"Erreur exécution sélection admin {commande}", "ADMIN", exception=e)
        bot.reply_to(message, f"❌ Erreur lors de l'exécution de {commande}.")
    return True
