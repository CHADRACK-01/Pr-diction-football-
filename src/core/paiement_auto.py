"""Compatibilité historique : importez depuis core.payments."""

from core.payments.mobile_provider import verifier_paiement_auto

__all__ = ["verifier_paiement_auto"]
