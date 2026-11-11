# telegram_bot/handlers/fallback.py
"""
Fallback pour les messages texte non reconnus.
- Ne capture plus les sessions de pronostic (géré en BDD)
- Ne capture plus les sessions admin (vérifié via ADMIN_SESSIONS)
"""

import telebot
import config
from users import get_langue, est_banni
from core.translations import get_text
from core.session import get_session
from core.utils.logs import log_info, log_error, log_warning


def enregistrer_fallback_handlers(bot):

    @bot.message_handler(
        func=lambda m: (
            m.text
            and not m.text.startswith("/")
            and not m.text.startswith("#")
            and m.text not in (
                "↩️ Retour au Menu", "🌍 Langue", "👑 Panneau Admin",
                "⚽ Faire un Pronostic", "📅 Matchs du Jour", "🎟️ Coupons",
                "🏆 Top Affiches", "📜 Historique", "📊 Statistiques",
                "🔔 Notifications", "💎 Premium", "🤝 Parrainage",
            )
        )
    )
    def handle_menu_fallback(message):
        user_id = message.from_user.id
        ctx = {
            "user_id": user_id,
            "user_name": message.from_user.first_name or "",
            "username": message.from_user.username or "",
            "chat_id": message.chat.id,
            "message_text": (message.text or "")[:100],
        }

        try:
            langue = get_langue(user_id)
            ctx["langue"] = langue
        except Exception as e:
            log_error(
                message="Impossible de récupérer la langue",
                module="FALLBACK",
                user_context=ctx,
                exception=e,
            )
            langue = "fr"

        try:
            if est_banni(user_id):
                bot.reply_to(message, get_text("banni", langue))
                return
        except Exception as e:
            log_error(
                message="Impossible de vérifier le bannissement",
                module="FALLBACK",
                user_context=ctx,
                exception=e,
            )
            return

        # Session de pronostic active ? On ignore
        try:
            session = get_session(user_id)
            if session:
                return
        except Exception as e:
            log_warning(
                message="Impossible de vérifier la session de pronostic",
                module="FALLBACK",
                user_context=ctx,
                exception=e,
            )

        # Session admin active ? On ignore
        try:
            from telegram_bot.admin.actions import ADMIN_SESSIONS
            if user_id in ADMIN_SESSIONS:
                return
        except Exception as e:
            log_warning(
                message="Impossible de vérifier les sessions admin",
                module="FALLBACK",
                user_context=ctx,
                exception=e,
            )

        # Mode vitrine
        if config.MODE_VITRINE:
            try:
                from telegram_bot.handlers.start import envoyer_menu_principal
                envoyer_menu_principal(message.chat.id, user_id, bot)
                return
            except Exception as e:
                log_error(
                    message="Impossible de rediriger en mode vitrine",
                    module="FALLBACK",
                    user_context=ctx,
                    exception=e,
                )
                return

        log_info("Message inconnu (fallback)", "FALLBACK", user_context=ctx)

        try:
            bot.reply_to(message, get_text("fallback", langue))
            from telegram_bot.handlers.start import envoyer_menu_principal
            envoyer_menu_principal(message.chat.id, user_id, bot)
        except Exception as e:
            log_error(
                message="Impossible d'envoyer le fallback",
                module="FALLBACK",
                user_context=ctx,
                exception=e,
            )

    # Anciens boutons #PRONO, etc.
    @bot.message_handler(
        func=lambda m: (
            m.text
            and m.text.startswith("#")
            and m.text not in ("#LANGUE", "#ADMIN")
        )
    )
    def handle_anciens_boutons(message):
        user_id = message.from_user.id
        ctx = {
            "user_id": user_id,
            "chat_id": message.chat.id,
            "message_text": (message.text or "")[:50],
        }
        log_info("Ancien bouton utilisé", "FALLBACK", user_context=ctx)
        try:
            bot.reply_to(message, "🔄 Menu mis à jour. Voici le nouveau :")
            from telegram_bot.handlers.start import envoyer_menu_principal
            envoyer_menu_principal(message.chat.id, user_id, bot)
        except Exception as e:
            log_error(
                message="Impossible de rediriger vers le nouveau menu",
                module="FALLBACK",
                user_context=ctx,
                exception=e,
            )
