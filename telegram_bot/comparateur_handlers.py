# telegram_bot/comparateur_handlers.py
"""
Handler pour la commande /comparer.
Compare les performances domicile/extérieur d'une équipe.
"""

import telebot
from core.comparateur import analyser_domicile_exterieur, formater_comparateur
from core.utils.logs import log_info, log_error


def enregistrer_comparateur_handlers(bot):

    @bot.message_handler(commands=['comparer'])
    def cmd_comparer(message):
        args = message.text.split(maxsplit=1)
        
        if len(args) < 2:
            bot.reply_to(
                message,
                "⚠️ Utilise : <code>/comparer NOM_EQUIPE</code>\n"
                "Exemple : <code>/comparer Chelsea</code>",
                parse_mode="HTML"
            )
            return

        nom_equipe = args[1].strip()
        bot.reply_to(message, f"⏳ Analyse de <b>{nom_equipe}</b>...", parse_mode="HTML")

        try:
            stats = analyser_domicile_exterieur(nom_equipe)
            texte = formater_comparateur(stats)
            bot.reply_to(message, texte, parse_mode="HTML")
        except Exception as e:
            log_error(f"Erreur commande /comparer pour {nom_equipe}", "COMPARATEUR", exception=e)
            bot.reply_to(message, "❌ Erreur lors de l'analyse.")
