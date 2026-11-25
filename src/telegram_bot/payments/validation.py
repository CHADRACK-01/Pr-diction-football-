"""Validation pure des paiements Telegram.

Ce module ne dépend pas de pyTelegramBotAPI ni du stockage. Les handlers
ne conservent que l'envoi/réception et délèguent les règles à ce service.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class PaiementStarsValide:
    user_id: int
    abo_key: str
    duree_jours: int
    montant_stars: int
    reference: str


class PaiementInvalide(ValueError):
    pass


def valider_paiement_stars(payment, abonnements, user_id):
    """Valide le payload, la devise, la formule et le montant d'un paiement."""
    try:
        payload = str(payment.invoice_payload or "")
        if f"_{user_id}" not in payload:
            raise PaiementInvalide("payload utilisateur")

        if str(payment.currency) != "XTR":
            raise PaiementInvalide("devise")

        parts = payload.split("_")
        abo_key = parts[1] if len(parts) >= 2 else ""
        abonnement = abonnements.get(abo_key)
        if abonnement is None:
            raise PaiementInvalide("formule")

        montant = int(payment.total_amount)
        montant_attendu = int(abonnement["prix_stars"])
        if montant != montant_attendu:
            raise PaiementInvalide("montant")

        charge_id = str(getattr(payment, "telegram_payment_charge_id", "") or "")
        reference = f"stars:{charge_id}" if charge_id else (
            f"stars_payload:{payload}:{user_id}:{montant}"
        )

        return PaiementStarsValide(
            user_id=user_id,
            abo_key=abo_key,
            duree_jours=int(abonnement["duree_jours"]),
            montant_stars=montant,
            reference=reference,
        )
    except PaiementInvalide:
        raise
    except (AttributeError, TypeError, ValueError) as exc:
        raise PaiementInvalide("structure") from exc
