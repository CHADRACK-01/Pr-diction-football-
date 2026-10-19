import os
os.environ['LOKY_MAX_CPU_COUNT'] = '1'

import time
import io
import joblib
import requests
import pandas as pd
import numpy as np
from datetime import datetime
from io import BytesIO
from sklearn.ensemble import RandomForestClassifier, StackingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier

from config import CHAMPIONNATS
from users import (
    inserer_matchs, charger_tous_les_matchs, compter_matchs,
    sauvegarder_modele_cache, charger_modele_cache, vider_modele_cache
)
from core.utils.logs import log_info, log_error

# Dictionnaire global : contiendra uniquement les données de base (léger)
global_model_data = {}

# ⚠️ CACHE LRU : Ne garde que les 3 derniers modèles utilisés en mémoire
CACHE_MODELES = {}
TAILLE_MAX_CACHE = 3

HOME_ADVANTAGE = 100
ELO_K = 32


def obtenir_code_saison_actuelle():
    now = datetime.now()
    annee_d = now.year if now.month >= 7 else now.year - 1
    annee_f = annee_d + 1
    return f"{str(annee_d)[-2:]}{str(annee_f)[-2:]}"


def _extraire_matchs(df, nom_competition):
    matchs = []
    if not all(c in df.columns for c in ['Date', 'HomeTeam', 'AwayTeam', 'FTHG', 'FTAG', 'FTR']):
        return matchs

    df = df.copy()
    df['Date'] = pd.to_datetime(df['Date'], dayfirst=True, errors='coerce')
    df = df.dropna(subset=['Date', 'HomeTeam', 'AwayTeam', 'FTHG', 'FTAG', 'FTR'])

    for _, r in df.iterrows():
        def g(col):
            if col in r.index and pd.notna(r[col]):
                try:
                    return r[col]
                except Exception:
                    return None
            return None

        m = {
            'date': r['Date'].date(),
            'home_team': str(r['HomeTeam']),
            'away_team': str(r['AwayTeam']),
            'fthg': int(r['FTHG']),
            'ftag': int(r['FTAG']),
            'ftr': str(r['FTR']),
            'competition': nom_competition,
            'hthg': int(g('HTHG')) if g('HTHG') is not None else None,
            'htag': int(g('HTAG')) if g('HTAG') is not None else None,
            'htr': str(g('HTR')) if g('HTR') is not None else None,
            'hs': int(g('HS')) if g('HS') is not None else None,
            'as_shots': int(g('AS')) if g('AS') is not None else None,
            'hst': int(g('HST')) if g('HST') is not None else None,
            'ast': int(g('AST')) if g('AST') is not None else None,
            'hc': int(g('HC')) if g('HC') is not None else None,
            'ac': int(g('AC')) if g('AC') is not None else None,
            'hf': int(g('HF')) if g('HF') is not None else None,
            'af': int(g('AF')) if g('AF') is not None else None,
            'hy': int(g('HY')) if g('HY') is not None else None,
            'ay': int(g('AY')) if g('AY') is not None else None,
            'hr': int(g('HR')) if g('HR') is not None else None,
            'ar': int(g('AR')) if g('AR') is not None else None,
            'b365h': float(g('B365H')) if g('B365H') is not None else None,
            'b365d': float(g('B365D')) if g('B365D') is not None else None,
            'b365a': float(g('B365A')) if g('B365A') is not None else None,
        }
        matchs.append(m)

    return matchs


def charger_et_entrainer(forcer_entrainement=False):
    """
    Charge UNIQUEMENT les données de base depuis le cache PostgreSQL.
    ⚠️ Ne charge PAS les modèles lourds (ils seront chargés à la demande).
    """
    global global_model_data

    if not forcer_entrainement:
        cache = charger_modele_cache()
        if cache:
            try:
                modele_bytes, precision, nb_matchs = cache
                log_info(f"Chargement des données de base depuis le cache...", "ML_MODEL")

                buffer = io.BytesIO(modele_bytes)
                donnees = joblib.load(buffer)

                # On ne charge que les infos utiles (léger)
                global_model_data['df'] = donnees.get('df')
                global_model_data['teams'] = donnees.get('teams')
                global_model_data['team_to_code'] = donnees.get('team_to_code')
                global_model_data['team_global_stats'] = donnees.get('team_global_stats')
                global_model_data['team_xg_stats'] = donnees.get('team_xg_stats')
                global_model_data['features'] = donnees.get('features')
                global_model_data['precision'] = precision
                global_model_data['_tables_initialisees'] = True
                
                # On garde juste la liste des noms de compétitions disponibles
                if 'modeles_par_competition' in donnees:
                    global_model_data['competitions_disponibles'] = list(donnees['modeles_par_competition'].keys())
                    log_info(f"{len(global_model_data['competitions_disponibles'])} compétitions disponibles.", "ML_MODEL")
                else:
                    global_model_data['competitions_disponibles'] = []

                log_info("Données de base chargées ! (Les modèles restent en BDD pour économiser la RAM)", "ML_MODEL")
                return
            except Exception as e:
                log_error(f"Erreur chargement cache : {e}", "ML_MODEL")

    log_error("Réentraînement demandé. Lance le script d'entraînement sur Colab.", "ML_MODEL")


