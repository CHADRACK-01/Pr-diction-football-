# telegram_bot/payment_handlers.py
"""
Gestion des paiements (Stars + Mobile Money + Codes).
⚠️ CORRECTIONS :
- Vérification du payload (user_id)
- Sessions PAIEMENT_SESSIONS nettoyées (TTL)
- Atomicité sur validation/refus (déjà fait dans users/paiements.py)
- Taux CDF/Star externalisé
"""

import time
import threading
import telebot
from datetime import datetime

from users import (
    get_langue, set_premium, ajouter_jours_premium,
    creer_demande_paiement, utiliser_code,
    est_administrateur, get_user_info, get_tous_admins,
    valider_demande, get_demande, refuser_demande,
)
from core.payments import ABONNEMENTS, envoyer_facture
from core.translations import get_text
from core.utils.logs import log_info, log_error, log_warning
from config import TAUX_CDF_PAR_STAR, ADMIN_ID

COORDONNEES_MOBILE = {
    "Airtel Money": "Fonctionnalité à venir",
    "Orange Money": "+243 842 453 217",
    "M-Pesa": "Fonctionnalité à venir",
}

# Sessions de paiement Mobile Money (avec timestamp)
PAIEMENT_SESSIONS = {}
_PAIEMENT_LOCK = threading.Lock()
PAIEMENT_TTL_SEC = 1800  # 30 min


def _get_contexte_user(user, chat_id=None):
    return {
        "user_id": user.id,
        "user_name": user.first_name or "",
        "username": user.username or "",
        "chat_id": chat_id or user.id,
    }


