import telebot
from core.utils.logs import log_info, log_error, log_warning


# =========================================================
# ABONNEMENTS PREMIUM (PRIX EN STARS)
# =========================================================
ABONNEMENTS = {
    "journalier": {
        "nom": "Journalier",
        "prix_stars": 50,
        "duree_jours": 1,
    },
    "hebdomadaire": {
        "nom": "Hebdomadaire",
        "prix_stars": 150,
        "duree_jours": 7,
    },
    "mensuel": {
        "nom": "Mensuel",
        "prix_stars": 250,
        "duree_jours": 30,
    },
}


def envoyer_facture(bot, chat_id, abo_key, user_id):
    """
    Envoie une facture Telegram Stars (XTR).
    - provider_token doit être VIDE pour les Stars
    - currency doit être 'XTR'
    Retourne True si l'envoi a réussi, False sinon.
    """
    if not abo_key or abo_key not in ABONNEMENTS:
        log_warning(f"Abonnement inconnu '{abo_key}' demandé par {user_id}", "PAYMENTS")
        try:
            bot.send_message(chat_id, "❌ Formule d'abonnement inconnue.")
        except Exception as e:
            log_warning(f"Impossible d'envoyer le message d'erreur à {chat_id} : {e}", "PAYMENTS")
        return False

    abo = ABONNEMENTS[abo_key]

    # Vérification des paramètres
    if not isinstance(abo.get('prix_stars'), int) or abo['prix_stars'] <= 0:
        log_error(f"Prix Stars invalide pour l'abonnement '{abo_key}' : {abo.get('prix_stars')}", "PAYMENTS")
        return False

    if not isinstance(chat_id, int) or not isinstance(user_id, int):
        log_error(f"chat_id ({chat_id}) ou user_id ({user_id}) invalide pour la facture", "PAYMENTS")
        return False

    try:
        bot.send_invoice(
            chat_id=chat_id,
            title=f"Abonnement {abo['nom']}",
            description=f"Pronostics illimités pendant {abo['duree_jours']} jour(s)",
            invoice_payload=f"abo_{abo_key}_{user_id}",
            provider_token="",  # ⚠️ VIDE pour Telegram Stars
            currency="XTR",     # ⚠️ Code des Stars
            prices=[
                telebot.types.LabeledPrice(
                    label=abo['nom'],
                    amount=abo['prix_stars']
                )
            ],
            start_parameter=f"abo_{abo_key}",
        )
        log_info(f"Facture envoyée : {abo['nom']} - {abo['prix_stars']} Stars (user {user_id})", "PAYMENTS")
        return True
    except Exception as e:
        log_error(
            f"Impossible d'envoyer la facture pour {abo['nom']} à {user_id}",
            "PAYMENTS",
            exception=e
        )
        try:
            bot.send_message(
                chat_id, 
                "❌ Impossible d'envoyer la facture. L'admin a été prévenu."
            )
        except Exception:
            pass
        return False
