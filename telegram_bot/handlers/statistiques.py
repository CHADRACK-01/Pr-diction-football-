# telegram_bot/handlers/statistiques.py
import telebot
from users import get_langue
from users.db import db_fetchone
from core.ml_model import global_model_data
from core.utils.logs import log_info, log_error

def enregistrer_statistiques_handlers(bot):

    @bot.message_handler(func=lambda m: m.text == "📊 Statistiques")
    def handle_statistiques(message):
        user_id = message.from_user.id
        try:
            langue = get_langue(user_id)
        except Exception:
            langue = "fr"

        modeles = global_model_data.get("modeles_par_competition")
        if not modeles:
            bot.reply_to(message, "📊 **Statistiques indisponibles**\n\nLe modèle est en cours de chargement. Réessaie dans un instant.", parse_mode="Markdown")
            return

        # 1. Calcul du nombre de matchs RÉELS dans la base de données
        total_matchs = 0
        try:
            row = db_fetchone("SELECT COUNT(*) FROM matchs")
            if row:
                total_matchs = row[0]
        except Exception as e:
            log_error("Impossible de compter les matchs", "STATS", exception=e)

        # 2. Calcul de la précision RÉELLE basée sur l'historique
        precision = 0
        try:
            row = db_fetchone("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN est_gagnant = 1 THEN 1 ELSE 0 END) as gagnes
                FROM resultats_pronostics 
                WHERE est_gagnant IS NOT NULL
            """)
            if row and row[0] > 0:
                total_verifies = row[0]
                gagnes = row[1] or 0
                precision = (gagnes / total_verifies) * 100
        except Exception as e:
            log_error("Impossible de calculer la précision", "STATS", exception=e)

        nb_competitions = len(modeles)
        nb_marches = sum(len(m) for m in modeles.values())

        texte = "📊 **STATISTIQUES DU MODÈLE IA**\n"
        texte += "━━━━━━━━━━━━━━━━━━━━\n\n"
        texte += "🧠 **Modèle** : LightGBM + Calibration Isotonic\n"
        texte += f"📚 **Compétitions** : {nb_competitions}\n"
        texte += f"🎯 **Prédictions totales** : {nb_marches}\n"
        
        if total_matchs > 0:
            texte += f"📈 **Matchs en base** : {total_matchs:,}\n".replace(",", " ")
        else:
            texte += "📈 **Matchs en base** : En cours de téléchargement\n"

        if precision > 0:
            texte += f"🎯 **Précision réelle** : {round(precision, 1)}%\n"
        else:
            texte += "🎯 **Précision réelle** : En attente de résultats vérifiés\n"

        texte += (
            "\n━━━━━━━━━━━━━━━━━━━━\n"
            "📋 **Marchés disponibles** :\n"
            "• 🛡️ Double Chance (1X, X2, 12)\n"
            "• 🎯 BTTS (Les 2 marquent)\n"
            "• 🥅 Over/Under 2.5 buts\n"
            "• ⏱️ Mi-temps la plus prolifique\n"
            "• 🏁 1N2 à la mi-temps\n\n"
            "💡 _La précision est calculée sur la base des pronostics vérifiés._"
        )

        try:
            bot.reply_to(message, texte, parse_mode="Markdown")
        except Exception as e:
            log_error("Impossible d'afficher les stats", "STATS", exception=e)
            bot.reply_to(message, texte.replace("**", "").replace("_", ""))
