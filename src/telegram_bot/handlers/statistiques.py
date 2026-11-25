# telegram_bot/handlers/statistiques.py
import telebot
from users import get_langue
from users.db import db_fetchone
from core.predictions.ml_model import global_model_data
from core.utils.logs import log_info, log_error

def enregistrer_statistiques_handlers(bot):

    @bot.message_handler(func=lambda m: m.text == "📊 Statistiques")
    def handle_statistiques(message):
        user_id = message.from_user.id
        try:
            langue = get_langue(user_id)
        except Exception:
            langue = "fr"

        modeles = global_model_data.get("models")
        if not modeles:
            bot.reply_to(message, "📊 **Statistiques indisponibles**\n\nLe modèle est en cours de chargement. Réessaie dans un instant.", parse_mode="Markdown")
            return

        # 1. Nombre de matchs en base
        total_matchs = 0
        try:
            row = db_fetchone("SELECT COUNT(*) FROM matchs")
            if row:
                total_matchs = row[0]
        except Exception as e:
            log_error("Impossible de compter les matchs", "STATS", exception=e)

        # 2. Précision réelle (basée sur les metrics du bundle)
        metrics = global_model_data.get("metrics", {})
        prec_1n2 = metrics.get("1N2", {}).get("accuracy", 0)
        prec_dc = metrics.get("DC_1X", {}).get("accuracy", 0)
        prec_over = metrics.get("Over25", {}).get("accuracy", 0)
        
        # Formater les pourcentages
        str_1n2 = f"{round(prec_1n2 * 100, 1)}%" if prec_1n2 else "N/A"
        str_dc = f"{round(prec_dc * 100, 1)}%" if prec_dc else "N/A"
        str_over = f"{round(prec_over * 100, 1)}%" if prec_over else "N/A"

        texte = "📊 **STATISTIQUES DU MODÈLE IA**\n"
        texte += "━━━━━━━━━━━━━━━━━━━━\n\n"
        texte += "🧠 **Modèle** : LightGBM (6 marchés)\n"
        texte += f"📚 **Matchs en base** : {total_matchs:,}\n".replace(",", " ")
        texte += f"📅 **Dernier entraînement** : {global_model_data.get('date_chargement', 'Inconnu')}\n\n"
        
        texte += "🎯 **Précisions (Test 2025-2026)** :\n"
        texte += f"• 1N2 : {str_1n2}\n"
        texte += f"• Double Chance (1X) : {str_dc}\n"
        texte += f"• Over 2.5 : {str_over}\n\n"

        texte += (
            "━━━━━━━━━━━━━━━━━━━━\n"
            "💡 _Les statistiques sont mises à jour à chaque ré-entraînement._"
        )

        try:
            bot.reply_to(message, texte, parse_mode="Markdown")
        except Exception as e:
            log_error("Impossible d'afficher les stats", "STATS", exception=e)
            bot.reply_to(message, texte.replace("**", "").replace("_", ""))
