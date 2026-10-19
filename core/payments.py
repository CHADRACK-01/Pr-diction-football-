import telebot
from core.utils.logs import log_info


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
    """
    if abo_key not in ABONNEMENTS:
        bot.send_message(chat_id, "Formule inconnue.")
        return False

    abo = ABONNEMENTS[abo_key]

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
