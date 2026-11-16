# telegram_bot/devises_handlers.py
"""
Commande /devise : permet à l'utilisateur de choisir sa devise préférée
(CDF, USD ou EUR) et de l'enregistrer dans la table utilisateurs.

La colonne `devise` est créée localement au premier appel via ALTER TABLE
pour ne pas dépendre de users/db.py. Les taux de change proviennent de
core/devises.py.
"""

import telebot

from users.db import db_execute, db_fetchone
from core.devises import formater_prix, get_taux_change
from core.utils.logs import log_info, log_error

DEVISES_VALIDES = ("CDF", "USD", "EUR")


def _assurer_colonne_devise():
    """Crée la colonne `devise` si elle n'existe pas (ALTER TABLE local).

    On interroge la forme table-valuee de PRAGMA table_info('utilisateurs')
    pour rester compatible avec db_fetchone (une seule ligne renvoyee).
    """
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
            log_info("Colonne devise ajoutee a la table utilisateurs", module="DEVISES")
        return True
    except Exception as e:
        # La colonne peut deja exister (course entre deux appels) : on ignore.
        if "duplicate column" in str(e).lower():
            return True
        log_error(
            message="Impossible d'assurer la colonne devise",
            module="DEVISES",
            exception=e,
        )
        return False


def set_devise(user_id, devise):
    """Enregistre la devise preferee d'un utilisateur."""
    if devise not in DEVISES_VALIDES:
        log_error(
            message="Devise non supportee",
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
    """Retourne la devise preferee d'un utilisateur (defaut : CDF)."""
    try:
        row = db_fetchone(
            "SELECT devise FROM utilisateurs WHERE user_id = ?",
            params=[user_id],
            db_context={"table": "utilisateurs", "operation": "get_devise"},
        )
        devise = row[0] if row and row[0] else "CDF"
        if devise not in DEVISES_VALIDES:
            return "CDF"
        return devise
    except Exception as e:
        log_error(
            message="Impossible de recuperer la devise",
            module="DEVISES",
            user_context={"user_id": user_id},
            exception=e,
        )
        return "CDF"


def _clavier_devises():
    """Construit le clavier inline des 3 devises proposees."""
    markup = telebot.types.InlineKeyboardMarkup(row_width=3)
    markup.add(
        telebot.types.InlineKeyboardButton("🇨🇩 CDF", callback_data="dev|CDF"),
        telebot.types.InlineKeyboardButton("🇺🇸 USD", callback_data="dev|USD"),
        telebot.types.InlineKeyboardButton("🇪🇺 EUR", callback_data="dev|EUR"),
    )
    return markup


def _texte_devise(devise):
    """Texte d'invitation affichant la devise courante et un exemple."""
    return (
        "💱 <b>Votre devise préférée</b>\n\n"
        f"Devise actuelle : <b>{devise}</b>\n"
        f"Exemple : 10 000 CDF = <b>{formater_prix(10000, devise)}</b>\n\n"
        "Choisissez votre devise ci-dessous :"
    )


def enregistrer_devises_handlers(bot):
    """Enregistre les handlers de la commande /devise."""

    @bot.message_handler(commands=['devise'])
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
        except Exception as e:
            log_error(
                message="Erreur lors de la commande /devise",
                module="DEVISES",
                user_context={"user_id": user_id},
                exception=e,
            )

    @bot.message_handler(func=lambda m: m.text == "💱 Devise")
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
        except Exception as e:
            log_error(
                message="Erreur lors du bouton Devise",
                module="DEVISES",
                user_context={"user_id": user_id},
                exception=e,
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
            taux = get_taux_change(devise)
            texte = (
                "💱 <b>Devise enregistrée</b>\n\n"
                f"Devise : <b>{devise}</b>\n"
                f"Taux : 1 {devise} = {taux} CDF\n"
                f"Exemple : 10 000 CDF = <b>{formater_prix(10000, devise)}</b>"
            )
            bot.edit_message_text(
                texte,
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=_clavier_devises(),
                parse_mode="HTML",
            )
        except Exception as e:
            log_error(
                message="Erreur lors du callback devise",
                module="DEVISES",
                user_context={"user_id": user_id},
                exception=e,
            )
