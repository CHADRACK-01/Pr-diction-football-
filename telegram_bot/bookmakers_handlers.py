# telegram_bot/bookmakers_handlers.py
"""
Handler pour la commande /cotes.
Compare les cotes réelles de plusieurs bookmakers.
"""

import telebot
from core.bookmakers import get_cotes_match, formater_comparateur_bookmakers
from core.utils.logs import log_info, log_error


def enregistrer_bookmakers_handlers(bot):

    @bot.message_handler(commands=['cotes'])
    def cmd_cotes(message):
        args = message.text.split(maxsplit=1)
        
        if len(args) < 2:
            bot.reply_to(
                message,
                "⚠️ Utilise : <code>/cotes EQUIPE1 vs EQUIPE2 [SPORT]</code>\n"
                "Exemple : <code>/cotes Chelsea vs Arsenal</code>\n"
                "Sports : <code>soccer_epl</code> (défaut), <code>soccer_spain_la_liga</code>, etc.",
                parse_mode="HTML"
            )
            return

        try:
            parties = args[1].split(" vs ")
            if len(parties) != 2:
                bot.reply_to(message, "❌ Format : <code>/cotes Equipe1 vs Equipe2</code>", parse_mode="HTML")
                return

            home_team = parties[0].strip()
            
            # On sépare l'équipe extérieure du sport éventuel
            away_parts = parties[1].split()
            away_team = away_parts[0].strip()
            sport = away_parts[1] if len(away_parts) > 1 else "soccer_epl"

            bot.reply_to(message, f"⏳ Récupération des cotes pour <b>{home_team} vs {away_team}</b>...", parse_mode="HTML")

            resultats = get_cotes_match(home_team, away_team, sport)
            
            texte = formater_comparateur_bookmakers(home_team, away_team, resultats)
            
            bot.reply_to(message, texte, parse_mode="HTML")

        except Exception as e:
            log_error("Erreur commande /cotes", "BOOKMAKERS", exception=e)
            bot.reply_to(message, "❌ Erreur lors de l'analyse des cotes.")
