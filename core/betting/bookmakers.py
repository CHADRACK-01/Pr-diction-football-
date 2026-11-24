# core/bookmakers.py
"""
Fonctionnalité 14 : Comparateur de Bookmakers.
Utilise l'API The Odds API pour récupérer les vraies cotes.
"""

import os
import requests
from datetime import datetime, timedelta
from core.utils.logs import log_info, log_warning, log_error

ODDS_API_KEY = os.environ.get("ODDS_API_KEY", "")
BASE_URL = "https://api.the-odds-api.com/v4"

# Cache simple (en mémoire) pour éviter d'épuiser le quota
_CACHE_COTES = {}
_CACHE_DUREE = 3600  # 1 heure

def _get_cache_key(sport, home_team, away_team):
    """Génère une clé de cache unique pour un match."""
    return f"{sport}|{home_team.lower()}|{away_team.lower()}"

def _est_en_cache(sport, home_team, away_team):
    """Vérifie si les cotes sont en cache et valides."""
    key = _get_cache_key(sport, home_team, away_team)
    if key in _CACHE_COTES:
        data, timestamp = _CACHE_COTES[key]
        if (datetime.now() - timestamp).total_seconds() < _CACHE_DUREE:
            return data
    return None

def _mettre_en_cache(sport, home_team, away_team, data):
    """Met les cotes en cache."""
    key = _get_cache_key(sport, home_team, away_team)
    _CACHE_COTES[key] = (data, datetime.now())

def rechercher_cotes(sport="soccer_epl", region="eu", bookmakers="betwinner,onexbet"):
    """
    Récupère les cotes depuis The Odds API.
    - sport : le championnat (ex: soccer_epl, soccer_spain_la_liga)
    - region : 'eu' pour l'Europe
    - bookmakers : liste séparée par des virgules
    """
    if not ODDS_API_KEY:
        log_warning("Clé ODDS_API_KEY manquante.", "BOOKMAKERS")
        return []

    url = f"{BASE_URL}/sports/{sport}/odds/"
    params = {
        "apiKey": ODDS_API_KEY,
        "regions": region,
        "markets": "h2h",
        "bookmakers": bookmakers,
        "oddsFormat": "decimal"
    }

    try:
        res = requests.get(url, params=params, timeout=15)
        
        if res.status_code != 200:
            log_warning(f"The Odds API a échoué (code {res.status_code})", "BOOKMAKERS")
            return []

        data = res.json()
        return data

    except Exception as e:
        log_error("Erreur appel The Odds API", "BOOKMAKERS", exception=e)
        return []

def get_cotes_match(home_team, away_team, sport="soccer_epl"):
    """
    Récupère les cotes d'un match spécifique.
    Utilise le cache si possible.
    """
    # Vérifier le cache
    cache = _est_en_cache(sport, home_team, away_team)
    if cache is not None:
        log_info(f"Cotes en cache pour {home_team} vs {away_team}", "BOOKMAKERS")
        return cache

    # Sinon, appel API
    data = rechercher_cotes(sport=sport)
    
    if not data:
        return []

    # Filtrer le match demandé
    resultats = []
    for match in data:
        if (match.get("home_team", "").lower() == home_team.lower() and 
            match.get("away_team", "").lower() == away_team.lower()):
            
            bookmakers_data = match.get("bookmakers", [])
            for bk in bookmakers_data:
                nom_bk = bk.get("title", "Inconnu")
                markets = bk.get("markets", [])
                for market in markets:
                    if market.get("key") == "h2h":
                        outcomes = market.get("outcomes", [])
                        cotes = {o["name"]: o["price"] for o in outcomes}
                        
                        resultats.append({
                            "bookmaker": nom_bk,
                            "cote_home": cotes.get(home_team, "?"),
                            "cote_draw": cotes.get("Draw", "?"),
                            "cote_away": cotes.get(away_team, "?")
                        })
            
            break

    _mettre_en_cache(sport, home_team, away_team, resultats)
    return resultats

def formater_comparateur_bookmakers(home_team, away_team, resultats):
    """Formate le comparateur pour Telegram."""
    if not resultats:
        return "❌ Aucune cote disponible pour ce match."

    texte = f"💰 <b>COMPARATEUR DE BOOKMAKERS</b>\n"
    texte += f"━━━━━━━━━━━━━━━━━━━━\n\n"
    texte += f"🏟️ {home_team} vs {away_team}\n\n"

    best_home = max(resultats, key=lambda x: x["cote_home"] if isinstance(x["cote_home"], (int, float)) else 0)
    best_draw = max(resultats, key=lambda x: x["cote_draw"] if isinstance(x["cote_draw"], (int, float)) else 0)
    best_away = max(resultats, key=lambda x: x["cote_away"] if isinstance(x["cote_away"], (int, float)) else 0)

    texte += f"🏠 <b>{home_team} gagne</b>\n"
    for r in resultats:
        emoji = "🏆" if r == best_home else "  "
        texte += f"{emoji} {r['bookmaker']} : {r['cote_home']}\n"
    texte += f"\n"

    texte += f"➖ <b>Match nul</b>\n"
    for r in resultats:
        emoji = "🏆" if r == best_draw else "  "
        texte += f"{emoji} {r['bookmaker']} : {r['cote_draw']}\n"
    texte += f"\n"

    texte += f"✈️ <b>{away_team} gagne</b>\n"
    for r in resultats:
        emoji = "🏆" if r == best_away else "  "
        texte += f"{emoji} {r['bookmaker']} : {r['cote_away']}\n"

    texte += f"\n━━━━━━━━━━━━━━━━━━━━\n"
    texte += f"💡 <i>🏆 = Meilleure cote du marché.</i>\n"

    return texte
