import requests
from datetime import datetime, timezone, timedelta

# =========================================================
# CONFIGURATION
# =========================================================
THESPORTSDB_KEY = "3"
BASE_URL = "https://www.thesportsdb.com/api/v1/json"

# Fuseau horaire de Kinshasa (UTC+1)
TZ_KINSHASA = timezone(timedelta(hours=1))


# =========================================================
# RÉCUPÉRATION DES MATCHS DU JOUR
# =========================================================
def get_matchs_du_jour(date_cible=None):
    """
    Récupère les matchs du jour via TheSportsDB.
    - date_cible : datetime.date (défaut = aujourd'hui à Kinshasa)
    """
    if date_cible is None:
        date_cible = datetime.now(TZ_KINSHASA).date()

    date_str = date_cible.strftime("%Y-%m-%d")
    url = f"{BASE_URL}/{THESPORTSDB_KEY}/eventsday.php"

    # Appel SANS paramètre 's' (comme l'URL qui marche dans le navigateur)
    params = {"d": date_str}

    print(f"📅 Appel TheSportsDB : {url}?d={date_str}")

    try:
        response = requests.get(url, params=params, timeout=20)
        print(f"📅 Réponse HTTP : {response.status_code}")
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"⚠️ Erreur TheSportsDB : {e}")
        return []

    events = data.get("events") or []
    # Filtrer uniquement les matchs de football
    events_soccer = [ev for ev in events if ev.get("strSport") == "Soccer"]

    print(f"📅 TheSportsDB : {len(events)} événement(s), {len(events_soccer)} match(s) de foot pour {date_str}")
    return events_soccer


# =========================================================
# FORMATAGE POUR TELEGRAM
# =========================================================
def formater_matchs_du_jour(events, limite=10):
    """Formate la liste des matchs pour Telegram."""
    date_str = datetime.now(TZ_KINSHASA).strftime("%d/%m/%Y")

    if not events:
        return f"📅 *Aucun match aujourd'hui ({date_str})* dans TheSportsDB."

    texte = f"📅 *Matchs du jour — {date_str}*\n"
    texte += f"_{len(events)} match(s) trouvé(s)_\n\n"

    for i, ev in enumerate(events[:limite], 1):
        home = ev.get("strHomeTeam", "?")
        away = ev.get("strAwayTeam", "?")
        league = ev.get("strLeague", "")
        time_utc = ev.get("strTime", "")

        texte += (
            f"*{i}. {home} vs {away}*\n"
            f"🏆 _{league}_\n"
        )
        if time_utc:
            texte += f"⏰ {time_utc} UTC\n"
        texte += "\n"

    texte += "💡 _Tapez une affiche pour obtenir le pronostic_"
    return texte
