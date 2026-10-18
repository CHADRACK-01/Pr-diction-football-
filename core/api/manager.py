from core.api import bzzoiro, openligadb
from core.api import football_data # Ton ancienne API (on va la garder en backup)
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
    try:
        if bzzoiro.tester_api():
            matchs = bzzoiro.get_matchs_du_jour()
            if matchs:
                log_info(f"✅ {len(matchs)} matchs récupérés via Bzzoiro.", "MANAGER")
                return matchs
            else:
                log_warning("Bzzoiro n'a renvoyé aucun match.", "MANAGER")
        else:
            log_warning("Bzzoiro est HS, on passe à OpenLigaDB.", "MANAGER")
    except Exception as e:
        log_error(f"Erreur Bzzoiro dans le manager : {e}", "MANAGER")

    # 2. OpenLigaDB
    try:
        if openligadb.tester_api():
            matchs = openligadb.get_matchs_du_jour()
            if matchs:
                log_info(f"✅ {len(matchs)} matchs récupérés via OpenLigaDB.", "MANAGER")
                return matchs
            else:
                log_warning("OpenLigaDB n'a renvoyé aucun match.", "MANAGER")
        else:
            log_warning("OpenLigaDB est HS, on passe à Football-Data.", "MANAGER")
    except Exception as e:
        log_error(f"Erreur OpenLigaDB dans le manager : {e}", "MANAGER")

    # 3. Football-Data (backup ultime)
    try:
        # On vérifie que l'ancienne fonction existe toujours
        if hasattr(football_data, 'recuperer_matchs_bruts'):
            matchs = football_data.recuperer_matchs_bruts()
            if matchs:
                log_info(f"✅ {len(matchs)} matchs récupérés via Football-Data (backup).", "MANAGER")
                return matchs
    except Exception as e:
        log_error(f"Erreur Football-Data dans le manager : {e}", "MANAGER")

    log_error("❌ Aucune source n'a pu fournir de matchs.", "MANAGER")
    return []
