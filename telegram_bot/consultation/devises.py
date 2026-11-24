"""Handlers Telegram pour la sélection de devise."""

import telebot

from core.devises import formater_prix, get_taux_change
from core.utils.logs import log_error, log_info
from users.db import db_execute, db_fetchone


DEVISES_VALIDES = ("CDF", "USD", "EUR")


def _assurer_colonne_devise():
    """Crée la colonne devise si elle n'existe pas encore."""
    try:
        row = db_fetchone(
            "SELECT COUNT(*) FROM pragma_table_info('utilisateurs') "
            "WHERE name = 'devise'"
        )
        if row and row[0]:
            return True

        resultat = db_execute(
            "ALTER TABLE utilisateurs ADD COLUMN devise TEXT DEFAULT 'CDF'",
            db_context={"table": "utilisateurs", "operation": "add_column_devise"},
        )
        if resultat is not None:
            log_info("Colonne devise ajoutée à la table utilisateurs", module="DEVISES")
        return True
    except Exception as exc:
        if "duplicate column" in str(exc).lower():
            return True
        log_error(
            message="Impossible d'assurer la colonne devise",
            module="DEVISES",
            exception=exc,
        )
        return False


def set_devise(user_id, devise):
    """Enregistre la devise préférée d'un utilisateur."""
    if devise not in DEVISES_VALIDES:
        log_error(
            message="Devise non supportée",
            module="DEVISES",
            user_context={"user_id": user_id},
            extra={"devise_demandee": devise},
        )
        return False

    rowcount = db_execute(
        "UPDATE utilisateurs SET devise = ? WHERE user_id = ?",
        params=[devise, user_id],
        db_context={"table": "utilisateurs", "operation": "set_devise"},
    )
    return rowcount is not None and rowcount > 0


def get_devise(user_id):
    """Retourne la devise préférée ou CDF par défaut."""
    try:
        row = db_fetchone(
            "SELECT devise FROM utilisateurs WHERE user_id = ?",
            params=[user_id],
            db_context={"table": "utilisateurs", "operation": "get_devise"},
        )
        devise = row[0] if row and row[0] else "CDF"
        return devise if devise in DEVISES_VALIDES else "CDF"
    except Exception as exc:
        log_error(
            message="Impossible de récupérer la devise",
            module="DEVISES",
            user_context={"user_id": user_id},
            exception=exc,
        )
        return "CDF"


def _clavier_devises():
    markup = telebot.types.InlineKeyboardMarkup(row_width=3)
    markup.add(
        telebot.types.InlineKeyboardButton("🇨🇩 CDF", callback_data="dev|CDF"),
        telebot.types.InlineKeyboardButton("🇺🇸 USD", callback_data="dev|USD"),
        telebot.types.InlineKeyboardButton("🇪🇺 EUR", callback_data="dev|EUR"),
    )
    return markup


def _texte_devise(devise):
    return (
        "💱 <b>Votre devise préférée</b>\n\n"
        f"Devise actuelle : <b>{devise}</b>\n"
        f"Exemple : 10 000 CDF = <b>{formater_prix(10000, devise)}</b>\n\n"
        "Choisissez votre devise ci-dessous :"
    )


def _ligne_taux(devise):
    taux = get_taux_change(devise)
    if taux is None:
        return "Taux : <i>indisponible pour le moment</i>"
    return f"Taux : 1 {devise} = {taux} CDF"


def enregistrer_devises_handlers(bot):
    """Enregistre les handlers de la commande /devise."""

    @bot.message_handler(commands=["devise"])
    def commande_devise(message):
        user_id = message.from_user.id
        try:
            _assurer_colonne_devise()
            devise = get_devise(user_id)
            bot.send_message(
                message.chat.id,
                _texte_devise(devise),
                reply_markup=_clavier_devises(),
                parse_mode="HTML",
            )
        except Exception as exc:
            log_error(
                message="Erreur lors de la commande /devise",
                module="DEVISES",
                user_context={"user_id": user_id},
                exception=exc,
            )

    @bot.message_handler(func=lambda message: message.text == "💎 Devise")
    def bouton_devise(message):
        user_id = message.from_user.id
        try:
            _assurer_colonne_devise()
            devise = get_devise(user_id)
            bot.send_message(
                message.chat.id,
                _texte_devise(devise),
                reply_markup=_clavier_devises(),
                parse_mode="HTML",
            )
        except Exception as exc:
            log_error(
                message="Erreur lors du bouton Devise",
                module="DEVISES",
                user_context={"user_id": user_id},
                exception=exc,
            )

    @bot.callback_query_handler(func=lambda call: call.data.startswith("dev|"))
    def callback_devise(call):
        user_id = call.from_user.id
        try:
            _assurer_colonne_devise()
            devise = call.data.split("|", 1)[1]
            if not set_devise(user_id, devise):
                bot.answer_callback_query(call.id, "❌ Devise invalide")
                return

            bot.answer_callback_query(call.id, "✅ Devise enregistrée")
            texte = (
                "💱 <b>Devise enregistrée</b>\n\n"
                f"Devise : <b>{devise}</b>\n"
                f"{_ligne_taux(devise)}\n"
                f"Exemple : 10 000 CDF = <b>{formater_prix(10000, devise)}</b>"
            )
            bot.edit_message_text(
                texte,
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=_clavier_devises(),
                parse_mode="HTML",
            )
        except Exception as exc:
            log_error(
                message="Erreur lors du callback devise",
                module="DEVISES",
                user_context={"user_id": user_id},
                exception=exc,
            )
