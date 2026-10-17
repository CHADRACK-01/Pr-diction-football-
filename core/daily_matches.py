import requests
import difflib
from datetime import datetime, timezone, timedelta

from core.ml_model import global_model_data
from core.prediction import predire_match


FOOTBALL_DATA_KEY = "5a7a6a3afcca4bc88400d73a0e394588"

TZ_KINSHASA = timezone(timedelta(hours=1))

COMPETITIONS = {
    "premier_league": "PL",
    "championship": "ELC",
    "laliga": "PD",
    "ligue_1": "FL1",
    "bundesliga_1": "BL1",
    "serie_a": "SA",
}


def _normaliser(nom):
    special = {
        "Manchester City FC": "Man City", "Manchester United FC": "Man United",
        "Newcastle United FC": "Newcastle", "Nottingham Forest FC": "Nott'm Forest",
        "Tottenham Hotspur FC": "Tottenham", "Wolverhampton Wanderers FC": "Wolves",
        "Brighton & Hove Albion FC": "Brighton", "West Ham United FC": "West Ham",
        "Hull City AFC": "Hull", "Leeds United FC": "Leeds", "Leicester City FC": "Leicester",
        "Norwich City FC": "Norwich", "Stoke City FC": "Stoke", "Sunderland AFC": "Sunderland",
        "Derby County FC": "Derby", "Swansea City AFC": "Swansea", "Cardiff City FC": "Cardiff",
        "AFC Bournemouth": "Bournemouth", "Preston North End FC": "Preston",
        "Queens Park Rangers FC": "QPR", "Bolton Wanderers FC": "Bolton",
        "Birmingham City FC": "Birmingham", "Wrexham AFC": "Wrexham",
        "Sheffield United FC": "Sheffield United", "Sheffield Wednesday FC": "Sheffield Weds",
        "West Bromwich Albion FC": "West Brom", "Bristol City FC": "Bristol City",
        "Coventry City FC": "Coventry", "Middlesbrough FC": "Middlesbrough",
        "Millwall FC": "Millwall", "Plymouth Argyle FC": "Plymouth",
        "Rotherham United FC": "Rotherham", "Huddersfield Town AFC": "Huddersfield",
        "Blackburn Rovers FC": "Blackburn", "Watford FC": "Watford",
        "Burnley FC": "Burnley", "Luton Town FC": "Luton",
        "Real Madrid CF": "Real Madrid", "FC Barcelona": "Barcelona",
        "Atletico de Madrid": "Ath Madrid", "Athletic Club": "Ath Bilbao",
        "Real Sociedad de Futbol": "Sociedad", "Real Betis Balompie": "Betis",
        "Real Betis Balompié": "Betis", "Sevilla FC": "Sevilla",
        "Valencia CF": "Valencia", "Villarreal CF": "Villarreal",
        "Getafe CF": "Getafe", "RCD Espanyol de Barcelona": "Espanol",
        "Rayo Vallecano de Madrid": "Vallecano", "RC Celta de Vigo": "Celta",
        "RCD Mallorca": "Mallorca", "CA Osasuna": "Osasuna",
        "Granada CF": "Granada", "Deportivo Alaves": "Alaves",
        "Deportivo Alavés": "Alaves", "Cadiz CF": "Cadiz",
        "UD Las Palmas": "Las Palmas", "Girona FC": "Girona",
        "Real Valladolid CF": "Valladolid", "Levante UD": "Levante",
        "Real Racing Club de Santander": "Santander", "Elche CF": "Elche",
        "CD Leganes": "Leganes", "Real Zaragoza": "Zaragoza", "Real Oviedo": "Oviedo",
        "Sporting Gijon": "Sp Gijon", "Racing de Ferrol": "Ferrol",
        "Albacete Balompie": "Albacete", "Burgos CF": "Burgos",
        "FC Andorra": "Andorra", "SD Huesca": "Huesca",
        "CD Mirandes": "Mirandes", "UD Ibiza": "Ibiza",
        "FC Bayern München": "Bayern Munich", "Borussia Dortmund": "Dortmund",
        "Bayer 04 Leverkusen": "Leverkusen", "Eintracht Frankfurt": "Ein Frankfurt",
        "VfB Stuttgart": "Stuttgart", "VfL Wolfsburg": "Wolfsburg",
        "Borussia Mönchengladbach": "M'gladbach", "1. FC Union Berlin": "Union Berlin",
        "SC Freiburg": "Freiburg", "TSG 1899 Hoffenheim": "Hoffenheim",
        "FC Augsburg": "Augsburg", "1. FSV Mainz 05": "Mainz",
        "SV Werder Bremen": "Werder Bremen", "VfL Bochum 1848": "Bochum",
        "1. FC Köln": "FC Koln", "SV Darmstadt 98": "Darmstadt",
        "1. FC Heidenheim 1846": "Heidenheim", "FC St. Pauli": "St Pauli",
        "Holstein Kiel": "Holstein Kiel", "Paris Saint-Germain FC": "Paris SG",
        "Olympique de Marseille": "Marseille", "Olympique Lyonnais": "Lyon",
        "AS Monaco FC": "Monaco", "LOSC Lille": "Lille", "OGC Nice": "Nice",
        "Stade Rennais FC 1901": "Rennes", "Racing Club de Lens": "Lens",
        "Stade de Reims": "Reims", "Montpellier HSC": "Montpellier",
        "FC Nantes": "Nantes", "Stade Brestois 29": "Brest",
        "RC Strasbourg Alsace": "Strasbourg", "Toulouse FC": "Toulouse",
        "FC Metz": "Metz", "Le Havre AC": "Le Havre", "Clermont Foot 63": "Clermont",
        "FC Lorient": "Lorient", "Angers SCO": "Angers", "AS Saint-Etienne": "St Etienne",
        "AJ Auxerre": "Auxerre", "AS Roma": "Roma", "SS Lazio": "Lazio",
        "Juventus FC": "Juventus", "AC Milan": "Milan",
        "FC Internazionale Milano": "Inter", "SSC Napoli": "Napoli",
        "ACF Fiorentina": "Fiorentina", "Atalanta BC": "Atalanta",
        "Bologna FC 1909": "Bologna", "Torino FC": "Torino",
        "Udinese Calcio": "Udinese", "US Sassuolo Calcio": "Sassuolo",
        "Empoli FC": "Empoli", "US Lecce": "Lecce", "Hellas Verona FC": "Verona",
        "Cagliari Calcio": "Cagliari", "Genoa CFC": "Genoa",
        "US Salernitana 1919": "Salernitana", "Frosinone Calcio": "Frosinone",
        "AC Monza": "Monza", "Parma Calcio 1913": "Parma", "Como 1907": "Como",
        "Venezia FC": "Venezia",
    }
    if nom in special:
        return special[nom]
    for suf in [" FC", " AFC", " CF", " SC", " AC", " Balompie", " Balompié"]:
        if nom.endswith(suf):
            return nom[:-len(suf)]
    return nom


