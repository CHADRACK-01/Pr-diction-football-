"""Tests des adaptateurs externes avec fournisseurs simulés."""

from core.payments import mobile_provider as paiement_auto


def test_paiement_mobile_reste_manuel_sans_configuration(monkeypatch):
    monkeypatch.setattr(paiement_auto, "AIRTEL_API_KEY", "")
    success, message = paiement_auto.verifier_paiement_auto(
        "Airtel", "0821234567", 100.0, "TX-AIRTEL-1"
    )
    assert success is False
    assert "manuelle" in message.lower()


def test_paiement_mobile_accepte_reponse_api_success(monkeypatch):
    class Reponse:
        status_code = 200

        def json(self):
            return {"status": "SUCCESS", "reference": "TX-ORANGE-1"}

    monkeypatch.setattr(paiement_auto, "ORANGE_API_KEY", "secret-test")
    monkeypatch.setattr(paiement_auto, "ORANGE_API_URL", "https://operator.example/verify")
    monkeypatch.setattr(paiement_auto.requests, "post", lambda *args, **kwargs: Reponse())

    success, message = paiement_auto.verifier_paiement_auto(
        "Orange", "0842453217", 100.0, "TX-ORANGE-1"
    )
    assert success is True
    assert "succès" in message.lower()


def test_paiement_mobile_refuse_operateur_inconnu():
    success, message = paiement_auto.verifier_paiement_auto(
        "Operateur-X", "000", 100.0, "TX-X"
    )
    assert success is False
    assert "opérateur" in message.lower()
