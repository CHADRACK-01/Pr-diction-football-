"""Helpers de sécurité réutilisables (authentification admin, échappement HTML)."""

import html
import hmac
import os


def verifier_token_admin(token: str) -> bool:
    """
    Vérifie que le token fourni correspond à la variable d'environnement ADMIN_SECRET.

    Refuse si le secret est absent ou vide, ou si le token n'est pas une chaîne
    non vide. La comparaison est faite à temps constant (hmac.compare_digest).
    """
    secret_attendu = os.environ.get("ADMIN_SECRET", "")
    if not secret_attendu:
        return False
    if not isinstance(token, str) or not token:
        return False
    return hmac.compare_digest(secret_attendu, token)


def nettoyer_html(texte: str) -> str:
    """
    Échappe les caractères <, > et & pour éviter les injections HTML dans
    les messages Telegram envoyés avec parse_mode HTML.

    Les guillemets ne sont pas touchés (quote=False).
    """
    if texte is None:
        return ""
    return html.escape(str(texte), quote=False)
