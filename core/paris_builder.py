# core/paris_builder.py
from datetime import datetime, timezone, timedelta
from core.utils.logs import log_info, log_error, log_warning

TZ_KINSHASA = timezone(timedelta(hours=1))

NIVEAUX = {
    "sur": {"min": 0.75, "max": 1.0, "matchs": 3},
    "modere": {"min": 0.65, "max": 0.75, "matchs": 5},
    "risque": {"min": 0.60, "max": 0.65, "matchs": 7},
}

def _meilleure_reco(prono):
    try:
        dc_1x = float(prono.get("dc_1x", 0.5))
        dc_x2 = float(prono.get("dc_x2", 0.5))
        dc_12 = float(prono.get("dc_12", 0.5))
        options = [("1X", dc_1x), ("X2", dc_x2), ("12", dc_12)]
        return max(options, key=lambda x: x[1])
    except Exception as e:
        log_error("Erreur calcul meilleure reco", "PARIS", exception=e)
        return "1X", 0.5

def get_tous_pronostics_disponibles():
    from core.daily_matches import get_matchs_du_jour
    try:
        matchs = get_matchs_du_jour()
    except Exception as e:
        log_error("Impossible de récupérer les matchs du jour", "PARIS", exception=e)
        return []
    if not matchs: return []

    resultats = []
    for m in matchs:
        try:
            reco_label = m.get("dc_label", "1X")
            reco_pct = float(m.get("dc_pct", 0.5))
            if reco_pct <= 0 or round(1 / reco_pct, 2) < 1.30: continue

            resultats.append({
                "home": m.get("home"), "away": m.get("away"),
                "competition": m.get("competition"),
                "nom_competition": m.get("nom_competition", m.get("competition")),
                "heure": m.get("heure"), "reco_label": reco_label, "reco_pct": reco_pct,
                "btts": float(m.get("btts", 0.5)), "over_25": float(m.get("over_25", 0.5)),
                "analyse_pari": m.get("analyse_pari"),
                "p_h": float(m.get("p_h", 0.33)),
                "p_d": float(m.get("p_d", 0.33)),
                "p_a": float(m.get("p_a", 0.33)),
            })
        except Exception: continue
    return resultats

def construire_coupon(niveau, matchs_disponibles):
    if niveau not in NIVEAUX: return None
    seuil = NIVEAUX[niveau]
    candidats = [m for m in matchs_disponibles if seuil["min"] <= m["reco_pct"] < seuil["max"]]
    if len(candidats) < 3: candidats = [m for m in matchs_disponibles if m["reco_pct"] >= seuil["min"]]
    if len(candidats) < 3: return None

    candidats.sort(key=lambda x: x["reco_pct"], reverse=True)
    selection = candidats[:min(seuil["matchs"], len(candidats))]

    cote_totale, confiance = 1.0, 1.0
    for m in selection:
        if m["reco_pct"] > 0:
            cote_totale *= 1 / m["reco_pct"]
            confiance *= m["reco_pct"]

    return {"niveau": niveau, "matchs": selection, "cote_totale": round(cote_totale, 2), "confiance_cumulee": round(confiance, 4)}

def construire_coupon_outside(matchs_disponibles):
    candidats = [m for m in matchs_disponibles if 0.45 <= m["reco_pct"] <= 0.60]
    if len(candidats) < 3: return None
    candidats.sort(key=lambda x: x["reco_pct"], reverse=True)
    selection = candidats[: min(4, len(candidats))]

    cote_totale, confiance = 1.0, 1.0
    for m in selection:
        if m["reco_pct"] > 0:
            cote_totale *= 1 / m["reco_pct"]
            confiance *= m["reco_pct"]

    return {"niveau": "outside", "matchs": selection, "cote_totale": round(cote_totale, 2), "confiance_cumulee": round(confiance, 4)}

