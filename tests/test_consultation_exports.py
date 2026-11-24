"""Contrats d'import pour les nouveaux modules Telegram de consultation."""


def test_exports_consultation_sont_compatibles():
    from telegram_bot.consultation import (
        enregistrer_codes_promo_handlers,
        enregistrer_devises_handlers,
        enregistrer_preuves_handlers,
        enregistrer_utilisation_code_handlers,
    )

    assert callable(enregistrer_codes_promo_handlers)
    assert callable(enregistrer_devises_handlers)
    assert callable(enregistrer_preuves_handlers)
    assert callable(enregistrer_utilisation_code_handlers)


def test_ancien_module_reexporte_les_nouveaux_handlers():
    from telegram_bot.consultation.codes_promo import (
        enregistrer_codes_promo_handlers as nouveau_creation,
        enregistrer_utilisation_code_handlers as nouveau_utilisation,
    )
    from telegram_bot.consultation.devises import enregistrer_devises_handlers as nouveau_devises
    from telegram_bot.consultation.preuves import enregistrer_preuves_handlers as nouveau_preuves
    from telegram_bot.consultation_handlers import (
        enregistrer_codes_promo_handlers as historique_creation,
        enregistrer_devises_handlers as historique_devises,
        enregistrer_preuves_handlers as historique_preuves,
        enregistrer_utilisation_code_handlers as historique_utilisation,
    )

    assert historique_creation is nouveau_creation
    assert historique_devises is nouveau_devises
    assert historique_preuves is nouveau_preuves
    assert historique_utilisation is nouveau_utilisation
