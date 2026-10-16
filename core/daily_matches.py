from core.fixtures import get_matchs_du_jour, formater_matchs_du_jour as format_fixtures


def matchs_du_jour(date_cible=None):
    """
    Récupère les matchs du jour via Football-Data.org.
    Retourne un texte formaté pour Telegram.
    """
    matches = get_matchs_du_jour(date_cible)
    return format_fixtures(matches)
