# core/devises.py
"""
Fonctionnalité 416 : Gestion des devises multiples (CDF, USD, EUR).
Permet de convertir un montant CDF en USD ou EUR selon les taux configurés.

⚠️ Politique d'erreur :
- Si le taux n'est pas disponible (BDD KO, config absente), on retourne
  None au lieu de 1.0 pour éviter d'afficher des montants faux (ex.
  "10 000 CDF = 10 000 $").
- formater_prix affiche "taux indisponible" dans ce cas.
"""

from users.admin import get_parametre
from core.utils.logs import log_info, log_error

# Taux par défaut (si non configurés dans l'admin)
TAUX_DEFAUT = {
    "USD": 2800,  # 1 USD = 2800 CDF
    "EUR": 3000,  # 1 EUR = 3000 CDF
}

DEVISES_VALIDES = ("CDF", "USD", "EUR")


def get_taux_change(devise):
    """Récupère le taux de change depuis la BDD (ou utilise le défaut).

    Retourne :
    - 1.0 pour CDF (par définition)
    - un float > 0 pour USD/EUR si le taux est disponible
    - None si le taux n'est pas disponible (erreur BDD, valeur invalide…)
    """
    if devise == "CDF":
        return 1.0

    if devise not in DEVISES_VALIDES:
        log_error(f"Devise inconnue : {devise}", "DEVISES")
        return None

    try:
        taux_str = get_parametre(
            f"taux_{devise.lower()}",
            str(TAUX_DEFAUT.get(devise, "")),
        )
        if not taux_str:
            log_error(
                f"Aucun taux disponible pour {devise}",
                "DEVISES",
                extra={"devise": devise},
            )
            return None
        taux = float(taux_str)
        if taux <= 0:
            log_error(
                f"Taux invalide pour {devise} : {taux}",
                "DEVISES",
                extra={"devise": devise, "taux": taux},
            )
            return None
        return taux
    except Exception as e:
        log_error(
            f"Impossible de récupérer le taux pour {devise}",
            "DEVISES",
            extra={"devise": devise},
            exception=e,
        )
        return None


def convertir_montant(montant_cdf, devise_cible):
    """Convertit un montant CDF vers la devise cible.

    Retourne None si la conversion est impossible (taux indisponible).
    """
    if devise_cible == "CDF":
        return montant_cdf

    taux = get_taux_change(devise_cible)
    if taux is None:
        return None
    if taux <= 0:
        return None

    montant_converti = montant_cdf / taux

    # Arrondi propre
    if devise_cible in ("USD", "EUR"):
        return round(montant_converti, 2)
    return montant_converti


def formater_prix(montant_cdf, devise="CDF"):
    """Retourne une chaîne formatée avec le symbole de la devise.

    Si le taux est indisponible, affiche "taux indisponible" au lieu d'un
    montant faux.
    """
    montant = convertir_montant(montant_cdf, devise)

    if montant is None:
        return f"taux {devise} indisponible"

    if devise == "CDF":
        return f"{montant:,.0f} CDF".replace(",", " ")
    elif devise == "USD":
        return f"{montant:.2f} $"
    elif devise == "EUR":
        return f"{montant:.2f} €"
    return f"{montant} {devise}"
