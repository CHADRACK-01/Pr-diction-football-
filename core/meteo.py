# core/meteo.py
"""
Fonctionnalité 35 : Alerte Météo Pelouse.
Simule la récupération de la météo et ajoute une analyse d'impact.
"""

import random
from core.utils.logs import log_info, log_error


def obtenir_meteo_simulee(ville="Kinshasa"):
    """
    Simule la météo pour une ville donnée.
    (À remplacer par une vraie API plus tard).
    """
    conditions = ["Ensoleillé", "Nuageux", "Pluie légère", "Pluie forte", "Orageux"]
    condition = random.choice(conditions)
    temperature = random.randint(15, 35)
    humidite = random.randint(40, 95)

    return {
        "ville": ville,
        "condition": condition,
        "temperature": temperature,
        "humidite": humidite
    }


def analyser_impact_meteo(meteo):
    """
    Analyse l'impact de la météo sur le match.
    Retourne un texte d'analyse.
    """
    condition = meteo["condition"]
    impact = []

    if condition == "Pluie forte" or condition == "Orageux":
        impact.append("🌧️ Terrain lourd : favorise les matchs fermés (Under 2.5)")
        impact.append("🟨 Plus de fautes et de cartons probables")
        impact.append("⚽ Moins de buts en général")

    elif condition == "Pluie légère":
        impact.append("🌦️ Pelouse humide : le ballon glisse plus vite")
        impact.append("⚽ Légère baisse des buts attendue")

    elif condition == "Ensoleillé" and meteo["temperature"] > 30:
        impact.append("☀️ Forte chaleur : rythme plus lent, moins de buts en fin de match")
        impact.append("💧 Pause fraîcheur probable")

    elif condition == "Nuageux":
        impact.append("☁️ Conditions idéales pour le football")
        impact.append("⚽ Aucun impact significatif sur le jeu")

    else:
        impact.append("🌤️ Conditions normales")

    return impact


def formater_alerte_meteo(home_team, away_team, meteo):
    """Formate l'alerte météo pour Telegram."""
    texte = f"🌦️ <b>MÉTÉO DU MATCH</b>\n"
    texte += f"━━━━━━━━━━━━━━━━━━━━\n\n"
    texte += f"🏟️ {home_team} vs {away_team}\n"
    texte += f"📍 Ville : {meteo['ville']}\n"
    texte += f"🌡️ Température : {meteo['temperature']}°C\n"
    texte += f"💧 Humidité : {meteo['humidite']}%\n"
    texte += f"☁️ Condition : {meteo['condition']}\n\n"

    impacts = analyser_impact_meteo(meteo)
    if impacts:
        texte += "🔍 <b>IMPACT SUR LE MATCH :</b>\n"
        for impact in impacts:
            texte += f"• {impact}\n"

    return texte
