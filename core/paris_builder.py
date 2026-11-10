from datetime import datetime, timezone, timedelta
from core.ml_model import global_model_data
from core.prediction import predire_match
from core.utils.logs import log_info, log_error, log_warning

TZ_KINSHASA = timezone(timedelta(hours=1))

NIVEAUX = {
    "sur": {"min": 0.75, "max": 1.0, "matchs": 3},
    "modere": {"min": 0.65, "max": 0.75, "matchs": 5},
    "risque": {"min": 0.60, "max": 0.65, "matchs": 7},
}


def _meilleure_reco(prono):
    """Renvoie la meilleure recommandation (1X, X2, ou 12) et sa probabilité."""
    try:
        dc_1x = float(prono.get('dc_1x', 0.5))
        dc_x2 = float(prono.get('dc_x2', 0.5))
        dc_12 = float(prono.get('dc_12', 0.5))

        options = [("1X", dc_1x), ("X2", dc_x2), ("12", dc_12)]
        meilleure = max(options, key=lambda x: x[1])
        return meilleure[0], meilleure[1]
    except Exception as e:
        log_error("Erreur lors du calcul de la meilleure recommandation", "PARIS", exception=e)
        return "1X", 0.5


def get_tous_pronostics_disponibles():
    """Récupère tous les pronostics disponibles pour les matchs du jour."""
    from core.daily_matches import get_matchs_du_jour
    from config import MAPPING_COMPETITIONS
    
    try:
        matchs = get_matchs_du_jour()
    except Exception as e:
        log_error("Impossible de récupérer les matchs du jour pour les coupons", "PARIS", exception=e)
        return []
    
    if not matchs:
        log_warning("Aucun match disponible pour les coupons.", "PARIS")
        return []

    resultats = []
    matchs_ignores = 0

    for m in matchs:
        try:
            home = m.get('home')
            away = m.get('away')
            
            if not home or not away:
                matchs_ignores += 1
                continue
            
            # Le manager a déjà mis "competition_reelle" (nom propre)
            competition_reelle = m.get('competition_reelle') or MAPPING_COMPETITIONS.get(m.get('competition'), m.get('competition'))
            
            try:
                prono = predire_match(home, away, competition=competition_reelle, cotes_book=m.get('cotes_book'))
            except Exception as e:
                log_error(f"Erreur de prédiction pour {home} vs {away} (coupons)", "PARIS", exception=e)
                matchs_ignores += 1
                continue
            
            if not isinstance(prono, dict) or 'erreur' in prono:
                matchs_ignores += 1
                continue

            reco_label, reco_pct = _meilleure_reco(prono)
            
            if reco_pct <= 0:
                matchs_ignores += 1
                continue
            
            cote = round(1 / reco_pct, 2)
            
            if cote < 1.30:
                matchs_ignores += 1
                continue

            resultats.append({
                'home': home, 'away': away, 
                'competition': m.get('competition'),
                'nom_competition': m.get('nom_competition', m.get('competition')),
                'heure': m.get('heure'), 
                'reco_label': reco_label,
                'reco_pct': float(reco_pct),
                'btts': float(prono.get('btts_yes', 0.5)),
                'over_25': float(prono.get('over_25', 0.5)),
                'analyse_pari': prono.get('analyse_pari'),
            })
        except Exception as e:
            log_error(f"Erreur de traitement d'un match pour les coupons", "PARIS", exception=e)
            matchs_ignores += 1
            continue

    log_info(f"{len(resultats)} pronostics retenus pour les coupons, {matchs_ignores} ignorés.", "PARIS")
    return resultats


def construire_coupon(niveau, matchs_disponibles):
    """Construit un coupon pour un niveau donné (sur, modéré, risque)."""
    if niveau not in NIVEAUX:
        log_warning(f"Niveau de coupon inconnu : {niveau}", "PARIS")
        return None
        
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
        if m['reco_pct'] > 0:
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
    
    try:
        matchs = get_tous_pronostics_disponibles()
    except Exception as e:
        log_error("Erreur lors de la génération des coupons", "PARIS", exception=e)
        return {'weekend': est_weekend, 'coupons': []}

    if not matchs:
        return {'weekend': est_weekend, 'coupons': []}

    coupons = []

    if not est_weekend:
        # En semaine : un coupon par niveau
        for niveau in ['sur', 'modere', 'risque']:
            try:
                coupon = construire_coupon(niveau, matchs)
                if coupon:
                    coupons.append(coupon)
            except Exception as e:
                log_error(f"Erreur construction coupon '{niveau}'", "PARIS", exception=e)
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
                if not m.get('heure'):
                    continue
                try:
                    dt = datetime.fromisoformat(str(m['heure']).replace("Z", "+00:00")).astimezone(TZ_KINSHASA)
                    if inter['min_h'] <= dt.hour < inter['max_h']:
                        matchs_inter.append(m)
                except Exception as e:
                    log_warning(f"Impossible de parser la date '{m.get('heure')}' : {e}", "PARIS")
                    continue

            if len(matchs_inter) < 3: 
                continue

            for niveau in ['sur', 'modere', 'risque']:
                try:
                    coupon = construire_coupon(niveau, matchs_inter)
                    if coupon:
                        coupon['intervalle'] = inter['nom']
                        coupons.append(coupon)
                except Exception as e:
                    log_error(f"Erreur construction coupon '{niveau}' pour l'intervalle '{inter['nom']}'", "PARIS", exception=e)

    # On ajoute toujours le coupon Outside
    try:
        coupon_outside = construire_coupon_outside(matchs)
        if coupon_outside:
            coupons.append(coupon_outside)
    except Exception as e:
        log_error("Erreur construction coupon 'outside'", "PARIS", exception=e)

    log_info(f"{len(coupons)} coupons générés pour aujourd'hui.", "PARIS")
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

    titre = niveau_labels.get(coupon.get('niveau'), "COUPON")
    if coupon.get('intervalle'):
        titre += f" - {intervalle_labels.get(coupon['intervalle'], '')}"

    texte = f"{titre}\n━━━━━━━━━━━━━━━━━━━━\n\n"

    for i, m in enumerate(coupon.get('matchs', []), 1):
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
        texte += f"━━━━━━━━━━━━━━━━━━━━\n💰 Cote totale : {coupon.get('cote_totale', '?')}\n🎯 Confiance cumulee : {round(coupon.get('confiance_cumulee', 0)*100, 1)}%\n"
    else:
        texte += "━━━━━━━━━━━━━━━━━━━━\n_Passe Premium pour les details et les autres coupons_\n"

    return texte
