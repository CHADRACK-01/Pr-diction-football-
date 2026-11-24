"""Règles locales de gestion du risque, anti-perte et mises progressives."""


def evaluer_plan_anti_perte(resultats_recents, limite=3):
    pertes = 0
    for resultat in resultats_recents:
        if str(resultat).upper() in {"P", "PERDU", "LOSE", "0", "-1"}:
            pertes += 1
        else:
            pertes = 0

    active = pertes >= limite
    return {
        "active": active,
        "pertes_consecutives": pertes,
        "bloquer_gros_combine": active,
        "niveau": "securise" if active else "normal",
    }


def calculer_martingale_douce(mise_initiale, perte=0, multiplicateur=2.0, plafond=5.0):
    if mise_initiale <= 0:
        raise ValueError("La mise initiale doit être positive")
    if perte <= 0:
        return round(mise_initiale, 2)
    facteur = min(multiplicateur ** min(perte, 10), plafond)
    return round(mise_initiale * facteur, 2)


def evaluer_cashout_partiel(mise, cote_initiale, cote_actuelle, fraction=0.5):
    if mise <= 0 or cote_initiale <= 1 or cote_actuelle <= 1:
        raise ValueError("Mise et cotes doivent être strictement positives")
    if not 0 < fraction <= 1:
        raise ValueError("La fraction doit être comprise entre 0 et 1")

    valeur_totale = mise * (cote_actuelle / cote_initiale)
    encaisse = valeur_totale * fraction
    reste = valeur_totale - encaisse
    return {
        "fraction": fraction,
        "encaisse_immediate": round(encaisse, 2),
        "reste_enjeu": round(reste, 2),
        "valeur_totale_estimee": round(valeur_totale, 2),
    }
