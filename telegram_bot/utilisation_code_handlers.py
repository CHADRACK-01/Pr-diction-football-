# telegram_bot/utilisation_code_handlers.py
"""
Handler utilisateur pour utiliser un code promo.
Commande : /utilisercode CODE

Le code accorde réellement les jours Premium stockés dans codes_promo.jours_premium.
"""

import telebot
from users import get_langue, ajouter_jours_premium
from users.credits import crediter_premium, deja_credite
from core.codes_promo import valider_code_promo
from core.utils.logs import log_info, log_error, log_warning


def enregistrer_utilisation_code_handlers(bot):

    @bot.message_handler(commands=['utilisercode'])
    def cmd_utilisercode(message):
        user_id = message.from_user.id
        args = message.text.split()

        if len(args) < 2:
            bot.reply_to(
                message,
                "⚠️ Utilise : <code>/utilisercode TON_CODE</code>",
                parse_mode="HTML"
            )
            return

        code = args[1].upper()

        # Un utilisateur ne peut utiliser un même code qu'une seule fois.
        # Vérifié AVANT valider_code_promo, qui incrémente le compteur du code.
        if deja_credite(f"codepromo:{code}:{user_id}"):
            bot.reply_to(message, "❌ Tu as déjà utilisé ce code.")
            return

        resultat = valider_code_promo(code, user_id)

        if not resultat.get("valide"):
            bot.reply_to(
                message,
                f"❌ {resultat.get('message', 'Code invalide.')}"
            )
            return

        jours = resultat.get("jours_premium", 1)
        type_reduction = resultat.get("type_reduction")
        valeur = resultat.get("valeur")

        # Application réelle des jours Premium
        try:
            if crediter_premium(f"codepromo:{code}:{user_id}", user_id, jours, "codepromo") == "echec":
                log_error(
                    message="Code validé mais ajout Premium échoué",
                    module="CODES_PROMO",
                    user_context={"user_id": user_id},
                    extra={"code": code, "jours": jours},
                )
                bot.reply_to(
                    message,
                    "❌ Code validé mais l'ajout Premium a échoué. "
                    "Contacte l'admin avec ce code : " + code
                )
                return
        except Exception as e:
            log_error(
                message="Erreur application code promo",
                module="CODES_PROMO",
                user_context={"user_id": user_id},
                exception=e,
            )
            bot.reply_to(
                message,
                "❌ Code validé mais erreur lors de l'application. "
                "Contacte l'admin avec ce code : " + code
            )
            return

        bot.reply_to(
            message,
            f"✅ Code <b>{code}</b> validé !\n\n"
            f"🎁 +{jours} jour(s) Premium offert(s)\n"
            f"Réduction commerciale : {valeur} ({type_reduction})",
            parse_mode="HTML"
        )
        log_info(
            f"Code {code} utilisé par {user_id} (+{jours}j)",
            "CODES_PROMO",
            user_context={"user_id": user_id},
            extra={"code": code, "jours": jours},
        )
