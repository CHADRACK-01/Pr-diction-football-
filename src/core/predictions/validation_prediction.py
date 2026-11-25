"""Garde-fous métier centraux pour toute sortie prédictive ou commerciale."""

import math


def valider_probabilites(probabilites):
    """Valide 1N2 : valeurs finies, plage 0-1 et somme normalisée."""
    if not isinstance(probabilites, dict):
        raise ValueError("Probabilités attendues sous forme de dictionnaire")
    requis = {"p_h", "p_d", "p_a"}
    manquants = requis - set(probabilites)
    if manquants:
        raise ValueError(f"Probabilités manquantes : {sorted(manquants)}")

    valeurs = []
    for cle in ("p_h", "p_d", "p_a"):
        try:
            valeur = float(probabilites[cle])
        except (TypeError, ValueError):
            raise ValueError(f"Probabilité invalide : {cle}")
        if not math.isfinite(valeur) or valeur < 0 or valeur > 1:
            raise ValueError(f"Probabilité hors bornes : {cle}")
        valeurs.append(valeur)

    total = sum(valeurs)
    if not math.isclose(total, 1.0, rel_tol=0.0, abs_tol=0.02):
        raise ValueError(f"Somme des probabilités invalide : {total:.6f}")
    return tuple(valeurs)


def avertissement_responsable():
    return "Analyse statistique, pas une garantie de gain. Ne mise que le montant que tu peux te permettre de perdre."


def construire_libelle_prediction(probabilites):
    p_h, p_d, p_a = valider_probabilites(probabilites)
    valeurs = (("Domicile", p_h), ("Nul", p_d), ("Extérieur", p_a))
    libelle, prob = max(valeurs, key=lambda item: item[1])
    return {"libelle": libelle, "probabilite": round(prob, 6), "incertitude": round(1 - prob, 6)}


def valider_mise(montant, bankroll, mise_max_pourcent=5.0):
    montant = float(montant)
    bankroll = float(bankroll)
    if not math.isfinite(montant) or montant < 0:
        raise ValueError("Mise invalide")
    if not math.isfinite(bankroll) or bankroll < 0:
        raise ValueError("Bankroll invalide")
    plafond = bankroll * mise_max_pourcent / 100
    autorisee = montant <= plafond
    return {"autorisee": autorisee, "plafond": round(plafond, 2), "montant": round(montant, 2)}
