# tests/conftest.py
"""Utilitaires partagés par la suite de tests.

Aucun import de ``config`` au niveau module : chaque vérification déclenche
l'import dans un sous-processus isolé, afin de contrôler précisément
l'environnement et d'observer le comportement au démarrage.
"""

import os
import subprocess
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Environnement minimal valide, point de départ de chaque sous-processus.
ENV_VALIDE = {
    "TELEGRAM_TOKEN": "token-de-test",
    "TURSO_URL": "libsql://base-de-test",
    "TURSO_TOKEN": "token-turso-de-test",
    "ADMIN_ID": "123456789",
    "CANAL_ID": "-1001234567890",
}

# Variables lues par config : neutralisées pour ne jamais fuiter depuis l'hôte.
VARIABLES_CONFIG = (
    "TELEGRAM_TOKEN",
    "TURSO_URL",
    "TURSO_TOKEN",
    "ADMIN_ID",
    "CANAL_ID",
    "CANAL_USERNAME",
    "CANAL_LIEN",
    "MODE_VITRINE",
    "MODE_TEST",
    "RENDER",
    "VALUE_BET_MIN_EV",
    "COTE_MIN_RECO",
    "SEUIL_CONF_SUR",
    "SEUIL_CONF_MODERE",
    "SEUIL_CONF_RISQUE",
    "FACTEUR_MT",
    "BANDE_OUTSIDE_MIN",
    "BANDE_OUTSIDE_MAX",
    "SEUIL_DIVERGENCE_DC",
    "COEF_AVANTAGE_TERRAIN",
    "POISSON_MAX_BUTS",
)



def lancer_code_config(env, code):
    """
    Exécute ``code`` (qui importe ``config``) dans un sous-processus isolé.

    L'environnement du sous-processus part de ``ENV_VALIDE`` puis applique
    ``env`` ; une valeur ``None`` retire la variable correspondante, ce qui
    permet de simuler les cas d'absence. Retourne le ``CompletedProcess``.
    """
    environnement = {
        cle: valeur
        for cle, valeur in os.environ.items()
        if cle not in VARIABLES_CONFIG
    }
    environnement.update(ENV_VALIDE)
    for cle, valeur in env.items():
        if valeur is None:
            environnement.pop(cle, None)
        else:
            environnement[cle] = valeur

    return subprocess.run(
        [sys.executable, "-c", code],
        cwd=RACINE,
        env=environnement,
        capture_output=True,
        text=True,
    )


def lancer_import_config(env):
    """Importe ``config`` puis exécute ``config.verifier_configuration()``."""
    return lancer_code_config(
        env, "import config; config.verifier_configuration()"
    )
