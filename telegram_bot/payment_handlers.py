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
from core.utils.logs import log_info, log_error, log_warning

COORDONNEES_MOBILE = {
    "Airtel Money": "Fonctionnalité à venir",
    "Orange Money": "+243 842 453 217",
    "M-Pesa": "Fonctionnalité à venir",
}

PAIEMENT_SESSIONS = {}


def enregistrer_payment_handlers(bot):

    # =========================================================
    # CALLBACK : Choix du mode de paiement
    # =========================================================
    @bot.callback_query_handler(func=lambda call: call.data.startswith("pay|"))
    def traiter_choix_paiement(call):
        user_id = call.from_user.id
        log_info(f"Choix paiement de {user_id} : {call.data}", "PAIEMENT")

        try:
            langue = get_langue(user_id)
        except Exception as e:
            log_error(f"Impossible de récupérer la langue de {user_id}", "PAIEMENT", exception=e)
            langue = "fr"

        try:
            bot.answer_callback_query(call.id, "OK")
        except Exception as e:
            log_warning(f"Impossible de répondre au callback {call.id} : {e}", "PAIEMENT")

        action = call.data.split("|")[1]

        try:
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
                bot.send_message(call.message.chat.id, get_text("premium_titre", langue), reply_markup=markup)

            elif action == "mobile":
                markup = telebot.types.InlineKeyboardMarkup(row_width=1)
                markup.add(
                    telebot.types.InlineKeyboardButton("Journalier - 2 000 CDF", callback_data="paym|journalier"),
                    telebot.types.InlineKeyboardButton("Hebdomadaire - 6 000 CDF", callback_data="paym|hebdomadaire"),
                    telebot.types.InlineKeyboardButton("Mensuel - 10 000 CDF", callback_data="paym|mensuel"),
                )
                bot.send_message(call.message.chat.id, "📱 **MOBILE MONEY**\n\nChoisis ton abonnement :", 
                                 reply_markup=markup, parse_mode="Markdown")

            elif action == "code":
                msg = bot.send_message(
                    call.message.chat.id,
                    get_text("pay_code_titre", langue) + "\n\nTape /annuler pour annuler."
                )
                bot.register_next_step_handler(msg, _traiter_code)

        except Exception as e:
            log_error(f"Erreur lors du choix de paiement pour {user_id}", "PAIEMENT", exception=e)
            try:
                bot.send_message(call.message.chat.id, "❌ Une erreur est survenue. Réessaie.")
            except Exception:
                pass

    # =========================================================
    # CALLBACK : Choix abonnement Mobile Money
    # =========================================================
    @bot.callback_query_handler(func=lambda call: call.data.startswith("paym|"))
    def traiter_abo_mobile(call):
        user_id = call.from_user.id
        abo_key = call.data.split("|")[1]

        if abo_key not in ABONNEMENTS:
            log_warning(f"Abonnement inconnu '{abo_key}' demandé par {user_id}", "PAIEMENT")
            try:
                bot.answer_callback_query(call.id, "Inconnu")
            except Exception:
                pass
            return

        try:
            langue = get_langue(user_id)
        except Exception as e:
            log_error(f"Impossible de récupérer la langue de {user_id}", "PAIEMENT", exception=e)
            langue = "fr"

        PAIEMENT_SESSIONS[user_id] = abo_key
        abo = ABONNEMENTS[abo_key]
        montant_cdf = int(abo['prix_stars']) * 40

        try:
            bot.answer_callback_query(call.id, "OK")
        except Exception as e:
            log_warning(f"Impossible de répondre au callback {call.id} : {e}", "PAIEMENT")

        texte = get_text("pay_mobile_titre", langue, montant=montant_cdf, abo=abo['nom'])
        texte += "\n\n"
        for nom, numero in COORDONNEES_MOBILE.items():
            texte += f"📱 {nom} : {numero}\n"

        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton("📸 J'ai payé (Envoyer la preuve)", callback_data="preuve_ok"))

        try:
            bot.send_message(call.message.chat.id, texte, reply_markup=markup)
        except Exception as e:
            log_error(f"Impossible d'envoyer le menu Mobile Money à {user_id}", "PAIEMENT", exception=e)

    # =========================================================
    # CALLBACK : Demander la preuve
    # =========================================================
    @bot.callback_query_handler(func=lambda call: call.data == "preuve_ok")
    def demander_preuve(call):
        try:
            bot.answer_callback_query(call.id, "OK")
        except Exception as e:
            log_warning(f"Impossible de répondre au callback preuve_ok : {e}", "PAIEMENT")
        
        try:
            msg = bot.send_message(call.message.chat.id, "📸 Envoie la capture d'écran de ton paiement :")
            bot.register_next_step_handler(msg, recevoir_capture)
        except Exception as e:
            log_error(f"Impossible de demander la preuve à {call.from_user.id}", "PAIEMENT", exception=e)

    # =========================================================
    # TRAITEMENT DU CODE PREMIUM
    # =========================================================
    def _traiter_code(message):
        user_id = message.from_user.id
        
        try:
            langue = get_langue(user_id)
        except Exception as e:
            log_error(f"Impossible de récupérer la langue de {user_id}", "PAIEMENT", exception=e)
            langue = "fr"

        code = message.text.strip().upper() if message.text else ""

        if code == "/ANNULER":
            bot.reply_to(message, "Annulé.")
            return

        try:
            resultat = utiliser_code(code, user_id)
        except Exception as e:
            log_error(f"Impossible d'utiliser le code '{code}' pour {user_id}", "PAIEMENT", exception=e)
            bot.reply_to(message, "❌ Une erreur est survenue. L'admin a été prévenu.")
            return

        if "erreur" in resultat:
            bot.reply_to(message, get_text("pay_code_erreur", langue, erreur=resultat['erreur']))
            return

        try:
            jours = resultat['jours']
            ajouter_jours_premium(user_id, jours)
            bot.reply_to(message, get_text("pay_code_ok", langue, jours=jours))
            log_info(f"Code Premium utilisé par {user_id} (+{jours} jours)", "PAIEMENT")
        except Exception as e:
            log_error(f"Impossible d'ajouter les jours Premium à {user_id}", "PAIEMENT", exception=e)
            bot.reply_to(message, "❌ Le code a été validé, mais l'ajout a échoué. Contacte l'admin.")

    # =========================================================
    # RÉCEPTION DE LA CAPTURE (photo)
    # =========================================================
    def recevoir_capture(message):
        user_id = message.from_user.id
        
        try:
            langue = get_langue(user_id)
        except Exception as e:
            log_error(f"Impossible de récupérer la langue de {user_id}", "PAIEMENT", exception=e)
            langue = "fr"

        # Vérification stricte de la photo
        if not message.photo or len(message.photo) == 0:
            log_warning(f"Capture invalide envoyée par {user_id}", "PAIEMENT")
            bot.reply_to(message, "❌ Ce n'est pas une photo valide. Action annulée.")
            return

        file_id = message.photo[-1].file_id
        abo_key = PAIEMENT_SESSIONS.get(user_id, "journalier")
        
        if abo_key not in ABONNEMENTS:
            log_warning(f"Abonnement inconnu '{abo_key}' pour {user_id}", "PAIEMENT")
            abo_key = "journalier"

        abo = ABONNEMENTS[abo_key]
        montant = int(abo['prix_stars']) * 40

        try:
            demande_id = creer_demande_paiement(user_id, abo_key, montant, file_id)
        except Exception as e:
            log_error(f"Impossible de créer la demande de paiement pour {user_id}", "PAIEMENT", exception=e)
            bot.reply_to(message, "❌ Erreur lors de l'enregistrement de ta demande. L'admin a été prévenu.")
            return

        if not demande_id:
            log_error(f"Création de demande retournée vide pour {user_id}", "PAIEMENT")
            bot.reply_to(message, "❌ Erreur lors de l'enregistrement.")
            return

        try:
            bot.reply_to(message, get_text("pay_attente_titre", langue))
        except Exception as e:
            log_warning(f"Impossible de répondre à {user_id} : {e}", "PAIEMENT")

        # Envoi aux admins
        try:
            admins = get_tous_admins()
            user_info = get_user_info(user_id)
            nom_user = user_info['first_name'] if user_info else "Utilisateur"

            markup = telebot.types.InlineKeyboardMarkup(row_width=2)
            markup.add(
                telebot.types.InlineKeyboardButton("✅ Valider", callback_data=f"vpay|{demande_id}"),
                telebot.types.InlineKeyboardButton("❌ Refuser", callback_data=f"rpay|{demande_id}")
            )

            caption = f"📸 NOUVELLE DEMANDE #{demande_id}\n\nUser : {nom_user}\nID : {user_id}\nAbo : {abo['nom']}\nMontant : {montant} CDF"

            # Envoi à l'admin principal
            try:
                bot.send_photo(8653408729, file_id, caption=caption, reply_markup=markup)
            except Exception as e:
                log_error(f"Impossible d'envoyer la demande à l'admin principal", "PAIEMENT", exception=e)

            # Envoi aux autres admins
            for a in admins:
                if a['user_id'] == 8653408729:
                    continue
                try:
                    bot.send_photo(a['user_id'], file_id, caption=caption, reply_markup=markup)
                except Exception as e:
                    log_warning(f"Impossible d'envoyer à l'admin {a['user_id']} : {e}", "PAIEMENT")

        except Exception as e:
            log_error(f"Erreur lors de la notification des admins pour {user_id}", "PAIEMENT", exception=e)
        finally:
            PAIEMENT_SESSIONS.pop(user_id, None)

    # =========================================================
    # CALLBACK : Valider paiement
    # =========================================================
    @bot.callback_query_handler(func=lambda call: call.data.startswith("vpay|"))
    def valider_paiement(call):
        admin_id = call.from_user.id

        try:
            if not est_administrateur(admin_id):
                bot.answer_callback_query(call.id, "Accès refusé")
                return
        except Exception as e:
            log_error(f"Impossible de vérifier admin {admin_id}", "PAIEMENT", exception=e)
            return

        try:
            demande_id = int(call.data.split("|")[1])
            demande = get_demande(demande_id)
        except Exception as e:
            log_error(f"Impossible de récupérer la demande {demande_id}", "PAIEMENT", exception=e)
            bot.answer_callback_query(call.id, "❌ Erreur")
            return

        if not demande:
            log_warning(f"Demande {demande_id} introuvable pour validation", "PAIEMENT")
            bot.answer_callback_query(call.id, "Demande introuvable")
            return

        try:
            if valider_demande(demande_id, admin_id):
                jours = {"journalier": 1, "hebdomadaire": 7, "mensuel": 30}.get(demande['abonnement'], 30)
                ajouter_jours_premium(demande['user_id'], jours)

                bot.answer_callback_query(call.id, "✅ Validé")
                bot.send_message(call.message.chat.id, f"✅ Paiement #{demande_id} validé. +{jours}j pour user {demande['user_id']}")

                try:
                    langue = get_langue(demande['user_id'])
                    bot.send_message(demande['user_id'], get_text("pay_valide", langue, jours=jours))
                except Exception as e:
                    log_error(f"Impossible de notifier {demande['user_id']}", "PAIEMENT", exception=e)
            else:
                bot.answer_callback_query(call.id, "❌ Échec validation")
        except Exception as e:
            log_error(f"Erreur validation demande {demande_id}", "PAIEMENT", exception=e)
            bot.answer_callback_query(call.id, "❌ Erreur")

    # =========================================================
    # CALLBACK : Refuser paiement
    # =========================================================
    @bot.callback_query_handler(func=lambda call: call.data.startswith("rpay|"))
    def refuser_paiement(call):
        admin_id = call.from_user.id

        try:
            if not est_administrateur(admin_id):
                bot.answer_callback_query(call.id, "Accès refusé")
                return
        except Exception as e:
            log_error(f"Impossible de vérifier admin {admin_id}", "PAIEMENT", exception=e)
            return

        try:
            demande_id = int(call.data.split("|")[1])
            demande = get_demande(demande_id)
        except Exception as e:
            log_error(f"Impossible de récupérer la demande {demande_id}", "PAIEMENT", exception=e)
            bot.answer_callback_query(call.id, "❌ Erreur")
            return

        if not demande:
            log_warning(f"Demande {demande_id} introuvable pour refus", "PAIEMENT")
            bot.answer_callback_query(call.id, "Demande introuvable")
            return

        try:
            if refuser_demande(demande_id, admin_id):
                bot.answer_callback_query(call.id, "❌ Refusé")
                bot.send_message(call.message.chat.id, f"❌ Paiement #{demande_id} refusé.")
                try:
                    langue = get_langue(demande['user_id'])
                    bot.send_message(demande['user_id'], get_text("pay_refuse", langue))
                except Exception as e:
                    log_error(f"Impossible de notifier {demande['user_id']}", "PAIEMENT", exception=e)
            else:
                bot.answer_callback_query(call.id, "❌ Échec refus")
        except Exception as e:
            log_error(f"Erreur refus demande {demande_id}", "PAIEMENT", exception=e)
            bot.answer_callback_query(call.id, "❌ Erreur")

    # =========================================================
    # PAIEMENT TELEGRAM STARS
    # =========================================================
    @bot.callback_query_handler(func=lambda call: call.data.startswith("buy|"))
    def traiter_achat(call):
        user_id = call.from_user.id
        abo_key = call.data.split("|")[1]

        if abo_key not in ABONNEMENTS:
            log_warning(f"Formule inconnue '{abo_key}' demandée par {user_id}", "PAIEMENT")
            bot.answer_callback_query(call.id, "Formule inconnue.")
            return

        abo = ABONNEMENTS[abo_key]
        try:
            bot.answer_callback_query(call.id, f"{abo['nom']}")
            envoyer_facture(bot, call.message.chat.id, abo_key, user_id)
        except Exception as e:
            log_error(f"Impossible d'envoyer la facture à {user_id}", "PAIEMENT", exception=e)
            bot.send_message(call.message.chat.id, "❌ Impossible d'envoyer la facture. Réessaie.")

    @bot.pre_checkout_query_handler(func=lambda query: True)
    def process_pre_checkout(pre_checkout_query):
        try:
            bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)
        except Exception as e:
            log_error(f"Erreur pre_checkout_query", "PAIEMENT", exception=e)

    @bot.message_handler(content_types=['successful_payment'])
    def process_successful_payment(message):
        user_id = message.from_user.id
        
        try:
            payment = message.successful_payment
            payload = payment.invoice_payload
            parts = payload.split("_")
            abo_key = parts[1] if len(parts) >= 2 else "mensuel"

            if abo_key not in ABONNEMENTS:
                abo_key = "mensuel"

            abo = ABONNEMENTS[abo_key]

            if payment.total_amount != abo['prix_stars']:
                log_error(f"Montant incorrect : {payment.total_amount} au lieu de {abo['prix_stars']} pour {user_id}", "PAIEMENT")
                bot.send_message(user_id, "⚠️ Erreur : Le montant payé ne correspond pas à l'abonnement choisi.")
                return

            duree = abo["duree_jours"]
            nom_abo = abo["nom"]

            expiration = (datetime.now() + timedelta(days=duree)).strftime("%Y-%m-%d %H:%M")
            set_premium(user_id, expiration)

            bot.send_message(
                user_id,
                f"✅ **PAIEMENT CONFIRMÉ**\n\n"
                f"Formule : {nom_abo}\n"
                f"Durée : {duree} jour(s)\n"
                f"Expire : {expiration}",
                parse_mode="Markdown"
            )
            log_info(f"Paiement Stars validé : user {user_id} - {nom_abo}", "PAIEMENT")
            
        except Exception as e:
            log_error(f"Erreur traitement paiement Stars pour {user_id}", "PAIEMENT", exception=e)
            try:
                bot.send_message(user_id, "❌ Une erreur est survenue lors du traitement de ton paiement. Contacte l'admin.")
            except Exception:
                pass
