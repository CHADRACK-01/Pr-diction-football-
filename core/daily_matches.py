# core/daily_matches.py
"""
Récupération et formatage des matchs du jour.
- Logs agrégés (plus de log_warning par match)
- Gestion des dates propre
"""

from datetime import datetime, timezone, timedelta

from core.ml_model import global_model_data
from core.prediction import predire_match
from core.api.orchestrator import collecter_tous_les_matchs
from core.utils.logs import log_info, log_warning, log_error
from core.utils.markdown import formater_proprement
from config import CHAMPIONNATS, INFOS_COMPETITIONS, MAPPING_COMPETITIONS

TZ_KINSHASA = timezone(timedelta(hours=1))


def _normaliser(nom):
    """Normalise les noms d'équipes (mapping manuel)."""
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
    for suf in (" FC", " AFC", " CF", " SC", " AC", " Balompie", " Balompié"):
        if nom.endswith(suf):
            return nom[: -len(suf)]
    return nom


def _charger_modele_si_necessaire():
    """Charge les modèles si nécessaire."""
    if global_model_data.get("modeles_par_competition") is not None:
        return True
    log_info("Modèles absents, chargement...", "MATCHS")
    try:
        from core.ml_model import charger_et_entrainer
        return charger_et_entrainer()
    except Exception as e:
        log_error(
            message="Impossible de charger les modèles",
            module="MATCHS",
            exception=e,
        )
        return False


def _nom_competition(code):
    return CHAMPIONNATS.get(code, code)


def _get_info_competition(nom_comp):
    infos = INFOS_COMPETITIONS.get(nom_comp)
    if infos:
        return f"{infos['emoji']} {infos['pays']}"
    return ""


def get_matchs_du_jour():
    """Orchestre la récupération et calcule les pronostics."""
    if not _charger_modele_si_necessaire():
        log_error(
            message="Modèles non chargés, matchs du jour indisponibles",
            module="MATCHS",
        )
        return []

    try:
        matchs_bruts = collecter_tous_les_matchs()
    except Exception as e:
        log_error(
            message="Erreur collecte des matchs",
            module="MATCHS",
            exception=e,
        )
        return []

    if not matchs_bruts:
        log_warning(message="Aucun match renvoyé par l'orchestrateur", module="MATCHS")
        return []

    matchs_trouves = []
    matchs_ignores = 0

    for m in matchs_bruts:
        try:
            home = _normaliser(m.get("home", ""))
            away = _normaliser(m.get("away", ""))
            competition_code = m.get("competition", "default")

            if not home or not away:
                matchs_ignores += 1
                continue

            competition_reelle = m.get("competition_reelle") or MAPPING_COMPETITIONS.get(
                competition_code, competition_code
            )

            try:
                prono = predire_match(
                    home, away, competition=competition_reelle,
                    cotes_book=m.get("cotes_book"),
                )
            except Exception as e:
                log_error(
                    message="Erreur de prédiction individuelle",
                    module="MATCHS",
                    extra={"home": home, "away": away, "competition": competition_reelle},
                    exception=e,
                )
                matchs_ignores += 1
                continue

            if not isinstance(prono, dict) or "erreur" in prono:
                matchs_ignores += 1
                continue

            # Filtre DC
            dc_1x = float(prono.get("dc_1x", 0.5))
            dc_x2 = float(prono.get("dc_x2", 0.5))
            dc_12 = float(prono.get("dc_12", 0.5))
            options = [("1X", dc_1x), ("X2", dc_x2), ("12", dc_12)]
            meilleure = max(options, key=lambda x: x[1])

            cote_bot = round(1 / meilleure[1], 2) if meilleure[1] > 0 else 999
            if cote_bot < 1.30:
                matchs_ignores += 1
                continue

            matchs_trouves.append({
                "competition": competition_code,
                "nom_competition": _nom_competition(competition_code),
                "heure": m.get("heure"),
                "home": home,
                "away": away,
                "dc_label": meilleure[0],
                "dc_pct": float(meilleure[1]),
                "btts": float(prono.get("btts_yes", 0.5)),
                "over_25": float(prono.get("over_25", 0.5)),
                "ht_prolific": prono.get("ht_prolific"),
                "htr": prono.get("htr"),
                "confiance": float(meilleure[1]),
                "analyse_pari": prono.get("analyse_pari"),
            })
        except Exception as e:
            log_error(
                message="Erreur traitement match",
                module="MATCHS",
                extra={"home": m.get("home"), "away": m.get("away")},
                exception=e,
            )
            matchs_ignores += 1
            continue

    matchs_trouves.sort(key=lambda x: (x.get("heure") or "", -x["confiance"]))

    log_info(
        f"{len(matchs_trouves)} matchs retenus, {matchs_ignores} ignorés.",
        "MATCHS",
        extra={"retenus": len(matchs_trouves), "ignores": matchs_ignores},
    )
    return matchs_trouves


