"""Compatibilité historique : importez depuis telegram_bot.payments.handlers."""

from telegram_bot.payments.handlers import enregistrer_payment_handlers

__all__ = ["enregistrer_payment_handlers"]
