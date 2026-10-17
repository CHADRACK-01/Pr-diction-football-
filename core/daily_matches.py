import io
import joblib
from datetime import datetime, timezone, timedelta

from core.ml_model import global_model_data
from core.prediction import predire_match
from core.api.football_data import recuperer_matchs_bruts
from core.utils.logs import log_info, log_warning, log_error
from core.utils.markdown import formater_proprement


TZ_KINSHASA = timezone(timedelta(hours=1))


def _normaliser(nom):
    """
    Dictionnaire de correspondance entre les noms de l'API 
    et les noms du modèle (ex: 'Real Betis Balompié' -> 'Betis').
    """
    special = {
        # Premier League / Championship
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
        # LaLiga
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
        # Bundesliga
        "FC Bayern München": "Bayern Munich", "Borussia Dortmund": "Dortmund",
        "Bayer 04 Leverkusen": "Leverkusen", "Eintracht Frankfurt": "Ein Frankfurt",
        "VfB Stuttgart": "Stuttgart", "VfL Wolfsburg": "Wolfsburg",
        "Borussia Mönchengladbach": "M'gladbach", "1. FC Union Berlin": "Union Berlin",
        "SC Freiburg": "Freiburg", "TSG 1899 Hoffenheim": "Hoffenheim",
        "FC Augsburg": "Augsburg", "1. FSV Mainz 05": "Mainz",
        "SV Werder Bremen": "Werder Bremen", "VfL Bochum 1848": "Bochum",
        "1. FC Köln": "FC Koln", "SV Darmstadt 98": "Darmstadt",
        "1. FC Heidenheim 1846": "Heidenheim", "FC St. Pauli": "St Pauli",
        "Holstein Kiel": "Holstein Kiel", 
        # Ligue 1
        "Paris Saint-Germain FC": "Paris SG", "Olympique de Marseille": "Marseille",
        "Olympique Lyonnais": "Lyon", "AS Monaco FC": "Monaco", "LOSC Lille": "Lille",
        "OGC Nice": "Nice", "Stade Rennais FC 1901": "Rennes", "Racing Club de Lens": "Lens",
        "Stade de Reims": "Reims", "Montpellier HSC": "Montpellier", "FC Nantes": "Nantes",
        "Stade Brestois 29": "Brest", "RC Strasbourg Alsace": "Strasbourg", "Toulouse FC": "Toulouse",
        "FC Metz": "Metz", "Le Havre AC": "Le Havre", "Clermont Foot 63": "Clermont",
        "FC Lorient": "Lorient", "Angers SCO": "Angers", "AS Saint-Etienne": "St Etienne",
        "AJ Auxerre": "Auxerre",
        # Serie A
        "AS Roma": "Roma", "SS Lazio": "Lazio", "Juventus FC": "Juventus", "AC Milan": "Milan",
        "FC Internazionale Milano": "Inter", "SSC Napoli": "Napoli", "ACF Fiorentina": "Fiorentina",
        "Atalanta BC": "Atalanta", "Bologna FC 1909": "Bologna", "Torino FC": "Torino",
        "Udinese Calcio": "Udinese", "US Sassuolo Calcio": "Sassuolo", "Empoli FC": "Empoli",
        "US Lecce": "Lecce", "Hellas Verona FC": "Verona", "Cagliari Calcio": "Cagliari",
        "Genoa CFC": "Genoa", "US Salernitana 1919": "Salernitana", "Frosinone Calcio": "Frosinone",
        "AC Monza": "Monza", "Parma Calcio 1913": "Parma", "Como 1907": "Como", "Venezia FC": "Venezia",
    }
    if nom in special:
        return special[nom]
    for suf in [" FC", " AFC", " CF", " SC", " AC", " Balompie", " Balompié"]:
        if nom.endswith(suf):
            return nom[:-len(suf)]
    return nom


def _charger_modele_si_necessaire():
    """Charge le modèle IA depuis PostgreSQL si la mémoire est vide."""
    if global_model_data and 'model' in global_model_data and global_model_data.get('model') is not None:
        return True
    
    log_info("Modèle absent en mémoire. Tentative de chargement depuis la BDD...", "MATCHS")
    try:
        from users import charger_modele_cache
        cache = charger_modele_cache()
        if not cache:
            log_error("Cache vide. Impossible de charger le modèle.", "MATCHS")
            return False
            
        modele_bytes, precision, nb_matchs = cache
        buffer = io.BytesIO(modele_bytes)
        donnees = joblib.load(buffer)
        
        global_model_data.update(donnees)
        global_model_data['precision'] = precision
        global_model_data['_tables_initialisees'] = True
        log_info(f"Modèle chargé avec succès ! (Précision : {round(precision*100, 2)}%)", "MATCHS")
        return True
    except Exception as e:
        log_error(f"Erreur lors du chargement du modèle : {e}", "MATCHS", e)
        return False


