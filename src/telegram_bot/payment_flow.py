"""Compatibilité historique : importez depuis telegram_bot.payments."""

from telegram_bot.payments.validation import PaiementInvalide, valider_paiement_stars

__all__ = ["PaiementInvalide", "valider_paiement_stars"]
