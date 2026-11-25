"""Moteurs locaux pour les fonctionnalités 138 à 700.

Calculs déterministes sans fournisseur externe ni secret.
"""

from datetime import datetime
import hashlib
import math
import random


def test_ab(user_id, ratio_b=0.5):
    if not 0 <= ratio_b <= 1:
        raise ValueError("ratio_b doit être compris entre 0 et 1")
    valeur = int(hashlib.sha256(str(user_id).encode()).hexdigest()[:8], 16) / 0xFFFFFFFF
    return "B" if valeur < ratio_b else "A"


def convertir_prix(montant, taux_usd=None, taux_eur=None):
    montants = {"CDF": montant}
    if taux_usd:
        montants["USD"] = round(montant / taux_usd, 4)
    if taux_eur:
        montants["EUR"] = round(montant / taux_eur, 4)
    return montants


def calculer_marge_nette(brut, frais_fixe=0, frais_pourcent=0):
    net = max(0, brut - frais_fixe - brut * max(0, frais_pourcent) / 100)
    return {"brut": brut, "frais": round(brut - net, 2), "net": round(net, 2)}


def evaluer_seuil_rentabilite(revenus_mensuels, cout_mensuel):
    marge = revenus_mensuels - cout_mensuel
    return {"rentable": marge >= 0, "marge_mensuelle": round(marge, 2)}


def analyser_cohorte(utilisateurs, statut="actif"):
    actifs = 0
    total = 0
    for utilisateur in utilisateurs:
        if not utilisateur.get("date_inscription"):
            continue
        try:
            datetime.fromisoformat(str(utilisateur["date_inscription"]).replace("Z", "+00:00"))
        except (TypeError, ValueError):
            continue
        actifs += utilisateur.get("status") == statut
        total += 1
    taux = round(actifs / total * 100, 2) if total else 0
    return {"total": total, "actifs": actifs, "taux_retention": taux}


def heure_pointe_evenements(evenements):
    compte = {}
    for evenement in evenements:
        try:
            heure = datetime.fromisoformat(str(evenement).replace("Z", "+00:00").replace(" ", "T")).hour
        except (TypeError, ValueError):
            continue
        compte[heure] = compte.get(heure, 0) + 1
    return sorted(compte.items(), key=lambda item: (-item[1], item[0]))


def score_brier(probabilites, resultats):
    if len(probabilites) != len(resultats) or not probabilites:
        raise ValueError("Probabilités et résultats doivent avoir la même taille non nulle")
    valeur = sum((float(p) - float(r)) ** 2 for p, r in zip(probabilites, resultats))
    return round(valeur / len(probabilites), 6)


def log_loss(probabilites, resultats, epsilon=1e-15):
    if len(probabilites) != len(resultats) or not probabilites:
        raise ValueError("Probabilités et résultats doivent avoir la même taille non nulle")
    valeur = 0.0
    for p, r in zip(probabilites, resultats):
        p = min(1 - epsilon, max(epsilon, float(p)))
        y = 1 if float(r) >= 0.5 else 0
        valeur -= y * math.log(p) + (1 - y) * math.log(1 - p)
    return round(valeur / len(probabilites), 6)


def detecter_doublons_matchs(matchs):
    vues = set()
    doublons = []
    uniques = []
    for match in matchs:
        norm = lambda value: " ".join(str(value or "").strip().lower().split())
        cle = (match.get("date", ""), norm(match.get("home")), norm(match.get("away")), norm(match.get("competition")))
        if cle in vues:
            doublons.append(match)
        else:
            vues.add(cle)
            uniques.append(match)
    return {"uniques": uniques, "doublons": doublons}


def fraicheur_donnees(dates, maximum_minutes=30, maintenant=None):
    maintenant = maintenant or datetime.now()
    ages = []
    for date_brute in dates:
        try:
            date = datetime.fromisoformat(str(date_brute).replace("Z", "+00:00"))
            if date.tzinfo:
                date = date.replace(tzinfo=None)
        except (TypeError, ValueError):
            continue
        ages.append(max(0, (maintenant - date).total_seconds() / 60))
    if not ages:
        return {"fraiche": False, "age_max_minutes": None}
    age_max = max(ages)
    return {"fraiche": age_max <= maximum_minutes, "age_max_minutes": round(age_max, 2)}


def generer_corpus_regression(predictions, graine=42):
    corpus = sorted(predictions, key=lambda item: str(item))
    empreinte = hashlib.sha256(str(corpus).encode()).hexdigest()
    rng = random.Random(graine)
    rng.shuffle(corpus)
    return {"empreinte": empreinte, "nb_cas": len(corpus), "cas": corpus}
