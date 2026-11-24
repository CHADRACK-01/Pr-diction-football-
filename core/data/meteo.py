# core/meteo.py
"""
Fonctionnalité 35 : Alerte Météo Pelouse.
Récupère la vraie météo via OpenWeatherMap (ou renvoie une valeur neutre).
"""

import os
import requests
from core.utils.logs import log_info, log_warning, log_error

# Clé API (à mettre dans les variables d'environnement Render)
OPENWEATHER_API_KEY = os.environ.get("OPENWEATHER_API_KEY", "")

# Mapping des villes par équipe (à enrichir avec les équipes de ta base)
VILLES_EQUIPES = {
    "Chelsea": "London",
    "Arsenal": "London",
    "Tottenham": "London",
    "Real Madrid": "Madrid",
    "Barcelona": "Barcelona",
    "PSG": "Paris",
    "Marseille": "Marseille",
    "Bayern Munich": "Munich",
    "Dortmund": "Dortmund",
    "Inter": "Milan",
    "Milan": "Milan",
    "Juventus": "Turin",
    "Mazembe": "Lubumbashi",
    "Vita Club": "Kinshasa",
}

def obtenir_ville_equipe(nom_equipe):
    """Devine la ville de l'équipe (par défaut : Kinshasa)."""
    for equipe, ville in VILLES_EQUIPES.items():
        if equipe.lower() in nom_equipe.lower():
            return ville
    return "Kinshasa" # Ville par défaut

def obtenir_meteo_reelle(ville):
    """
    Récupère la vraie météo via OpenWeatherMap.
    Si l'API n'est pas configurée ou échoue, retourne une valeur neutre.
    """
    if not OPENWEATHER_API_KEY:
        log_warning("Clé OPENWEATHER_API_KEY manquante. Météo neutre utilisée.", "METEO")
        return _meteo_neutre(ville)

    url = f"https://api.openweathermap.org/data/2.5/weather?q={ville}&appid={OPENWEATHER_API_KEY}&units=metric&lang=fr"
    
    try:
        res = requests.get(url, timeout=10)
        if res.status_code != 200:
            log_warning(f"OpenWeatherMap a échoué (code {res.status_code})", "METEO")
            return _meteo_neutre(ville)

        data = res.json()
        condition = data["weather"][0]["main"].lower()
        temperature = data["main"]["temp"]
        humidite = data["main"]["humidity"]

        # Traduction des conditions en français
        if "rain" in condition or "drizzle" in condition:
            condition_fr = "Pluie"
        elif "thunderstorm" in condition:
            condition_fr = "Orageux"
        elif "clear" in condition:
            condition_fr = "Ensoleillé"
        elif "clouds" in condition:
            condition_fr = "Nuageux"
        else:
            condition_fr = "Inconnu"

        return {
            "ville": ville,
            "condition": condition_fr,
            "temperature": round(temperature, 1),
            "humidite": humidite,
            "fiable": True,
        }

    except Exception as e:
        log_error(f"Erreur API météo pour {ville}", "METEO", exception=e)
        return _meteo_neutre(ville)

def _meteo_neutre(ville):
    """Retourne une météo neutre (aucun impact sur le pari)."""
    return {
        "ville": ville,
        "condition": "Normale",
        "temperature": 20.0,
        "humidite": 50,
        "fiable": False,
    }

def analyser_impact_meteo(meteo):
    """Analyse l'impact de la météo sur le match."""
    if not meteo["fiable"]:
        return ["🌤️ Météo non disponible (aucun impact pris en compte)"]

    condition = meteo["condition"]
    impact = []

    if condition == "Pluie":
        impact.append("🌧️ Terrain lourd : favorise Under 2.5 et plus de fautes")
    elif condition == "Orageux":
        impact.append("⛈️ Match à risque : possible report ou arrêt")
        impact.append("⚽ Moins de buts attendus")
    elif condition == "Ensoleillé" and meteo["temperature"] > 30:
        impact.append("☀️ Forte chaleur : rythme plus lent, moins de buts")
    elif condition == "Nuageux":
        impact.append("☁️ Conditions idéales pour le football")
    else:
        impact.append("🌤️ Pas d'impact significatif")

    return impact

def formater_alerte_meteo(home_team, away_team, meteo):
    """Formate l'alerte météo pour Telegram."""
    texte = f"🌦️ <b>MÉTÉO DU MATCH</b>\n"
    texte += f"━━━━━━━━━━━━━━━━━━━━\n\n"
    texte += f"🏟️ {home_team} vs {away_team}\n"
    texte += f"📍 Ville : {meteo['ville']}\n"
    
    if meteo["fiable"]:
        texte += f"🌡️ Température : {meteo['temperature']}°C\n"
        texte += f"💧 Humidité : {meteo['humidite']}%\n"
        texte += f"☁️ Condition : {meteo['condition']}\n\n"
    else:
        texte += f"⚠️ <i>Météo non disponible pour le moment.</i>\n\n"

    impacts = analyser_impact_meteo(meteo)
    if impacts:
        texte += "🔍 <b>IMPACT SUR LE MATCH :</b>\n"
        for impact in impacts:
            texte += f"• {impact}\n"

    return texte
