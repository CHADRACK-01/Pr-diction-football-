# core/api/orchestrator.py
"""
Orchestrateur multi-sources UNIQUE (remplace manager.py).

Sources "fixtures" (matchs à venir) :
- football_data (boost 3)
- bzzoiro (boost 2)
- openligadb (boost 1)

Fallback dégradé : thesportsdb (boost 0) — utilisé UNIQUEMENT si les 3
sources principales échouent (retournent 0 match).

⚠️ api_football.get_live_matches n'est PLUS une source de collecte :
elle retourne du live, pas des matchs à venir.
"""

import unicodedata

from core.api import football_data, bzzoiro, openligadb, thesportsdb
from core.utils.logs import log_info, log_error, log_warning
from config import MAPPING_COMPETITIONS

COMPETITIONS_SUPPORTEES = set(MAPPING_COMPETITIONS.values())
NOMS_VERS_CODES = {v: k for k, v in MAPPING_COMPETITIONS.items()}

# Sources "fixtures" avec boost
SOURCES_FIXTURES = {
    "football_data": {"func": football_data.recuperer_matchs_bruts, "boost": 3},
    "bzzoiro": {"func": bzzoiro.get_matchs_du_jour, "boost": 2},
    "openligadb": {"func": openligadb.get_matchs_du_jour, "boost": 1},
}

# Source de fallback (boost 0)
SOURCE_FALLBACK = {
    "thesportsdb": {"func": thesportsdb.get_matchs_du_jour, "boost": 0},
}


def _normaliser_cle_match(match):
    """Clé unique pour déduplication."""
    try:
        date_str = str(match.get("heure", ""))[:10]
        home = (
            unicodedata.normalize("NFKD", match.get("home", ""))
            .encode("ascii", "ignore")
            .decode("utf-8")
            .lower()
            .strip()
        )
        away = (
            unicodedata.normalize("NFKD", match.get("away", ""))
            .encode("ascii", "ignore")
            .decode("utf-8")
            .lower()
            .strip()
        )
        return f"{date_str}|{home}|{away}"
    except Exception:
        return None


def _extraire_competition_supportee(match):
    """
    Retourne le nom propre de la compétition (ex: "Ligue 1") ou None.
    Accepte un code interne, un nom propre exact, ou une correspondance
    insensible à la casse/accents.
    """
    comp = str(match.get("competition", "")).strip()
    if not comp:
        return None

    # 1. Code interne
    if comp in MAPPING_COMPETITIONS:
        return MAPPING_COMPETITIONS[comp]

    # 2. Nom propre exact
    if comp in COMPETITIONS_SUPPORTEES:
        return comp

    # 3. Correspondance normalisée
    try:
        comp_norm = (
            unicodedata.normalize("NFKD", comp)
            .encode("ascii", "ignore")
            .decode("utf-8")
            .lower()
            .strip()
        )
        for nom_propre in COMPETITIONS_SUPPORTEES:
            nom_norm = (
                unicodedata.normalize("NFKD", nom_propre)
                .encode("ascii", "ignore")
                .decode("utf-8")
                .lower()
                .strip()
            )
            if comp_norm == nom_norm:
                return nom_propre
    except Exception:
        pass

    return None


def _collecter_depuis_source(nom, config_source, matchs_collectes):
    """
    Interroge une source et ajoute ses matchs à `matchs_collectes`.
    Retourne (nb_valides, nb_filtrés).
    """
    try:
        log_info(f"Interrogation de {nom}...", "ORCHESTRATOR")
        matchs_source = config_source["func"]()
    except Exception as e:
        log_error(
            message=f"Erreur lors de l'appel à {nom}",
            module="ORCHESTRATOR",
            api_context={"source": nom},
            exception=e,
        )
        return 0, 0

    if not matchs_source:
        log_warning(
            message=f"{nom} n'a renvoyé aucun match",
            module="ORCHESTRATOR",
            api_context={"source": nom},
        )
        return 0, 0

    valides = 0
    filtres = 0
    for m in matchs_source:
        if not isinstance(m, dict):
            continue
        comp_supportee = _extraire_competition_supportee(m)
        if comp_supportee is None:
            filtres += 1
            continue

        m["competition_reelle"] = comp_supportee
        m["_source"] = nom

        cle = _normaliser_cle_match(m)
        if not cle:
            continue

        if cle in matchs_collectes:
            existant, boost_existant = matchs_collectes[cle]
            if config_source["boost"] > boost_existant:
                matchs_collectes[cle] = (m, config_source["boost"])
        else:
            matchs_collectes[cle] = (m, config_source["boost"])
        valides += 1

    log_info(
        f"{nom} : {valides} valides, {filtres} filtrés (sur {len(matchs_source)})",
        "ORCHESTRATOR",
        api_context={"source": nom},
        extra={"valides": valides, "filtres": filtres, "total": len(matchs_source)},
    )
    return valides, filtres


def collecter_tous_les_matchs():
    """
    Collecte unifiée : sources fixtures -> fusion -> filtrage -> déduplication.
    Fallback thesportsdb si zéro match au total.
    """
    log_info("Début collecte multi-sources...", "ORCHESTRATOR")

    matchs_collectes = {}
    stats = {}

    # 1. Sources principales
    for nom, cfg in SOURCES_FIXTURES.items():
        valides, filtres = _collecter_depuis_source(nom, cfg, matchs_collectes)
        stats[nom] = {"valides": valides, "filtres": filtres}

    # 2. Fallback si zéro match
    if not matchs_collectes:
        log_warning(
            message="Aucune source principale n'a retourné de match. Activation fallback thesportsdb.",
            module="ORCHESTRATOR",
        )
        nom_fb, cfg_fb = next(iter(SOURCE_FALLBACK.items()))
        valides, filtres = _collecter_depuis_source(nom_fb, cfg_fb, matchs_collectes)
        stats[nom_fb] = {"valides": valides, "filtres": filtres, "fallback": True}

    # 3. Extraction finale
    matchs_finaux = [m for m, _ in matchs_collectes.values()]

    log_info(
        f"Collecte terminée : {len(matchs_finaux)} matchs uniques",
        "ORCHESTRATOR",
        extra={**{k: v.get("valides", 0) for k, v in stats.items()},
               "total": len(matchs_finaux)},
    )

    if not matchs_finaux:
        log_warning(
            message="Aucun match retenu après fusion",
            module="ORCHESTRATOR",
            extra=stats,
        )

    return matchs_finaux
