"""Outils locaux pouvant compléter plusieurs fonctionnalités sans fournisseur tiers.

Ces fonctions sont déterministes et ne garantissent aucun gain sportif ou financier.
"""

from datetime import datetime


def construire_combine(matchs, cote_cible, tolerance=0.25):
    """Sélectionne les matchs dont le produit des cotes approche la cote cible."""
    retenus = []
    cote = 1.0
    for match in sorted(matchs, key=lambda item: item.get("proba", 0), reverse=True):
        cote_match = float(match.get("cote", 1.0))
        if cote_match <= 1:
            continue
        nouvelle_cote = cote * cote_match
        if nouvelle_cote <= cote_cible * (1 + tolerance):
            retenus.append(match)
            cote = nouvelle_cote
        if cote >= cote_cible:
            break
    ecart = abs(cote - cote_cible) / cote_cible if cote_cible > 0 else 1
    return {"matchs": retenus, "cote_estimee": round(cote, 2), "ecart_pourcent": round(ecart * 100, 2), "conforme": ecart <= tolerance}


def detecter_match_nul(proba_nul, cote_nul):
    """Fonctionnalité 23 : filtre conservateur pour les matchs nuls."""
    if not 0 <= proba_nul <= 1:
        raise ValueError("La probabilité doit être comprise entre 0 et 1")
    valide = proba_nul > 0.32 and cote_nul >= 3.30
    return {"eligible": valide, "proba_nul": proba_nul, "cote_nul": cote_nul, "niveau": "eleve" if valide else "normal"}


def detecter_underdog(proba, cote):
    """Fonctionnalité 39 : signale un outsider seulement sur des critères explicites."""
    eligible = 0 <= proba <= 1 and cote >= 4.0 and proba >= 0.20
    return {"eligible": eligible, "fun_bet": eligible, "proba": proba, "cote": cote}


def checklist_avant_pari(match, mise, bankroll):
    """Fonctionnalité 54 : checklist locale avec blocage en cas de risque élevé."""
    controles = {
        "composition_verifiee": bool(match.get("composition_verifiee")),
        "meteo_verifiee": bool(match.get("meteo_verifiee")),
        "mise_controlee": 0 < mise <= bankroll * 0.05,
        "cote_disponible": float(match.get("cote", 0)) > 1,
    }
    return {"controles": controles, "pret": all(controles.values())}


def calculer_mise_progressive(mise_initiale, resultat_precedent, strategie="fibonacci"):
    """Fonctionnalités 42 : fixe, Fibonacci ou Martingale douce."""
    if mise_initiale <= 0:
        raise ValueError("La mise initiale doit être positive")
    if strategie == "fixe":
        return round(mise_initiale, 2)
    if strategie == "martingale_douce":
        facteur = 2 if str(resultat_precedent).upper() in {"P", "PERDU", "0", "-1"} else 1
        return round(mise_initiale * facteur, 2)
    fib = (1, 1, 2, 3, 5, 8, 13, 21)
    rang = int(resultat_precedent) if str(resultat_precedent).isdigit() else 0
    rang = min(rang, len(fib) - 1)
    return round(mise_initiale * fib[rang], 2)


def generer_debrief(match, pari, resultat):
    """Fonctionnalité 53 : texte explicatif après match."""
    gagnant = str(resultat).upper() in {"G", "GAGNE", "1", "WIN"}
    if gagnant:
        cause = "le scénario prévu s'est réalisé"
    else:
        cause = "un facteur imprévu ou une variance défavorable a modifié le scénario"
    return {"gagnant": gagnant, "texte": f"Prono {pari}: {cause}. Match {match}."}


def moderer_texte(texte, mots_interdits=None):
    """Fonctions 112/113 : filtre de mots et liens sans modération externe."""
    mots_interdits = mots_interdits or ("insulte", "spam", "numero")
    texte_normalise = str(texte).lower()
    contient_lien = "http://" in texte_normalise or "https://" in texte_normalise or "t.me/" in texte_normalise
    interdit = [mot for mot in mots_interdits if mot in texte_normalise]
    return {"autorise": not contient_lien and not interdit, "contient_lien": contient_lien, "mots_interdits": interdit}


def evaluer_anti_spam(timestamps, maintenant=None, fenetre_secondes=10, limite=5):
    """Fonctionnalité 113 : détecte un burst de messages."""
    maintenant = maintenant or datetime.now().timestamp()
    recents = [timestamp for timestamp in timestamps if maintenant - float(timestamp) <= fenetre_secondes]
    return {"spam": len(recents) >= limite, "messages_recentes": len(recents)}