def _nom_competition(code):
    noms = {
        "premier_league": "Premier League", "championship": "Championship",
        "laliga": "LaLiga", "ligue_1": "Ligue 1",
        "bundesliga_1": "Bundesliga", "serie_a": "Serie A",
    }
    return noms.get(code, code)


def get_matchs_du_jour():
    """Récupère les matchs via l'API avec les cotes bookmaker et une gestion d'erreur robuste."""
    if not global_model_data: 
        print("⚠️ API : Modèle non chargé.")
        return []
    if 'teams' not in global_model_data: 
        print("⚠️ API : Données des équipes manquantes.")
        return []

    teams_data = global_model_data.get('teams')
    if teams_data is None or len(teams_data) == 0: 
        print("⚠️ API : Liste des équipes vide.")
        return []

    date_debut = datetime.now(TZ_KINSHASA).strftime("%Y-%m-%d")
    date_fin = (datetime.now(TZ_KINSHASA) + timedelta(days=3)).strftime("%Y-%m-%d")

    headers = {"X-Auth-Token": FOOTBALL_DATA_KEY}
    matchs_trouves = []

    for code, comp_code in COMPETITIONS.items():
        try:
            url = f"https://api.football-data.org/v4/competitions/{comp_code}/matches"
            params = {"dateFrom": date_debut, "dateTo": date_fin}
            res = requests.get(url, headers=headers, params=params, timeout=15)

            if res.status_code != 200: 
                print(f"⚠️ API Error {res.status_code} pour {code}")
                continue

            data = res.json()
            for m in data.get("matches", []):
                status = m.get("status", "")
                if status not in ["SCHEDULED", "TIMED"]: continue

                home = _normaliser(m["homeTeam"]["name"])
                away = _normaliser(m["awayTeam"]["name"])
                heure_utc = m["utcDate"]

                # RÉCUPÉRATION DES COTES BOOKMAKER (Bet365)
                cotes_book = None
                odds = m.get("odds", {})
                if isinstance(odds, dict) and "bet365" in odds:
                    b365 = odds["bet365"]
                    cotes_book = {
                        'h': b365.get('homeWin'),
                        'd': b365.get('draw'),
                        'a': b365.get('awayWin')
                    }
                elif isinstance(odds, dict) and odds.get('homeWin'):
                    cotes_book = {
                        'h': odds.get('homeWin'),
                        'd': odds.get('draw'),
                        'a': odds.get('awayWin')
                    }

                try:
                    prono = predire_match(home, away, cotes_book=cotes_book)
                    if not isinstance(prono, dict): continue
                    if 'erreur' in prono: 
                        print(f"⚠️ Skip {home} vs {away} : équipe inconnue du modèle.")
                        continue
                    if 'dc_1x' not in prono: continue

                    dc_1x = float(prono['dc_1x'])
                    dc_x2 = float(prono['dc_x2'])
                    dc_12 = float(prono['dc_12'])

                    options = [("1X", dc_1x), ("X2", dc_x2), ("12", dc_12)]
                    meilleure = max(options, key=lambda x: x[1])

                    cote_bot = round(1 / meilleure[1], 2) if meilleure[1] > 0 else 999
                    if cote_bot < 1.30:
                        continue

                    matchs_trouves.append({
                        "competition": code,
                        "heure": heure_utc,
                        "home": home,
                        "away": away,
                        "p_h": float(prono['p_h']),
                        "p_d": float(prono['p_d']),
                        "p_a": float(prono['p_a']),
                        "score": prono['best_score'],
                        "dc_label": meilleure[0],
                        "dc_pct": float(meilleure[1]),
                        "confiance": float(meilleure[1]),
                        "analyse_pari": prono.get('analyse_pari')
                    })
                except Exception as e:
                    print(f"⚠️ Exception match {home} vs {away}: {e}")
                    continue

        except Exception as e:
            print(f"⚠️ Exception API {code}: {e}")
            continue

    # --- LOGS DE DIAGNOSTIC ---
    if not matchs_trouves:
        print("⚠️ API : Aucun match trouvé via l'API (date ou championnat vide).")
    else:
        print(f"🔍 {len(matchs_trouves)} matchs trouvés AVANT filtrage des cotes.")
        
    matchs_filtres = []
    for m in matchs_trouves:
        if m.get('analyse_pari') and m['analyse_pari']['cote_bot'] >= 1.30:
            matchs_filtres.append(m)
            
    if not matchs_filtres:
        print("⚠️ Filtrage : Aucun match ne passe le filtre de cote (≥ 1.30).")
    else:
        print(f"✅ {len(matchs_filtres)} matchs après filtrage des cotes.")

    matchs_filtres.sort(key=lambda x: (x['heure'], -x['confiance']))
    return matchs_filtres


