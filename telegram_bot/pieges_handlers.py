# telegram_bot/pieges_handlers.py
"""
Handler pour la commande /piege.
Détecte si un match est un piège potentiel.
"""

import telebot
from core.pieges import detecter_piege, formater_alerte_piege
from core.utils.logs import log_info, log_error


def enregistrer_pieges_handlers(bot):

    @bot.message_handler(commands=['piege'])
    def cmd_piege(message):
        args = message.text.split(maxsplit=1)
        
        if len(args) < 2:
            bot.reply_to(
                message,
                "⚠️ Utilise : <code>/piege EQUIPE1 vs EQUIPE2</code>\n"
                "Exemple : <code>/piege Real Madrid vs Barcelona</code>",
                parse_mode="HTML"
            )
            return

        try:
            match = args[1].split(" vs ")
            if len(match) != 2:
                bot.reply_to(message, "❌ Format : <code>/piege Equipe1 vs Equipe2</code>", parse_mode="HTML")
                return

            home_team = match[0].strip()
            away_team = match[1].strip()

            bot.reply_to(message, f"⏳ Analyse de <b>{home_team} vs {away_team}</b>...", parse_mode="HTML")

            resultat = detecter_piege(home_team, away_team)
            
            if resultat["est_piege"]:
                texte = f"⚠️ <b>ATTENTION : MATCH PIÈGE</b>\n\n"
                texte += f"🏟️ {home_team} vs {away_team}\n\n"
                texte += f"🔍 <b>Raisons :</b>\n{resultat['raison']}\n\n"
                texte += "💡 <i>Sois prudent sur ce match.</i>"
            else:
                texte = f"✅ <b>Match sans piège détecté</b>\n\n"
                texte += f"🏟️ {home_team} vs {away_team}\n\n"
                texte += "💡 <i>Ce match ne présente pas de risque particulier.</i>"

            bot.reply_to(message, texte, parse_mode="HTML")

        except Exception as e:
            log_error("Erreur commande /piege", "PIEGES", exception=e)
            bot.reply_to(message, "❌ Erreur lors de l'analyse.")
