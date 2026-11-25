# core/backtest.py
"""
Backtest chronologique : que vaudrait la stratégie sur l'historique ?

Entrées : une liste de matchs déjà joués, dans l'ordre chronologique, avec :
  - p : probabilités du modèle (p_h, p_d, p_a) calculées AVANT le match ;
  - cotes : cotes de clôture (cote_h, cote_d, cote_a) ;
  - issue : "H", "D" ou "A".

Mise fixe de 1 unité. Une seule règle : parier sur l'issue dont l'avantage
(p × cote − 1) dépasse un seuil. Le résultat est donné avec le nombre de paris :
un ROI sur peu de paris ne prouve rien.
"""
import math

ISSUES = ("H", "D", "A")


def _cotes_valides(c):
    try:
        return all(float(x) > 1.0 for x in c)
    except (TypeError, ValueError):
        return False


def backtest(matchs, seuil_avantage=0.05):
    """Retourne un dict de résultats. `matchs` : liste de dicts {p, cotes, issue}."""
    paris = 0
    gagnants = 0
    mise_totale = 0.0
    gain_total = 0.0
    matchs_utiles = 0
    brier_modele = 0.0
    brier_marche = 0.0

    for m in matchs:
        p, cotes, issue = m.get("p"), m.get("cotes"), m.get("issue")
        if issue not in ISSUES or not p or not cotes or not _cotes_valides(cotes):
            continue
        matchs_utiles += 1
        somme_inv = sum(1 / float(c) for c in cotes)
        marche = [ (1 / float(c)) / somme_inv for c in cotes ]
        onehot = [1.0 if k == issue else 0.0 for k in ISSUES]
        brier_modele += sum((p[i] - onehot[i]) ** 2 for i in range(3))
        brier_marche += sum((marche[i] - onehot[i]) ** 2 for i in range(3))

        avantages = [p[i] * float(cotes[i]) - 1.0 for i in range(3)]
        i_best = max(range(3), key=lambda i: avantages[i])
        if avantages[i_best] <= seuil_avantage:
            continue
        paris += 1
        mise_totale += 1.0
        if ISSUES[i_best] == issue:
            gagnants += 1
            gain_total += float(cotes[i_best])

    roi = (gain_total - mise_totale) / mise_totale if mise_totale else None
    return {
        "matchs_utiles": matchs_utiles,
        "paris": paris,
        "gagnants": gagnants,
        "taux_reussite": (gagnants / paris) if paris else None,
        "roi": roi,
        "brier_modele": (brier_modele / matchs_utiles) if matchs_utiles else None,
        "brier_marche": (brier_marche / matchs_utiles) if matchs_utiles else None,
        "seuil": seuil_avantage,
        "fiable": paris >= 300,
    }


def lire(res):
    """Texte honnête à présenter (jamais un ROI sans son effectif)."""
    if res["paris"] == 0:
        return "Aucun pari retenu par la règle : rien à conclure."
    lignes = [
        f"Paris : {res['paris']} sur {res['matchs_utiles']} matchs",
        f"Taux de réussite : {res['taux_reussite'] * 100:.1f} %",
        f"ROI : {res['roi'] * 100:+.1f} % (mise fixe)",
    ]
    if res["brier_modele"] is not None:
        lignes.append(f"Brier modèle {res['brier_modele']:.4f} · marché {res['brier_marche']:.4f} (plus bas = mieux)")
    if not res["fiable"]:
        lignes.append("⚠️ Moins de 300 paris : résultat trop incertain pour conclure.")
    return "\n".join(lignes)