def generer_coupons_du_jour():
    est_weekend = datetime.now(TZ_KINSHASA).weekday() >= 5
    try: matchs = get_tous_pronostics_disponibles()
    except Exception: return {"weekend": est_weekend, "coupons": []}
    if not matchs: return {"weekend": est_weekend, "coupons": []}

    coupons = []
    if not est_weekend:
        for niveau in ("sur", "modere", "risque"):
            c = construire_coupon(niveau, matchs)
            if c: coupons.append(c)
    else:
        intervalles = [{"nom": "matin", "min_h": 8, "max_h": 14}, {"nom": "apres_midi", "min_h": 14, "max_h": 19}, {"nom": "soir", "min_h": 19, "max_h": 23}]
        for inter in intervalles:
            matchs_inter = []
            for m in matchs:
                if not m.get("heure"): continue
                try:
                    dt = datetime.fromisoformat(str(m["heure"]).replace("Z", "+00:00")).astimezone(TZ_KINSHASA)
                    if inter["min_h"] <= dt.hour < inter["max_h"]: matchs_inter.append(m)
                except Exception: continue
            if len(matchs_inter) < 3: continue
            for niveau in ("sur", "modere", "risque"):
                c = construire_coupon(niveau, matchs_inter)
                if c:
                    c["intervalle"] = inter["nom"]
                    coupons.append(c)

    c_out = construire_coupon_outside(matchs)
    if c_out: coupons.append(c_out)

    return {"weekend": est_weekend, "coupons": coupons}

def formater_coupon(coupon, langue="fr", montrer_details=True):
    niveau_labels = {"sur": "🔥 COUPON SUR", "modere": "⚖️ COUPON MODÉRÉ", "risque": "🎲 COUPON RISQUE", "outside": "💎 COUPON OUTSIDE"}
    intervalle_labels = {"matin": "🌅 Matin", "apres_midi": "☀️ Après-midi", "soir": "🌙 Soir"}

    titre = niveau_labels.get(coupon.get("niveau"), "COUPON")
    if coupon.get("intervalle"): titre += f" - {intervalle_labels.get(coupon['intervalle'], '')}"

    texte = f"{titre}\n━━━━━━━━━━━━━━━━━━━━\n\n"

    for i, m in enumerate(coupon.get("matchs", []), 1):
        texte += f"{i}. **{m['home']}** vs **{m['away']}**\n"
        if montrer_details:
            p_h, p_d, p_a = m.get('p_h', 0.33), m.get('p_d', 0.33), m.get('p_a', 0.33)
            texte += f"🏆 **Victoire {m['home']} :** {round(p_h*100)}%\n"
            texte += f"🤝 **Match Nul :** {round(p_d*100)}%\n"
            texte += f"✈️ **Victoire {m['away']} :** {round(p_a*100)}%\n"
            
            texte += f"🛡️ **Pari Sûr (Double Chance) :** {m['reco_label']} ({round(m['reco_pct'] * 100, 1)}%)\n"
            texte += f"🎯 **Les 2 marquent :** {round(m['btts'] * 100, 1)}% | 🥅 **Plus de 2.5 :** {round(m['over_25'] * 100, 1)}%\n"
            
            analyse = m.get("analyse_pari")
            if analyse and analyse.get("cote_book"):
                texte += f"💰 **Cote Bookmaker :** {analyse['cote_book']}\n"
                if analyse.get("is_value"):
                    texte += "🔥 **VALUE BET DÉTECTÉ !**\n"
        else:
            texte += f"🎯 Reco : {m['reco_label']}\n"
        texte += "\n"

    if montrer_details:
        texte += f"━━━━━━━━━━━━━━━━━━━━\n💰 **Cote totale :** {coupon.get('cote_totale', '?')}\n🎯 **Confiance :** {round(coupon.get('confiance_cumulee', 0) * 100, 1)}%\n"
    else:
        texte += "━━━━━━━━━━━━━━━━━━━━\n_Passe Premium pour les détails complets._\n"

    return texte
