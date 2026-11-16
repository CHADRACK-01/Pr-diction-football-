# telegram_bot/utilisation_code_handlers.py
"""
Handler utilisateur pour utiliser un code promo.
Commande : /utilisercode CODE
"""

import telebot
from users import get_langue, ajouter_jours_premium
from core.codes_promo import valider_code_promo
from core.utils.logs import log_info, log_error


def enregistrer_utilisation_code_handlers(bot):

    @bot.message_handler(commands=['utilisercode'])
    def cmd_utilisercode(message):
        user_id = message.from_user.id
        args = message.text.split()
        
        if len(args) < 2:
            bot.reply_to(message, "⚠️ Utilise : <code>/utilisercode TON_CODE</code>", parse_mode="HTML")
            return

        code = args[1].upper()
        resultat = valider_code_promo(code, user_id)

        if not resultat.get("valide"):
            bot.reply_to(message, f"❌ {resultat.get('message', 'Code invalide.')}")
            return

        try:
            ajouter_jours_premium(user_id, 1)  # Exemple : 1 jour offert
            bot.reply_to(
                message,
                f"✅ Code <b>{code}</b> validé !\n"
                f"Réduction : {resultat.get('valeur')} ({resultat.get('type_reduction')})\n"
                f"🎁 +1 jour Premium offert !",
                parse_mode="HTML"
            )
            log_info(f"Code {code} utilisé par {user_id}", "CODES_PROMO")
        except Exception as e:
            log_error(f"Erreur application code promo", "CODES_PROMO", exception=e)
            bot.reply_to(message, "❌ Code validé mais erreur lors de l'application. Contacte l'admin.")
