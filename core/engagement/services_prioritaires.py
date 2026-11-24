"""Services P0/P1 réutilisables : essai Premium et dashboard administrateur."""

from core.administration.feature_flags import est_active

_ESSAIS_ACTIVES = set()


def demarrer_essai_premium(user_id):
    """Accorde une seule fois 24 heures Premium à un utilisateur."""
    if not est_active("32"):
        return False
    if user_id in _ESSAIS_ACTIVES:
        return False

    from users.account_base import ajouter_jours_premium
    if not ajouter_jours_premium(user_id, 1):
        return False

    _ESSAIS_ACTIVES.add(user_id)
    return True


def construire_dashboard_admin():
    """Construit les compteurs essentiels du dashboard administrateur."""
    from users import get_stats_globales
    from users.admin import get_liste_bannis
    from users.paiements import get_demandes_en_attente

    stats = get_stats_globales()
    return {
        "utilisateurs": {
            "total": stats.get("total", 0),
            "premium": stats.get("premium", 0),
            "free": stats.get("free", 0),
        },
        "paiements_en_attente": len(get_demandes_en_attente(limite=1000)),
        "utilisateurs_bannis": len(get_liste_bannis()),
    }
