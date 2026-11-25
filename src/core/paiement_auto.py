# core/paiement_auto.py
"""
Shim de compatibilité historique.

L'adaptateur de paiement Mobile Money vit désormais dans
``core.adaptateurs.paiements.AdaptateurPaiementMobileMoney``.
"""

from core.adaptateurs.paiements import AdaptateurPaiementMobileMoney  # noqa: F401

__all__ = ["AdaptateurPaiementMobileMoney"]

def verifier_paiement_auto(*args, **kwargs):
    """Déprécié : utilisez AdaptateurPaiementMobileMoney.verifier_reference."""
    adaptateur = AdaptateurPaiementMobileMoney()
    return adaptateur.verifier_reference(*args, **kwargs)
