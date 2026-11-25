"""Handlers Telegram regroupés par domaine de consultation."""

from telegram_bot.consultation.codes_promo import (
    enregistrer_codes_promo_handlers,
    enregistrer_utilisation_code_handlers,
)
from telegram_bot.consultation.devises import (
    DEVISES_VALIDES,
    _assurer_colonne_devise,
    _clavier_devises,
    _ligne_taux,
    _texte_devise,
    enregistrer_devises_handlers,
    get_devise,
    set_devise,
)
from telegram_bot.consultation.preuves import enregistrer_preuves_handlers

__all__ = [
    "DEVISES_VALIDES",
    "_assurer_colonne_devise",
    "_clavier_devises",
    "_ligne_taux",
    "_texte_devise",
    "enregistrer_codes_promo_handlers",
    "enregistrer_devises_handlers",
    "enregistrer_preuves_handlers",
    "enregistrer_utilisation_code_handlers",
    "get_devise",
    "set_devise",
]
