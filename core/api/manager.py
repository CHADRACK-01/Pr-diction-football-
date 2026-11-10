from core.api import bzzoiro, openligadb, football_data
from core.utils.logs import log_info, log_warning, log_error


def get_matchs_du_jour():
    """
    Récupère les matchs du jour en essayant les sources dans l'ordre :
    1. Bzzoiro (prioritaire : live, xG, cotes)
    2. Football-Data.org (backup principal : 5 grands championnats + C1)
    3. OpenLigaDB (backup ultime : Bundesliga uniquement)
    Retourne une liste de matchs (vide si tout échoue).
    """
    log_info("Début de la récupération des matchs via le manager...", "MANAGER")
    
    # 1. Bzzoiro
    try:
        if bzzoiro.tester_api():
            matchs = bzzoiro.get_matchs_du_jour()
            if matchs:
                log_info(f"✅ {len(matchs)} matchs récupérés via Bzzoiro.", "MANAGER")
                return matchs
            else:
                log_warning("Bzzoiro n'a renvoyé aucun match.", "MANAGER")
        else:
            log_warning("Bzzoiro est HS, on passe à Football-Data.org.", "MANAGER")
    except Exception as e:
        log_error("Erreur Bzzoiro dans le manager", "MANAGER", exception=e)

    # 2. Football-Data.org (backup principal)
    try:
        matchs = football_data.recuperer_matchs_bruts()
        if matchs:
            log_info(f"✅ {len(matchs)} matchs récupérés via Football-Data.org.", "MANAGER")
            return matchs
        else:
            log_warning("Football-Data.org n'a renvoyé aucun match.", "MANAGER")
    except Exception as e:
        log_error("Erreur Football-Data.org dans le manager", "MANAGER", exception=e)

    # 3. OpenLigaDB (backup ultime : Bundesliga uniquement)
    try:
        if openligadb.tester_api():
            matchs = openligadb.get_matchs_du_jour()
            if matchs:
                log_info(f"✅ {len(matchs)} matchs récupérés via OpenLigaDB (backup ultime).", "MANAGER")
                return matchs
            else:
                log_warning("OpenLigaDB n'a renvoyé aucun match.", "MANAGER")
        else:
            log_warning("OpenLigaDB est HS.", "MANAGER")
    except Exception as e:
        log_error("Erreur OpenLigaDB dans le manager", "MANAGER", exception=e)

    # ❌ Si toutes les sources ont échoué
    log_error(
        "AUCUNE source n'a pu fournir de matchs. Toutes les APIs sont potentiellement HS ou mal configurées.",
        "MANAGER"
    )
    return []
