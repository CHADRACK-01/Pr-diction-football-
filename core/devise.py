# core/devises.py
"""
Fonctionnalité 416 : Gestion des devises multiples (CDF, USD, EUR).
Permet de convertir un montant CDF en USD ou EUR selon les taux configurés.
"""

from users.admin import get_parametre
from core.utils.logs import log_info, log_error

# Taux par défaut (si non configurés dans l'admin)
TAUX_DEFAUT = {
    "USD": 2800,  # 1 USD = 2800 CDF
    "EUR": 3000,  # 1 EUR = 3000 CDF
}

def get_taux_change(devise):
    """Récupère le taux de change depuis la BDD (ou utilise le défaut)."""
    if devise == "CDF":
        return 1.0
    try:
        taux_str = get_parametre(f"taux_{devise.lower()}", str(TAUX_DEFAUT.get(devise, 1)))
        return float(taux_str)
    except Exception as e:
        log_error(f"Impossible de récupérer le taux pour {devise}", "DEVISES", exception=e)
        return TAUX_DEFAUT.get(devise, 1.0)

def convertir_montant(montant_cdf, devise_cible):
    """Convertit un montant CDF vers la devise cible."""
    if devise_cible == "CDF":
        return montant_cdf
    
    taux = get_taux_change(devise_cible)
    if taux <= 0:
        return montant_cdf
        
    montant_converti = montant_cdf / taux
    
    # Arrondi propre
    if devise_cible == "USD":
        return round(montant_converti, 2)
    elif devise_cible == "EUR":
        return round(montant_converti, 2)
    return montant_converti

def formater_prix(montant_cdf, devise="CDF"):
    """Retourne une chaîne formatée avec le symbole de la devise."""
    montant = convertir_montant(montant_cdf, devise)
    
    if devise == "CDF":
        return f"{montant:,.0f} CDF".replace(",", " ")
    elif devise == "USD":
        return f"{montant:.2f} $"
    elif devise == "EUR":
        return f"{montant:.2f} €"
    return f"{montant} {devise}"
