# telegram_bot/meteo_handlers.py
"""
Handler pour la commande /meteo.
Affiche la météo et son impact sur un match.
"""

import telebot
from core.meteo import obtenir_meteo_simulee, formater_alerte_meteo
from core.utils.logs import log_info, log_error


def enregistrer_meteo_handlers(bot):

    @bot.message_handler(commands=['meteo'])
    def cmd_meteo(message):
        args = message.text.split(maxsplit=1)
        
        if len(args) < 2:
            bot.reply_to(
                message,
                "⚠️ Utilise : <code>/meteo EQUIPE1 vs EQUIPE2</code>\n"
                "Exemple : <code>/meteo Chelsea vs Arsenal</code>",
                parse_mode="HTML"
            )
            return

        try:
            match = args[1].split(" vs ")
            if len(match) != 2:
                bot.reply_to(message, "❌ Format : <code>/meteo Equipe1 vs Equipe2</code>", parse_mode="HTML")
                return

            home_team = match[0].strip()
            away_team = match[1].strip()

            bot.reply_to(message, f"⏳ Analyse météo pour <b>{home_team} vs {away_team}</b>...", parse_mode="HTML")

            meteo = obtenir_meteo_simulee()
            texte = formater_alerte_meteo(home_team, away_team, meteo)
            
            bot.reply_to(message, texte, parse_mode="HTML")

        except Exception as e:
            log_error("Erreur commande /meteo", "METEO", exception=e)
            bot.reply_to(message, "❌ Erreur lors de l'analyse météo.")