def _nom_competition(code):
    noms = {
        "premier_league": "Premier League", "championship": "Championship",
        "laliga": "LaLiga", "ligue_1": "Ligue 1",
        "bundesliga_1": "Bundesliga", "serie_a": "Serie A",
    }
    return noms.get(code, code)


def get_matchs_du_jour():
    """
    Orchestre la récupération des matchs, le calcul des pronostics, 
    et renvoie une liste propre.
    """
    if not _charger_modele_si_necessaire():
        return []

    # 1. Récupération des matchs bruts via l'API
    matchs_bruts = recuperer_matchs_bruts()
    if not matchs_bruts:
        log_warning("Aucun match renvoyé par l'API.", "MATCHS")
        return []

    matchs_trouves = []
    
    # 2. Analyse de chaque match avec le modèle IA
    for m in matchs_bruts:
        home = _normaliser(m["home"])
        away = _normaliser(m["away"])
        
        try:
            # On calcule la prédiction
            prono = predire_match(home, away, cotes_book=m.get("cotes_book"))
            
            if not isinstance(prono, dict) or 'erreur' in prono:
                log_warning(f"Skip {home} vs {away} : équipe inconnue du modèle.", "MATCHS")
                continue

            dc_1x = float(prono['dc_1x'])
            dc_x2 = float(prono['dc_x2'])
            dc_12 = float(prono['dc_12'])

            options = [("1X", dc_1x), ("X2", dc_x2), ("12", dc_12)]
            meilleure = max(options, key=lambda x: x[1])

            # 3. Filtrage des cotes < 1.30
            cote_bot = round(1 / meilleure[1], 2) if meilleure[1] > 0 else 999
            if cote_bot < 1.30:
                continue

            matchs_trouves.append({
                "competition": m["competition"],
                "heure": m["heure"],
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
            log_error(f"Exception pour {home} vs {away}: {e}", "MATCHS", e)
            continue

    # 4. Logs de diagnostic
    if not matchs_trouves:
        log_warning("Aucun match ne passe le filtre de cote (≥ 1.30).", "MATCHS")
    else:
        log_info(f"{len(matchs_trouves)} matchs prêts à être publiés.", "MATCHS")

    matchs_trouves.sort(key=lambda x: (x['heure'], -x['confiance']))
    return matchs_trouves


def formater_matchs_du_jour(matchs, langue="fr", est_premium=False, nb_max=None):
    """
    Formate la liste des matchs pour Telegram.
    Utilise formater_proprement() pour éviter les erreurs Markdown.
    """
    date_str = datetime.now(TZ_KINSHASA).strftime("%d/%m/%Y")

    if matchs is None or len(matchs) == 0:
        return f"📅 Aucun match disponible pour le {date_str}."

    if nb_max is not None:
        matchs = matchs[:nb_max]

    jours = {}
    matchs_affiches = 0

    for m in matchs:
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
        return f"📅 Aucun match avec une cote intéressante aujourd'hui."

    texte = f"📅 **MATCHS DU JOUR - {date_str}**\n"
    texte += f"({matchs_affiches} matchs avec cote ≥ 1.30)\n\n"

    jours_fr = {
        "Monday": "Lundi", "Tuesday": "Mardi", "Wednesday": "Mercredi",
        "Thursday": "Jeudi", "Friday": "Vendredi", "Saturday": "Samedi", "Sunday": "Dimanche"
    }

    for jour_label, matchs_jour in jours.items():
        jour_parts = jour_label.split(" ", 1)
        jour_en = jour_parts[0]
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

            # On sécurise chaque ligne avec formater_proprement
            texte += formater_proprement(f"⚽ {m['home']} vs {m['away']}\n")
            texte += formater_proprement(f"   🕐 {heure_local} | 🏆 {nom_comp}\n")

            if est_premium:
                analyse = m.get('analyse_pari')
                if analyse:
                    texte += formater_proprement(f"   🎯 Reco : {analyse['label']} ({round(analyse['proba']*100, 1)}%)\n")
                    texte += formater_proprement(f"   🤖 Cote Bot : {analyse['cote_bot']}\n")
                    if analyse['cote_book']:
                        texte += formater_proprement(f"   🏢 Cote Book : {analyse['cote_book']}\n")
                        if analyse['is_value']:
                            texte += formater_proprement(f"   🔥 VALUE BET !\n")
                    else:
                        texte += "   🏢 Cote Book : N/A\n"
                else:
                    texte += formater_proprement(f"   💡 Reco : {m['dc_label']} à {round(m['dc_pct']*100, 1)}%\n")

            texte += "\n"

    if not est_premium:
        texte += "\n━━━━━━━━━━━━━━━━━━━━\n"
        texte += "⭐ Passe Premium pour voir les recommandations et les cotes !\n"

    return texte
