# core/services/__init__.py
"""
Services métier du bot de pronostics football.

Chaque service encapsule la logique métier d'un domaine (prédiction, paris,
risque, paiement, utilisateurs, alertes, administration) et utilise les
adaptateurs injectables pour les dépendances externes.

Convention : chaque service expose des fonctions pures avec des entrées
validées (core/domaine.py) et lève des exceptions métier (core/exceptions.py)
en cas d'erreur. Jamais de succès simulé.
"""

from core.services.prediction import ServicePrediction
from core.services.paris import ServiceParis
from core.services.risque import ServiceRisque
from core.services.paiement import ServicePaiement
from core.services.utilisateurs import ServiceUtilisateurs
from core.services.alertes import ServiceAlertes
from core.services.admin import ServiceAdmin

__all__ = [
    "ServicePrediction",
    "ServiceParis",
    "ServiceRisque",
    "ServicePaiement",
    "ServiceUtilisateurs",
    "ServiceAlertes",
    "ServiceAdmin",
]
