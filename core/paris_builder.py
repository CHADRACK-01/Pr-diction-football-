# core/paris_builder.py
"""
Génération des coupons du jour et calculs avancés (Value Bet, Corners, Cartons, 1ère MT).
- Utilise les prédictions déjà calculées.
- Détecte les Value Bets (cote bookmaker > proba IA).
- Estime les probabilités pour la 1ère mi-temps.
- Affiche les conseils sous forme de phrases positives (Format HTML).
"""

from datetime import datetime, timezone, timedelta
from core.feature_flags import est_active
from core.utils.logs import log_info, log_error, log_warning

TZ_KINSHASA = timezone(timedelta(hours=1))

# Seuils de confiance pour les coupons
NIVEAUX = {
    "sur": {"min": 0.75, "max": 1.0, "matchs": 3},
    "modere": {"min": 0.65, "max": 0.75, "matchs": 5},
    "risque": {"min": 0.60, "max": 0.65, "matchs": 7},
}

def _meilleure_reco(prono):
    """Retourne (label, proba) de la meilleure recommandation 1N2."""
    try:
        dc_1x = float(prono.get("dc_1x", 0.5))
        dc_x2 = float(prono.get("dc_x2", 0.5))
        dc_12 = float(prono.get("dc_12", 0.5))
        options = [("1X", dc_1x), ("X2", dc_x2), ("12", dc_12)]
        return max(options, key=lambda x: x[1])
    except Exception as e:
        log_error("Erreur calcul meilleure reco", "PARIS", exception=e)
        return "1X", 0.5

def _traduire_pari(home, away, label_dc):
    """Traduit les codes 1X, X2, 12 en phrases positives."""
    if label_dc == "1X":
        return f"<b>{home}</b> va gagner ou faire match nul"
    elif label_dc == "X2":
        return f"<b>{away}</b> va gagner ou faire match nul"
    elif label_dc == "12":
        return "Un vainqueur sera désigné (pas de match nul)"
    return label_dc

def _calculer_value_bet(proba_ia, cote_book):
    """
    Fonctionnalité 2 : Détecteur de Value Bet.
    Calcule l'espérance mathématique.
    """
    if not cote_book or cote_book <= 1.0:
        return False
    # EV = (Probabilité * Cote) - 1
    ev = (proba_ia * cote_book) - 1
    return ev > 0.05  # On demande au moins 5% d'avantage

def calculer_proba_mi_temps(prono):
    """
    Fonctionnalité 413 : Estime les probabilités pour la 1ère mi-temps.
    Généralement, les équipes marquent moins en 1ère mi-temps (environ 40% des buts).
    """
    p_h = float(prono.get("p_h", 0.33))
    p_d = float(prono.get("p_d", 0.33))
    p_a = float(prono.get("p_a", 0.33))
    
    # Ajustement empirique : moins de buts en 1ère période
    p_h_mt = p_h * 0.80
    p_a_mt = p_a * 0.80
    p_d_mt = 1.0 - (p_h_mt + p_a_mt)  # Le reste va au match nul
    
    # Déterminer la meilleure option pour la MT
    options = [
        ("1X", p_h_mt + p_d_mt),
        ("X2", p_a_mt + p_d_mt),
        ("12", p_h_mt + p_a_mt)
    ]
    best_mt = max(options, key=lambda x: x[1])
    
    return {
        "p_h_mt": round(p_h_mt, 3),
        "p_d_mt": round(p_d_mt, 3),
        "p_a_mt": round(p_a_mt, 3),
        "label_mt": best_mt[0],
        "proba_mt": best_mt[1]
    }

