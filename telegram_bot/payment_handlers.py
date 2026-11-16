# telegram_bot/payment_handlers.py
"""
Gestion des paiements (Stars + Mobile Money + Codes).
- Intégration des devises multiples (Fonctionnalité 416)
- Vérification manuelle simplifiée (Numéro + Référence + Preuve) (Fonctionnalité 31)
"""

import time
import threading
import telebot
from datetime import datetime, timedelta

from users import (
    get_langue, set_premium, ajouter_jours_premium,
    creer_demande_paiement, utiliser_code,
    est_administrateur, get_user_info, get_tous_admins,
    valider_demande, get_demande, refuser_demande,
)
from core.payments import ABONNEMENTS, envoyer_facture
from core.devises import formater_prix
from core.translations import get_text
from core.utils.logs import log_info, log_error, log_warning
from config import TAUX_CDF_PAR_STAR, ADMIN_ID

COORDONNEES_MOBILE = {
    "Airtel Money": "Fonctionnalité à venir",
    "Orange Money": "+243 842 453 217",
    "M-Pesa": "Fonctionnalité à venir",
}

PAIEMENT_SESSIONS = {}
_PAIEMENT_LOCK = threading.Lock()
PAIEMENT_TTL_SEC = 1800


def _get_contexte_user(message_or_user, chat_id=None):
    user = getattr(message_or_user, "from_user", message_or_user)
    if chat_id:
        cid = chat_id
    elif hasattr(message_or_user, "chat"):
        cid = message_or_user.chat.id
    else:
        cid = user.id

    return {
        "user_id": user.id,
        "user_name": getattr(user, "first_name", "") or "",
        "username": getattr(user, "username", "") or "",
        "chat_id": cid,
    }


def _nettoyer_sessions_paiement():
    maintenant = time.time()
    with _PAIEMENT_LOCK:
        expires = [
            uid for uid, data in PAIEMENT_SESSIONS.items()
            if maintenant - data.get("ts", 0) > PAIEMENT_TTL_SEC
        ]
        for uid in expires:
            del PAIEMENT_SESSIONS[uid]


def _set_session_paiement(user_id, abo_key):
    with _PAIEMENT_LOCK:
        PAIEMENT_SESSIONS[user_id] = {"abo": abo_key, "ts": time.time()}


def _get_session_paiement(user_id):
    _nettoyer_sessions_paiement()
    with _PAIEMENT_LOCK:
        data = PAIEMENT_SESSIONS.get(user_id)
        return data if data else None


def _pop_session_paiement(user_id):
    with _PAIEMENT_LOCK:
        PAIEMENT_SESSIONS.pop(user_id, None)


def _jours_pour_abo(abo_key):
    abo = ABONNEMENTS.get(abo_key)
    return abo["duree_jours"] if abo else 30


def _montant_cdf(abo_key):
    abo = ABONNEMENTS.get(abo_key)
    if not abo:
        return 0
    return int(abo["prix_stars"]) * TAUX_CDF_PAR_STAR


