"""Validation métier centralisée des paiements et crédits Premium."""

import math

from core.payments import ABONNEMENTS


def valider_abonnement(abo_key):
    abo = ABONNEMENTS.get(str(abo_key or "").strip().lower())
    if not abo:
        raise ValueError("Abonnement inconnu")
    duree = int(abo.get("duree_jours", 0))
    if duree <= 0:
        raise ValueError("Durée Premium invalide")
    return abo_key, abo


def valider_montant_cdf(montant, montant_attendu):
    try:
        montant = float(montant)
        montant_attendu = float(montant_attendu)
    except (TypeError, ValueError):
        raise ValueError("Montant CDF invalide")
    if not math.isfinite(montant) or montant <= 0:
        raise ValueError("Montant CDF invalide")
    if not math.isclose(montant, montant_attendu, rel_tol=0.0, abs_tol=0.01):
        raise ValueError("Montant différent du tarif configuré")
    return round(montant, 2)


def valider_reference(reference):
    reference = str(reference or "").strip()
    if not reference or len(reference) > 128:
        raise ValueError("Référence de paiement invalide")
    if any(caractere in reference for caractere in ("\n", "\r", "\x00")):
        raise ValueError("Référence de paiement invalide")
    return reference


def valider_credit(reference, user_id, jours):
    reference = valider_reference(reference)
    if not isinstance(user_id, int) or user_id <= 0:
        raise ValueError("Utilisateur invalide")
    if not isinstance(jours, int) or jours <= 0 or jours > 365:
        raise ValueError("Durée du crédit invalide")
    return reference, user_id, jours
