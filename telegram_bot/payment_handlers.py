import telebot
from datetime import datetime, timedelta

from users import get_langue, set_premium
from core.payments import ABONNEMENTS, envoyer_facture


def enregistrer_payment_handlers(bot):

    # Callback de choix de formule
    @bot.callback_query_handler(func=lambda call: call.data.startswith("buy|"))
    def traiter_achat(call):
        user_id = call.from_user.id
        abo_key = call.data.split("|")[1]

        if abo_key not in ABONNEMENTS:
            bot.answer_callback_query(call.id, "Formule inconnue.")
            return

        abo = ABONNEMENTS[abo_key]
        bot.answer_callback_query(call.id, f"{abo['nom']}")

        envoyer_facture(bot, call.message.chat.id, abo_key, user_id)


    # Pre-checkout (obligatoire)
    @bot.pre_checkout_query_handler(func=lambda query: True)
    def process_pre_checkout(pre_checkout_query):
        try:
            bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)
        except Exception as e:
            print(f"Erreur pre_checkout : {e}")


    # Paiement réussi
    @bot.message_handler(content_types=['successful_payment'])
    def process_successful_payment(message):
        try:
            payment = message.successful_payment
            user_id = message.from_user.id
            payload = payment.invoice_payload

            parts = payload.split("_")
            abo_key = parts[1] if len(parts) >= 2 else "mensuel"

            if abo_key not in ABONNEMENTS:
                abo_key = "mensuel"

            abo = ABONNEMENTS[abo_key]
            duree = abo["duree_jours"]
            nom_abo = abo["nom"]

            expiration = (datetime.now() + timedelta(days=duree)).strftime("%Y-%m-%d %H:%M")
            set_premium(user_id, expiration)

            langue = get_langue(user_id)

            if langue == "en":
                texte = (
                    f"PAYMENT CONFIRMED\n\n"
                    f"Plan: {nom_abo}\n"
                    f"Duration: {duree} day(s)\n"
                    f"Expires: {expiration}\n\n"
                    f"Enjoy your unlimited predictions!"
                )
            elif langue == "ln":
                texte = (
                    f"MBONGO EZALI\n\n"
                    f"Formule: {nom_abo}\n"
                    f"Duree: {duree} mokolo\n"
                    f"Ekosila: {expiration}\n\n"
                    f"Kende na bokano!"
                )
            else:
                texte = (
                    f"PAIEMENT CONFIRME\n\n"
                    f"Formule : {nom_abo}\n"
                    f"Duree : {duree} jour(s)\n"
                    f"Expire : {expiration}\n\n"
                    f"Profite de tes pronostics illimites !"
                )

            bot.send_message(user_id, texte)
            print(f"Paiement Stars valide : user {user_id} - {nom_abo} - {payment.total_amount} Stars")

        except Exception as e:
            print(f"Erreur traitement paiement : {e}")
            bot.send_message(message.chat.id, f"Erreur : {str(e)}")
