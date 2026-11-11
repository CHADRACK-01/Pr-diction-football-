import unicodedata
from core.api import bzzoiro, openligadb, football_data
from config import MAPPING_COMPETITIONS
from core.utils.logs import log_info, log_warning, log_error


# Système de boost : plus le score est élevé, plus la source est fiable
BOOST_SOURCES = {
    "bzzoiro": 3,
    "football_data": 2,
    "openligadb": 1,
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
    
    # 3. Correspondance insensible à la casse et aux accents
    try:
        comp_norm = unicodedata.normalize('NFKD', comp).encode('ascii', 'ignore').decode('utf-8').lower().strip()
        for nom_propre in COMPETITIONS_SUPPORTEES:
            nom_norm = unicodedata.normalize('NFKD', nom_propre).encode('ascii', 'ignore').decode('utf-8').lower().strip()
            if comp_norm == nom_norm:
                return nom_propre
    except Exception:
        pass
    
    return None


def get_matchs_du_jour():
    """
    Récupère les matchs du jour en interrogeant TOUTES les sources disponibles.
    Fusionne, filtre par compétition supportée, et déduplique.
    """
    log_info("Début de la récupération multi-sources des matchs...", "MANAGER")
    
    matchs_collectes = {}
    stats_sources = {}
    
    # =========================================================
    # 1. BZZOIRO (priorité 3)
    # =========================================================
    try:
        if bzzoiro.tester_api():
            matchs_bz = bzzoiro.get_matchs_du_jour()
            stats_sources['bzzoiro'] = len(matchs_bz) if matchs_bz else 0
            for m in (matchs_bz or []):
                m['_source'] = 'bzzoiro'
                cle = _normaliser_cle_match(m)
                if not cle:
                    continue
                if cle in matchs_collectes:
                    _, boost_existant = matchs_collectes[cle]
                    if BOOST_SOURCES['bzzoiro'] > boost_existant:
                        matchs_collectes[cle] = (m, BOOST_SOURCES['bzzoiro'])
                else:
                    matchs_collectes[cle] = (m, BOOST_SOURCES['bzzoiro'])
            log_info(f"Bzzoiro : {len(matchs_bz) if matchs_bz else 0} matchs récupérés.", "MANAGER")
        else:
            log_warning("Bzzoiro est HS.", "MANAGER")
            stats_sources['bzzoiro'] = 0
    except Exception as e:
        log_error("Erreur Bzzoiro dans le manager", "MANAGER", exception=e)
        stats_sources['bzzoiro'] = 0

    # =========================================================
    # 2. FOOTBALL-DATA (priorité 2)
    # =========================================================
    try:
        matchs_fd = football_data.recuperer_matchs_bruts()
        stats_sources['football_data'] = len(matchs_fd) if matchs_fd else 0
        for m in (matchs_fd or []):
            m['_source'] = 'football_data'
            cle = _normaliser_cle_match(m)
            if not cle:
                continue
            if cle in matchs_collectes:
                _, boost_existant = matchs_collectes[cle]
                if BOOST_SOURCES['football_data'] > boost_existant:
                    matchs_collectes[cle] = (m, BOOST_SOURCES['football_data'])
            else:
                matchs_collectes[cle] = (m, BOOST_SOURCES['football_data'])
        log_info(f"Football-Data : {len(matchs_fd) if matchs_fd else 0} matchs récupérés.", "MANAGER")
    except Exception as e:
        log_error("Erreur Football-Data dans le manager", "MANAGER", exception=e)
        stats_sources['football_data'] = 0

    # =========================================================
    # 3. OPENLIGADB (priorité 1)
    # =========================================================
    try:
        if openligadb.tester_api():
            matchs_ol = openligadb.get_matchs_du_jour()
            stats_sources['openligadb'] = len(matchs_ol) if matchs_ol else 0
            for m in (matchs_ol or []):
                m['_source'] = 'openligadb'
                cle = _normaliser_cle_match(m)
                if not cle:
                    continue
                if cle in matchs_collectes:
                    _, boost_existant = matchs_collectes[cle]
                    if BOOST_SOURCES['openligadb'] > boost_existant:
                        matchs_collectes[cle] = (m, BOOST_SOURCES['openligadb'])
                else:
                    matchs_collectes[cle] = (m, BOOST_SOURCES['openligadb'])
            log_info(f"OpenLigaDB : {len(matchs_ol) if matchs_ol else 0} matchs récupérés.", "MANAGER")
        else:
            log_warning("OpenLigaDB est HS.", "MANAGER")
            stats_sources['openligadb'] = 0
    except Exception as e:
        log_error("Erreur OpenLigaDB dans le manager", "MANAGER", exception=e)
        stats_sources['openligadb'] = 0

    # =========================================================
    # 4. FILTRAGE PAR COMPÉTITION SUPPORTÉE
    # =========================================================
    matchs_finaux = []
    filtres_par_competition = 0
    comps_filtrees = set()
    
    for cle, (match, boost) in matchs_collectes.items():
        comp_supportee = _extraire_competition_supportee(match)
        
        if comp_supportee is None:
            filtres_par_competition += 1
            comps_filtrees.add(match.get('competition', 'Inconnu'))
            continue
        
        match['competition_reelle'] = comp_supportee
        matchs_finaux.append(match)

    # =========================================================
    # 5. LOG FINAL
    # =========================================================
    log_info(
        f"📊 BILAN MANAGER : "
        f"Bzzoiro={stats_sources.get('bzzoiro', 0)}, "
        f"Football-Data={stats_sources.get('football_data', 0)}, "
        f"OpenLigaDB={stats_sources.get('openligadb', 0)} "
        f"→ {len(matchs_finaux)} matchs retenus "
        f"({filtres_par_competition} filtrés).",
        "MANAGER"
    )

    if comps_filtrees:
        log_info(f"Compétitions ignorées : {list(comps_filtrees)[:10]}", "MANAGER")

    if not matchs_finaux:
        log_warning(
            "Aucun match retenu après fusion et filtrage. "
            "Soit aucune compétition supportée n'a de match aujourd'hui, "
            "soit toutes les APIs sont HS.",
            "MANAGER"
        )

    return matchs_finaux
