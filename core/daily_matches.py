import requests
import difflib
from datetime import datetime, timezone, timedelta

from core.ml_model import global_model_data
from core.prediction import predire_match


# Clé API Football-Data.org
FOOTBALL_DATA_KEY = "5a7a6a3afcca4bc88400d73a0e394588"

# Fuseau horaire de Kinshasa (UTC+1)
TZ_KINSHASA = timezone(timedelta(hours=1))

# Codes des compétitions Football-Data.org
COMPETITIONS = {
    "premier_league": "PL",
    "championship": "ELC",
    "laliga": "PD",
    "ligue_1": "FL1",
    "bundesliga_1": "BL1",
    "serie_a": "SA",
}


def _normaliser(nom):
    """Convertit un nom Football-Data.org vers le nom utilisé dans ton modèle."""
    special = {
        "Manchester City FC": "Man City",
        "Manchester United FC": "Man United",
        "Newcastle United FC": "Newcastle",
        "Nottingham Forest FC": "Nott'm Forest",
        "Tottenham Hotspur FC": "Tottenham",
        "Wolverhampton Wanderers FC": "Wolves",
        "Brighton & Hove Albion FC": "Brighton",
        "West Ham United FC": "West Ham",
        "Hull City AFC": "Hull",
        "Leeds United FC": "Leeds",
        "Leicester City FC": "Leicester",
        "Norwich City FC": "Norwich",
        "Stoke City FC": "Stoke",
        "Sunderland AFC": "Sunderland",
        "Derby County FC": "Derby",
        "Swansea City AFC": "Swansea",
        "Cardiff City FC": "Cardiff",
        "AFC Bournemouth": "Bournemouth",
        "Real Madrid CF": "Real Madrid",
        "FC Barcelona": "Barcelona",
        "Atletico de Madrid": "Ath Madrid",
        "Athletic Club": "Ath Bilbao",
        "Real Sociedad de Futbol": "Sociedad",
        "Real Betis Balompie": "Betis",
        "Sevilla FC": "Sevilla",
        "Valencia CF": "Valencia",
        "Villarreal CF": "Villarreal",
        "Getafe CF": "Getafe",
        "RCD Espanyol de Barcelona": "Espanol",
        "Rayo Vallecano de Madrid": "Vallecano",
        "RC Celta de Vigo": "Celta",
        "RCD Mallorca": "Mallorca",
        "CA Osasuna": "Osasuna",
        "Granada CF": "Granada",
        "Deportivo Alaves": "Alaves",
        "Cadiz CF": "Cadiz",
        "UD Las Palmas": "Las Palmas",
        "Girona FC": "Girona",
        "Real Valladolid CF": "Valladolid",
        "Levante UD": "Levante",
        "FC Bayern München": "Bayern Munich",
        "Borussia Dortmund": "Dortmund",
        "Bayer 04 Leverkusen": "Leverkusen",
        "Eintracht Frankfurt": "Ein Frankfurt",
        "VfB Stuttgart": "Stuttgart",
        "VfL Wolfsburg": "Wolfsburg",
        "Borussia Mönchengladbach": "M'gladbach",
        "1. FC Union Berlin": "Union Berlin",
        "SC Freiburg": "Freiburg",
        "TSG 1899 Hoffenheim": "Hoffenheim",
        "FC Augsburg": "Augsburg",
        "1. FSV Mainz 05": "Mainz",
        "SV Werder Bremen": "Werder Bremen",
        "VfL Bochum 1848": "Bochum",
        "1. FC Köln": "FC Koln",
        "SV Darmstadt 98": "Darmstadt",
        "1. FC Heidenheim 1846": "Heidenheim",
        "Paris Saint-Germain FC": "Paris SG",
        "Olympique de Marseille": "Marseille",
        "Olympique Lyonnais": "Lyon",
        "AS Monaco FC": "Monaco",
        "LOSC Lille": "Lille",
        "OGC Nice": "Nice",
        "Stade Rennais FC 1901": "Rennes",
        "Racing Club de Lens": "Lens",
        "Stade de Reims": "Reims",
        "Montpellier HSC": "Montpellier",
        "FC Nantes": "Nantes",
        "Stade Brestois 29": "Brest",
        "RC Strasbourg Alsace": "Strasbourg",
        "Toulouse FC": "Toulouse",
        "FC Metz": "Metz",
        "Le Havre AC": "Le Havre",
        "Clermont Foot 63": "Clermont",
        "FC Lorient": "Lorient",
        "AS Roma": "Roma",
        "SS Lazio": "Lazio",
        "Juventus FC": "Juventus",
        "AC Milan": "Milan",
        "FC Internazionale Milano": "Inter",
        "SSC Napoli": "Napoli",
        "ACF Fiorentina": "Fiorentina",
        "Atalanta BC": "Atalanta",
        "Bologna FC 1909": "Bologna",
        "Torino FC": "Torino",
        "Udinese Calcio": "Udinese",
        "US Sassuolo Calcio": "Sassuolo",
        "Empoli FC": "Empoli",
        "US Lecce": "Lecce",
        "Hellas Verona FC": "Verona",
        "Cagliari Calcio": "Cagliari",
        "Genoa CFC": "Genoa",
        "US Salernitana 1919": "Salernitana",
        "Frosinone Calcio": "Frosinone",
        "AC Monza": "Monza",
    }
    if nom in special:
        return special[nom]
    for suf in [" FC", " AFC", " CF", " SC", " AC"]:
        if nom.endswith(suf):
            return nom[:-len(suf)]
    return nom


