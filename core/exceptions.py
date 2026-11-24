# core/exceptions.py
"""
Hiérarchie d'exceptions personnalisées du bot de pronostics football.

Chaque domaine métier possède sa propre exception, toutes héritant de
``BotException``. Cela permet :
- un ciblage précis des `except` (jamais de `except Exception` nu) ;
- l'ajout de contexte métier (code, détails) sans polluer le message ;
- une conversion explicite en réponse utilisateur (Telegram / admin).
"""


class BotException(Exception):
    """Exception de base pour toutes les erreurs métier du bot."""

    def __init__(self, message: str, code: str | None = None, details: dict | None = None):
        super().__init__(message)
        self.message = message
        self.code = code or self.__class__.__name__
        self.details = details or {}

    def to_dict(self) -> dict:
        return {
            "exception": self.__class__.__name__,
            "code": self.code,
            "message": self.message,
            "details": self.details,
        }


# ---------------------------------------------------------------------------
# Configuration et démarrage
# ---------------------------------------------------------------------------


class ConfigurationError(BotException):
    """Variable d'environnement manquante ou invalide au démarrage."""


class ConfigurationIncoherenteError(ConfigurationError):
    """Seuils ou paramètres de configuration incohérents entre eux."""


# ---------------------------------------------------------------------------
# Base de données
# ---------------------------------------------------------------------------


class DatabaseError(BotException):
    """Échec d'une opération sur la base Turso/libSQL."""


class TableManquanteError(DatabaseError):
    """Une table requise est absente de la base."""


class ConnexionBaseIndisponibleError(DatabaseError):
    """Impossible d'établir la connexion à la base (Turso)."""


# ---------------------------------------------------------------------------
# Modèle de prédiction
# ---------------------------------------------------------------------------


class ModeleIndisponibleError(BotException):
    """Aucun modèle ML chargé ou bundle non conforme au contrat."""


class ContratModeleInvalideError(ModeleIndisponibleError):
    """Le bundle sérialisé ne respecte pas le contrat de version/features."""


class DonneesEntrainementInsuffisantesError(ModeleIndisponibleError):
    """Pas assez de matchs pour entraîner ou charger un modèle fiable."""


# ---------------------------------------------------------------------------
# Prédiction métier
# ---------------------------------------------------------------------------


class PredictionError(BotException):
    """Échec lors du calcul d'une prédiction (match, score, probabilité)."""


class FeaturesInsuffisantesError(PredictionError):
    """Historique d'équipe insuffisant pour calculer les features."""


class ProbabiliteInvalideError(PredictionError):
    """Probabilités hors bornes [0,1] ou somme non normalisée."""


# ---------------------------------------------------------------------------
# Paris et risque
# ---------------------------------------------------------------------------


class PariError(BotException):
    """Erreur sur un pari, coupon ou gestion de bankroll."""


class CoteInvalideError(PariError):
    """Cote bookmaker absente ou <= 1.0."""


class BankrollInsuffisanteError(PariError):
    """Mise demandée supérieure au plafond autorisé par la bankroll."""


# ---------------------------------------------------------------------------
# APIs externes
# ---------------------------------------------------------------------------


class ApiExterneError(BotException):
    """Échec d'un appel à une API externe (football, paiement, météo)."""


class QuotaApiDepasseError(ApiExterneError):
    """Quota d'une clé API atteint ou dépassé."""


class SourceApiIndisponibleError(ApiExterneError):
    """Source de données indisponible, bascule possible vers une autre."""


# ---------------------------------------------------------------------------
# Utilisateurs, abonnements, paiements
# ---------------------------------------------------------------------------


class UtilisateurError(BotException):
    """Erreur liée à un utilisateur (inexistant, banni, statut invalide)."""


class AbonnementExpiréError(UtilisateurError):
    """L'abonnement Premium de l'utilisateur est expiré."""


class PaiementError(BotException):
    """Échec d'un paiement Mobile Money ou d'un code promo."""


class CodePromoInvalideError(PaiementError):
    """Code promo inexistant, épuisé ou expiré."""


# ---------------------------------------------------------------------------
# Fonctionnalités et feature flags
# ---------------------------------------------------------------------------


class FonctionnaliteInactiveError(BotException):
    """Fonctionnalité désactivée via le catalogue des feature flags."""


class FonctionnaliteInconnueError(BotException):
    """Identifiant de fonctionnalité absent du catalogue."""
