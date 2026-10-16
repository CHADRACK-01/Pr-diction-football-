import telebot
from datetime import datetime, timedelta

from users import (
    get_langue, set_premium, ajouter_jours_premium,
    creer_demande_paiement, utiliser_code,
    est_administrateur, get_user_info, get_tous_admins,
    valider_demande, get_demande, refuser_demande
)
from core.payments import ABONNEMENTS, envoyer_facture
from core.translations import get_text


# Coordonnées Mobile Money
COORDONNEES_MOBILE = {
    "Airtel Money": "+243 8XX XXX XXX",
    "Orange Money": "+243 8XX XXX XXX",
    "M-Pesa": "+243 8XX XXX XXX",
}


def enregistrer_payment_handlers(bot):

    # =========================================================
    # CALLBACK : Choix du mode de paiement
    # =========================================================
    @bot.callback_query_handler(func=lambda call: call.data.startswith("pay|"))
    def traiter_choix_paiement(call):
        user_id = call.from_user.id
        langue = get_langue(user_id)
        action = call.data.split("|")[1]

        bot.answer_callback_query(call.id, "OK")

        # --- Telegram Stars ---
        if action == "stars":
            markup = telebot.types.InlineKeyboardMarkup(row_width=1)
            markup.add(
                telebot.types.InlineKeyboardButton(
                    f"Journalier - {ABONNEMENTS['journalier']['prix_stars']} Stars",
                    callback_data="buy|journalier"
                ),
                telebot.types.InlineKeyboardButton(
                    f"Hebdomadaire - {ABONNEMENTS['hebdomadaire']['prix_stars']} Stars",
                    callback_data="buy|hebdomadaire"
                ),
                telebot.types.InlineKeyboardButton(
                    f"Mensuel - {ABONNEMENTS['mensuel']['prix_stars']} Stars",
                    callback_data="buy|mensuel"
                ),
            )
            bot.send_message(
                call.message.chat.id,
                get_text("premium_titre", langue),
                reply_markup=markup
            )

        # --- Mobile Money ---
        elif action == "mobile":
            markup = telebot.types.InlineKeyboardMarkup(row_width=1)
            markup.add(
                telebot.types.InlineKeyboardButton("Journalier - 2 000 CDF", callback_data="paym|journalier"),
                telebot.types.InlineKeyboardButton("Hebdomadaire - 6 000 CDF", callback_data="paym|hebdomadaire"),
                telebot.types.InlineKeyboardButton("Mensuel - 10 000 CDF", callback_data="paym|mensuel"),
            )
            bot.send_message(
                call.message.chat.id,
                "MOBILE MONEY\n\nChoisis ton abonnement :",
                reply_markup=markup
            )

        # --- Code Premium ---
        elif action == "code":
            msg = bot.send_message(
                call.message.chat.id,
                get_text("pay_code_titre", langue) + "\n\nTape /annuler pour annuler."
            )
            bot.register_next_step_handler(msg, _traiter_code)


    # =========================================================
    # CALLBACK : Choix abonnement Mobile Money
    # =========================================================
    @bot.callback_query_handler(func=lambda call: call.data.startswith("paym|"))
    def traiter_abo_mobile(call):
        user_id = call.from_user.id
        langue = get_langue(user_id)
        abo_key = call.data.split("|")[1]

        if abo_key not in ABONNEMENTS:
            bot.answer_callback_query(call.id, "Inconnu")
            return

        abo = ABONNEMENTS[abo_key]
        montant_cdf = int(abo['prix_stars']) * 40

        bot.answer_callback_query(call.id, "OK")

        texte = get_text(
            "pay_mobile_titre", langue,
            montant=montant_cdf,
            abo=abo['nom']
        )
        texte += "\n\n"
        for nom, numero in COORDONNEES_MOBILE.items():
            texte += f"📱 {nom} : {numero}\n"

        bot.send_message(call.message.chat.id, texte)


    # =========================================================
    # TRAITEMENT DU CODE PREMIUM
    # =========================================================
    def _traiter_code(message):
        user_id = message.from_user.id
        langue = get_langue(user_id)
        code = message.text.strip().upper()

        if code == "/ANNULER":
            bot.reply_to(message, "Annule.")
            return

        resultat = utiliser_code(code, user_id)

        if "erreur" in resultat:
            bot.reply_to(
                message,
                get_text("pay_code_erreur", langue, erreur=resultat['erreur'])
            )
            return

        jours = resultat['jours']
        ajouter_jours_premium(user_id, jours)
        bot.reply_to(
            message,
            get_text("pay_code_ok", langue, jours=jours)
        )


    # =========================================================
    # RÉCEPTION DE LA CAPTURE (photo)
    # =========================================================
    @bot.message_handler(content_types=['photo'])
    def recevoir_capture(message):
        user_id = message.from_user.id
        langue = get_langue(user_id)

        file_id = message.photo[-1].file_id

        abo_key = "journalier"
        abo = ABONNEMENTS[abo_key]
        montant = int(abo['prix_stars']) * 40

        demande_id = creer_demande_paiement(user_id, abo_key, montant, file_id)

        if not demande_id:
            bot.reply_to(message, "Erreur lors de l'enregistrement.")
            return

        bot.reply_to(
            message,
            get_text("pay_attente_titre", langue)
        )

        admins = get_tous_admins()
        user_info = get_user_info(user_id)
        nom_user = user_info['first_name'] if user_info else "Utilisateur"

        markup = telebot.types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            telebot.types.InlineKeyboardButton("✅ Valider", callback_data=f"vpay|{demande_id}"),
            telebot.types.InlineKeyboardButton("❌ Refuser", callback_data=f"rpay|{demande_id}")
        )

        caption = (
            f"NOUVELLE DEMANDE #{demande_id}\n\n"
            f"User : {nom_user}\nID : {user_id}\n"
            f"Abo : {abo['nom']}\nMontant : {montant} CDF"
        )

        # Notifier admin principal
        try:
            bot.send_photo(8653408729, file_id, caption=caption, reply_markup=markup)
        except Exception as e:
            print(f"⚠️ Erreur notif admin principal : {e}")

        # Notifier les autres admins
        for a in admins:
            if a['user_id'] == 8653408729:
                continue
            try:
                bot.send_photo(a['user_id'], file_id, caption=caption, reply_markup=markup)
            except Exception as e:
                print(f"⚠️ Erreur notif admin {a['user_id']} : {e}")


    # =========================================================
    # CALLBACK : Valider paiement
    # =========================================================
    @bot.callback_query_handler(func=lambda call: call.data.startswith("vpay|"))
    def valider_paiement(call):
        if not est_administrateur(call.from_user.id):
            bot.answer_callback_query(call.id, "Acces refuse")
            return

        demande_id = int(call.data.split("|")[1])
        demande = get_demande(demande_id)

        if not demande:
            bot.answer_callback_query(call.id, "Demande introuvable")
            return

        if valider_demande(demande_id, call.from_user.id):
            jours = 30
            if demande['abonnement'] == 'journalier':
                jours = 1
            elif demande['abonnement'] == 'hebdomadaire':
                jours = 7
            elif demande['abonnement'] == 'mensuel':
                jours = 30

            ajouter_jours_premium(demande['user_id'], jours)

            bot.answer_callback_query(call.id, "Valide !")
            bot.send_message(
                call.message.chat.id,
                f"✅ Paiement #{demande_id} valide. +{jours}j pour user {demande['user_id']}"
            )

            try:
                langue = get_langue(demande['user_id'])
                bot.send_message(
                    demande['user_id'],
                    get_text("pay_valide", langue, jours=jours)
                )
            except Exception:
                pass


    # =========================================================
    # CALLBACK : Refuser paiement
    # =========================================================
    @bot.callback_query_handler(func=lambda call: call.data.startswith("rpay|"))
    def refuser_paiement(call):
        if not est_administrateur(call.from_user.id):
            bot.answer_callback_query(call.id, "Acces refuse")
            return

        demande_id = int(call.data.split("|")[1])
        demande = get_demande(demande_id)

        if not demande:
            bot.answer_callback_query(call.id, "Demande introuvable")
            return

        if refuser_demande(demande_id, call.from_user.id):
            bot.answer_callback_query(call.id, "Refuse !")
            bot.send_message(
                call.message.chat.id,
                f"❌ Paiement #{demande_id} refuse."
            )

            try:
                langue = get_langue(demande['user_id'])
                bot.send_message(
                    demande['user_id'],
                    get_text("pay_refuse", langue)
                )
            except Exception:
                pass


    # =========================================================
    # PAIEMENT TELEGRAM STARS
    # =========================================================
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


    @bot.pre_checkout_query_handler(func=lambda query: True)
    def process_pre_checkout(pre_checkout_query):
        try:
            bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)
        except Exception as e:
            print(f"Erreur pre_checkout : {e}")


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

            bot.send_message(
                user_id,
                f"PAIEMENT CONFIRME\n\n"
                f"Formule : {nom_abo}\n"
                f"Duree : {duree} jour(s)\n"
                f"Expire : {expiration}"
            )
            print(f"Paiement Stars valide : user {user_id} - {nom_abo}")

        except Exception as e:
            print(f"Erreur traitement paiement : {str(e)}")
