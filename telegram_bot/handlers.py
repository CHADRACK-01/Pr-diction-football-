"""
Point d'entrée des handlers Telegram.
Enregistre tous les modules dans le bon ordre.
"""

from telegram_bot.menu_handlers import enregistrer_menu_handlers
from telegram_bot.prediction_handlers import enregistrer_prediction_handlers
from telegram_bot.user_handlers import enregistrer_user_handlers
from telegram_bot.payment_handlers import enregistrer_payment_handlers


def enregistrer_handlers(bot):
    """
    Enregistre tous les handlers utilisateur.
    ⚠️ L'ORDRE est important :
    - Les commandes spécifiques AVANT le fallback du menu.
    """

    # 1. Paiement (avant les autres car successful_payment est prioritaire)
    enregistrer_payment_handlers(bot)

    # 2. Prédictions (boutons inline)
    enregistrer_prediction_handlers(bot)

    # 3. Commandes utilisateur (stats, historique, notifs, langue, parrainage)
    enregistrer_user_handlers(bot)

    # 4. Menu principal + /start (fallback, EN DERNIER)
    enregistrer_menu_handlers(bot)

    print("✅ Handlers utilisateur enregistrés")
