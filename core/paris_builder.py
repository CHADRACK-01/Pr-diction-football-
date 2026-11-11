# core/paris_builder.py
"""
Génération des coupons du jour.
- Utilise les prédictions déjà calculées (pas de recalcul)
- Logs enrichis
"""

from datetime import datetime, timezone, timedelta

from core.utils.logs import log_info, log_error, log_warning

TZ_KINSHASA = timezone(timedelta(hours=1))

NIVEAUX = {
    "sur": {"min": 0.75, "max": 1.0, "matchs": 3},
    "modere": {"min": 0.65, "max": 0.75, "matchs": 5},
    "risque": {"min": 0.60, "max": 0.65, "matchs": 7},
}


def _meilleure_reco(prono):
    """Retourne (label, proba)."""
    try:
        dc_1x = float(prono.get("dc_1x", 0.5))
        dc_x2 = float(prono.get("dc_x2", 0.5))
        dc_12 = float(prono.get("dc_12", 0.5))
        options = [("1X", dc_1x), ("X2", dc_x2), ("12", dc_12)]
        return max(options, key=lambda x: x[1])
    except Exception as e:
        log_error(
            message="Erreur calcul meilleure reco",
            module="PARIS",
            exception=e,
        )
        return "1X", 0.5


def get_tous_pronostics_disponibles():
    """Récupère tous les pronostics calculés."""
    from core.daily_matches import get_matchs_du_jour

    try:
        matchs = get_matchs_du_jour()
    except Exception as e:
        log_error(
            message="Impossible de récupérer les matchs du jour",
            module="PARIS",
            exception=e,
        )
        return []

    if not matchs:
        log_warning(message="Aucun match pour les coupons", module="PARIS")
        return []

    resultats = []
    matchs_ignores = 0

    for m in matchs:
        try:
            reco_label = m.get("dc_label", "1X")
            reco_pct = float(m.get("dc_pct", 0.5))

            if reco_pct <= 0:
                matchs_ignores += 1
                continue

            cote = round(1 / reco_pct, 2)
            if cote < 1.30:
                matchs_ignores += 1
                continue

            resultats.append({
                "home": m.get("home"),
                "away": m.get("away"),
                "competition": m.get("competition"),
                "nom_competition": m.get("nom_competition", m.get("competition")),
                "heure": m.get("heure"),
                "reco_label": reco_label,
                "reco_pct": reco_pct,
                "btts": float(m.get("btts", 0.5)),
                "over_25": float(m.get("over_25", 0.5)),
                "analyse_pari": m.get("analyse_pari"),
            })
        except Exception as e:
            log_error(
                message="Erreur traitement match pour coupons",
                module="PARIS",
                exception=e,
            )
            matchs_ignores += 1
            continue

    log_info(
        f"{len(resultats)} pronostics pour coupons ({matchs_ignores} ignorés)",
        module="PARIS",
        extra={"retenus": len(resultats), "ignores": matchs_ignores},
    )
    return resultats


def construire_coupon(niveau, matchs_disponibles):
    """Construit un coupon pour un niveau donné."""
    if niveau not in NIVEAUX:
        log_warning(
            message=f"Niveau inconnu : {niveau}",
            module="PARIS",
            extra={"niveau": niveau},
        )
        return None

    seuil = NIVEAUX[niveau]
    candidats = [
        m for m in matchs_disponibles
        if seuil["min"] <= m["reco_pct"] < seuil["max"]
    ]

    if len(candidats) < 3:
        candidats = [m for m in matchs_disponibles if m["reco_pct"] >= seuil["min"]]
    if len(candidats) < 3:
        return None

    candidats.sort(key=lambda x: x["reco_pct"], reverse=True)
    nb = min(seuil["matchs"], len(candidats))
    selection = candidats[:nb]

    cote_totale = 1.0
    confiance = 1.0
    for m in selection:
        if m["reco_pct"] > 0:
            cote_totale *= 1 / m["reco_pct"]
            confiance *= m["reco_pct"]

    return {
        "niveau": niveau,
        "matchs": selection,
        "cote_totale": round(cote_totale, 2),
        "confiance_cumulee": round(confiance, 4),
    }


def construire_coupon_outside(matchs_disponibles):
    """Coupon Outside (value, proba plus faible)."""
    candidats = [m for m in matchs_disponibles if 0.45 <= m["reco_pct"] <= 0.60]
    if len(candidats) < 3:
        return None

    candidats.sort(key=lambda x: x["reco_pct"], reverse=True)
    selection = candidats[: min(4, len(candidats))]

    cote_totale = 1.0
    confiance = 1.0
    for m in selection:
        if m["reco_pct"] > 0:
            cote_totale *= 1 / m["reco_pct"]
            confiance *= m["reco_pct"]

    return {
        "niveau": "outside",
        "matchs": selection,
        "cote_totale": round(cote_totale, 2),
        "confiance_cumulee": round(confiance, 4),
    }


