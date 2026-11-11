import unicodedata
from core.api import football_data, bzzoiro, openligadb, api_football, thesportsdb
from core.utils.logs import log_info, log_error, log_warning
from config import MAPPING_COMPETITIONS

# Registre des sources : nom -> (fonction, boost)
SOURCES = {
    "football_data": {"func": football_data.recuperer_matchs_bruts, "boost": 3},
    "bzzoiro": {"func": bzzoiro.get_matchs_du_jour, "boost": 2},
    "openligadb": {"func": openligadb.get_matchs_du_jour, "boost": 1},
    "api_football": {"func": api_football.get_live_matches, "boost": 4},
    "thesportsdb": {"func": thesportsdb.get_live_matches, "boost": 2},
}

# Liste des noms propres de compétitions supportées
COMPETITIONS_SUPPORTEES = set(MAPPING_COMPETITIONS.values())


def _normaliser_cle_match(match):
    """Crée une clé unique pour dédupliquer les matchs."""
    try:
        date_str = str(match.get('heure', ''))[:10]
        home = unicodedata.normalize('NFKD', match.get('home', '')).encode('ascii', 'ignore').decode('utf-8').lower().strip()
        away = unicodedata.normalize('NFKD', match.get('away', '')).encode('ascii', 'ignore').decode('utf-8').lower().strip()
        return f"{date_str}|{home}|{away}"
    except Exception:
        return None


def _extraire_competition_supportee(match):
    """
    Vérifie si le match appartient à une compétition supportée.
    Retourne le nom propre (ex: "Ligue 1") ou None.
    """
    comp = str(match.get('competition', '')).strip()
    
    # 1. Si c'est un code connu (ex: "ligue_1")
    if comp in MAPPING_COMPETITIONS:
        return MAPPING_COMPETITIONS[comp]
    
    # 2. Si c'est déjà un nom propre connu (ex: "Ligue 1")
    if comp in COMPETITIONS_SUPPORTEES:
        return comp
    
    # 3. Sinon, on tente une correspondance insensible à la casse et aux accents
    try:
        comp_norm = unicodedata.normalize('NFKD', comp).encode('ascii', 'ignore').decode('utf-8').lower().strip()
        for nom_propre in COMPETITIONS_SUPPORTEES:
            nom_norm = unicodedata.normalize('NFKD', nom_propre).encode('ascii', 'ignore').decode('utf-8').lower().strip()
            if comp_norm == nom_norm:
                return nom_propre
    except Exception:
        pass
    
    # 4. Compétition non supportée
    return None


def collecter_tous_les_matchs():
    """
    Interroge toutes les sources, fusionne, filtre les compétitions 
    supportées et déduplique les matchs.
    """
    log_info("Début de la collecte multi-sources...", "ORCHESTRATOR")
    
    matchs_collectes = {}
    
    for nom, config_source in SOURCES.items():
        try:
            log_info(f"Interrogation de {nom}...", "ORCHESTRATOR")
            matchs_source = config_source["func"]()
            
            if not matchs_source:
                log_warning(f"{nom} n'a renvoyé aucun match.", "ORCHESTRATOR")
                continue
            
            # On filtre les compétitions supportées ET on stocke le nom propre
            matchs_valides = 0
            for m in matchs_source:
                comp_supportee = _extraire_competition_supportee(m)
                if comp_supportee is None:
                    continue  # On ignore les compétitions non supportées
                
                # On stocke le nom propre dans le match pour les étapes suivantes
                m['competition_reelle'] = comp_supportee
                m['_source'] = nom
                
                cle = _normaliser_cle_match(m)
                if not cle:
                    continue
                
                # Fusion : on garde le match avec le meilleur boost
                if cle in matchs_collectes:
                    existant, boost_existant = matchs_collectes[cle]
                    if config_source["boost"] > boost_existant:
                        matchs_collectes[cle] = (m, config_source["boost"])
                else:
                    matchs_collectes[cle] = (m, config_source["boost"])
                
                matchs_valides += 1
                    
            log_info(f"{nom} : {matchs_valides} matchs valides sur {len(matchs_source)}.", "ORCHESTRATOR")
            
        except Exception as e:
            log_error(f"Erreur avec {nom}", "ORCHESTRATOR", exception=e)
            continue
    
    # On extrait les matchs (sans le boost)
    matchs_finaux = [m for m, _ in matchs_collectes.values()]
    
    log_info(f"Total après fusion : {len(matchs_finaux)} matchs uniques.", "ORCHESTRATOR")
    return matchs_finaux