def charger_modele_competition(competition):
    """
    Charge le modèle d'une compétition spécifique depuis la BDD.
    Utilise un cache LRU pour ne garder que les 3 derniers modèles en RAM.
    """
    # 1. Si le modèle est déjà dans le cache, on le retourne
    if competition in CACHE_MODELES:
        return CACHE_MODELES[competition]

    # 2. Sinon, on va le chercher dans la BDD
    log_info(f"Chargement du modèle pour '{competition}' depuis la BDD...", "ML_MODEL")
    try:
        cache_bdd = charger_modele_cache()
        if not cache_bdd:
            return None
        
        modele_bytes, _, _ = cache_bdd
        buffer = io.BytesIO(modele_bytes)
        donnees = joblib.load(buffer)
        
        modeles = donnees.get('modeles_par_competition', {})
        if competition not in modeles:
            log_error(f"Modèle introuvable pour la compétition : {competition}", "ML_MODEL")
            return None
        
        # 3. Gestion du cache LRU (si trop de modèles en RAM, on supprime le plus ancien)
        if len(CACHE_MODELES) >= TAILLE_MAX_CACHE:
            plus_ancien = next(iter(CACHE_MODELES))
            del CACHE_MODELES[plus_ancien]
            log_info(f"Cache plein. Suppression du modèle '{plus_ancien}' de la RAM.", "ML_MODEL")
        
        # 4. On ajoute le nouveau modèle au cache
        CACHE_MODELES[competition] = modeles[competition]['model']
        log_info(f"Modèle '{competition}' chargé en RAM (Précision: {round(modeles[competition]['precision']*100, 2)}%).", "ML_MODEL")
        
        return CACHE_MODELES[competition]
    except Exception as e:
        log_error(f"Erreur lors du chargement du modèle '{competition}' : {e}", "ML_MODEL")
        return None


def tache_arriere_plan_maj(chat_id, bot):
    try:
        now = datetime.now()
        annee_courante_debut = now.year if now.month >= 7 else now.year - 1
        saison_actuelle_code = obtenir_code_saison_actuelle()

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                          '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }

        matchs_a_inserer = []

        def _traiter_saison(code_saison):
            for nom_propre, code in CHAMPIONNATS.items():
                url = f"https://www.football-data.co.uk/mmz4281/{code_saison}/{code}.csv"
                try:
                    res = requests.get(url, headers=headers, timeout=10)
                    if res.status_code == 200 and b',' in res.content and b'<!DOCTYPE html>' not in res.content:
                        temp_df = pd.read_csv(BytesIO(res.content), encoding='latin1', low_memory=False)
                        matchs = _extraire_matchs(temp_df, nom_propre.replace("_", " ").title())
                        matchs_a_inserer.extend(matchs)
                    time.sleep(0.1)
                except Exception:
                    continue

        for i in range(1, 5):
            annee_d = annee_courante_debut - i
            annee_f = annee_d + 1
            code_saison = f"{str(annee_d)[-2:]}{str(annee_f)[-2:]}"
            _traiter_saison(code_saison)

        _traiter_saison(saison_actuelle_code)

        inseres = inserer_matchs(matchs_a_inserer)
        total = compter_matchs()

        vider_modele_cache()
        
        bot.send_message(
            chat_id,
            f"✅ *Synchronisation réussie !*\n\n"
            f"📥 {inseres} nouveau(x) match(s) téléchargé(s).\n"
            f"💾 Total en base : *{total} matchs*.\n\n"
            f"⚠️ Le modèle doit être réentraîné sur Colab pour intégrer ces nouvelles données.",
            parse_mode="Markdown"
        )
    except Exception as e:
        bot.send_message(chat_id, f"❌ Erreur critique : {str(e)}")


def get_top_pronostics_du_jour(nb=3):
    """Retourne les N meilleurs pronostics parmi les matchs les plus récents."""
    from core.prediction import predire_match

    if not global_model_data or not global_model_data.get('df'):
        return []

    df = global_model_data['df']
    if df is None or len(df) == 0:
        return []

    df_recent = df.tail(100).copy()
    df_recent = df_recent.sort_values('Date', ascending=False)

    resultats = []
    for _, row in df_recent.iterrows():
        home = row['HomeTeam']
        away = row['AwayTeam']
        competition = row.get('Competition', 'default')
        try:
            prono = predire_match(home, away, competition=competition)
            if "erreur" in prono:
                continue

            max_dc = max(prono['dc_1x'], prono['dc_x2'], prono['dc_12'])

            resultats.append({
                'home': home,
                'away': away,
                'prono': prono,
                'score_confiance': max_dc
            })
        except Exception:
            continue

    resultats.sort(key=lambda x: x['score_confiance'], reverse=True)

    return resultats[:nb]
