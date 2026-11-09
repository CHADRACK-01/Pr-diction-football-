import io
import joblib
from datetime import datetime, timezone, timedelta

from core.ml_model import global_model_data
from core.prediction import predire_match
from core.api.manager import get_matchs_du_jour as manager_get_matchs_du_jour
from core.utils.logs import log_info, log_warning, log_error
from core.utils.markdown import formater_proprement
from config import CHAMPIONNATS, INFOS_COMPETITIONS, MAPPING_COMPETITIONS

TZ_KINSHASA = timezone(timedelta(hours=1))


def _normaliser(nom):
    """Dictionnaire de correspondance entre les noms des API et les noms du modèle."""
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
        "Holstein Kiel": "Holstein Kiel", 
        "Paris Saint-Germain FC": "Paris SG", "Olympique de Marseille": "Marseille",
        "Olympique Lyonnais": "Lyon", "AS Monaco FC": "Monaco", "LOSC Lille": "Lille",
        "OGC Nice": "Nice", "Stade Rennais FC 1901": "Rennes", "Racing Club de Lens": "Lens",
        "Stade de Reims": "Reims", "Montpellier HSC": "Montpellier", "FC Nantes": "Nantes",
        "Stade Brestois 29": "Brest", "RC Strasbourg Alsace": "Strasbourg", "Toulouse FC": "Toulouse",
        "FC Metz": "Metz", "Le Havre AC": "Le Havre", "Clermont Foot 63": "Clermont",
        "FC Lorient": "Lorient", "Angers SCO": "Angers", "AS Saint-Etienne": "St Etienne",
        "AJ Auxerre": "Auxerre",
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
    """Charge les modèles depuis Turso si la mémoire est vide."""
    if global_model_data.get('modeles_par_competition') is not None:
        return True
    
    log_info("Modèles absents en mémoire. Chargement depuis Turso...", "MATCHS")
    from core.ml_model import charger_et_entrainer
    return charger_et_entrainer()


def _nom_competition(code):
    """Renvoie le nom propre de la compétition à partir de son code."""
    return CHAMPIONNATS.get(code, code)


def _get_info_competition(nom_comp):
    """Renvoie l'emoji et le pays de la compétition."""
    infos = INFOS_COMPETITIONS.get(nom_comp)
    if infos:
        return f"{infos['emoji']} {infos['pays']}"
    return ""


def get_matchs_du_jour():
    """Orchestre la récupération via le manager, puis calcule les pronostics."""
    if not _charger_modele_si_necessaire():
        return []

    matchs_bruts = manager_get_matchs_du_jour()
    if not matchs_bruts:
        log_warning("Aucun match renvoyé par le manager.", "MATCHS")
        return []

    matchs_trouves = []
    
    for m in matchs_bruts:
        home = _normaliser(m["home"])
        away = _normaliser(m["away"])
        competition_code = m.get("competition", "default")
        
        # ⚠️ CONVERSION : code API -> nom propre du modèle
        competition_reelle = MAPPING_COMPETITIONS.get(competition_code, competition_code)
        
        prono = predire_match(home, away, competition=competition_reelle, cotes_book=m.get("cotes_book"))
        
        if not isinstance(prono, dict) or 'erreur' in prono:
            log_warning(f"Skip {home} vs {away} : {prono.get('erreur', 'erreur inconnue')}", "MATCHS")
            continue

        # ⚠️ On filtre sur la Double Chance (notre marché le plus fiable)
        dc_1x = float(prono.get('dc_1x', 0.5))
        dc_x2 = float(prono.get('dc_x2', 0.5))
        dc_12 = float(prono.get('dc_12', 0.5))

        options = [("1X", dc_1x), ("X2", dc_x2), ("12", dc_12)]
        meilleure = max(options, key=lambda x: x[1])

        cote_bot = round(1 / meilleure[1], 2) if meilleure[1] > 0 else 999
        if cote_bot < 1.30:
            continue

        matchs_trouves.append({
            "competition": competition_code,
            "nom_competition": _nom_competition(competition_code),
            "heure": m.get("heure"),
            "home": home,
            "away": away,
            # Marchés
            "dc_label": meilleure[0],
            "dc_pct": float(meilleure[1]),
            "btts": float(prono.get('btts_yes', 0.5)),
            "over_25": float(prono.get('over_25', 0.5)),
            # Mi-temps (peut être None si le modèle n'a pas chargé)
            "ht_prolific": prono.get('ht_prolific'),
            "htr": prono.get('htr'),
            # Confiance & analyse
            "confiance": float(meilleure[1]),
            "analyse_pari": prono.get('analyse_pari')
        })

    matchs_trouves.sort(key=lambda x: (x['heure'] or '', -x['confiance']))
    return matchs_trouves


def formater_matchs_du_jour(matchs, langue="fr", est_premium=False, nb_max=None):
    """Formate la liste des matchs pour Telegram avec les nouveaux marchés."""
    date_str = datetime.now(TZ_KINSHASA).strftime("%d/%m/%Y")

    if matchs is None or len(matchs) == 0:
        return f"📅 Aucun match disponible pour le {date_str}."

    if nb_max is not None:
        matchs = matchs[:nb_max]

    jours = {}
    matchs_affiches = 0

    for m in matchs:
        dt = datetime.fromisoformat(m['heure'].replace("Z", "+00:00")).astimezone(TZ_KINSHASA)
        jour_key = dt.strftime("%A %d/%m/%Y")
        
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
            heure_local = datetime.fromisoformat(
                m['heure'].replace("Z", "+00:00")
            ).astimezone(TZ_KINSHASA).strftime("%H:%M")

            nom_comp = m.get('nom_competition', m['competition'])
            info_pays = _get_info_competition(nom_comp)

            texte += formater_proprement(f"⚽ {m['home']} vs {m['away']}\n")
            texte += formater_proprement(f"   🕐 {heure_local} | 🏆 {nom_comp}\n")
            
            if info_pays:
                texte += formater_proprement(f"   📍 {info_pays}\n")

            if est_premium:
                texte += formater_proprement(f"   🛡️ DC : {m['dc_label']} ({round(m['dc_pct']*100, 1)}%)\n")
                texte += formater_proprement(f"   🎯 BTTS : {round(m['btts']*100, 1)}%\n")
                texte += formater_proprement(f"   🥅 Over 2.5 : {round(m['over_25']*100, 1)}%\n")
                
                # Mi-temps
                if m.get('ht_prolific'):
                    ht = m['ht_prolific']
                    texte += formater_proprement(f"   ⏱️ MT : 1ère={round(ht.get('1ere_mt',0.33)*100,1)}% | 2ème={round(ht.get('2eme_mt',0.33)*100,1)}%\n")
                
                # Value bet
                analyse = m.get('analyse_pari')
                if analyse:
                    texte += formater_proprement(f"   💰 Cote Bot : {analyse['cote_bot']}\n")
                    if analyse.get('cote_book'):
                        texte += formater_proprement(f"   🏢 Cote Book : {analyse['cote_book']}\n")
                        if analyse.get('is_value'):
                            texte += formater_proprement(f"   🔥 VALUE BET !\n")
            else:
                texte += formater_proprement(f"   🛡️ DC : {m['dc_label']} ({round(m['dc_pct']*100, 1)}%)\n")

            texte += "\n"

    if not est_premium:
        texte += "\n━━━━━━━━━━━━━━━━━━━━\n"
        texte += "⭐ Passe Premium pour voir les recommandations complètes (BTTS, Over, Mi-temps, Value Bets) !\n"

    return texte