def _nettoyer_sessions_paiement():
    """Supprime les sessions de paiement expirées."""
    maintenant = time.time()
    with _PAIEMENT_LOCK:
        expires = [
            uid for uid, data in PAIEMENT_SESSIONS.items()
            if maintenant - data["ts"] > PAIEMENT_TTL_SEC
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
        return data["abo"] if data else None


def _pop_session_paiement(user_id):
    with _PAIEMENT_LOCK:
        PAIEMENT_SESSIONS.pop(user_id, None)


def _jours_pour_abo(abo_key):
    """Retourne la durée en jours d'un abonnement (source unique : ABONNEMENTS)."""
    abo = ABONNEMENTS.get(abo_key)
    return abo["duree_jours"] if abo else 30


def _montant_cdf(abo_key):
    """Calcule le montant CDF à partir des Stars (taux externalisé)."""
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

        log_info(
            f"Choix paiement : {action}",
            "PAIEMENT",
            user_context=ctx,
            extra={"action": action},
        )

        try:
            bot.answer_callback_query(call.id, "OK")
        except Exception as e:
            log_warning(
                message="Impossible de répondre au callback",
                module="PAIEMENT",
                user_context=ctx,
                exception=e,
            )

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
                    markup.add(telebot.types.InlineKeyboardButton(
                        f"{abo['nom']} - {montant:,} CDF".replace(",", " "),
                        callback_data=f"paym|{key}",
                    ))
                bot.send_message(
                    call.message.chat.id,
                    "📱 **MOBILE MONEY**\n\nChoisis ton abonnement :",
                    reply_markup=markup,
                    parse_mode="Markdown",
                )

            elif action == "code":
                msg = bot.send_message(
                    call.message.chat.id,
                    get_text("pay_code_titre", langue) + "\n\nTape /annuler pour annuler.",
                )
                bot.register_next_step_handler(msg, _traiter_code)

        except Exception as e:
            log_error(
                message=f"Erreur lors du choix de paiement ({action})",
                module="PAIEMENT",
                user_context=ctx,
                exception=e,
            )
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
            log_warning(
                message=f"Abonnement inconnu demandé : {abo_key}",
                module="PAIEMENT",
                user_context=ctx,
            )
            try:
                bot.answer_callback_query(call.id, "Inconnu")
            except Exception:
                pass
            return

        _set_session_paiement(user_id, abo_key)
        abo = ABONNEMENTS[abo_key]
        montant = _montant_cdf(abo_key)

        try:
            bot.answer_callback_query(call.id, "OK")
        except Exception as e:
            log_warning(
                message="Impossible de répondre au callback",
                module="PAIEMENT",
                user_context=ctx,
                exception=e,
            )

        texte = get_text("pay_mobile_titre", langue, montant=montant, abo=abo["nom"])
        texte += "\n\n"
        for nom, numero in COORDONNEES_MOBILE.items():
            texte += f"📱 {nom} : {numero}\n"

        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton(
            "📸 J'ai payé (Envoyer la preuve)", callback_data="preuve_ok",
        ))

        try:
            bot.send_message(call.message.chat.id, texte, reply_markup=markup)
        except Exception as e:
            log_error(
                message="Impossible d'envoyer le menu Mobile Money",
                module="PAIEMENT",
                user_context=ctx,
                exception=e,
            )

    # =========================================================
    # DEMANDE DE PREUVE
    # =========================================================
    @bot.callback_query_handler(func=lambda call: call.data == "preuve_ok")
    def demander_preuve(call):
        try:
            bot.answer_callback_query(call.id, "OK")
        except Exception as e:
            log_warning(
                message="Impossible de répondre au callback preuve_ok",
                module="PAIEMENT",
                exception=e,
            )

        try:
            msg = bot.send_message(
                call.message.chat.id,
                "📸 Envoie la capture d'écran de ton paiement :",
            )
            bot.register_next_step_handler(msg, recevoir_capture)
        except Exception as e:
            log_error(
                message="Impossible de demander la preuve",
                module="PAIEMENT",
                user_context=_get_contexte_user(call.from_user, call.message.chat.id),
                exception=e,
            )

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
            log_error(
                message="Erreur lors de l'utilisation du code",
                module="PAIEMENT",
                user_context=ctx,
                exception=e,
            )
            bot.reply_to(message, "❌ Une erreur est survenue.")
            return

        if "erreur" in resultat:
            bot.reply_to(message, get_text("pay_code_erreur", langue, erreur=resultat["erreur"]))
            return

        jours = resultat["jours"]
        try:
            ajouter_jours_premium(user_id, jours)
            bot.reply_to(message, get_text("pay_code_ok", langue, jours=jours))
            log_info(
                f"Code utilisé : +{jours}j",
                "PAIEMENT",
                user_context=ctx,
            )
        except Exception as e:
            log_error(
                message="Code validé mais ajout premium échoué",
                module="PAIEMENT",
                user_context=ctx,
                extra={"jours": jours},
                exception=e,
            )
            bot.reply_to(message, "❌ Le code a été validé mais l'ajout a échoué. Contacte l'admin.")

    # =========================================================
    # CAPTURE DE PAIEMENT
    # =========================================================
    def recevoir_capture(message):
        user_id = message.from_user.id
        langue = get_langue(user_id)
        ctx = _get_contexte_user(message)

        if not message.photo or len(message.photo) == 0:
            log_warning(
                message="Capture invalide (pas une photo)",
                module="PAIEMENT",
                user_context=ctx,
            )
            bot.reply_to(message, "❌ Ce n'est pas une photo valide. Action annulée.")
            return

        file_id = message.photo[-1].file_id
        abo_key = _get_session_paiement(user_id) or "journalier"
        if abo_key not in ABONNEMENTS:
            abo_key = "journalier"

        abo = ABONNEMENTS[abo_key]
        montant = _montant_cdf(abo_key)

        try:
            demande_id = creer_demande_paiement(user_id, abo_key, montant, file_id)
        except Exception as e:
            log_error(
                message="Impossible de créer la demande de paiement",
                module="PAIEMENT",
                user_context=ctx,
                extra={"abonnement": abo_key, "montant": montant},
                exception=e,
            )
            bot.reply_to(message, "❌ Erreur lors de l'enregistrement. L'admin a été prévenu.")
            return

        if not demande_id:
            bot.reply_to(message, "❌ Erreur lors de l'enregistrement.")
            return

        try:
            bot.reply_to(message, get_text("pay_attente_titre", langue))
        except Exception as e:
            log_warning(
                message="Impossible de répondre à l'utilisateur",
                module="PAIEMENT",
                user_context=ctx,
                exception=e,
            )

        # Notification admins
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
                f"📸 NOUVELLE DEMANDE #{demande_id}\n\n"
                f"User : {nom_user}\nID : {user_id}\n"
                f"Abo : {abo['nom']}\nMontant : {montant} CDF"
            )

            # Admin principal
            try:
                bot.send_photo(ADMIN_ID, file_id, caption=caption, reply_markup=markup)
            except Exception as e:
                log_error(
                    message="Impossible d'envoyer la demande à l'admin principal",
                    module="PAIEMENT",
                    extra={"demande_id": demande_id},
                    exception=e,
                )

            # Autres admins
            for a in admins:
                if a["user_id"] == ADMIN_ID:
                    continue
                try:
                    bot.send_photo(a["user_id"], file_id, caption=caption, reply_markup=markup)
                except Exception as e:
                    log_warning(
                        message=f"Impossible d'envoyer à l'admin {a['user_id']}",
                        module="PAIEMENT",
                        extra={"admin_id": a["user_id"]},
                        exception=e,
                    )
        except Exception as e:
            log_error(
                message="Erreur lors de la notification des admins",
                module="PAIEMENT",
                user_context=ctx,
                exception=e,
            )
        finally:
            _pop_session_paiement(user_id)

    # =========================================================
    # VALIDATION
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
            log_error(
                message="Impossible de vérifier admin (validation)",
                module="PAIEMENT",
                user_context=ctx,
                exception=e,
            )
            return

        try:
            demande_id = int(call.data.split("|")[1])
        except (ValueError, IndexError) as e:
            log_error(
                message="Demande ID invalide",
                module="PAIEMENT",
                user_context=ctx,
                extra={"callback_data": call.data},
                exception=e,
            )
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
            bot.send_message(
                call.message.chat.id,
                f"✅ Paiement #{demande_id} validé. +{jours}j pour user {demande['user_id']}",
            )

            try:
                langue = get_langue(demande["user_id"])
                bot.send_message(
                    demande["user_id"],
                    get_text("pay_valide", langue, jours=jours),
                )
            except Exception as e:
                log_error(
                    message="Impossible de notifier l'utilisateur (validation)",
                    module="PAIEMENT",
                    extra={"user_id": demande["user_id"]},
                    exception=e,
                )
        else:
            bot.answer_callback_query(call.id, "❌ Déjà traité ou échec")

    # =========================================================
    # REFUS
    # =========================================================
    @bot.callback_query_handler(func=lambda call: call.data.startswith("rpay|"))
    def refuser_paiement(call):
        admin_id = call.from_user.id
        ctx = _get_contexte_user(call.from_user, call.message.chat.id)

        try:
            if not est_administrateur(admin_id):
                bot.answer_callback_query(call.id, "Accès refusé")
                return
        except Exception as e:
            log_error(
                message="Impossible de vérifier admin (refus)",
                module="PAIEMENT",
                user_context=ctx,
                exception=e,
            )
            return

        try:
            demande_id = int(call.data.split("|")[1])
        except (ValueError, IndexError) as e:
            bot.answer_callback_query(call.id, "❌ ID invalide")
            log_error(
                message="Demande ID invalide (refus)",
                module="PAIEMENT",
                user_context=ctx,
                exception=e,
            )
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
                log_error(
                    message="Impossible de notifier l'utilisateur (refus)",
                    module="PAIEMENT",
                    extra={"user_id": demande["user_id"]},
                    exception=e,
                )
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
            log_warning(
                message="Formule inconnue demandée",
                module="PAIEMENT",
                user_context=ctx,
                extra={"abo_key": abo_key},
            )
            bot.answer_callback_query(call.id, "Formule inconnue.")
            return

        abo = ABONNEMENTS[abo_key]
        try:
            bot.answer_callback_query(call.id, f"{abo['nom']}")
            envoyer_facture(bot, call.message.chat.id, abo_key, user_id)
        except Exception as e:
            log_error(
                message="Impossible d'envoyer la facture",
                module="PAIEMENT",
                user_context=ctx,
                extra={"abo_key": abo_key},
                exception=e,
            )
            bot.send_message(call.message.chat.id, "❌ Impossible d'envoyer la facture.")

    @bot.pre_checkout_query_handler(func=lambda query: True)
    def process_pre_checkout(pre_checkout_query):
        try:
            bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)
        except Exception as e:
            log_error(
                message="Erreur pre_checkout_query",
                module="PAIEMENT",
                exception=e,
            )

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

            # ⚠️ VÉRIFICATION : le payload doit contenir l'user_id
            if f"_{user_id}" not in payload:
                log_error(
                    message="Payload de paiement ne correspond pas à l'utilisateur",
                    module="PAIEMENT",
                    user_context=ctx,
                    extra={"payload": payload[:50]},
                )
                bot.send_message(user_id, "⚠️ Erreur : payload invalide. Contacte l'admin.")
                return

            # ⚠️ VÉRIFICATION : devise = XTR
            if payment.currency != "XTR":
                log_error(
                    message=f"Devise inattendue : {payment.currency}",
                    module="PAIEMENT",
                    user_context=ctx,
                    extra={"currency": payment.currency},
                )
                bot.send_message(user_id, "⚠️ Erreur : devise invalide.")
                return

            parts = payload.split("_")
            abo_key = parts[1] if len(parts) >= 2 else "mensuel"
            if abo_key not in ABONNEMENTS:
                abo_key = "mensuel"

            abo = ABONNEMENTS[abo_key]
            if payment.total_amount != abo["prix_stars"]:
                log_error(
                    message=f"Montant incorrect : {payment.total_amount} != {abo['prix_stars']}",
                    module="PAIEMENT",
                    user_context=ctx,
                    extra={"abo": abo_key},
                )
                bot.send_message(user_id, "⚠️ Le montant payé ne correspond pas.")
                return

            duree = abo["duree_jours"]
            from datetime import datetime as dt
            expiration = (dt.now() + __import__("datetime").timedelta(days=duree)).strftime(
                "%Y-%m-%d %H:%M"
            )
            set_premium(user_id, expiration)

            bot.send_message(
                user_id,
                f"✅ **PAIEMENT CONFIRMÉ**\n\n"
                f"Formule : {abo['nom']}\n"
                f"Durée : {duree} jour(s)\n"
                f"Expire : {expiration}",
                parse_mode="Markdown",
            )
            log_info(
                f"Paiement Stars validé : {abo['nom']}",
                "PAIEMENT",
                user_context=ctx,
            )
        except Exception as e:
            log_error(
                message="Erreur traitement paiement Stars",
                module="PAIEMENT",
                user_context=ctx,
                exception=e,
            )
            try:
                bot.send_message(user_id, "❌ Une erreur est survenue lors du paiement.")
            except Exception:
                pass
