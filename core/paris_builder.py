from datetime import datetime, timezone, timedelta

from core.ml_model import global_model_data
from core.prediction import predire_match


TZ_KINSHASA = timezone(timedelta(hours=1))

NIVEAUX = {
    "sur": {"min": 0.75, "max": 1.0, "matchs": 3},
    "modere": {"min": 0.65, "max": 0.75, "matchs": 5},
    "risque": {"min": 0.60, "max": 0.65, "matchs": 7},
}


def _meilleure_reco(prono):
    dc_1x = float(prono['dc_1x'])
    dc_x2 = float(prono['dc_x2'])
    dc_12 = float(prono['dc_12'])

    options = [("1X", dc_1x), ("X2", dc_x2), ("12", dc_12)]
    meilleure = max(options, key=lambda x: x[1])
    return meilleure[0], meilleure[1]


def get_tous_pronostics_disponibles():
    from core.daily_matches import get_matchs_du_jour
    matchs = get_matchs_du_jour()
    resultats = []

    for m in matchs:
        home = m['home']
        away = m['away']
        try:
            prono = predire_match(home, away)
            if not isinstance(prono, dict) or 'erreur' in prono:
                continue

            reco_label, reco_pct = _meilleure_reco(prono)
            cote = round(1 / reco_pct, 2) if reco_pct > 0 else 999

            if cote < 1.30:
                continue

            resultats.append({
                'home': home, 'away': away, 'competition': m['competition'],
                'heure': m['heure'], 'reco_label': reco_label,
                'reco_pct': float(reco_pct), 'score_exact': prono.get('best_score', (0, 0)),
                'top_scores': prono.get('top_scores', []),
                'over_25': float(prono.get('over_25', 0.5)),
                'btts_yes': float(prono.get('btts_yes', 0.5)),
            })
        except Exception:
            continue
    return resultats


def construire_coupon(niveau, matchs_disponibles):
    seuil = NIVEAUX[niveau]
    candidats = [m for m in matchs_disponibles if seuil['min'] <= m['reco_pct'] < seuil['max']]

    if len(candidats) < 3:
        candidats = [m for m in matchs_disponibles if m['reco_pct'] >= seuil['min']]

    if len(candidats) < 3:
        return None

    candidats.sort(key=lambda x: x['reco_pct'], reverse=True)
    nb_matchs = min(seuil['matchs'], len(candidats))
    selection = candidats[:nb_matchs]

    cote_totale = 1.0
    confiance_cumulee = 1.0
    for m in selection:
        if m['reco_pct'] > 0:
            cote_totale *= (1 / m['reco_pct'])
            confiance_cumulee *= m['reco_pct']

    return {
        'niveau': niveau, 'matchs': selection,
        'cote_totale': round(cote_totale, 2),
        'confiance_cumulee': round(confiance_cumulee, 4),
    }


def construire_coupon_outside(matchs_disponibles):
    """
    Construit un coupon Outside avec des matchs ayant une cote entre 1.65 et 2.20.
    (Probabilité entre 45% et 60%, pour avoir plus d'options)
    """
    candidats = [m for m in matchs_disponibles if 0.45 <= m['reco_pct'] <= 0.60]
    
    if len(candidats) < 3:
        return None
    
    candidats.sort(key=lambda x: x['reco_pct'], reverse=True)
    nb_matchs = min(len(candidats), 4) # On prend 4 matchs pour une cote totale plus sympa
    selection = candidats[:nb_matchs]
    
    cote_totale = 1.0
    confiance_cumulee = 1.0
    for m in selection:
        cote_totale *= (1 / m['reco_pct'])
        confiance_cumulee *= m['reco_pct']
    
    return {
        'niveau': 'outside',
        'matchs': selection,
        'cote_totale': round(cote_totale, 2),
        'confiance_cumulee': round(confiance_cumulee, 4),
    }


def generer_coupons_du_jour():
    maintenant = datetime.now(TZ_KINSHASA)
    est_weekend = maintenant.weekday() >= 5
    matchs = get_tous_pronostics_disponibles()

    if not matchs:
        return {'weekend': est_weekend, 'coupons': []}

    coupons = []

    if not est_weekend:
        for niveau in ['sur', 'modere', 'risque']:
            coupon = construire_coupon(niveau, matchs)
            if coupon:
                coupons.append(coupon)
    else:
        intervalles = [
            {"nom": "matin", "min_h": 8, "max_h": 14},
            {"nom": "apres_midi", "min_h": 14, "max_h": 19},
            {"nom": "soir", "min_h": 19, "max_h": 23},
        ]
        for inter in intervalles:
            matchs_inter = []
            for m in matchs:
                try:
                    dt = datetime.fromisoformat(m['heure'].replace("Z", "+00:00")).astimezone(TZ_KINSHASA)
                    if inter['min_h'] <= dt.hour < inter['max_h']:
                        matchs_inter.append(m)
                except Exception: continue

            if len(matchs_inter) < 3: continue

            for niveau in ['sur', 'modere', 'risque']:
                coupon = construire_coupon(niveau, matchs_inter)
                if coupon:
                    coupon['intervalle'] = inter['nom']
                    coupons.append(coupon)

    # Coupon Outside (tous les jours)
    coupon_outside = construire_coupon_outside(matchs)
    if coupon_outside:
        coupons.append(coupon_outside)

    return {'weekend': est_weekend, 'coupons': coupons}


def formater_coupon(coupon, langue="fr", montrer_details=True):
    niveau_labels = {
        "sur": "🔥 COUPON SUR", "modere": "⚖️ COUPON MODÉRÉ",
        "risque": "🎲 COUPON RISQUE", "outside": "💎 COUPON OUTSIDE (Value)",
    }
    intervalle_labels = {"matin": "🌅 Matin", "apres_midi": "☀️ Apres-midi", "soir": "🌙 Soir"}

    titre = niveau_labels.get(coupon['niveau'], "COUPON")
    if coupon.get('intervalle'):
        titre += f" - {intervalle_labels.get(coupon['intervalle'], '')}"

    texte = f"{titre}\n━━━━━━━━━━━━━━━━━━━━\n\n"

    for i, m in enumerate(coupon['matchs'], 1):
        texte += f"{i}. {m['home']} vs {m['away']}\n"
        if montrer_details:
            texte += f"   🎯 Reco : {m['reco_label']}\n"
            texte += f"   📊 Confiance : {round(m['reco_pct']*100, 1)}%\n"
            if m.get('score_exact'):
                texte += f"   ⚽ Score : {m['score_exact'][0]}-{m['score_exact'][1]}\n"
        else:
            texte += f"   🎯 Reco : {m['reco_label']}\n"
        texte += "\n"

    if montrer_details:
        texte += f"━━━━━━━━━━━━━━━━━━━━\n💰 Cote totale : {coupon['cote_totale']}\n🎯 Confiance cumulee : {round(coupon['confiance_cumulee']*100, 1)}%\n"
    else:
        texte += "━━━━━━━━━━━━━━━━━━━━\n_Passe Premium pour les details et les autres coupons_\n"

    return texte,
