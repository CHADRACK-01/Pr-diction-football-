"""Tests de gouvernance des modèles et QA."""

from core.model_governance import detecter_drift
from core.qa_extension import verifier_reponse_prediction, executer_checks_qa


def test_drift_detection():
    assert detecter_drift(0.20, 0.26, tolerance=0.20)["drift"] is True
    assert detecter_drift(0.20, 0.21, tolerance=0.20)["drift"] is False


def test_prediction_normalisee():
    resultat = verifier_reponse_prediction({"p_h": 0.5, "p_d": 0.2, "p_a": 0.3})
    assert resultat["valide"] is True


def test_qa_reussit():
    resultat = executer_checks_qa(
        utilisateur={"user_id": 1, "first_name": "Test", "status": "free"},
        prediction={"p_h": 0.4, "p_d": 0.3, "p_a": 0.3},
        sources=["2099-01-01T12:00:00"],
    )
    assert "valide" in resultat
