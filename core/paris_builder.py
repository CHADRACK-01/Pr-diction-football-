from datetime import datetime, timezone, timedelta
from core.ml_model import global_model_data
from core.prediction import predire_match
from core.utils.logs import log_info

TZ_KINSHASA = timezone(timedelta(hours=1))

NIVEAUX = {
    "sur": {"min": 0.75, "max": 1.0, "matchs": 3},
    "modere": {"min": 0.65, "max": 0.75, "matchs": 5},
    "risque": {"min": 0.60, "max": 0.65, "matchs": 7},
}


def _meilleure_reco(prono):
    """Renvoie la meilleure recommandation (1X, X2, ou 12) et sa probabilité."""
    dc_1x = float(prono.get('dc_1x', 0.5))
    dc_x2 = float(prono.get('dc_x2', 0.5))
    dc_12 = float(prono.get('dc_12', 0.5))

    options = [("1X", dc_1x), ("X2", dc_x2), ("12", dc_12)]
    meilleure = max(options, key=lambda x: x[1])
    return meilleure[0], meilleure[1]


def get_tous_pronostics_disponibles():
    """Récupère tous les pronostics disponibles pour les matchs du jour."""
    from core.daily_matches import get_matchs_du_jour
    from config import MAPPING_COMPETITIONS
    
    matchs = get_matchs_du_jour()
    resultats = []

    for m in matchs:
        home = m['home']
        away = m['away']
        
        # ⚠️ On récupère le nom propre de la compétition
        competition_reelle = MAPPING_COMPETITIONS.get(m['competition'], m['competition'])
        
        prono = predire_match(home, away, competition=competition_reelle, cotes_book=m.get('cotes_book'))
        
        if not isinstance(prono, dict) or 'erreur' in prono:
            continue

        reco_label, reco_pct = _meilleure_reco(prono)
        cote = round(1 / reco_pct, 2) if reco_pct > 0 else 999

        if cote < 1.30:
            continue

        resultats.append({
            'home': home, 'away': away, 'competition': m['competition'],
            'nom_competition': m.get('nom_competition', m['competition']),
            'heure': m['heure'], 
            'reco_label': reco_label,
            'reco_pct': float(reco_pct),
            'btts': float(prono.get('btts_yes', 0.5)),
            'over_25': float(prono.get('over_25', 0.5)),
            'analyse_pari': prono.get('analyse_pari'),
        })
    return resultats


def construire_coupon(niveau, matchs_disponibles):
    """Construit un coupon pour un niveau donné (sur, modéré, risque)."""
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
    """Construit un coupon 'Outside' (Value) avec des probabilités plus faibles."""
    candidats = [m for m in matchs_disponibles if 0.45 <= m['reco_pct'] <= 0.60]
    if len(candidats) < 3:
        return None
    
    candidats.sort(key=lambda x: x['reco_pct'], reverse=True)
    nb_matchs = min(len(candidats), 4)
    selection = candidats[:nb_matchs]
    
    cote_totale = 1.0
    confiance_cumulee = 1.0
    for m in selection:
        cote_totale *= (1 / m['reco_pct'])
        confiance_cumulee *= m['reco_pct']
    
    return {
        'niveau': 'outside', 'matchs': selection,
        'cote_totale': round(cote_totale, 2),
        'confiance_cumulee': round(confiance_cumulee, 4),
    }


def generer_coupons_du_jour():
    """Génère tous les coupons du jour (sur, modéré, risque, outside)."""
    maintenant = datetime.now(TZ_KINSHASA)
    est_weekend = maintenant.weekday() >= 5
    matchs = get_tous_pronostics_disponibles()

    if not matchs:
        return {'weekend': est_weekend, 'coupons': []}

    coupons = []

    if not est_weekend:
        # En semaine : un coupon par niveau
        for niveau in ['sur', 'modere', 'risque']:
            coupon = construire_coupon(niveau, matchs)
            if coupon:
                coupons.append(coupon)
    else:
        # Le week-end : on découpe par intervalle horaire
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
                except:
                    continue

            if len(matchs_inter) < 3: 
                continue

            for niveau in ['sur', 'modere', 'risque']:
                coupon = construire_coupon(niveau, matchs_inter)
                if coupon:
                    coupon['intervalle'] = inter['nom']
                    coupons.append(coupon)

    # On ajoute toujours le coupon Outside
    coupon_outside = construire_coupon_outside(matchs)
    if coupon_outside:
        coupons.append(coupon_outside)

    return {'weekend': est_weekend, 'coupons': coupons}


def formater_coupon(coupon, langue="fr", montrer_details=True):
    """Formate un coupon pour l'affichage Telegram."""
    niveau_labels = {
        "sur": "🔥 COUPON SUR",
        "modere": "⚖️ COUPON MODÉRÉ",
        "risque": "🎲 COUPON RISQUE",
        "outside": "💎 COUPON OUTSIDE (Value)",
    }
    intervalle_labels = {"matin": "🌅 Matin", "apres_midi": "☀️ Apres-midi", "soir": "🌙 Soir"}

    titre = niveau_labels.get(coupon['niveau'], "COUPON")
    if coupon.get('intervalle'):
        titre += f" - {intervalle_labels.get(coupon['intervalle'], '')}"

    texte = f"{titre}\n━━━━━━━━━━━━━━━━━━━━\n\n"

    for i, m in enumerate(coupon['matchs'], 1):
        texte += f"{i}. {m['home']} vs {m['away']}\n"
        if montrer_details:
            texte += f"   🎯 Reco : {m['reco_label']} ({round(m['reco_pct']*100, 1)}%)\n"
            texte += f"   🎯 BTTS : {round(m['btts']*100, 1)}% | 🥅 Over 2.5 : {round(m['over_25']*100, 1)}%\n"
            
            analyse = m.get('analyse_pari')
            if analyse and analyse.get('cote_book'):
                texte += f"   🏢 Cote Book : {analyse['cote_book']}\n"
                if analyse.get('is_value'):
                    texte += f"   🔥 VALUE BET !\n"
        else:
            texte += f"   🎯 Reco : {m['reco_label']}\n"
        texte += "\n"

    if montrer_details:
        texte += f"━━━━━━━━━━━━━━━━━━━━\n💰 Cote totale : {coupon['cote_totale']}\n🎯 Confiance cumulee : {round(coupon['confiance_cumulee']*100, 1)}%\n"
    else:
        texte += "━━━━━━━━━━━━━━━━━━━━\n_Passe Premium pour les details et les autres coupons_\n"

    return texte
