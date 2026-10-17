"""
Point d'entrée des handlers Telegram.
Enregistre tous les modules dans le bon ordre.
"""

from telegram_bot.admin_handlers import enregistrer_admin_handlers
from telegram_bot.payment_handlers import enregistrer_payment_handlers
from telegram_bot.premium_handlers import enregistrer_premium_handlers
from telegram_bot.prediction_handlers import enregistrer_prediction_handlers
from telegram_bot.user_handlers import enregistrer_user_handlers
from telegram_bot.menu_handlers import enregistrer_menu_handlers


def enregistrer_handlers(bot):
    """
    Enregistre tous les handlers utilisateur.
    ⚠️ L'ORDRE est CRUCIAL :
    1. Admin (pour qu'il attrape 'Panneau Admin' en premier)
    2. Paiement
    3. Premium
    4. Prédictions
    5. Commandes utilisateur
    6. Menu principal (en dernier, c'est le fallback)
    """

    # 1. ADMIN EN PREMIER (Très important pour le bouton Panneau Admin)
    enregistrer_admin_handlers(bot)

    # 2. Paiement
    enregistrer_payment_handlers(bot)

    # 3. Premium (coupons + top affiches)
    enregistrer_premium_handlers(bot)

    # 4. Prédictions (boutons inline)
    enregistrer_prediction_handlers(bot)

    # 5. Commandes utilisateur (stats, historique, notifs, langue, parrainage)
    enregistrer_user_handlers(bot)

    # 6. Menu principal + /start (fallback, EN DERNIER)
    enregistrer_menu_handlers(bot)

    print("✅ Handlers utilisateur enregistrés dans le bon ordre")