def formater_matchs_du_jour(matchs, langue="fr", est_premium=False, nb_max=None):
    """Formate la liste des matchs avec filtrage et gestion d'erreur."""
    from core.translations import get_text

    date_str = datetime.now(TZ_KINSHASA).strftime("%d/%m/%Y")

    if matchs is None or len(matchs) == 0:
        return get_text("aucun_match_jour", langue, date=date_str)

    if nb_max is not None:
        matchs = matchs[:nb_max]

    jours = {}
    matchs_affiches = 0

    for m in matchs:
        analyse = m.get('analyse_pari')
        if est_premium and analyse and analyse['cote_bot'] < 1.30:
            continue
            
        try:
            dt = datetime.fromisoformat(m['heure'].replace("Z", "+00:00")).astimezone(TZ_KINSHASA)
            jour_key = dt.strftime("%A %d/%m/%Y")
        except Exception:
            jour_key = "?"

        if jour_key not in jours:
            jours[jour_key] = []
        jours[jour_key].append(m)
        matchs_affiches += 1

    if matchs_affiches == 0:
        return (
            f"📅 Matchs du {date_str}\n\n"
            f"⚠️ **Aucun match avec une cote intéressante (≥ 1.30) aujourd'hui.**\n\n"
            f"👉 Essaie les **Coupons** ou les **Top affiches** pour d'autres opportunités !\n"
            f"👉 Ou tape **Faire un Pronostic** pour analyser un match spécifique."
        )

    texte = get_text("titre_matchs_jour", langue, date=date_str)
    texte += f"\n({matchs_affiches} matchs avec cote ≥ 1.30)\n\n"

    jours_fr = {
        "Monday": "Lundi", "Tuesday": "Mardi", "Wednesday": "Mercredi",
        "Thursday": "Jeudi", "Friday": "Vendredi", "Saturday": "Samedi", "Sunday": "Dimanche"
    }
    jours_en = {
        "Monday": "Monday", "Tuesday": "Tuesday", "Wednesday": "Wednesday",
        "Thursday": "Thursday", "Friday": "Friday", "Saturday": "Saturday", "Sunday": "Sunday"
    }

    for jour_label, matchs_jour in jours.items():
        jour_parts = jour_label.split(" ", 1)
        jour_en = jour_parts[0]
        if langue == "en":
            jour_trad = jours_en.get(jour_en, jour_en)
        else:
            jour_trad = jours_fr.get(jour_en, jour_en)

        date_part = jour_parts[1] if len(jour_parts) > 1 else ""
        texte += f"━━━━━━━━━━━━━━━━━━━━\n"
        texte += f"📅 {jour_trad} {date_part}\n"
        texte += f"━━━━━━━━━━━━━━━━━━━━\n\n"

        for m in matchs_jour:
            try:
                heure_local = datetime.fromisoformat(
                    m['heure'].replace("Z", "+00:00")
                ).astimezone(TZ_KINSHASA).strftime("%H:%M")
            except Exception:
                heure_local = "?"

            nom_comp = _nom_competition(m['competition'])

            texte += f"⚽ {m['home']} vs {m['away']}\n"
            texte += f"   🕐 {heure_local} | 🏆 {nom_comp}\n"

            if est_premium:
                analyse = m.get('analyse_pari')
                if analyse:
                    texte += f"   🎯 Reco : {analyse['label']} ({round(analyse['proba']*100, 1)}%)\n"
                    texte += f"   🤖 Cote Bot : {analyse['cote_bot']}\n"
                    if analyse['cote_book']:
                        texte += f"   🏢 Cote Book : {analyse['cote_book']}\n"
                        if analyse['is_value']:
                            texte += f"   🔥 **VALUE BET !**\n"
                    else:
                        texte += f"   🏢 Cote Book : N/A\n"
                else:
                    texte += f"   💡 Reco : {m['dc_label']} à {round(m['dc_pct']*100, 1)}%\n"

            texte += "\n"

    if not est_premium:
        texte += "\n━━━━━━━━━━━━━━━━━━━━\n"
        texte += "⭐ Passe Premium pour voir les recommandations et les cotes !\n"

    texte += get_text("tip_matchs_jour", langue)
    return texte
