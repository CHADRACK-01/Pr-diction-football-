# core/api/orchestrator.py
import unicodedata
from core.api import football_data, bzzoiro, openligadb
from core.utils.logs import log_info, log_error, log_warning

# Registre des sources : nom -> (fonction, boost)
# Le boost sert à prioriser une source en cas de conflit.
SOURCES = {
    "football_data": {"func": football_data.recuperer_matchs_bruts, "boost": 3},
    "bzzoiro": {"func": bzzoiro.get_matchs_du_jour, "boost": 2},
    "openligadb": {"func": openligadb.get_matchs_du_jour, "boost": 1},
}

def _normaliser_cle_match(match):
    """Crée une clé unique pour dédupliquer les matchs."""
    try:
        date_str = str(match.get('heure', ''))[:10]
        home = unicodedata.normalize('NFKD', match.get('home', '')).encode('ascii', 'ignore').decode('utf-8').lower().strip()
        away = unicodedata.normalize('NFKD', match.get('away', '')).encode('ascii', 'ignore').decode('utf-8').lower().strip()
        return f"{date_str}|{home}|{away}"
    except Exception:
        return None

def collecter_tous_les_matchs():
    """
    Interroge toutes les sources, fusionne et déduplique les matchs.
    """
    log_info("Début de la collecte multi-sources...", "ORCHESTRATOR")
    
    matchs_collectes = {}
    
    for nom, config in SOURCES.items():
        try:
            log_info(f"Interrogation de {nom}...", "ORCHESTRATOR")
            matchs_source = config["func"]()
            
            if not matchs_source:
                log_warning(f"{nom} n'a renvoyé aucun match.", "ORCHESTRATOR")
                continue
                
            for m in matchs_source:
                cle = _normaliser_cle_match(m)
                if not cle:
                    continue
                
                # Si le match existe déjà, on garde la version avec le meilleur boost
                # ou celle qui a le plus d'informations (cotes, stats)
                if cle in matchs_collectes:
                    existant, boost_existant = matchs_collectes[cle]
                    # Priorité au boost, puis à la présence de cotes
                    if config["boost"] > boost_existant:
                        matchs_collectes[cle] = (m, config["boost"])
                else:
                    matchs_collectes[cle] = (m, config["boost"])
                    
            log_info(f"{nom} : {len(matchs_source)} matchs récupérés.", "ORCHESTRATOR")
            
        except Exception as e:
            log_error(f"Erreur avec {nom}", "ORCHESTRATOR", exception=e)
            continue
    
    # On extrait juste les matchs (sans le boost)
    matchs_finaux = [m for m, _ in matchs_collectes.values()]
    
    log_info(f"Total après fusion : {len(matchs_finaux)} matchs uniques.", "ORCHESTRATOR")
    return matchs_finaux
