# telegram_bot/handlers/fallback.py
"""
Fallback pour les messages texte non reconnus.
- Ne capture plus les sessions de pronostic (géré en BDD)
- Ne capture plus les sessions admin (vérifié via ADMIN_SESSIONS)
- Exclut TOUS les boutons du menu utilisateur ET du menu admin
  (source unique : telegram_bot.handlers.start.BOUTONS_MENU)
"""

import telebot
import config
from users import get_langue, est_banni
from core.translations import get_text
from core.session import get_session
from core.utils.logs import log_info, log_error, log_warning
from core.administration.urgence import est_en_panique

# Import différé pour éviter les cycles au chargement
def _boutons_menu():
    """Retourne l'ensemble des libellés de boutons à exclure du fallback."""
    try:
        from telegram_bot.handlers.start import BOUTONS_MENU
        return BOUTONS_MENU
    except Exception as e:
        # Fallback de secours si l'import échoue (ne devrait jamais arriver)
        log_warning(
            message="Impossible d'importer BOUTONS_MENU, utilisation liste locale",
            module="FALLBACK",
            exception=e,
        )
        return frozenset({
            "↩️ Retour au Menu", "🌍 Langue", "👑 Panneau Admin",
            "⚽ Faire un Pronostic", "📅 Matchs du Jour", "🎟️ Coupons",
            "🏆 Top Affiches", "📜 Historique", "📊 Statistiques",
            "🔔 Notifications", "💎 Premium", "🤝 Parrainage",
            "📊 Stats Admin", "🚨 Panique", "📸 Preuves",
            "🎟️ Codes", "🔧 Features", "💱 Taux",
            "💎 Devise", "📊 Fiabilité", "🔍 Comparer", "⚽ Série",
            "💰 Cotes", "📈 Bankroll", "💸 Cash-out", "⚠️ Piège",
            "🌦️ Météo", "🎯 Favoris", "🎟️ Code Promo",
        })


def enregistrer_fallback_handlers(bot):

    @bot.message_handler(
        func=lambda m: (
            m.text
            and not m.text.startswith("/")
            and not m.text.startswith("#")
            and m.text not in _boutons_menu()
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

        # Mode panique : on bloque le fallback
        try:
            if est_en_panique():
                bot.reply_to(message, '🚨 Le bot est en mode maintenance. Veuillez patienter.')
                log_info("Message bloqué par le mode panique", "FALLBACK", user_context=ctx)
                return
        except Exception as e:
            log_warning(
                message="Impossible de vérifier le mode panique",
                module="FALLBACK",
                user_context=ctx,
                exception=e,
            )

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

        # Sélection admin en cours (boutons paramétrés) ? On ignore
        try:
            from telegram_bot.admin.selection import ADMIN_SELECTIONS
            if user_id in ADMIN_SELECTIONS:
                return
        except Exception as e:
            log_warning(
                message="Impossible de vérifier les sélections admin",
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
