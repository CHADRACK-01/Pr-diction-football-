# telegram_bot/bankroll_handlers.py
"""
Handler pour la commande /bankroll.
Permet de gérer sa bankroll et de calculer les mises.
"""

import telebot
from core.bankroll import set_bankroll, get_bankroll, calculer_mise, formater_bankroll
from core.utils.logs import log_info, log_error


def enregistrer_bankroll_handlers(bot):

    @bot.message_handler(commands=['bankroll'])
    def cmd_bankroll(message):
        user_id = message.from_user.id
        args = message.text.split()

        if len(args) < 2:
            # Afficher la bankroll actuelle
            bankroll = get_bankroll(user_id)
            if not bankroll:
                bot.reply_to(
                    message,
                    "⚠️ Tu n'as pas encore défini ta bankroll.\n\n"
                    "Utilise : <code>/bankroll MONTANT [STRATEGIE]</code>\n"
                    "Exemples :\n"
                    "<code>/bankroll 50000</code>\n"
                    "<code>/bankroll 50000 fixe</code>\n"
                    "<code>/bankroll 50000 kelly_fractionne</code>",
                    parse_mode="HTML"
                )
            else:
                texte = f"💰 <b>TA BANKROLL</b>\n\n"
                texte += f"💵 Montant : {bankroll['montant_total']:,.0f} CDF\n"
                texte += f"📊 Stratégie : {bankroll['strategie']}\n"
                texte += f"📈 Pourcentage de mise : {bankroll['pourcentage_mise']}%"
                bot.reply_to(message, texte, parse_mode="HTML")
            return

        try:
            montant = float(args[1])
            strategie = args[2].lower() if len(args) > 2 else "kelly_fractionne"

            if strategie not in ("kelly_fractionne", "fixe"):
                bot.reply_to(message, "❌ Stratégie invalide. Utilise 'kelly_fractionne' ou 'fixe'.")
                return

            succes = set_bankroll(user_id, montant, strategie)
            
            if succes:
                bot.reply_to(
                    message,
                    f"✅ Bankroll mise à jour !\n\n"
                    f"💵 Montant : {montant:,.0f} CDF\n"
                    f"📊 Stratégie : {strategie}\n\n"
                    f"Utilise <code>/mise PROBA COTE</code> pour calculer ta prochaine mise.",
                    parse_mode="HTML"
                )
            else:
                bot.reply_to(message, "❌ Erreur lors de l'enregistrement.")

        except ValueError:
            bot.reply_to(message, "❌ Le montant doit être un nombre.")

    @bot.message_handler(commands=['mise'])
    def cmd_mise(message):
        user_id = message.from_user.id
        args = message.text.split()

        if len(args) < 3:
            bot.reply_to(
                message,
                "⚠️ Utilise : <code>/mise PROBA COTE</code>\n"
                "Exemple : <code>/mise 0.65 2.10</code>",
                parse_mode="HTML"
            )
            return

        try:
            proba = float(args[1])
            cote = float(args[2])

            if proba > 1:
                proba = proba / 100  # Convertir 65 en 0.65

            bankroll = get_bankroll(user_id)
            if not bankroll:
                bot.reply_to(message, "❌ Tu dois d'abord définir ta bankroll avec /bankroll MONTANT")
                return

            mise, explication = calculer_mise(user_id, proba, cote)
            texte = formater_bankroll(bankroll, mise, explication)
            
            bot.reply_to(message, texte, parse_mode="HTML")

        except ValueError:
            bot.reply_to(message, "❌ La proba et la cote doivent être des nombres.")
