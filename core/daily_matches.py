import io
import joblib
from datetime import datetime, timezone, timedelta

from core.ml_model import global_model_data
from core.prediction import predire_match
from core.api.manager import get_matchs_du_jour as manager_get_matchs_du_jour
from core.utils.logs import log_info, log_warning, log_error
from core.utils.markdown import formater_proprement
from config import CHAMPIONNATS, INFOS_COMPETITIONS

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
        "1. FC Heidenheim 1846": "Heidenheim", "FC St. Pauli": "St
