# telegram_bot/fiabilite_handlers.py
"""
Handler pour la commande /fiabilite.
Affiche le taux de réussite par championnat.
"""

import telebot
from core.fiabilite import calculer_fiabilite_par_championnat, formater_fiabilite
from core.utils.logs import log_info, log_error


def enregistrer_fiabilite_handlers(bot):

    @bot.message_handler(commands=['fiabilite'])
    def cmd_fiabilite(message):
        bot.reply_to(message, "⏳ Analyse des résultats par championnat...")

        try:
            resultats = calculer_fiabilite_par_championnat()
            texte = formater_fiabilite(resultats)
            bot.reply_to(message, texte, parse_mode="HTML")
        except Exception as e:
            log_error("Erreur commande /fiabilite", "FIABILITE", exception=e)
            bot.reply_to(message, "❌ Erreur lors de l'analyse.")
