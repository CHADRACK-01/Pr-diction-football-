"""Accès centralisé aux variables d'environnement critiques."""

import os


def lire_env(nom, defaut=""):
    """Lit une variable sans exposer sa valeur dans les logs."""
    return os.environ.get(nom, defaut).strip()


def lire_bool(nom, defaut=False):
    valeur = lire_env(nom)
    if not valeur:
        return defaut
    return valeur.lower() in {"1", "true", "yes", "on"}


def lire_liste(nom, separateur=","):
    brut = lire_env(nom)
    if not brut:
        return []
    return [item.strip() for item in brut.split(separateur) if item.strip()]
