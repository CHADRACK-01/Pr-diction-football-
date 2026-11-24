"""Protection des routes HTTP administratives."""

from functools import wraps

from flask import request

from core.securite import verifier_token_admin
from core.utils.logs import log_warning


def secret_est_valide():
    fourni = request.args.get("secret") or request.headers.get("X-Admin-Secret")
    return verifier_token_admin(fourni)


def admin_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if not secret_est_valide():
            log_warning(
                message="Accès refusé à une route admin",
                module="FLASK",
                extra={"route": request.path, "ip": request.remote_addr},
            )
            return "🔒 Accès refusé. Secret manquant ou invalide.", 403
        return view(*args, **kwargs)

    return wrapper