def formater_matchs_du_jour(matchs, langue="fr", est_premium=False, nb_max=None):
    """Formate les matchs pour Telegram."""
    date_str = datetime.now(TZ_KINSHASA).strftime("%d/%m/%Y")

    if not matchs:
        return f"📅 Aucun match disponible pour le {date_str}."

    if nb_max is not None:
        matchs = matchs[:nb_max]

    jours = {}
    matchs_affiches = 0
    erreurs_parse = 0

    for m in matchs:
        if not m.get("heure"):
            continue
        try:
            dt = datetime.fromisoformat(
                str(m["heure"]).replace("Z", "+00:00")
            ).astimezone(TZ_KINSHASA)
            jour_key = dt.strftime("%A %d/%m/%Y")
            jours.setdefault(jour_key, []).append(m)
            matchs_affiches += 1
        except Exception:
            erreurs_parse += 1
            continue

    if erreurs_parse > 0:
        log_warning(
            message=f"{erreurs_parse} dates non parsables (ignorées)",
            module="MATCHS",
            extra={"erreurs_parse": erreurs_parse},
        )

    if matchs_affiches == 0:
        return f"📅 Aucun match avec une cote intéressante aujourd'hui."

    texte = f"📅 **MATCHS DU JOUR - {date_str}**\n"
    texte += f"({matchs_affiches} matchs avec cote ≥ 1.30)\n\n"

    jours_fr = {
        "Monday": "Lundi", "Tuesday": "Mardi", "Wednesday": "Mercredi",
        "Thursday": "Jeudi", "Friday": "Vendredi", "Saturday": "Samedi",
        "Sunday": "Dimanche",
    }

    for jour_label, matchs_jour in jours.items():
        jour_parts = jour_label.split(" ", 1)
        jour_en = jour_parts[0]
        jour_trad = jours_fr.get(jour_en, jour_en)
        date_part = jour_parts[1] if len(jour_parts) > 1 else ""

        texte += "━━━━━━━━━━━━━━━━━━━━\n"
        texte += f"📅 {jour_trad} {date_part}\n"
        texte += "━━━━━━━━━━━━━━━━━━━━\n\n"

        for m in matchs_jour:
            try:
                heure_local = datetime.fromisoformat(
                    str(m["heure"]).replace("Z", "+00:00")
                ).astimezone(TZ_KINSHASA).strftime("%H:%M")
            except Exception:
                heure_local = "?"

            nom_comp = m.get("nom_competition", m.get("competition", "?"))
            info_pays = _get_info_competition(nom_comp)

            try:
                texte += formater_proprement(f"⚽ {m['home']} vs {m['away']}\n")
                texte += formater_proprement(f"   🕐 {heure_local} | 🏆 {nom_comp}\n")
                if info_pays:
                    texte += formater_proprement(f"   📍 {info_pays}\n")

                if est_premium:
                    texte += formater_proprement(
                        f"   🛡️ DC : {m['dc_label']} ({round(m['dc_pct'] * 100, 1)}%)\n"
                    )
                    texte += formater_proprement(
                        f"   🎯 BTTS : {round(m['btts'] * 100, 1)}%\n"
                    )
                    texte += formater_proprement(
                        f"   🥅 Over 2.5 : {round(m['over_25'] * 100, 1)}%\n"
                    )
                    if m.get("ht_prolific"):
                        ht = m["ht_prolific"]
                        texte += formater_proprement(
                            f"   ⏱️ MT : 1ère={round(ht.get('1ere_mt', 0.33) * 100, 1)}% | "
                            f"2ème={round(ht.get('2eme_mt', 0.33) * 100, 1)}%\n"
                        )
                    analyse = m.get("analyse_pari")
                    if analyse:
                        texte += formater_proprement(f"   💰 Cote Bot : {analyse['cote_bot']}\n")
                        if analyse.get("cote_book"):
                            texte += formater_proprement(
                                f"   🏢 Cote Book : {analyse['cote_book']}\n"
                            )
                            if analyse.get("is_value"):
                                texte += formater_proprement("   🔥 VALUE BET !\n")
                else:
                    texte += formater_proprement(
                        f"   🛡️ DC : {m['dc_label']} ({round(m['dc_pct'] * 100, 1)}%)\n"
                    )
            except Exception as e:
                log_warning(
                    message="Erreur formatage match",
                    module="MATCHS",
                    extra={"home": m.get("home"), "away": m.get("away")},
                    exception=e,
                )

            texte += "\n"

    if not est_premium:
        texte += "\n━━━━━━━━━━━━━━━━━━━━\n"
        texte += "⭐ Passe Premium pour les recommandations complètes !\n"

    return texte
