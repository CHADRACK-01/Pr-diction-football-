from datetime import datetime, timezone, timedelta
from sports_skills import football

# Fuseau horaire de Kinshasa (UTC+1)
TZ_KINSHASA = timezone(timedelta(hours=1))


def get_matchs_du_jour(date_cible=None):
    """
    Récupère les matchs du jour via sports-skills (ESPN).
    """
    if date_cible is None:
        date_cible = datetime.now(TZ_KINSHASA).date()

    date_str = date_cible.strftime("%Y-%m-%d")

    try:
        # Appel à sports-skills
        result = football.get_daily_schedule(date=date_str)
        
        # Extraction des matchs
        events = result.get("data", {}).get("events", [])
        print(f"📅 sports-skills : {len(events)} match(s) trouvé(s) pour {date_str}")
        return events

    except Exception as e:
        print(f"⚠️ Erreur sports-skills : {e}")
        return []


def formater_matchs_du_jour(events, limite=15):
    """Formate la liste des matchs pour Telegram."""
    date_str = datetime.now(TZ_KINSHASA).strftime("%d/%m/%Y")

    if not events:
        return f"📅 *Aucun match aujourd'hui ({date_str})* dans vos championnats suivis."

    texte = f"📅 *Matchs du jour — {date_str}*\n"
    texte += f"_{len(events)} match(s) trouvé(s)_\n\n"

    for i, ev in enumerate(events[:limite], 1):
        # Adapter selon la structure retournée par sports-skills
        home = ev.get("homeTeam", {}).get("name", ev.get("home", "?"))
        away = ev.get("awayTeam", {}).get("name", ev.get("away", "?"))
        league = ev.get("competition", {}).get("name", ev.get("league", ""))
        time_utc = ev.get("date", "")

        heure_locale = ""
        if time_utc:
            try:
                dt_utc = datetime.fromisoformat(time_utc.replace("Z", "+00:00"))
                dt_local = dt_utc.astimezone(TZ_KINSHASA)
                heure_locale = dt_local.strftime("%H:%M")
            except Exception:
                pass

        texte += (
            f"*{i}. {home} vs {away}*\n"
            f"🏆 _{league}_\n"
        )
        if heure_locale:
            texte += f"⏰ {heure_locale} (Kinshasa)\n"
        texte += "\n"

    texte += "💡 _Tapez une affiche pour obtenir le pronostic détaillé_"
    return texte
