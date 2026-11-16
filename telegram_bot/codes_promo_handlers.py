# telegram_bot/codes_promo_handlers.py
"""
Handler admin pour créer des codes promo.
Commande : /codepromo CODE TYPE VALEUR [LIMITE]
Exemple : /codepromo CAN2026 pourcentage 30 100
"""

import telebot
from users import est_administrateur
from core.codes_promo import creer_code_promo
from core.utils.logs import log_info, log_error, log_warning


def enregistrer_codes_promo_handlers(bot):

    @bot.message_handler(commands=['codepromo'])
    def cmd_codepromo(message):
        user_id = message.from_user.id
        
        if not est_administrateur(user_id):
            bot.reply_to(message, "⛔ Commande réservée aux administrateurs.")
            return

        args = message.text.split()
        if len(args) < 4:
            bot.reply_to(
                message,
                "⚠️ <b>Format incorrect.</b>\n\n"
                "Utilise : <code>/codepromo CODE TYPE VALEUR [LIMITE]</code>\n\n"
                "Exemples :\n"
                "<code>/codepromo CAN2026 pourcentage 30 100</code>\n"
                "<code>/codepromo BIENVENUE fixe 2000</code>",
                parse_mode="HTML"
            )
            return

        code = args[1].upper()
        type_reduction = args[2].lower()
        try:
            valeur = float(args[3])
            limite = int(args[4]) if len(args) > 4 else 0
        except ValueError:
            bot.reply_to(message, "❌ VALEUR et LIMITE doivent être des nombres.")
            return

        if type_reduction not in ("pourcentage", "fixe"):
            bot.reply_to(message, "❌ TYPE doit être 'pourcentage' ou 'fixe'.")
            return

        succes = creer_code_promo(code, type_reduction, valeur, limite)
        
        if succes:
            bot.reply_to(
                message,
                f"✅ Code <b>{code}</b> créé !\n"
                f"Type : {type_reduction}\n"
                f"Valeur : {valeur}\n"
                f"Limite : {'Illimitée' if limite == 0 else limite}",
                parse_mode="HTML"
            )
        else:
            bot.reply_to(message, f"❌ Impossible de créer le code {code}. Il existe peut-être déjà.")
