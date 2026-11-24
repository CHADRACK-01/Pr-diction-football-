"""Analyseurs locaux pour les fonctionnalités 24, 58, 59, 63 et 64."""

import math
import random
from datetime import datetime


def calculer_elo_live(elo_home, elo_away, score_actuel=(0, 0), but_equipe=None, k=24):
    expected_home = 1 / (1 + 10 ** ((elo_away - elo_home) / 400))
    home_goals, away_goals = score_actuel
    if but_equipe == "home":
        resultat_home = 1.0
        bonus = 1
    elif but_equipe == "away":
        resultat_home = 0.0
        bonus = 1
    else:
        resultat_home = 0.5
        bonus = 0

    goal_diff = abs(home_goals - away_goals)
    mouvement = k * max(bonus, 1 if goal_diff > 0 else 0) * (resultat_home - expected_home)
    return {"home": round(elo_home + mouvement, 1), "away": round(elo_away - mouvement, 1)}


def simuler_monte_carlo(lambda_home, lambda_away, simulations=10000, graine=None):
    if lambda_home <= 0 or lambda_away <= 0:
        raise ValueError("Les espérances de buts doivent être strictement positives")
    if simulations <= 0:
        raise ValueError("Le nombre de simulations doit être positif")

    rng = random.Random(graine)
    compte = {"1": 0, "N": 0, "2": 0}

    def poisson(lamb):
        limite = math.exp(-lamb)
        nombre = 0
        produit = 1.0
        while produit > limite:
            nombre += 1
            produit *= rng.random()
        return max(0, nombre - 1)

    for _ in range(simulations):
        home = poisson(float(lambda_home))
        away = poisson(float(lambda_away))
        if home > away:
            compte["1"] += 1
        elif home == away:
            compte["N"] += 1
        else:
            compte["2"] += 1

    return {
        "simulations": simulations,
        "probabilites": {cle: valeur / simulations for cle, valeur in compte.items()},
        "comptes": compte,
    }


def detecter_derby(equipe_home, equipe_away):
    derbys = {
        frozenset(("Real Madrid", "Barcelona")),
        frozenset(("Manchester United", "Manchester City")),
        frozenset(("Paris Saint-Germain", "Marseille")),
        frozenset(("PSG", "Marseille")),
        frozenset(("Bayern Munich", "Borussia Dortmund")),
        frozenset(("Inter Milan", "AC Milan")),
        frozenset(("Roma", "Lazio")),
        frozenset(("Arsenal", "Tottenham")),
        frozenset(("Liverpool", "Everton")),
        frozenset(("TP Mazembe", "AS Vita Club")),
    }
    for paire in derbys:
        if equipe_home in paire and equipe_away in paire:
            return True
    return False


def calculer_fatigue_calendrier(dates_matchs, maintenant=None):
    if not dates_matchs:
        return {"nb_matchs": 0, "jours": [], "epuisement": 0, "alerte": False}

    dates = sorted(datetime.strptime(date, "%Y-%m-%d") for date in dates_matchs)
    ecarts = [
        (dates[index] - dates[index - 1]).days
        for index in range(1, len(dates))
        if (dates[index] - dates[index - 1]).days >= 0
    ]
    nb_serre = sum(1 for ecart in ecarts if ecart <= 7)
    epuisement = min(10, nb_serre * 3)
    return {
        "nb_matchs": len(dates),
        "jours": [(date.strftime("%Y-%m-%d")) for date in dates],
        "epuisement": epuisement,
        "alerte": epuisement >= 6,
    }
