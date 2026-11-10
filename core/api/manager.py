from datetime import datetime
from core.api import bzzoiro, openligadb, football_data
from config import MAPPING_COMPETITIONS
from core.utils.logs import log_info, log_warning, log_error


# Système de boost : plus le score est élevé, plus la source est fiable
BOOST_SOURCES = {
    "bzzoiro": 3,        # Cotes + xG + live
    "football_data": 2,  # Fiable, mais pas de cotes
    "openligadb": 1,     # Basique (Bundesliga uniquement)
}

# Liste des compétitions supportées (noms propres)
COMPETITIONS_SUPPORTEES = set(MAPPING_COMPETITIONS.values())


def _normaliser_cle_match(match):
    """
    Crée une clé unique pour dédupliquer les matchs.
    Ex: "2026-11-10|Paris SG|Marseille"
    """
    try:
        # On extrait la date (au format YYYY-MM-DD)
        date_str = str(match.get('heure', ''))[:10]
        home = str(match.get('home', '')).lower().strip()
        away = str(match.get('away', '')).lower().strip()
        return f"{date_str}|{home}|{away}"
    except Exception:
        return None


def _extraire_competition_supportee(match):
    """
    Vérifie si le match appartient à une compétition supportée.
    Retourne le nom propre de la compétition (ex: "Ligue 1") ou None.
    """
    comp_code = match.get('competition', '')
    
    # On essaie d'abord le mapping direct (code -> nom propre)
    if comp_code in MAPPING_COMPETITIONS:
        return MAPPING_COMPETITIONS[comp_code]
    
    # Si c'est déjà un nom propre (ex: "Ligue 1"), on vérifie qu'il est supporté
    if comp_code in COMPETITIONS_SUPPORTEES:
        return comp_code
    
    return None


def get_matchs_du_jour():
    """
    Récupère les matchs du jour en interrogeant TOUTES les sources disponibles.
    Fusionne, filtre par compétition supportée, et déduplique.
    """
    log_info("Début de la récupération multi-sources des matchs...", "MANAGER")
    
    # Dictionnaire : clé_match -> (match, boost)
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
                # Si déjà présent, on garde la version avec le meilleur boost
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
    
    for cle, (match, boost) in matchs_collectes.items():
        comp_supportee = _extraire_competition_supportee(match)
        
        if comp_supportee is None:
            filtres_par_competition += 1
            continue
        
        # On stocke le nom propre et la source
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
        f"({filtres_par_competition} filtrés car compétition non supportée).",
        "MANAGER"
    )

    if not matchs_finaux:
        log_warning(
            "Aucun match retenu après fusion et filtrage. "
            "Soit aucune compétition supportée n'a de match aujourd'hui, "
            "soit toutes les APIs sont HS.",
            "MANAGER"
        )

    return matchs_finaux
