from core.utils.logs import log_error, log_warning


def gerer_erreur_api(status_code, competition, module="API"):
    """
    Gère les erreurs HTTP de l'API football-data.org.
    Retourne True si on peut continuer, False s'il faut arrêter.
    """
    if status_code == 403:
        log_error(f"Accès refusé à l'API ({competition}). Vérifie ta clé API.", module)
        return False
    elif status_code == 404:
        log_warning(f"Compétition introuvable ({competition}).", module)
        return False
    elif status_code == 429:
        log_error("Trop de requêtes envoyées à l'API (Rate Limit). Pause nécessaire.", module)
        return False
    elif status_code == 500:
        log_error("Erreur interne du serveur de l'API (500).", module)
        return False
    else:
        log_error(f"Erreur API inconnue ({status_code}) pour {competition}.", module)
        return False
