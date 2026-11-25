"""Tests unitaires du flux métier Telegram Stars."""

from types import SimpleNamespace

import pytest

from telegram_bot.payments import PaiementInvalide, valider_paiement_stars


ABONNEMENTS = {
    "mensuel": {"nom": "Mensuel", "prix_stars": 250, "duree_jours": 30}
}


def test_paiement_stars_valide():
    payment = SimpleNamespace(
        invoice_payload="abo_mensuel_123",
        currency="XTR",
        total_amount=250,
        telegram_payment_charge_id="charge-1",
    )
    resultat = valider_paiement_stars(payment, ABONNEMENTS, 123)
    assert resultat.user_id == 123
    assert resultat.abo_key == "mensuel"
    assert resultat.reference == "stars:charge-1"


def test_paiement_rejete_si_mauvais_utilisateur():
    payment = SimpleNamespace(invoice_payload="abo_mensuel_999", currency="XTR", total_amount=250)
    with pytest.raises(PaiementInvalide):
        valider_paiement_stars(payment, ABONNEMENTS, 123)


def test_paiement_rejete_si_mauvaise_devise():
    payment = SimpleNamespace(invoice_payload="abo_mensuel_123", currency="USD", total_amount=250)
    with pytest.raises(PaiementInvalide):
        valider_paiement_stars(payment, ABONNEMENTS, 123)


def test_paiement_rejete_si_mauvais_montant():
    payment = SimpleNamespace(invoice_payload="abo_mensuel_123", currency="XTR", total_amount=1)
    with pytest.raises(PaiementInvalide):
        valider_paiement_stars(payment, ABONNEMENTS, 123)
