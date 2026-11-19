# telegram_bot/codes_promo_handlers.py
"""
Handler admin pour créer des codes promo.
Commande : /codepromo CODE TYPE VALEUR [LIMITE] [JOURS]

Exemples :
  /codepromo CAN2026 pourcentage 30 100        → 100 utilisations, 1 jour offert
  /codepromo BIENVENUE fixe 2000               → illimité, 1 jour offert
  /codepromo VIP pourcentage 50 10 7           → 10 utilisations, 7 jours offerts
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
                "Utilise : <code>/codepromo CODE TYPE VALEUR [LIMITE] [JOURS]</code>\n\n"
                "• <b>TYPE</b> : <code>pourcentage</code> ou <code>fixe</code>\n"
                "• <b>VALEUR</b> : nombre positif\n"
                "• <b>LIMITE</b> : nombre d'utilisations max (0 = illimité, défaut)\n"
                "• <b>JOURS</b> : jours Premium offerts (défaut 1)\n\n"
                "Exemples :\n"
                "<code>/codepromo CAN2026 pourcentage 30 100</code>\n"
                "<code>/codepromo BIENVENUE fixe 2000</code>\n"
                "<code>/codepromo VIP pourcentage 50 10 7</code>",
                parse_mode="HTML"
            )
            return

        code = args[1].upper()
        type_reduction = args[2].lower()

        try:
            valeur = float(args[3])
            limite = int(args[4]) if len(args) > 4 else 0
            jours = int(args[5]) if len(args) > 5 else 1
        except ValueError:
            bot.reply_to(message, "❌ VALEUR, LIMITE et JOURS doivent être des nombres.")
            return

        if type_reduction not in ("pourcentage", "fixe"):
            bot.reply_to(message, "❌ TYPE doit être 'pourcentage' ou 'fixe'.")
            return

        succes = creer_code_promo(
            code, type_reduction, valeur,
            limite_utilisation=limite,
            jours_premium=jours,
        )

        if succes:
            bot.reply_to(
                message,
                f"✅ Code <b>{code}</b> créé !\n"
                f"Type : {type_reduction}\n"
                f"Valeur : {valeur}\n"
                f"Limite : {'Illimitée' if limite == 0 else limite}\n"
                f"Jours Premium offerts : {jours}",
                parse_mode="HTML"
            )
            log_info(
                f"Code promo {code} créé par admin {user_id}",
                "CODES_PROMO",
                user_context={"user_id": user_id},
                extra={"code": code, "type": type_reduction, "jours": jours},
            )
        else:
            bot.reply_to(
                message,
                f"❌ Impossible de créer le code {code}.\n"
                f"Il existe peut-être déjà, ou les paramètres sont invalides."
            )
