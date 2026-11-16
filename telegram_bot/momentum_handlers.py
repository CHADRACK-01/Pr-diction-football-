# telegram_bot/momentum_handlers.py
"""
Handler pour la commande /serie.
Affiche la série actuelle d'une équipe.
"""

import telebot
from core.momentum import calculer_serie_equipe, formater_serie
from core.utils.logs import log_info, log_error


def enregistrer_momentum_handlers(bot):

    @bot.message_handler(commands=['serie'])
    def cmd_serie(message):
        args = message.text.split(maxsplit=1)
        
        if len(args) < 2:
            bot.reply_to(
                message,
                "⚠️ Utilise : <code>/serie NOM_EQUIPE</code>\n"
                "Exemple : <code>/serie Bayern Munich</code>",
                parse_mode="HTML"
            )
            return

        nom_equipe = args[1].strip()
        bot.reply_to(message, f"⏳ Analyse de la série de <b>{nom_equipe}</b>...", parse_mode="HTML")

        try:
            resultat = calculer_serie_equipe(nom_equipe)
            texte = formater_serie(nom_equipe, resultat)
            bot.reply_to(message, texte, parse_mode="HTML")
        except Exception as e:
            log_error(f"Erreur calcul série pour {nom_equipe}", "MOMENTUM", exception=e)
            bot.reply_to(message, "❌ Erreur lors de l'analyse.")