def generer_coupons_du_jour():
    """Génère tous les coupons du jour."""
    maintenant = datetime.now(TZ_KINSHASA)
    est_weekend = maintenant.weekday() >= 5

    try:
        matchs = get_tous_pronostics_disponibles()
    except Exception as e:
        log_error(
            message="Erreur génération coupons",
            module="PARIS",
            exception=e,
        )
        return {"weekend": est_weekend, "coupons": []}

    if not matchs:
        return {"weekend": est_weekend, "coupons": []}

    coupons = []

    if not est_weekend:
        for niveau in ("sur", "modere", "risque"):
            try:
                coupon = construire_coupon(niveau, matchs)
                if coupon:
                    coupons.append(coupon)
            except Exception as e:
                log_error(
                    message=f"Erreur construction coupon '{niveau}'",
                    module="PARIS",
                    exception=e,
                )
    else:
        intervalles = [
            {"nom": "matin", "min_h": 8, "max_h": 14},
            {"nom": "apres_midi", "min_h": 14, "max_h": 19},
            {"nom": "soir", "min_h": 19, "max_h": 23},
        ]
        for inter in intervalles:
            matchs_inter = []
            for m in matchs:
                if not m.get("heure"):
                    continue
                try:
                    dt = datetime.fromisoformat(
                        str(m["heure"]).replace("Z", "+00:00")
                    ).astimezone(TZ_KINSHASA)
                    if inter["min_h"] <= dt.hour < inter["max_h"]:
                        matchs_inter.append(m)
                except Exception:
                    continue

            if len(matchs_inter) < 3:
                continue

            for niveau in ("sur", "modere", "risque"):
                try:
                    coupon = construire_coupon(niveau, matchs_inter)
                    if coupon:
                        coupon["intervalle"] = inter["nom"]
                        coupons.append(coupon)
                except Exception as e:
                    log_error(
                        message=f"Erreur coupon {niveau}/{inter['nom']}",
                        module="PARIS",
                        exception=e,
                    )

    try:
        coupon_outside = construire_coupon_outside(matchs)
        if coupon_outside:
            coupons.append(coupon_outside)
    except Exception as e:
        log_error(
            message="Erreur coupon outside",
            module="PARIS",
            exception=e,
        )

    log_info(
        f"{len(coupons)} coupons générés",
        module="PARIS",
        extra={"weekend": est_weekend, "coupons": len(coupons)},
    )
    return {"weekend": est_weekend, "coupons": coupons}


def formater_coupon(coupon, langue="fr", montrer_details=True):
    """Formate un coupon pour Telegram."""
    niveau_labels = {
        "sur": "🔥 COUPON SUR",
        "modere": "⚖️ COUPON MODÉRÉ",
        "risque": "🎲 COUPON RISQUE",
        "outside": "💎 COUPON OUTSIDE (Value)",
    }
    intervalle_labels = {"matin": "🌅 Matin", "apres_midi": "☀️ Après-midi", "soir": "🌙 Soir"}

    titre = niveau_labels.get(coupon.get("niveau"), "COUPON")
    if coupon.get("intervalle"):
        titre += f" - {intervalle_labels.get(coupon['intervalle'], '')}"

    texte = f"{titre}\n━━━━━━━━━━━━━━━━━━━━\n\n"

    for i, m in enumerate(coupon.get("matchs", []), 1):
        texte += f"{i}. {m['home']} vs {m['away']}\n"
        if montrer_details:
            texte += f"   🎯 Reco : {m['reco_label']} ({round(m['reco_pct'] * 100, 1)}%)\n"
            texte += (
                f"   🎯 BTTS : {round(m['btts'] * 100, 1)}% | "
                f"🥅 Over 2.5 : {round(m['over_25'] * 100, 1)}%\n"
            )
            analyse = m.get("analyse_pari")
            if analyse and analyse.get("cote_book"):
                texte += f"   🏢 Cote Book : {analyse['cote_book']}\n"
                if analyse.get("is_value"):
                    texte += "   🔥 VALUE BET !\n"
        else:
            texte += f"   🎯 Reco : {m['reco_label']}\n"
        texte += "\n"

    if montrer_details:
        texte += (
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"💰 Cote totale : {coupon.get('cote_totale', '?')}\n"
            f"🎯 Confiance : {round(coupon.get('confiance_cumulee', 0) * 100, 1)}%\n"
        )
    else:
        texte += (
            "━━━━━━━━━━━━━━━━━━━━\n"
            "_Passe Premium pour les détails et les autres coupons_\n"
        )

    return texte
