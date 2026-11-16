# telegram_bot/favoris_handlers.py
"""
Handler pour la commande /favoris.
Permet de gérer ses équipes favorites.
"""

import telebot
from core.equipes_favorites import ajouter_favori, supprimer_favori, lister_favoris
from core.utils.logs import log_info, log_error


def enregistrer_favoris_handlers(bot):

    @bot.message_handler(commands=['favoris'])
    def cmd_favoris(message):
        user_id = message.from_user.id
        args = message.text.split(maxsplit=1)

        if len(args) < 2:
            # Afficher la liste des favoris
            favoris = lister_favoris(user_id)
            if not favoris:
                texte = "📋 <b>TES ÉQUIPES FAVORITES</b>\n\n"
                texte += "Tu n'as pas encore d'équipe favorite.\n\n"
                texte += "Utilise : <code>/favoris ajouter NOM_EQUIPE</code>"
            else:
                texte = "📋 <b>TES ÉQUIPES FAVORITES</b>\n\n"
                for i, equipe in enumerate(favoris, 1):
                    texte += f"{i}. {equipe}\n"
                texte += f"\n📊 {len(favoris)}/5 équipes\n"
                texte += "\nPour supprimer : <code>/favoris supprimer NOM_EQUIPE</code>"

            bot.reply_to(message, texte, parse_mode="HTML")
            return

        action = args[1].split(maxsplit=1)
        if len(action) < 2:
            bot.reply_to(message, "❌ Format : <code>/favoris ajouter/supprimer NOM_EQUIPE</code>", parse_mode="HTML")
            return

        commande = action[0].lower()
        equipe = action[1].strip()

        if commande == "ajouter":
            succes, msg = ajouter_favori(user_id, equipe)
            bot.reply_to(message, msg)
        elif commande == "supprimer":
            succes, msg = supprimer_favori(user_id, equipe)
            bot.reply_to(message, msg)
        else:
            bot.reply_to(message, "❌ Commande inconnue. Utilise 'ajouter' ou 'supprimer'.")
