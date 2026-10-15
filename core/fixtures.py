import requests
from datetime import datetime


# Clé API publique gratuite (aucune inscription requise)
# Limite : 30 requêtes/minute, 10 résultats par endpoint
THESPORTSDB_KEY = "3"
BASE_URL = "https://www.thesportsdb.com/api/v1/json"


def get_matchs_du_jour(date_cible=None, sport="Soccer"):
    """
    Récupère les matchs du jour via TheSportsDB.
    - date_cible : datetime.date (défaut = aujourd'hui)
    - sport : "Soccer" par défaut
    """
    if date_cible is None:
        date_cible = datetime.now().date()

    date_str = date_cible.strftime("%Y-%m-%d")
    url = f"{BASE_URL}/{THESPORTSDB_KEY}/eventsday.php"
    params = {"d": date_str, "s": sport}

    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"⚠️ Erreur TheSportsDB : {e}")
        return []

    events = data.get("events") or []
    return events


def formater_matchs_du_jour(events, limite=10):
    """Formate la liste des matchs pour Telegram."""
    if not events:
        date_str = datetime.now().strftime("%d/%m/%Y")
        return f"📅 *Aucun match aujourd'hui ({date_str})* dans TheSportsDB."

    date_str = datetime.now().strftime("%d/%m/%Y")
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
