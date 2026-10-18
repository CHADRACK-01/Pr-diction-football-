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


global_model_data = {}
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
    Charge le modèle depuis le cache PostgreSQL.
    Si forcer_entrainement=True, réentraîne le modèle (code d'entraînement).
    """
    global global_model_data

    if not forcer_entrainement:
        cache = charger_modele_cache()
        if cache:
            try:
                modele_bytes, precision, nb_matchs = cache
                log_info(f"Chargement du modèle depuis le cache ({nb_matchs} matchs, précision={round(precision*100, 2)}%)...", "ML_MODEL")

                buffer = io.BytesIO(modele_bytes)
                donnees = joblib.load(buffer)

                # ⚠️ On charge TOUT, y compris les modèles par compétition
                global_model_data.update(donnees)
                global_model_data['precision'] = precision
                global_model_data['_tables_initialisees'] = True

                # Vérification : est-ce qu'on a bien les modèles par compétition ?
                if 'modeles_par_competition' in donnees:
                    log_info(f"{len(donnees['modeles_par_competition'])} modèles par compétition chargés.", "ML_MODEL")
                else:
                    log_info("Modèle unique chargé (pas de séparation par compétition).", "ML_MODEL")

                log_info("Modèle chargé depuis le cache !", "ML_MODEL")
                return
            except Exception as e:
                log_error(f"Erreur chargement cache : {e}. Réentraînement...", "ML_MODEL")

    # ⚠️ Si on doit réentraîner, on utilise le script d'entraînement complet
    # (qui sera lancé depuis Colab, pas depuis Render)
    log_error("Réentraînement demandé. Lance le script d'entraînement sur Colab.", "ML_MODEL")


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
        
        # ⚠️ On ne réentraîne plus ici, on demande à Colab
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


# =========================================================
# TOP PRONOSTICS DU JOUR (pour notifications)
# =========================================================
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
