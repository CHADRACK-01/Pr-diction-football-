import telebot
from datetime import datetime, timezone, timedelta

from users import get_langue, est_premium, est_banni
from core.paris_builder import generer_coupons_du_jour, formater_coupon
from core.top_matches import get_top_affiches, formater_top_affiches


TZ_KINSHASA = timezone(timedelta(hours=1))


def enregistrer_premium_handlers(bot):

    # =========================================================
    # BOUTON : Coupons
    # =========================================================
    @bot.message_handler(func=lambda m: m.from_user and m.text in [
        "Coupons", "Coupons du jour", "Coupons ya lelo"
    ])
    def handle_coupons(message):
        user_id = message.from_user.id
        langue = get_langue(user_id)

        if est_banni(user_id):
            bot.reply_to(message, "Tu es banni.")
            return

        bot.reply_to(message, "Construction des coupons en cours...")

        try:
            data = generer_coupons_du_jour()
            coupons = data['coupons']

            if not coupons:
                bot.send_message(
                    message.chat.id,
                    "Aucun coupon disponible aujourd'hui."
                )
                return

            is_premium = est_premium(user_id)

            if is_premium:
                # Premium : tout voir
                for coupon in coupons:
                    texte = formater_coupon(coupon, langue, montrer_details=True)
                    bot.send_message(message.chat.id, texte)
            else:
                # Free : voir uniquement le coupon Modere sans details
                coupon_modere = next(
                    (c for c in coupons if c['niveau'] == 'modere'),
                    coupons[0]
                )
                texte = formater_coupon(coupon_modere, langue, montrer_details=False)
                bot.send_message(message.chat.id, texte)

        except Exception as e:
            import traceback
            print(f"ERREUR COUPONS :\n{traceback.format_exc()}")
            bot.send_message(message.chat.id, f"Erreur : {str(e)[:200]}")


    # =========================================================
    # BOUTON : Top affiches
    # =========================================================
    @bot.message_handler(func=lambda m: m.from_user and m.text in [
        "Top affiches", "Affiches du jour", "Affiches ya lelo"
    ])
    def handle_top_affiches(message):
        user_id = message.from_user.id
        langue = get_langue(user_id)

        if est_banni(user_id):
            bot.reply_to(message, "Tu es banni.")
            return

        bot.reply_to(message, "Recherche des meilleures affiches...")

        try:
            affiches = get_top_affiches(limite=10)

            if not affiches:
                bot.send_message(
                    message.chat.id,
                    "Aucune affiche a fort potentiel aujourd'hui."
                )
                return

            is_premium = est_premium(user_id)

            if is_premium:
                texte = formater_top_affiches(affiches, langue, montrer_details=True)
                bot.send_message(message.chat.id, texte)
            else:
                # Free : voir 1 seule affiche sans details
                texte = formater_top_affiches(affiches[:1], langue, montrer_details=False)
                bot.send_message(message.chat.id, texte)

        except Exception as e:
            import traceback
            print(f"ERREUR TOP AFFICHES :\n{traceback.format_exc()}")
            bot.send_message(message.chat.id, f"Erreur : {str(e)[:200]}")