def get_tous_pronostics_disponibles():
    """Récupère tous les pronostics calculés avec les options avancées."""
    from core.daily_matches import get_matchs_du_jour

    try:
        matchs = get_matchs_du_jour()
    except Exception as e:
        log_error("Impossible de récupérer les matchs du jour", "PARIS", exception=e)
        return []

    if not matchs:
        log_warning("Aucun match pour les coupons", "PARIS")
        return []

    resultats = []
    matchs_ignores = 0

    for m in matchs:
        try:
            reco_label, reco_pct = _meilleure_reco(m)
            
            cote = round(1 / reco_pct, 2) if reco_pct > 0 else 0
            if cote < 1.30:
                matchs_ignores += 1
                continue

            # --- Calcul des Value Bets (Fonctionnalité 2) ---
            cotes_book = m.get("cotes_book", {})
            is_value_bet = False
            if est_active("2") and cotes_book:
                if reco_label == "1X" and "h" in cotes_book and "d" in cotes_book:
                    cote_1x = (cotes_book["h"] * cotes_book["d"]) / (cotes_book["h"] + cotes_book["d"])
                    is_value_bet = _calculer_value_bet(reco_pct, cote_1x)
                elif reco_label == "X2" and "a" in cotes_book and "d" in cotes_book:
                    cote_x2 = (cotes_book["a"] * cotes_book["d"]) / (cotes_book["a"] + cotes_book["d"])
                    is_value_bet = _calculer_value_bet(reco_pct, cote_x2)
                elif reco_label == "12" and "h" in cotes_book and "a" in cotes_book:
                    cote_12 = (cotes_book["h"] * cotes_book["a"]) / (cotes_book["h"] + cotes_book["a"])
                    is_value_bet = _calculer_value_bet(reco_pct, cote_12)

            # --- Corners et Cartons (Fonctionnalité 9) ---
            corners_pct = 0.5
            cartons_pct = 0.5
            if est_active("9"):
                corners_pct = float(m.get("over_95_corners", 0.5))
                cartons_pct = float(m.get("over_35_cartons", 0.5))

            resultats.append({
                "home": m.get("home"),
                "away": m.get("away"),
                "competition": m.get("competition"),
                "nom_competition": m.get("nom_competition", m.get("competition")),
                "heure": m.get("heure"),
                "reco_label": reco_label,
                "reco_pct": reco_pct,
                "is_value_bet": is_value_bet,
                "cotes_book": cotes_book,
                "corners_pct": corners_pct,
                "cartons_pct": cartons_pct,
                "p_h": float(m.get("p_h", 0.33)),
                "p_d": float(m.get("p_d", 0.33)),
                "p_a": float(m.get("p_a", 0.33)),
            })
        except Exception as e:
            log_error("Erreur traitement match pour coupons", "PARIS", exception=e)
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
        log_warning(f"Niveau inconnu : {niveau}", "PARIS")
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
        log_error("Erreur génération coupons", "PARIS", exception=e)
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
                log_error(f"Erreur construction coupon '{niveau}'", "PARIS", exception=e)
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
                    log_error(f"Erreur coupon {niveau}/{inter['nom']}", "PARIS", exception=e)

    try:
        coupon_outside = construire_coupon_outside(matchs)
        if coupon_outside:
            coupons.append(coupon_outside)
    except Exception as e:
        log_error("Erreur coupon outside", "PARIS", exception=e)

    log_info(
        f"{len(coupons)} coupons générés",
        module="PARIS",
        extra={"weekend": est_weekend, "coupons": len(coupons)},
    )
    return {"weekend": est_weekend, "coupons": coupons}

def formater_coupon(coupon, langue="fr", montrer_details=True):
    """Formate un coupon pour Telegram avec le ton du Coach Personnel (HTML)."""
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

    texte = f"<b>{titre}</b>\n━━━━━━━━━━━━━━━━━━━━\n\n"

    for i, m in enumerate(coupon.get("matchs", []), 1):
        phrase = _traduire_pari(m['home'], m['away'], m['reco_label'])
        
        texte += f"{i}. <b>{m['home']} vs {m['away']}</b>\n"
        
        if montrer_details:
            texte += f"   👉 Mon conseil : {phrase}\n"
            texte += f"   📊 (Fiabilité : {round(m['reco_pct'] * 100, 1)}%)\n"
            
            # Affichage du Value Bet (Fonctionnalité 2)
            if m.get("is_value_bet") and est_active("2"):
                texte += f"   💰 <b>Value Bet Détecté !</b>\n"

            # Affichage Corners/Cartons (Fonctionnalité 9)
            if est_active("9"):
                texte += f"   🚩 Corners > 9.5 : {round(m['corners_pct']*100, 1)}%\n"
                texte += f"   🟨 Cartons > 3.5 : {round(m['cartons_pct']*100, 1)}%\n"

            # Affichage 1ère Mi-Temps (Fonctionnalité 413)
            if est_active("413"):
                mt = calculer_proba_mi_temps(m)
                texte += f"   ⏱️ 1ère MT ({mt['label_mt']}) : {round(mt['proba_mt']*100, 1)}%\n"
        else:
            texte += f"   👉 Mon conseil : {phrase}\n"
        
        texte += "\n"

    if montrer_details:
        texte += (
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🎯 <b>Fiabilité globale du coupon :</b> {round(coupon.get('confiance_cumulee', 0) * 100, 1)}%\n"
        )
    else:
        texte += (
            "━━━━━━━━━━━━━━━━━━━━\n"
            "⭐ <i>Passe Premium pour voir les conseils détaillés et les cotes.</i>\n"
        )

    return texte
