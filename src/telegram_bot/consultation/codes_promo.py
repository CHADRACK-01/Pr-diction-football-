"""Handlers Telegram pour la création et l'utilisation des codes promotionnels."""

from core.engagement.codes_promo import (
    annuler_utilisation_promo,
    creer_code_promo,
    valider_code_promo,
)
from core.utils.logs import log_error, log_info
from users.admin import est_administrateur
from users.credits import crediter_premium, deja_credite


def enregistrer_codes_promo_handlers(bot):
    @bot.message_handler(commands=["codepromo"])
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
                parse_mode="HTML",
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
            code,
            type_reduction,
            valeur,
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
                parse_mode="HTML",
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
                "Il existe peut-être déjà, ou les paramètres sont invalides.",
            )


def enregistrer_utilisation_code_handlers(bot):
    @bot.message_handler(commands=["utilisercode"])
    def cmd_utilisercode(message):
        user_id = message.from_user.id
        args = message.text.split()

        if len(args) < 2:
            bot.reply_to(
                message,
                "⚠️ Utilise : <code>/utilisercode TON_CODE</code>",
                parse_mode="HTML",
            )
            return

        code = args[1].upper()

        if deja_credite(f"codepromo:{code}:{user_id}"):
            bot.reply_to(message, "❌ Tu as déjà utilisé ce code.")
            return

        resultat = valider_code_promo(code, user_id)

        if not resultat.get("valide"):
            bot.reply_to(message, f"❌ {resultat.get('message', 'Code invalide.')}")
            return

        jours = resultat.get("jours_premium", 1)
        type_reduction = resultat.get("type_reduction")
        valeur = resultat.get("valeur")

        try:
            resultat_credit = crediter_premium(
                f"codepromo:{code}:{user_id}",
                user_id,
                jours,
                "codepromo",
            )
        except Exception as exc:
            log_error(
                message="Erreur application code promo",
                module="CODES_PROMO",
                user_context={"user_id": user_id},
                exception=exc,
            )
            resultat_credit = "echec"

        if resultat_credit != "ok":
            annuler_utilisation_promo(code)
            if resultat_credit == "deja":
                bot.reply_to(message, "❌ Tu as déjà utilisé ce code.")
            else:
                log_error(
                    message="Code validé mais ajout Premium échoué",
                    module="CODES_PROMO",
                    user_context={"user_id": user_id},
                    extra={"code": code, "jours": jours},
                )
                bot.reply_to(
                    message,
                    "❌ Le code n'a pas pu être appliqué (erreur technique). "
                    "Il n'a pas été consommé, réessaie plus tard.",
                )
            return

        bot.reply_to(
            message,
            f"✅ Code <b>{code}</b> validé !\n\n"
            f"🎁 +{jours} jour(s) Premium offert(s)\n"
            f"Réduction commerciale : {valeur} ({type_reduction})",
            parse_mode="HTML",
        )
        log_info(
            f"Code {code} utilisé par {user_id} (+{jours}j)",
            "CODES_PROMO",
            user_context={"user_id": user_id},
            extra={"code": code, "jours": jours},
        )