def enregistrer_payment_handlers(bot):

    # =========================================================
    # CHOIX DU MODE DE PAIEMENT
    # =========================================================
    @bot.callback_query_handler(func=lambda call: call.data.startswith("pay|"))
    def traiter_choix_paiement(call):
        user_id = call.from_user.id
        langue = get_langue(user_id)
        ctx = _get_contexte_user(call.from_user, call.message.chat.id)
        action = call.data.split("|", 1)[1] if "|" in call.data else ""

        log_info(f"Choix paiement : {action}", "PAIEMENT", user_context=ctx)

        try:
            bot.answer_callback_query(call.id, "OK")
        except Exception as e:
            log_warning(f"Impossible de répondre au callback", "PAIEMENT", exception=e)

        try:
            if action == "stars":
                markup = telebot.types.InlineKeyboardMarkup(row_width=1)
                for key, abo in ABONNEMENTS.items():
                    markup.add(telebot.types.InlineKeyboardButton(
                        f"{abo['nom']} - {abo['prix_stars']} Stars",
                        callback_data=f"buy|{key}",
                    ))
                bot.send_message(call.message.chat.id, get_text("premium_titre", langue), reply_markup=markup)

            elif action == "mobile":
                markup = telebot.types.InlineKeyboardMarkup(row_width=1)
                for key, abo in ABONNEMENTS.items():
                    montant = _montant_cdf(key)
                    prix_str = f"{formater_prix(montant, 'CDF')} / {formater_prix(montant, 'USD')}"
                    markup.add(telebot.types.InlineKeyboardButton(
                        f"{abo['nom']} - {prix_str}",
                        callback_data=f"paym|{key}",
                    ))
                bot.send_message(
                    call.message.chat.id,
                    "📱 <b>MOBILE MONEY</b>\n\nChoisis ton abonnement :",
                    reply_markup=markup,
                    parse_mode="HTML",
                )

            elif action == "code":
                msg = bot.send_message(
                    call.message.chat.id,
                    get_text("pay_code_titre", langue) + "\n\nTape /annuler pour annuler.",
                )
                bot.register_next_step_handler(msg, _traiter_code)

        except Exception as e:
            log_error(f"Erreur lors du choix de paiement ({action})", "PAIEMENT", user_context=ctx, exception=e)
            try:
                bot.send_message(call.message.chat.id, "❌ Une erreur est survenue.")
            except Exception:
                pass

    # =========================================================
    # CHOIX ABONNEMENT MOBILE MONEY
    # =========================================================
    @bot.callback_query_handler(func=lambda call: call.data.startswith("paym|"))
    def traiter_abo_mobile(call):
        user_id = call.from_user.id
        langue = get_langue(user_id)
        ctx = _get_contexte_user(call.from_user, call.message.chat.id)
        abo_key = call.data.split("|", 1)[1]

        if abo_key not in ABONNEMENTS:
            try: bot.answer_callback_query(call.id, "Inconnu")
            except Exception: pass
            return

        _set_session_paiement(user_id, abo_key)
        abo = ABONNEMENTS[abo_key]
        montant_cdf = _montant_cdf(abo_key)

        try:
            bot.answer_callback_query(call.id, "OK")
        except Exception:
            pass

        # Affichage multi-devises (Fonctionnalité 416)
        texte = f"📱 <b>PAIEMENT MOBILE MONEY</b>\n\n"
        texte += f"Abonnement : <b>{abo['nom']}</b>\n\n"
        texte += f"💰 <b>Montant à payer :</b>\n"
        texte += f"• En CDF : {formater_prix(montant_cdf, 'CDF')}\n"
        texte += f"• En USD : {formater_prix(montant_cdf, 'USD')}\n"
        texte += f"• En EUR : {formater_prix(montant_cdf, 'EUR')}\n\n"
        texte += f"👇 <b>Envoyez le montant sur l'un de ces numéros :</b>\n\n"
        
        for nom, numero in COORDONNEES_MOBILE.items():
            texte += f"📱 {nom} : <code>{numero}</code>\n"

        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton(
            "📸 J'ai payé (Envoyer la preuve)", callback_data="preuve_ok",
        ))

        try:
            bot.send_message(call.message.chat.id, texte, reply_markup=markup, parse_mode="HTML")
        except Exception as e:
            log_error(f"Impossible d'envoyer le menu Mobile Money", "PAIEMENT", user_context=ctx, exception=e)

    # =========================================================
    # ÉTAPE 1 : DEMANDER LE NUMÉRO
    # =========================================================
    @bot.callback_query_handler(func=lambda call: call.data == "preuve_ok")
    def demander_preuve(call):
        try:
            bot.answer_callback_query(call.id, "OK")
        except Exception:
            pass

        try:
            msg = bot.send_message(
                call.message.chat.id,
                "📱 <b>ÉTAPE 1/2</b>\n\n"
                "Envoie le <b>numéro de téléphone</b> depuis lequel tu as payé :\n"
                "Exemple : 0821234567",
                parse_mode="HTML"
            )
            bot.register_next_step_handler(msg, _recevoir_numero)
        except Exception as e:
            log_error(f"Impossible de demander le numéro", "PAIEMENT", exception=e)

    def _recevoir_numero(message):
        user_id = message.from_user.id
        numero = (message.text or "").strip()
        
        if not numero or len(numero) < 9:
            bot.reply_to(message, "❌ Numéro invalide. Action annulée.")
            return
        
        # Stockage du numéro dans la session
        with _PAIEMENT_LOCK:
            if user_id in PAIEMENT_SESSIONS:
                PAIEMENT_SESSIONS[user_id]["numero"] = numero
            else:
                PAIEMENT_SESSIONS[user_id] = {"numero": numero, "ts": time.time()}
        
        msg = bot.send_message(
            message.chat.id,
            "🔢 <b>ÉTAPE 2/2</b>\n\n"
            "Envoie la <b>référence de la transaction</b> (ID de l'opération) :\n"
            "Exemple : MP240711.1234.A56789",
            parse_mode="HTML"
        )
        bot.register_next_step_handler(msg, _recevoir_reference)

    def _recevoir_reference(message):
        user_id = message.from_user.id
        reference = (message.text or "").strip()
        
        if not reference:
            bot.reply_to(message, "❌ Référence invalide. Action annulée.")
            return
            
        with _PAIEMENT_LOCK:
            if user_id in PAIEMENT_SESSIONS:
                PAIEMENT_SESSIONS[user_id]["reference"] = reference
        
        msg = bot.send_message(
            message.chat.id,
            "📸 Envoie la <b>capture d'écran</b> de ton paiement pour validation finale :",
            parse_mode="HTML"
        )
        bot.register_next_step_handler(msg, recevoir_capture)

    # =========================================================
    # ÉTAPE 3 : RECEVOIR LA PREUVE
    # =========================================================
    def recevoir_capture(message):
        user_id = message.from_user.id
        langue = get_langue(user_id)
        ctx = _get_contexte_user(message)

        if not message.photo or len(message.photo) == 0:
            log_warning("Capture invalide (pas une photo)", "PAIEMENT", user_context=ctx)
            bot.reply_to(message, "❌ Ce n'est pas une photo valide. Action annulée.")
            return

        file_id = message.photo[-1].file_id
        
        session = _get_session_paiement(user_id) or {}
        abo_key = session.get("abo", "journalier")
        if abo_key not in ABONNEMENTS:
            abo_key = "journalier"
            
        numero = session.get("numero", "Non fourni")
        reference = session.get("reference", "Non fournie")
        abo = ABONNEMENTS[abo_key]
        montant = _montant_cdf(abo_key)

        try:
            demande_id = creer_demande_paiement(user_id, abo_key, montant, file_id)
        except Exception as e:
            log_error(f"Impossible de créer la demande", "PAIEMENT", user_context=ctx, exception=e)
            bot.reply_to(message, "❌ Erreur. L'admin a été prévenu.")
            return

        if not demande_id:
            bot.reply_to(message, "❌ Erreur lors de l'enregistrement.")
            return

        bot.reply_to(message, get_text("pay_attente_titre", langue))

        try:
            admins = get_tous_admins()
            user_info = get_user_info(user_id)
            nom_user = user_info["first_name"] if user_info else "Utilisateur"

            markup = telebot.types.InlineKeyboardMarkup(row_width=2)
            markup.add(
                telebot.types.InlineKeyboardButton("✅ Valider", callback_data=f"vpay|{demande_id}"),
                telebot.types.InlineKeyboardButton("❌ Refuser", callback_data=f"rpay|{demande_id}"),
            )

            caption = (
                f"📸 <b>NOUVELLE DEMANDE #{demande_id}</b>\n\n"
                f"User : {nom_user}\nID : {user_id}\n"
                f"Abo : {abo['nom']}\nMontant : {formater_prix(montant, 'CDF')}\n\n"
                f"📱 <b>Infos de paiement :</b>\n"
                f"Numéro : <code>{numero}</code>\n"
                f"Référence : <code>{reference}</code>"
            )

            # Envoi à tous les admins
            for a in admins:
                try:
                    bot.send_photo(a["user_id"], file_id, caption=caption, reply_markup=markup, parse_mode="HTML")
                except Exception as e:
                    log_warning(f"Impossible d'envoyer à l'admin {a['user_id']}", "PAIEMENT", exception=e)
                    
        except Exception as e:
            log_error(f"Erreur notification admins", "PAIEMENT", user_context=ctx, exception=e)
        finally:
            _pop_session_paiement(user_id)

    # =========================================================
    # CODE PREMIUM
    # =========================================================
    def _traiter_code(message):
        user_id = message.from_user.id
        langue = get_langue(user_id)
        ctx = _get_contexte_user(message)

        code = (message.text or "").strip().upper()
        if code == "/ANNULER":
            bot.reply_to(message, "Annulé.")
            return

        try:
            resultat = utiliser_code(code, user_id)
        except Exception as e:
            log_error(f"Erreur lors de l'utilisation du code", "PAIEMENT", user_context=ctx, exception=e)
            bot.reply_to(message, "❌ Une erreur est survenue.")
            return

        if "erreur" in resultat:
            bot.reply_to(message, get_text("pay_code_erreur", langue, erreur=resultat["erreur"]))
            return

        jours = resultat["jours"]
        try:
            ajouter_jours_premium(user_id, jours)
            bot.reply_to(message, get_text("pay_code_ok", langue, jours=jours))
            log_info(f"Code utilisé : +{jours}j", "PAIEMENT", user_context=ctx)
        except Exception as e:
            log_error(f"Code validé mais ajout premium échoué", "PAIEMENT", user_context=ctx, extra={"jours": jours}, exception=e)
            bot.reply_to(message, "❌ Le code a été validé mais l'ajout a échoué. Contacte l'admin.")

    # =========================================================
    # VALIDATION / REFUS
    # =========================================================
    @bot.callback_query_handler(func=lambda call: call.data.startswith("vpay|"))
    def valider_paiement(call):
        admin_id = call.from_user.id
        ctx = _get_contexte_user(call.from_user, call.message.chat.id)

        try:
            if not est_administrateur(admin_id):
                bot.answer_callback_query(call.id, "Accès refusé")
                return
        except Exception as e:
            log_error(f"Impossible de vérifier admin (validation)", "PAIEMENT", user_context=ctx, exception=e)
            return

        try:
            demande_id = int(call.data.split("|")[1])
        except (ValueError, IndexError) as e:
            log_error(f"Demande ID invalide", "PAIEMENT", user_context=ctx, exception=e)
            bot.answer_callback_query(call.id, "❌ ID invalide")
            return

        demande = get_demande(demande_id)
        if not demande:
            bot.answer_callback_query(call.id, "Demande introuvable")
            return

        if valider_demande(demande_id, admin_id):
            jours = _jours_pour_abo(demande["abonnement"])
            ajouter_jours_premium(demande["user_id"], jours)

            bot.answer_callback_query(call.id, "✅ Validé")
            bot.send_message(call.message.chat.id, f"✅ Paiement #{demande_id} validé. +{jours}j pour user {demande['user_id']}")

            try:
                langue = get_langue(demande["user_id"])
                bot.send_message(demande["user_id"], get_text("pay_valide", langue, jours=jours))
            except Exception as e:
                log_error(f"Impossible de notifier l'utilisateur (validation)", "PAIEMENT", exception=e)
        else:
            bot.answer_callback_query(call.id, "❌ Déjà traité ou échec")

    @bot.callback_query_handler(func=lambda call: call.data.startswith("rpay|"))
    def refuser_paiement(call):
        admin_id = call.from_user.id
        ctx = _get_contexte_user(call.from_user, call.message.chat.id)

        try:
            if not est_administrateur(admin_id):
                bot.answer_callback_query(call.id, "Accès refusé")
                return
        except Exception as e:
            log_error(f"Impossible de vérifier admin (refus)", "PAIEMENT", user_context=ctx, exception=e)
            return

        try:
            demande_id = int(call.data.split("|")[1])
        except (ValueError, IndexError) as e:
            bot.answer_callback_query(call.id, "❌ ID invalide")
            log_error(f"Demande ID invalide (refus)", "PAIEMENT", user_context=ctx, exception=e)
            return

        demande = get_demande(demande_id)
        if not demande:
            bot.answer_callback_query(call.id, "Demande introuvable")
            return

        if refuser_demande(demande_id, admin_id):
            bot.answer_callback_query(call.id, "❌ Refusé")
            bot.send_message(call.message.chat.id, f"❌ Paiement #{demande_id} refusé.")
            try:
                langue = get_langue(demande["user_id"])
                bot.send_message(demande["user_id"], get_text("pay_refuse", langue))
            except Exception as e:
                log_error(f"Impossible de notifier l'utilisateur (refus)", "PAIEMENT", exception=e)
        else:
            bot.answer_callback_query(call.id, "❌ Déjà traité ou échec")

    # =========================================================
    # ACHAT STARS
    # =========================================================
    @bot.callback_query_handler(func=lambda call: call.data.startswith("buy|"))
    def traiter_achat(call):
        user_id = call.from_user.id
        ctx = _get_contexte_user(call.from_user, call.message.chat.id)

        try:
            abo_key = call.data.split("|")[1]
        except IndexError:
            bot.answer_callback_query(call.id, "Formule inconnue")
            return

        if abo_key not in ABONNEMENTS:
            log_warning(f"Formule inconnue demandée", "PAIEMENT", user_context=ctx, extra={"abo_key": abo_key})
            bot.answer_callback_query(call.id, "Formule inconnue.")
            return

        abo = ABONNEMENTS[abo_key]
        try:
            bot.answer_callback_query(call.id, f"{abo['nom']}")
            envoyer_facture(bot, call.message.chat.id, abo_key, user_id)
        except Exception as e:
            log_error(f"Impossible d'envoyer la facture", "PAIEMENT", user_context=ctx, extra={"abo_key": abo_key}, exception=e)
            bot.send_message(call.message.chat.id, "❌ Impossible d'envoyer la facture.")

    @bot.pre_checkout_query_handler(func=lambda query: True)
    def process_pre_checkout(pre_checkout_query):
        try:
            bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)
        except Exception as e:
            log_error(f"Erreur pre_checkout_query", "PAIEMENT", exception=e)

    # =========================================================
    # PAIEMENT RÉUSSI (Stars)
    # =========================================================
    @bot.message_handler(content_types=["successful_payment"])
    def process_successful_payment(message):
        user_id = message.from_user.id
        ctx = _get_contexte_user(message)

        try:
            payment = message.successful_payment
            payload = payment.invoice_payload or ""

            if f"_{user_id}" not in payload:
                log_error(f"Payload de paiement ne correspond pas à l'utilisateur", "PAIEMENT", user_context=ctx, extra={"payload": payload[:50]})
                bot.send_message(user_id, "⚠️ Erreur : payload invalide. Contacte l'admin.")
                return

            if payment.currency != "XTR":
                log_error(f"Devise inattendue : {payment.currency}", "PAIEMENT", user_context=ctx)
                bot.send_message(user_id, "⚠️ Erreur : devise invalide.")
                return

            parts = payload.split("_")
            abo_key = parts[1] if len(parts) >= 2 else "mensuel"
            if abo_key not in ABONNEMENTS:
                abo_key = "mensuel"

            abo = ABONNEMENTS[abo_key]
            if payment.total_amount != abo["prix_stars"]:
                log_error(f"Montant incorrect : {payment.total_amount} != {abo['prix_stars']}", "PAIEMENT", user_context=ctx, extra={"abo": abo_key})
                bot.send_message(user_id, "⚠️ Le montant payé ne correspond pas.")
                return

            duree = abo["duree_jours"]
            expiration = (datetime.now() + timedelta(days=duree)).strftime("%Y-%m-%d %H:%M")
            set_premium(user_id, expiration)

            bot.send_message(
                user_id,
                f"✅ <b>PAIEMENT CONFIRMÉ</b>\n\n"
                f"Formule : {abo['nom']}\n"
                f"Durée : {duree} jour(s)\n"
                f"Expire : {expiration}",
                parse_mode="HTML",
            )
            log_info(f"Paiement Stars validé : {abo['nom']}", "PAIEMENT", user_context=ctx)
        except Exception as e:
            log_error(f"Erreur traitement paiement Stars", "PAIEMENT", user_context=ctx, exception=e)
            try:
                bot.send_message(user_id, "❌ Une erreur est survenue lors du paiement.")
            except Exception:
                pass
