# telegram_bot/handlers/statistiques.py
"""
Statistiques du modèle IA.
- Affiche les vraies valeurs (ou "non disponible" si absent)
- Logs enrichis
"""

import telebot
from users import get_langue
from core.ml_model import global_model_data
from core.utils.logs import log_info, log_error, log_warning


def enregistrer_statistiques_handlers(bot):

    @bot.message_handler(func=lambda m: m.text == "📊 Statistiques")
    def handle_statistiques(message):
        user_id = message.from_user.id
        ctx = {
            "user_id": user_id,
            "user_name": message.from_user.first_name or "",
            "username": message.from_user.username or "",
            "chat_id": message.chat.id,
            "command": "📊 Statistiques",
        }

        try:
            langue = get_langue(user_id)
        except Exception as e:
            log_error(
                message="Impossible de récupérer la langue",
                module="STATS",
                user_context=ctx,
                exception=e,
            )
            langue = "fr"

        modeles = global_model_data.get("modeles_par_competition")
        if not modeles:
            log_warning(
                message="Stats demandées mais modèle non chargé",
                module="STATS",
                user_context=ctx,
            )
            bot.reply_to(
                message,
                "📊 **Statistiques indisponibles**\n\n"
                "Le modèle est en cours de chargement. Réessaie dans un instant.",
                parse_mode="Markdown",
            )
            return

        precision = global_model_data.get("precision_moyenne")
        total_matchs = global_model_data.get("total_matchs")
        nb_competitions = len(modeles)
        nb_marches = sum(len(m) for m in modeles.values())

        texte = "📊 **STATISTIQUES DU MODÈLE IA**\n"
        texte += "━━━━━━━━━━━━━━━━━━━━\n\n"
        texte += "🧠 **Modèle** : LightGBM + Calibration Isotonic\n"
        texte += f"📚 **Compétitions** : {nb_competitions}\n"
        texte += f"🎯 **Prédictions totales** : {nb_marches}\n"

        if total_matchs:
            texte += f"📈 **Matchs d'entraînement** : {total_matchs:,}\n".replace(",", " ")
        else:
            texte += "📈 **Matchs d'entraînement** : non disponible\n"

        if precision:
            texte += f"🎯 **Précision moyenne** : {round(precision * 100, 2)}%\n"
        else:
            texte += "🎯 **Précision moyenne** : non disponible\n"

        texte += (
            "\n━━━━━━━━━━━━━━━━━━━━\n"
            "📋 **Marchés disponibles** :\n"
            "• 🛡️ Double Chance (1X, X2, 12)\n"
            "• 🎯 BTTS (Les 2 marquent)\n"
            "• 🥅 Over/Under 2.5 buts\n"
            "• ⏱️ Mi-temps la plus prolifique\n"
            "• 🏁 1N2 à la mi-temps\n\n"
            "💡 _Les marchés Mi-temps sont indicatifs._"
        )

        try:
            bot.reply_to(message, texte, parse_mode="Markdown")
        except Exception as e:
            log_error(
                message="Impossible d'afficher les stats en Markdown",
                module="STATS",
                user_context=ctx,
                exception=e,
            )
            try:
                bot.reply_to(message, texte.replace("**", "").replace("_", ""))
            except Exception as e2:
                log_error(
                    message="Impossible d'afficher les stats (fallback)",
                    module="STATS",
                    user_context=ctx,
                    exception=e2,
                )
