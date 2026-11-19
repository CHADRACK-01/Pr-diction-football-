"""
Point d'entrée des handlers Telegram.
Ce fichier orchestre l'enregistrement de tous les modules.

ORDRE CRITIQUE :
1. Start (le plus prioritaire)
2. Admin / Panique
3. Fonctionnalités
4. Paiements / Prédictions / IA
5. MenuCommandes AVANT Fallback (sinon fallback intercepte les boutons admin)
6. Fallback EN DERNIER (attrape tout ce qui n'a pas été traité)
"""

# 1. Le Start en PREMIER
from telegram_bot.handlers.start import enregistrer_start_handlers

# 2. L'Admin ensuite
from telegram_bot.admin_handlers import enregistrer_admin_handlers

# Panique (réservé aux administrateurs)
from telegram_bot.panique_handlers import enregistrer_panique_handlers

# 3. Les modules de fonctionnalités
from telegram_bot.handlers.pronostic import enregistrer_pronostic_handlers
from telegram_bot.premium_handlers import enregistrer_premium_handlers
from telegram_bot.handlers.premium_menu import enregistrer_premium_menu_handlers
from telegram_bot.handlers.notifications import enregistrer_notifications_handlers
from telegram_bot.handlers.historique import enregistrer_historique_handlers
from telegram_bot.handlers.statistiques import enregistrer_statistiques_handlers
from telegram_bot.handlers.parrainage import enregistrer_parrainage_handlers
from telegram_bot.devises_handlers import enregistrer_devises_handlers
from telegram_bot.preuves_handlers import enregistrer_preuves_handlers

# Codes Promo (manuels)
from telegram_bot.codes_promo_handlers import enregistrer_codes_promo_handlers
from telegram_bot.utilisation_code_handlers import enregistrer_utilisation_code_handlers

# 4. Les paiements et prédictions
from telegram_bot.payment_handlers import enregistrer_payment_handlers
from telegram_bot.prediction_handlers import enregistrer_prediction_handlers

# Le Bot Auto-évolutif (IA)
from telegram_bot.ai_dev_handlers import enregistrer_ai_dev_handlers

# 5. Fonctionnalités annexes (commandes admin paramétrées)
from telegram_bot.momentum_handlers import enregistrer_momentum_handlers
from telegram_bot.fiabilite_handlers import enregistrer_fiabilite_handlers
from telegram_bot.pieges_handlers import enregistrer_pieges_handlers
from telegram_bot.comparateur_handlers import enregistrer_comparateur_handlers
from telegram_bot.favoris_handlers import enregistrer_favoris_handlers
from telegram_bot.meteo_handlers import enregistrer_meteo_handlers
from telegram_bot.bookmakers_handlers import enregistrer_bookmakers_handlers
from telegram_bot.cashout_handlers import enregistrer_cashout_handlers
from telegram_bot.bankroll_handlers import enregistrer_bankroll_handlers

# 6. MenuCommandes AVANT Fallback (sinon les boutons admin sont interceptés)
from telegram_bot.menu_commandes_handlers import enregistrer_menu_commandes_handlers

# 7. Le Fallback en TOUT DERNIER
from telegram_bot.handlers.fallback import enregistrer_fallback_handlers


def enregistrer_handlers(bot):
    handlers_modules = [
        # --- Priorité haute ---
        ("Start", enregistrer_start_handlers),
        ("Admin", enregistrer_admin_handlers),
        ("Panique", enregistrer_panique_handlers),
        # --- Fonctionnalités principales ---
        ("Pronostic", enregistrer_pronostic_handlers),
        ("Premium", enregistrer_premium_handlers),
        ("Premium Menu", enregistrer_premium_menu_handlers),
        ("Notifs", enregistrer_notifications_handlers),
        ("Historique", enregistrer_historique_handlers),
        ("Stats", enregistrer_statistiques_handlers),
        ("Parrainage", enregistrer_parrainage_handlers),
        ("Devises", enregistrer_devises_handlers),
        ("Preuves", enregistrer_preuves_handlers),
        # --- Codes promo ---
        ("CodesPromo", enregistrer_codes_promo_handlers),
        ("UtilisationCode", enregistrer_utilisation_code_handlers),
        # --- Paiements & prédictions ---
        ("Paiement", enregistrer_payment_handlers),
        ("Prédiction", enregistrer_prediction_handlers),
        ("Fiabilite", enregistrer_fiabilite_handlers),
        ("Momentum", enregistrer_momentum_handlers),
        ("Pieges", enregistrer_pieges_handlers),
        ("Comparateur", enregistrer_comparateur_handlers),
        ("Favoris", enregistrer_favoris_handlers),
        ("Meteo", enregistrer_meteo_handlers),
        ("Bookmakers", enregistrer_bookmakers_handlers),
        ("AI_Dev", enregistrer_ai_dev_handlers),
        ("Bankroll", enregistrer_bankroll_handlers),
        ("Cashout", enregistrer_cashout_handlers),
        # --- Menu admin (doit passer AVANT Fallback) ---
        ("MenuCommandes", enregistrer_menu_commandes_handlers),
        # --- Fallback EN DERNIER ---
        ("Fallback", enregistrer_fallback_handlers),
    ]

    for nom, enregistrer in handlers_modules:
        try:
            enregistrer(bot)
            print(f"✅ Module {nom} enregistré.")
        except Exception as e:
            print(f"❌ Erreur d'enregistrement du module {nom} : {e}")

    noms = " -> ".join([nom for nom, _ in handlers_modules])
    print(f"✅ Handlers enregistrés dans l'ordre : {noms}")