def get_matchs_du_jour():
    """
    Récupère les matchs du jour depuis Football-Data.org,
    puis génère les prédictions avec ton IA.
    """
    # ✅ FIX : ne pas tester la véracité d'un array
    if not global_model_data:
        print("⚠️ Modèle non chargé (vide)")
        return []

    if 'teams' not in global_model_data:
        print("⚠️ Pas de 'teams' dans global_model_data")
        return []

    teams_data = global_model_data.get('teams')
    if teams_data is None or len(teams_data) == 0:
        print("⚠️ Aucune équipe dans le modèle")
        return []

    aujourd_hui = datetime.now(TZ_KINSHASA).strftime("%Y-%m-%d")
    headers = {"X-Auth-Token": FOOTBALL_DATA_KEY}
    matchs_du_jour = []

    for nom_comp, code in COMPETITIONS.items():
        try:
            url = f"https://api.football-data.org/v4/competitions/{code}/matches"
            params = {"dateFrom": aujourd_hui, "dateTo": aujourd_hui}
            res = requests.get(url, headers=headers, params=params, timeout=15)

            if res.status_code != 200:
                print(f"⚠️ {nom_comp} : HTTP {res.status_code}")
                continue

            data = res.json()
            for m in data.get("matches", []):
                if m.get("status") != "SCHEDULED":
                    continue

                home = _normaliser(m["homeTeam"]["name"])
                away = _normaliser(m["awayTeam"]["name"])
                heure_utc = m["utcDate"]

                try:
                    prono = predire_match(home, away)
                    # ✅ FIX : vérifier explicitement
                    if not isinstance(prono, dict):
                        continue
                    if 'erreur' in prono:
                        continue
                    if 'dc_1x' not in prono:
                        continue

                    dc_1x = float(prono['dc_1x'])
                    dc_x2 = float(prono['dc_x2'])
                    dc_12 = float(prono['dc_12'])

                    options = [
                        ("1X", dc_1x),
                        ("X2", dc_x2),
                        ("12", dc_12),
                    ]
                    meilleure = max(options, key=lambda x: x[1])
                    max_dc = meilleure[1]

                    matchs_du_jour.append({
                        "competition": nom_comp,
                        "heure": heure_utc,
                        "home": home,
                        "away": away,
                        "p_h": float(prono['p_h']),
                        "p_d": float(prono['p_d']),
                        "p_a": float(prono['p_a']),
                        "score": prono['best_score'],
                        "dc_label": meilleure[0],
                        "dc_pct": float(meilleure[1]),
                        "confiance": float(max_dc),
                    })
                except Exception as e:
                    print(f"⚠️ Erreur prediction {home} vs {away} : {e}")
                    continue

        except Exception as e:
            print(f"⚠️ Erreur {nom_comp} : {e}")
            continue

    # Trier par confiance décroissante
    matchs_du_jour.sort(key=lambda x: x['confiance'], reverse=True)
    print(f"✅ {len(matchs_du_jour)} matchs du jour trouvés")
    return matchs_du_jour


def formater_matchs_du_jour(matchs, langue="fr"):
    """Formate la liste des matchs du jour."""
    from core.translations import get_text

    date_str = datetime.now(TZ_KINSHASA).strftime("%d/%m/%Y")

    # ✅ FIX : vérifier explicitement len()
    if matchs is None or len(matchs) == 0:
        return get_text("aucun_match_jour", langue, date=date_str)

    texte = get_text("titre_matchs_jour", langue, date=date_str)
    texte += f"\n({len(matchs)} matchs)\n\n"

    for i, m in enumerate(matchs[:8], 1):
        try:
            heure_local = datetime.fromisoformat(
                m['heure'].replace("Z", "+00:00")
            ).astimezone(TZ_KINSHASA).strftime("%H:%M")
        except Exception:
            heure_local = "?"

        texte += (
            f"{i}. {m['home']} vs {m['away']}\n"
            f"   {heure_local} - {m['competition']}\n"
            f"   Reco : {m['dc_label']} a {round(m['dc_pct']*100, 1)}%\n\n"
        )

    texte += get_text("tip_matchs_jour", langue)
    return texte
