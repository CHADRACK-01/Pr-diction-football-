from datetime import datetime, timezone, timedelta

from core.ml_model import global_model_data
from core.prediction import predire_match


TZ_KINSHASA = timezone(timedelta(hours=1))


# Seuils par niveau de coupon
NIVEAUX = {
    "sur": {"min": 0.75, "max": 1.0, "matchs": 3},
    "modere": {"min": 0.65, "max": 0.75, "matchs": 5},
    "risque": {"min": 0.60, "max": 0.65, "matchs": 7},
}


def _normaliser_nom(nom):
    """Normalise un nom d'équipe (retire les FC, AFC, etc.)."""
    suffixes = [" FC", " AFC", " CF", " SC", " AC", " City FC", " United FC"]
    for suf in suffixes:
        if nom.endswith(suf):
            return nom[:-len(suf)]
    return nom


def _meilleure_reco(prono):
    """Retourne la meilleure double chance et son pourcentage."""
    dc_1x = float(prono['dc_1x'])
    dc_x2 = float(prono['dc_x2'])
    dc_12 = float(prono['dc_12'])

    options = [
        ("1X", dc_1x),
        ("X2", dc_x2),
        ("12", dc_12),
    ]
    meilleure = max(options, key=lambda x: x[1])
    return meilleure[0], meilleure[1]


def get_tous_pronostics_disponibles():
    """
    Récupère tous les pronostics possibles depuis les matchs du jour.
    Utilise les matchs déjà en mémoire (via get_matchs_du_jour).
    """
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

            resultats.append({
                'home': home,
                'away': away,
                'competition': m['competition'],
                'heure': m['heure'],
                'reco_label': reco_label,
                'reco_pct': float(reco_pct),
                'score_exact': prono.get('best_score', (0, 0)),
                'top_scores': prono.get('top_scores', []),
                'over_25': float(prono.get('over_25', 0.5)),
                'btts_yes': float(prono.get('btts_yes', 0.5)),
            })
        except Exception as e:
            print(f"⚠️ Erreur prono {home} vs {away} : {e}")
            continue

    return resultats


def construire_coupon(niveau, matchs_disponibles):
    """
    Construit un coupon d'un niveau donné.
    - niveau : 'sur', 'modere', 'risque'
    - matchs_disponibles : liste des pronostics
    """
    seuil = NIVEAUX[niveau]

    # Filtrer les matchs selon le seuil
    candidats = [
        m for m in matchs_disponibles
        if seuil['min'] <= m['reco_pct'] < seuil['max']
    ]

    # Si pas assez de candidats, élargir la fourchette
    if len(candidats) < 3:
        candidats = [m for m in matchs_disponibles if m['reco_pct'] >= seuil['min']]

    # Si toujours rien
    if len(candidats) < 3:
        return None

    # Trier par confiance décroissante
    candidats.sort(key=lambda x: x['reco_pct'], reverse=True)

    # Prendre le nombre de matchs cible
    nb_matchs = min(seuil['matchs'], len(candidats))
    selection = candidats[:nb_matchs]

    # Calculer cote totale et confiance cumulée
    cote_totale = 1.0
    confiance_cumulee = 1.0

    for m in selection:
        if m['reco_pct'] > 0:
            cote_totale *= (1 / m['reco_pct'])
            confiance_cumulee *= m['reco_pct']

    return {
        'niveau': niveau,
        'matchs': selection,
        'cote_totale': round(cote_totale, 2),
        'confiance_cumulee': round(confiance_cumulee, 4),
    }


def generer_coupons_du_jour():
    """
    Génère les coupons du jour selon la stratégie :
    - Semaine (Lun-Ven) : 3 coupons (sur, modere, risque)
    - Weekend (Sam-Dim) : 9 coupons (3 intervalles × 3 niveaux)
    """
    maintenant = datetime.now(TZ_KINSHASA)
    jour_semaine = maintenant.weekday()  # 0=Lundi, 6=Dimanche
    est_weekend = jour_semaine >= 5

    matchs = get_tous_pronostics_disponibles()

    if not matchs:
        return {'weekend': est_weekend, 'coupons': []}

    coupons = []

    if not est_weekend:
        # Semaine : 3 coupons classiques
        for niveau in ['sur', 'modere', 'risque']:
            coupon = construire_coupon(niveau, matchs)
            if coupon:
                coupons.append(coupon)
    else:
        # Weekend : 9 coupons (3 intervalles × 3 niveaux)
        intervalles = [
            {"nom": "matin", "min_h": 8, "max_h": 14},
            {"nom": "apres_midi", "min_h": 14, "max_h": 19},
            {"nom": "soir", "min_h": 19, "max_h": 23},
        ]

        for inter in intervalles:
            # Filtrer les matchs de cet intervalle
            matchs_inter = []
            for m in matchs:
                try:
                    dt = datetime.fromisoformat(m['heure'].replace("Z", "+00:00")).astimezone(TZ_KINSHASA)
                    if inter['min_h'] <= dt.hour < inter['max_h']:
                        matchs_inter.append(m)
                except Exception:
                    continue

            if len(matchs_inter) < 3:
                continue

            for niveau in ['sur', 'modere', 'risque']:
                coupon = construire_coupon(niveau, matchs_inter)
                if coupon:
                    coupon['intervalle'] = inter['nom']
                    coupons.append(coupon)

    return {'weekend': est_weekend, 'coupons': coupons}


def formater_coupon(coupon, langue="fr", montrer_details=True):
    """Formate un coupon pour l'affichage Telegram."""
    niveau_labels = {
        "sur": "🔥 COUPON SUR",
        "modere": "⚖️ COUPON MODERE",
        "risque": "🎲 COUPON RISQUE",
    }

    intervalle_labels = {
        "matin": "🌅 Matin",
        "apres_midi": "☀️ Apres-midi",
        "soir": "🌙 Soir",
    }

    titre = niveau_labels.get(coupon['niveau'], "COUPON")

    if coupon.get('intervalle'):
        titre += f" - {intervalle_labels.get(coupon['intervalle'], '')}"

    texte = f"{titre}\n"
    texte += "━━━━━━━━━━━━━━━━━━━━\n\n"

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
        texte += "━━━━━━━━━━━━━━━━━━━━\n"
        texte += f"💰 Cote totale : {coupon['cote_totale']}\n"
        texte += f"🎯 Confiance cumulee : {round(coupon['confiance_cumulee']*100, 1)}%\n"
    else:
        texte += "━━━━━━━━━━━━━━━━━━━━\n"
        texte += "_Passe Premium pour les details et les autres coupons_\n"

    return texte
