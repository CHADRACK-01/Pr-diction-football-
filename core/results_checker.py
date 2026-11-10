import unicodedata
import requests
from datetime import datetime, timedelta, timezone

from users.db import get_connection
from config import FOOTBALL_DATA_KEY
from core.utils.logs import log_info, log_error, log_warning

TZ_KINSHASA = timezone(timedelta(hours=1))

# Suffixes/préfixes courants à retirer pour normaliser les noms d'équipes
PREFIXES_SUFFIXES = [
    "fc", "afc", "cf", "sc", "ac", "as", "ss", "us", "rc", "rcd",
    "ca", "ud", "cd", "sd", "sco", "hsc", "sv", "vfl", "vfb", "tsg",
    "fsv", "ssv", "1.", "1900", "1901", "1909", "1913", "1848", "1899",
    "1919", "1846", "1898", "bsc", "sc", "aj", "sco", "usl", "csm"
]


def _normaliser_nom(nom):
    """
    Normalise un nom d'équipe pour le matching.
    Retire les accents, les suffixes/préfixes courants, et les espaces multiples.
    Ex: "FC Barcelona" -> "barcelona"
    Ex: "Paris Saint-Germain FC" -> "paris saint germain"
    """
    if not nom:
        return ""
    
    try:
        # Retirer les accents
        nom = unicodedata.normalize('NFKD', nom).encode('ascii', 'ignore').decode('utf-8')
        nom = nom.lower().strip()
        
        # Retirer les suffixes/préfixes (mot par mot)
        mots = nom.split()
        mots_filtres = [m for m in mots if m not in PREFIXES_SUFFIXES]
        
        if not mots_filtres:
            mots_filtres = mots  # Sécurité si tout est filtré
        
        return "".join(mots_filtres).replace(" ", "")
    except Exception as e:
        log_warning(f"Impossible de normaliser '{nom}' : {e}", "RESULTS")
        return nom.lower().strip()


def _extraire_scores(match_api):
    """
    Extrait les scores full-time d'un match API Football-Data.
    Retourne (score_home, score_away) ou (None, None) si pas de score.
    """
    try:
        score = match_api.get("score", {})
        full_time = score.get("fullTime", {})
        home = full_time.get("home")
        away = full_time.get("away")
        
        # Si le match n'a pas de score (match reporté, annulé)
        if home is None or away is None:
            return None, None
        
        return int(home), int(away)
    except Exception:
        return None, None


def verifier_resultats_veille():
    """
    Récupère les matchs d'hier, vérifie les pronostics et met à jour la BDD.
    Retourne un dictionnaire {total, gagnes, pourcentage, texte}.
    """
    hier = (datetime.now(TZ_KINSHASA) - timedelta(days=1)).strftime("%Y-%m-%d")
    
    if not FOOTBALL_DATA_KEY:
        log_error("Clé API Football-Data manquante (FOOTBALL_DATA_KEY vide)", "RESULTS")
        return {"total": 0, "gagnes": 0, "pourcentage": 0, "texte": "❌ Clé API manquante."}
    
    # =========================================================
    # 1. Lire les pronostics d'hier dans la BDD
    # =========================================================
    try:
        conn = get_connection()
        cur = conn.execute("""
            SELECT id, home_team, away_team, pronostic_reco 
            FROM resultats_pronostics 
            WHERE date_match = ? AND est_gagnant IS NULL
        """, (hier,))
        pronos = cur.fetchall()
        conn.close()
    except Exception as e:
        log_error("Impossible de lire les pronostics d'hier dans la BDD", "RESULTS", exception=e)
        return {"total": 0, "gagnes": 0, "pourcentage": 0, "texte": "❌ Erreur de lecture BDD."}

    if not pronos:
        log_info("Aucun pronostic à vérifier pour hier.", "RESULTS")
        return {"total": 0, "gagnes": 0, "pourcentage": 0, "texte": "Aucun pronostic à vérifier hier."}

    # =========================================================
    # 2. Récupérer les résultats réels via l'API
    # =========================================================
    headers = {"X-Auth-Token": FOOTBALL_DATA_KEY}
    url = f"https://api.football-data.org/v4/matches?dateFrom={hier}&dateTo={hier}"
    
    try:
        res = requests.get(url, headers=headers, timeout=15)
        if res.status_code != 200:
            log_error(f"Erreur API Football-Data ({res.status_code}) pour les résultats du {hier}", "RESULTS")
            return {"total": 0, "gagnes": 0, "pourcentage": 0, "texte": "❌ Erreur API lors de la vérification."}
        matchs_api = res.json().get("matches", [])
    except requests.exceptions.Timeout:
        log_error("Timeout de l'API Football-Data pour les résultats", "RESULTS")
        return {"total": 0, "gagnes": 0, "pourcentage": 0, "texte": "❌ Timeout de l'API."}
    except Exception as e:
        log_error("Erreur réseau lors de la vérification des résultats", "RESULTS", exception=e)
        return {"total": 0, "gagnes": 0, "pourcentage": 0, "texte": "❌ Erreur réseau."}

    # =========================================================
    # 3. Construire un index des résultats (clé: "home_norm_away_norm")
    # =========================================================
    resultats_api = {}
    for m in matchs_api:
        try:
            if m.get("status") != "FINISHED":
                continue
            
            home = _normaliser_nom(m.get("homeTeam", {}).get("name", ""))
            away = _normaliser_nom(m.get("awayTeam", {}).get("name", ""))
            
            if not home or not away:
                continue
            
            sh, sa = _extraire_scores(m)
            if sh is None or sa is None:
                continue
            
            resultats_api[f"{home}_{away}"] = (sh, sa)
        except Exception as e:
            log_warning(f"Erreur de parsing d'un match API : {e}", "RESULTS")
            continue

    log_info(f"{len(resultats_api)} résultats récupérés depuis l'API.", "RESULTS")

    # =========================================================
    # 4. Comparer avec nos pronostics
    # =========================================================
    gagnes = 0
    total = len(pronos)
    matchs_non_trouves = 0
    resultats_a_mettre_a_jour = []
    
    for p in pronos:
        try:
            p_id, home, away, reco = p
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
            else:
                matchs_non_trouves += 1
        except Exception as e:
            log_warning(f"Erreur de comparaison d'un pronostic : {e}", "RESULTS")
            continue

    if matchs_non_trouves > 0:
        log_warning(f"{matchs_non_trouves} pronostics non trouvés dans l'API.", "RESULTS")

    # =========================================================
    # 5. Mettre à jour la BDD
    # =========================================================
    if resultats_a_mettre_a_jour:
        try:
            conn = get_connection()
            for est_gagnant, p_id in resultats_a_mettre_a_jour:
                try:
                    conn.execute(
                        "UPDATE resultats_pronostics SET est_gagnant = ? WHERE id = ?", 
                        (1 if est_gagnant else 0, p_id)
                    )
                except Exception as e:
                    log_error(f"Impossible de mettre à jour le pronostic #{p_id}", "RESULTS", exception=e)
            conn.commit()
            conn.close()
        except Exception as e:
            log_error("Impossible de mettre à jour la BDD avec les résultats", "RESULTS", exception=e)

    # =========================================================
    # 6. Préparer le message pour le canal
    # =========================================================
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
