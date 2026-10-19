import requests
from datetime import datetime, timedelta, timezone
from users.db import get_connection
from config import FOOTBALL_DATA_KEY
from core.utils.logs import log_info, log_error

TZ_KINSHASA = timezone(timedelta(hours=1))


def _normaliser_nom(nom):
    """Petite fonction pour matcher les noms de l'API avec ceux de la BDD."""
    return nom.lower().replace("fc", "").replace("afc", "").replace("cf", "").replace(" ", "").strip()


def verifier_resultats_veille():
    """Récupère les matchs d'hier, vérifie les pronostics et met à jour la BDD."""
    hier = (datetime.now(TZ_KINSHASA) - timedelta(days=1)).strftime("%Y-%m-%d")
    headers = {"X-Auth-Token": FOOTBALL_DATA_KEY}
    
    with get_connection() as conn:
        with conn.cursor() as cur:
            # 1. On récupère tous les pronostics d'hier qui n'ont pas encore été vérifiés
            cur.execute("""
                SELECT id, home_team, away_team, pronostic_reco 
                FROM resultats_pronostics 
                WHERE date_match = %s AND est_gagnant IS NULL
            """, (hier,))
            pronos = cur.fetchall()
            
            if not pronos:
                return {"total": 0, "gagnes": 0, "texte": "Aucun pronostic à vérifier hier."}

            # 2. On récupère les résultats réels via l'API
            url = f"https://api.football-data.org/v4/matches?dateFrom={hier}&dateTo={hier}"
            res = requests.get(url, headers=headers, timeout=15)
            
            if res.status_code != 200:
                log_error(f"Erreur API résultats ({res.status_code})", "RESULTS")
                return {"total": 0, "gagnes": 0, "texte": "Erreur API lors de la vérification."}

            matchs_api = res.json().get("matches", [])
            resultats_api = {}
            
            for m in matchs_api:
                if m.get("status") == "FINISHED":
                    home = _normaliser_nom(m["homeTeam"]["name"])
                    away = _normaliser_nom(m["awayTeam"]["name"])
                    score_h = m["score"]["fullTime"]["home"]
                    score_a = m["score"]["fullTime"]["away"]
                    resultats_api[f"{home}_{away}"] = (score_h, score_a)
            
            # 3. On compare nos pronostics avec les résultats
            gagnes = 0
            total = len(pronos)
            resultats_a_mettre_a_jour = []
            
            for p_id, home, away, reco in pronos:
                home_norm = _normaliser_nom(home)
                away_norm = _normaliser_nom(away)
                api_key = f"{home_norm}_{away_norm}"
                
                if api_key in resultats_api:
                    sh, sa = resultats_api[api_key]
                    
                    est_gagnant = False
                    if reco == "1X" and sh >= sa: 
                        est_gagnant = True
                    elif reco == "X2" and sa >= sh: 
                        est_gagnant = True
                    elif reco == "12" and sh != sa: 
                        est_gagnant = True
                    
                    if est_gagnant:
                        gagnes += 1
                    
                    resultats_a_mettre_a_jour.append((est_gagnant, p_id))
            
            # 4. Mise à jour de la BDD
            for est_gagnant, p_id in resultats_a_mettre_a_jour:
                cur.execute("UPDATE resultats_pronostics SET est_gagnant = %s WHERE id = %s", (est_gagnant, p_id))
            
        conn.commit()
    
    # 5. Préparation du message pour le canal
    pourcentage = round((gagnes / total) * 100, 1) if total > 0 else 0
    
    if pourcentage >= 70:
        emoji_titre = "🔥"
    elif pourcentage >= 50:
        emoji_titre = "✅"
    else:
        emoji_titre = "📉"

    texte_canal = (
        f"{emoji_titre} **BILAN DE LA VEILLE** {emoji_titre}\n\n"
        f"✅ Pronostics gagnants : {gagnes}/{total}\n"
        f"🎯 Taux de réussite : **{pourcentage}%**\n\n"
        f"👉 Rejoignez-nous pour les pronostics du jour : @MonPronosticFootball_bot"
    )
    
    log_info(f"Résultats vérifiés : {gagnes}/{total} gagnants ({pourcentage}%)", "RESULTS")
    return {"total": total, "gagnes": gagnes, "pourcentage": pourcentage, "texte": texte_canal}
