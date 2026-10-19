from core.api import bzzoiro, openligadb, football_data
from core.utils.logs import log_info, log_warning, log_error


def get_matchs_du_jour():
    """
    Récupère les matchs du jour en essayant les sources dans l'ordre :
    1. Bzzoiro (prioritaire : live, xG, cotes)
    2. OpenLigaDB (backup : Bundesliga)
    3. Football-Data (backup ultime : ancienne API)
    """
    log_info("Début de la récupération des matchs via le manager...", "MANAGER")
    
    # 1. Bzzoiro
    if bzzoiro.tester_api():
        matchs = bzzoiro.get_matchs_du_jour()
        if matchs:
            log_info(f"✅ {len(matchs)} matchs récupérés via Bzzoiro.", "MANAGER")
            return matchs
        log_warning("Bzzoiro n'a renvoyé aucun match.", "MANAGER")
    else:
        log_warning("Bzzoiro est HS, on passe à OpenLigaDB.", "MANAGER")

    # 2. OpenLigaDB
    if openligadb.tester_api():
        matchs = openligadb.get_matchs_du_jour()
        if matchs:
            log_info(f"✅ {len(matchs)} matchs récupérés via OpenLigaDB.", "MANAGER")
            return matchs
        log_warning("OpenLigaDB n'a renvoyé aucun match.", "MANAGER")
    else:
        log_warning("OpenLigaDB est HS, on passe à Football-Data.", "MANAGER")

    # 3. Football-Data (backup ultime)
    if hasattr(football_data, 'recuperer_matchs_bruts'):
        matchs = football_data.recuperer_matchs_bruts()
        if matchs:
            log_info(f"✅ {len(matchs)} matchs récupérés via Football-Data (backup).", "MANAGER")
            return matchs

    log_error("❌ Aucune source n'a pu fournir de matchs.", "MANAGER")
    return []
