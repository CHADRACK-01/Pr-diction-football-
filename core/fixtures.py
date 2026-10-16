import requests
from datetime import datetime, timezone, timedelta

# =========================================================
# CONFIGURATION
# =========================================================
# Récupère la clé depuis les variables d'environnement de Render
import os
FOOTBALL_DATA_KEY = os.environ.get("FOOTBALL_DATA_KEY", "")

# URL de l'API
BASE_URL = "https://api.football-data.org/v4"
HEADERS = {"X-Auth-Token": FOOTBALL_DATA_KEY}

# Fuseau horaire de Kinshasa (UTC+1)
TZ_KINSHASA = timezone(timedelta(hours=1))


# =========================================================
# RÉCUPÉRATION DES MATCHS DU JOUR
# =========================================================
def get_matchs_du_jour(date_cible=None):
    """
    Récupère les matchs du jour via Football-Data.org.
    """
    if date_cible is None:
        date_cible = datetime.now(TZ_KINSHASA).date()

    date_str = date_cible.strftime("%Y-%m-%d")
    url = f"{BASE_URL}/matches"
    params = {"date": date_str}

    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=20)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"⚠️ Erreur Football-Data.org : {e}")
        return []

    matches = data.get("matches", [])
    print(f"📅 Football-Data.org : {len(matches)} match(s) trouvé(s) pour {date_str}")
    return matches


# =========================================================
# FORMATAGE POUR TELEGRAM
# =========================================================
def formater_matchs_du_jour(matches, limite=15):
    """Formate la liste des matchs pour Telegram."""
    date_str = datetime.now(TZ_KINSHASA).strftime("%d/%m/%Y")

    if not matches:
        return f"📅 *Aucun match aujourd'hui ({date_str})* dans vos championnats."

    texte = f"📅 *Matchs du jour — {date_str}*\n"
    texte += f"_{len(matches)} match(s) dans vos championnats_\n\n"

    for i, match in enumerate(matches[:limite], 1):
        home = match.get("homeTeam", {}).get("name", "?")
        away = match.get("awayTeam", {}).get("name", "?")
        competition = match.get("competition", {}).get("name", "")
        # L'heure est au format UTC (ex: 2026-10-16T20:00:00Z)
        time_utc = match.get("utcDate", "")
        
        # Convertir l'heure UTC en heure locale de Kinshasa pour l'affichage
        if time_utc:
            try:
                dt_utc = datetime.fromisoformat(time_utc.replace("Z", "+00:00"))
                dt_local = dt_utc.astimezone(TZ_KINSHASA)
                heure_locale = dt_local.strftime("%H:%M")
            except Exception:
                heure_locale = time_utc.split("T")[1][:5] if "T" in time_utc else ""
        else:
            heure_locale = ""

        texte += (
            f"*{i}. {home} vs {away}*\n"
            f"🏆 _{competition}_\n"
        )
        if heure_locale:
            texte += f"⏰ {heure_locale} (Kinshasa)\n"
        texte += "\n"

    texte += "💡 _Tapez une affiche pour obtenir le pronostic détaillé_"
    return texte
