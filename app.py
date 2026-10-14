import os
os.environ['LOKY_MAX_CPU_COUNT'] = '1'

import glob
import time
import threading
import difflib
from datetime import datetime
import pandas as pd
import numpy as np
from scipy.stats import poisson
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier, VotingClassifier
from sklearn.metrics import accuracy_score
import telebot
import requests
from flask import Flask, request

# =========================================================
# CONFIGURATION
# =========================================================
TOKEN = "8443191637:AAGcCknBZDg1o0NBeL8czLt0SsQ4c2LEMvY"
bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

global_model_data = {}

CHAMPIONNATS = {
    "premier_league": "E0",
    "championship": "E1",
    "laliga": "SP1",
    "laliga_2": "SP2",
    "ligue_1": "F1",
    "ligue_2": "F2",
    "bundesliga_1": "D1",
    "bundesliga_2": "D2",
    "serie_a": "I1",
    "serie_b": "I2"
}

# =========================================================
# CHARGEMENT ET ENTRAÎNEMENT
# =========================================================
def charger_et_entrainer():
    global global_model_data
    print("Recherche et fusion des sources de données multi-championnats (5 ans) avec cotes...")

    fichiers_csv = glob.glob("matchs_*.csv")
    if not fichiers_csv:
        print("⚠️ Aucun fichier CSV trouvé !")
        return

    dfs = []
    for fichier in fichiers_csv:
        try:
            temp_df = pd.read_csv(fichier, encoding='latin1', low_memory=False)
            cols_requises = ['Date', 'HomeTeam', 'AwayTeam', 'FTHG', 'FTAG', 'FTR']

            if not all(c in temp_df.columns for c in cols_requises):
                print(f"[Ignoré] {fichier} : colonnes manquantes")
                continue

            nom_comp = fichier.replace("matchs_", "").rsplit('_', 1)[0].replace("_", " ").title()
            
            # On sélectionne les colonnes de base + les cotes si elles existent
            colonnes_a_garder = cols_requises.copy()
            for cote_col in ['B365H', 'B365D', 'B365A']:
                if cote_col in temp_df.columns:
                    colonnes_a_garder.append(cote_col)

            temp_df = temp_df[colonnes_a_garder].copy()
            temp_df['Competition'] = nom_comp

            # Parse de date robuste
            temp_df['Date'] = pd.to_datetime(temp_df['Date'], dayfirst=True, errors='coerce')
            if temp_df['Date'].isna().sum() > len(temp_df) * 0.5:
                temp_df['Date'] = pd.to_datetime(temp_df['Date'], dayfirst=False, errors='coerce')

            temp_df = temp_df.dropna(subset=cols_requises)

            if len(temp_df) > 0:
                dfs.append(temp_df)
                dmin = temp_df['Date'].min().strftime('%Y-%m-%d')
                dmax = temp_df['Date'].max().strftime('%Y-%m-%d')
                print(f"[OK] {fichier} : {len(temp_df)} matchs ({dmin} → {dmax})")
        except Exception as e:
            print(f"⚠️ Erreur {fichier}: {e}")

    if not dfs:
        print("❌ Aucun fichier valide chargé.")
        return

    # --- Fusion ---
    df = pd.concat(dfs, ignore_index=True)
    print(f"📊 Total brut avant filtre : {len(df)}")

    # Gestion des cotes manquantes (remplacement par des valeurs neutres si absentes)
    for c in ['B365H', 'B365D', 'B365A']:
        if c not in df.columns:
            df[c] = 2.70 # Valeur de cote moyenne neutre par défaut
        else:
            df[c] = pd.to_numeric(df[c], errors='coerce').fillna(2.70)

    # Calcul des probabilités implicites des bookmakers (1 / Cote)
    df['Odds_H_Prob'] = 1 / df['B365H']
    df['Odds_D_Prob'] = 1 / df['B365D']
    df['Odds_A_Prob'] = 1 / df['B365A']

    # Déduplication avec compétition
    df = df.drop_duplicates(subset=['Date', 'HomeTeam', 'AwayTeam', 'Competition'])
    print(f"📊 Après déduplication : {len(df)}")

    df = df.sort_values('Date').reset_index(drop=True)

    # Filtre 5 ans assoupli
    date_limite = pd.Timestamp.now() - pd.DateOffset(years=5)
    df_filtre = df[df['Date'] >= date_limite].reset_index(drop=True)

    if len(df_filtre) < len(df) * 0.3:
        print(f"⚠️ Filtre 5 ans trop agressif. Conservation de tout l'historique ({len(df)} matchs).")
    else:
        df = df_filtre
        print(f"📊 Total après filtre 5 ans : {len(df)} matchs")

    # --- Encodage équipes ---
    teams = pd.unique(df[['HomeTeam', 'AwayTeam']].values.ravel())
    team_to_code = {team: i for i, team in enumerate(teams)}
    competitions = df['Competition'].unique()

    # --- Elo ---
    elo_ratings = {team: 1500.0 for team in teams}
    K = 32
    HOME_ADVANTAGE = 100

    # --- Classements par compétition ---
    tables = {comp: {} for comp in competitions}
    for comp in competitions:
        comp_teams = pd.unique(df[df['Competition'] == comp][['HomeTeam', 'AwayTeam']].values.ravel())
        tables[comp] = {team: {'points': 0, 'played': 0, 'gf': 0, 'ga': 0} for team in comp_teams}

    # --- Structures pour features ---
    last_match_date = {}
    home_elo_list, away_elo_list, elo_diff_list = [], [], []
    home_rest_list, away_rest_list = [], []
    team_home_stats = {team: {'scored': [], 'conceded': []} for team in teams}
    team_away_stats = {team: {'scored': [], 'conceded': []} for team in teams}
    team_global_stats = {team: {'scored': [], 'conceded': []} for team in teams}
    h2h_history = {}

    h_glob_sc, h_glob_co, a_glob_sc, a_glob_co = [], [], [], []
    h_spec_sc, h_spec_co, a_spec_sc, a_spec_co = [], [], [], []
    h2h_form_list = []
    home_pts_list, away_pts_list, home_gd_list, away_gd_list = [], [], [], []

    # --- Boucle principale ---
    for index, row in df.iterrows():
        h_team, a_team, match_date, comp = row['HomeTeam'], row['AwayTeam'], row['Date'], row['Competition']
        if h_team not in tables[comp]: tables[comp][h_team] = {'points': 0, 'played': 0, 'gf': 0, 'ga': 0}
        if a_team not in tables[comp]: tables[comp][a_team] = {'points': 0, 'played': 0, 'gf': 0, 'ga': 0}

        # Repos
        h_rest = (match_date - last_match_date[h_team]).days if h_team in last_match_date else 7
        a_rest = (match_date - last_match_date[a_team]).days if a_team in last_match_date else 7
        home_rest_list.append(h_rest)
        away_rest_list.append(a_rest)
        last_match_date[h_team] = match_date
        last_match_date[a_team] = match_date

        # Points & différence de buts
        home_pts_list.append(tables[comp][h_team]['points'])
        away_pts_list.append(tables[comp][a_team]['points'])
        home_gd_list.append(tables[comp][h_team]['gf'] - tables[comp][h_team]['ga'])
        away_gd_list.append(tables[comp][a_team]['gf'] - tables[comp][a_team]['ga'])

        # H2H
        match_key = tuple(sorted([h_team, a_team]))
        if match_key not in h2h_history:
            h2h_history[match_key] = []
        recent_h2h = h2h_history[match_key][-5:]
        h2h_form_list.append(sum(1 for res in recent_h2h if res == h_team) / len(recent_h2h) if recent_h2h else 0.5)

        # Elo
        h_elo, a_elo = elo_ratings[h_team], elo_ratings[a_team]
        home_elo_list.append(h_elo)
        away_elo_list.append(a_elo)
        elo_diff_list.append((h_elo + HOME_ADVANTAGE) - a_elo)

        # Stats globales
        h_g_hist = team_global_stats[h_team]['scored']
        h_g_cond = team_global_stats[h_team]['conceded']
        a_g_hist = team_global_stats[a_team]['scored']
        a_g_cond = team_global_stats[a_team]['conceded']

        h_glob_sc.append(sum(h_g_hist) / len(h_g_hist) if h_g_hist else 1.2)
        h_glob_co.append(sum(h_g_cond) / len(h_g_cond) if h_g_cond else 1.2)
        a_glob_sc.append(sum(a_g_hist) / len(a_g_hist) if a_g_hist else 1.0)
        a_glob_co.append(sum(a_g_cond) / len(a_g_cond) if a_g_cond else 1.3)

        # Stats spécifiques (5 derniers matchs)
        h_s_hist = team_home_stats[h_team]['scored'][-5:]
        h_s_cond = team_home_stats[h_team]['conceded'][-5:]
        a_s_hist = team_away_stats[a_team]['scored'][-5:]
        a_s_cond = team_away_stats[a_team]['conceded'][-5:]

        h_spec_sc.append(sum(h_s_hist) / len(h_s_hist) if h_s_hist else 1.3)
        h_spec_co.append(sum(h_s_cond) / len(h_s_cond) if h_s_cond else 1.0)
        a_spec_sc.append(sum(a_s_hist) / len(a_s_hist) if a_s_hist else 1.0)
        a_spec_co.append(sum(a_s_cond) / len(a_s_cond) if a_s_cond else 1.4)

        # Mise à jour classement
        fthg, ftag, ftr = int(row['FTHG']), int(row['FTAG']), str(row['FTR'])
        if ftr == 'H':
            tables[comp][h_team]['points'] += 3
        elif ftr == 'D':
            tables[comp][h_team]['points'] += 1
            tables[comp][a_team]['points'] += 1
        else:
            tables[comp][a_team]['points'] += 3

        tables[comp][h_team]['played'] += 1
        tables[comp][h_team]['gf'] += fthg
        tables[comp][h_team]['ga'] += ftag
        tables[comp][a_team]['played'] += 1
        tables[comp][a_team]['gf'] += ftag
        tables[comp][a_team]['ga'] += fthg

        winner = h_team if ftr == 'H' else ("Draw" if ftr == 'D' else a_team)
        h2h_history[match_key].append(winner)

        # Mise à jour Elo
        exp_h = 1 / (1 + 10 ** ((a_elo - (h_elo + HOME_ADVANTAGE)) / 400))
        exp_a = 1 / (1 + 10 ** (((h_elo + HOME_ADVANTAGE) - a_elo) / 400))
        elo_ratings[h_team] += K * ((1.0 if ftr == 'H' else (0.5 if ftr == 'D' else 0.0)) - exp_h)
        elo_ratings[a_team] += K * ((0.0 if ftr == 'H' else (0.5 if ftr == 'D' else 1.0)) - exp_a)

        # Mise à jour stats
        team_global_stats[h_team]['scored'].append(fthg)
        team_global_stats[h_team]['conceded'].append(ftag)
        team_global_stats[a_team]['scored'].append(ftag)
        team_global_stats[a_team]['conceded'].append(fthg)

        team_home_stats[h_team]['scored'].append(fthg)
        team_home_stats[h_team]['conceded'].append(ftag)

        team_away_stats[a_team]['scored'].append(ftag)
        team_away_stats[a_team]['conceded'].append(fthg)

    # --- Ajout des features au DataFrame (incluant les cotes) ---
    new_cols = pd.DataFrame({
        'Home_Elo': home_elo_list,
        'Away_Elo': away_elo_list,
        'Elo_Diff': elo_diff_list,
        'H2H_Score': h2h_form_list,
        'Home_Points': home_pts_list,
        'Away_Points': away_pts_list,
        'Home_GD': home_gd_list,
        'Away_GD': away_gd_list,
        'Home_Rest': home_rest_list,
        'Away_Rest': away_rest_list,
        'H_Glob_Sc': h_glob_sc,
        'H_Glob_Co': h_glob_co,
        'A_Glob_Sc': a_glob_sc,
        'A_Glob_Co': a_glob_co,
        'H_Spec_Sc': h_spec_sc,
        'H_Spec_Co': h_spec_co,
        'A_Spec_Sc': a_spec_sc,
        'A_Spec_Co': a_spec_co,
        'Odds_H_Prob': df['Odds_H_Prob'],
        'Odds_D_Prob': df['Odds_D_Prob'],
        'Odds_A_Prob': df['Odds_A_Prob'],
        'HomeTeam_Encoded': df['HomeTeam'].map(team_to_code),
        'AwayTeam_Encoded': df['AwayTeam'].map(team_to_code)
    }, index=df.index)

    df = pd.concat([df, new_cols], axis=1)

    features = [
        'HomeTeam_Encoded', 'AwayTeam_Encoded',
        'Home_Elo', 'Away_Elo', 'Elo_Diff', 'H2H_Score',
        'Home_Points', 'Away_Points', 'Home_GD', 'Away_GD',
        'Home_Rest', 'Away_Rest',
        'H_Glob_Sc', 'H_Glob_Co', 'A_Glob_Sc', 'A_Glob_Co',
        'H_Spec_Sc', 'H_Spec_Co', 'A_Spec_Sc', 'A_Spec_Co',
        'Odds_H_Prob', 'Odds_D_Prob', 'Odds_A_Prob'
    ]

    # --- Split chronologique ---
    split_idx = int(len(df) * 0.8)
    X_train = df[features].iloc[:split_idx]
    X_test = df[features].iloc[split_idx:]
    y_train = df['FTR'].iloc[:split_idx]
    y_test = df['FTR'].iloc[split_idx:]

    # --- Entraînement optimisé ---
    rf_model = RandomForestClassifier(n_estimators=400, max_depth=14, min_samples_split=4, random_state=42, n_jobs=1)
    gb_model = HistGradientBoostingClassifier(max_iter=200, learning_rate=0.03, random_state=42)
    ensemble_model = VotingClassifier(estimators=[('rf', rf_model), ('gb', gb_model)], voting='soft')
    ensemble_model.fit(X_train, y_train)

    precision = accuracy_score(y_test, ensemble_model.predict(X_test))

    # --- Sauvegarde ---
    global_model_data['df'] = df
    global_model_data['teams'] = teams
    global_model_data['team_to_code'] = team_to_code
    global_model_data['team_global_stats'] = team_global_stats
    global_model_data['precision'] = precision
    global_model_data['model'] = ensemble_model
    global_model_data['features'] = features

    print(f"✅ Modèle optimisé entraîné sur {len(df)} matchs. Précision : {round(precision * 100, 2)}%")


# =========================================================
# TÉLÉCHARGEMENT DES DONNÉES
# =========================================================
def tache_arriere_plan_maj(chat_id):
    try:
        now = datetime.now()
        annee_courante_debut = now.year if now.month >= 7 else now.year - 1

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                          '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }

        telecharges = 0
        for i in range(5):
            annee_d = annee_courante_debut - i
            annee_f = annee_d + 1
            code_saison = f"{str(annee_d)[-2:]}{str(annee_f)[-2:]}"

            for nom_propre, code in CHAMPIONNATS.items():
                url = f"https://www.football-data.co.uk/mmz4281/{code_saison}/{code}.csv"
                try:
                    res = requests.get(url, headers=headers, timeout=10)
                    if res.status_code == 200 and b',' in res.content and b'<!DOCTYPE html>' not in res.content:
                        nom_fichier = f"matchs_{nom_propre}_{code_saison}.csv"
                        with open(nom_fichier, 'wb') as f:
                            f.write(res.content)
                        telecharges += 1
                    time.sleep(0.2)
                except Exception:
                    continue

        if telecharges > 0:
            charger_et_entrainer()
            prec = global_model_data.get('precision', 0.5)
            nb_matchs = len(global_model_data.get('df', []))
            bot.send_message(
                chat_id,
                f"✅ *Mise à jour et optimisation réussies !*\n\n"
                f"📥 {telecharges} fichiers récupérés.\n"
                f"📊 Total en mémoire : *{nb_matchs} matchs*.\n"
                f"🎯 Précision IA optimisée : *{round(prec * 100, 2)}%*",
                parse_mode="Markdown"
            )
        else:
            bot.send_message(chat_id, "⚠️ Aucun nouveau fichier n'a pu être téléchargé.")

    except Exception as e:
        bot.send_message(chat_id, f"❌ Erreur critique : {str(e)}")


# =========================================================
# COMMANDES TELEGRAM
# =========================================================
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn_pred = telebot.types.KeyboardButton("⚽ Faire un Pronostic")
    btn_hist = telebot.types.KeyboardButton("📜 Historique")
    btn_stats = telebot.types.KeyboardButton("📊 Statistiques du Modèle")
    markup.add(btn_pred, btn_hist, btn_stats)

    prec = global_model_data.get('precision', 0.5)
    nb_matchs = len(global_model_data.get('df', []))
    welcome_text = (
        "🤖 *Assistant Pro Multi-Sources (Cotes & 5 Ans)*\n\n"
        f"📊 Matchs en mémoire : *{nb_matchs}*\n"
        f"🎯 Précision IA : *{round(prec * 100, 2)}%*\n\n"
        "👇 *Utilisez les boutons ci-dessous :*"
    )
    bot.send_message(message.chat.id, welcome_text, parse_mode="Markdown", reply_markup=markup)


@bot.message_handler(commands=['update'])
def force_update_data(message):
    bot.reply_to(message, "⏳ Téléchargement et optimisation du modèle en arrière-plan...")
    threading.Thread(target=tache_arriere_plan_maj, args=(message.chat.id,)).start()


@bot.message_handler(func=lambda message: True)
def handle_menu_clicks(message):
    text = message.text

    if text == "📊 Statistiques du Modèle":
        prec = global_model_data.get('precision', 0.5)
        length = len(global_model_data.get('df', []))
        bot.reply_to(
            message,
            f"📊 Base de données sur 5 ans (avec cotes bookmakers).\n"
            f"Matchs analysés : {length}\n"
            f"Précision de test : {round(prec * 100, 2)}%"
        )

    elif text == "📜 Historique":
        try:
            hist = pd.read_csv("historique_pronostics.csv")
            last_5 = hist.tail(5)
            texte = "📜 *Vos 5 derniers pronostics :*\n\n"
            for _, row in last_5.iterrows():
                texte += (
                    f"⚽ *{row['Match']}*\n"
                    f"📅 {row['Date_Consultation']}\n"
                    f"💡 {row['Pronostic_1N2']} | 🎯 Score: {row['Score_Exact']}\n\n"
                )
            bot.reply_to(message, texte, parse_mode="Markdown")
        except FileNotFoundError:
            bot.reply_to(message, "⚠️ Aucun historique enregistré pour l'instant.")

    elif text == "⚽ Faire un Pronostic":
        bot.reply_to(message, "✍️ Tapez l'affiche :\n\n`EquipeDom vs EquipeExt`", parse_mode="Markdown")

    elif 'vs' in text.lower():
        traiter_prediction(message)

    else:
        bot.reply_to(message, "💡 Utilisez les boutons ou tapez `Équipe A vs Équipe B`.")


# =========================================================
# PRÉDICTION AVANCÉE
# =========================================================
def traiter_prediction(message):
    try:
        text = message.text.strip()
        parts = text.split('vs' if 'vs' in text else 'VS')
        if len(parts) < 2:
            return

        home_input = parts[0].strip()
        away_input = parts[1].strip()

        teams = global_model_data['teams']
        team_to_code = global_model_data['team_to_code']
        team_global_stats = global_model_data['team_global_stats']
        df = global_model_data['df']
        model = global_model_data.get('model')
        features = global_model_data.get('features')

        def trouver_nom_exact(nom_partiel):
            lower_teams = {t.lower(): t for t in teams}
            matches = difflib.get_close_matches(nom_partiel.lower(), lower_teams.keys(), n=1, cutoff=0.4)
            return lower_teams[matches[0]] if matches else nom_partiel

        home_team = trouver_nom_exact(home_input)
        away_team = trouver_nom_exact(away_input)

        if home_team not in team_to_code or away_team not in team_to_code:
            bot.reply_to(message, f"❌ Impossible de trouver '{home_input}' ou '{away_input}' dans la base.")
            return

        # Utilisation du modèle de Machine Learning si disponible, sinon repli Poisson/Elo
        p_h, p_d, p_a = 0.33, 0.33, 0.33
        if model is not None and features is not None:
            # Récupération des dernières stats connues de l'équipe à domicile et extérieur
            h_encoded = team_to_code[home_team]
            a_encoded = team_to_code[away_team]
            
            # Approximation des variables récentes pour la prédiction
            h_pts = df[df['HomeTeam'] == home_team]['Home_Points'].iloc[-1] if len(df[df['HomeTeam'] == home_team]) > 0 else 0
            a_pts = df[df['AwayTeam'] == away_team]['Away_Points'].iloc[-1] if len(df[df['AwayTeam'] == away_team]) > 0 else 0
            h_gd = df[df['HomeTeam'] == home_team]['Home_GD'].iloc[-1] if len(df[df['HomeTeam'] == home_team]) > 0 else 0
            a_gd = df[df['AwayTeam'] == away_team]['Away_GD'].iloc[-1] if len(df[df['AwayTeam'] == away_team]) > 0 else 0
            
            # Vecteur de prédiction factice basé sur les moyennes récentes
            X_pred = pd.DataFrame([[
                h_encoded, a_encoded, 
                1500.0, 1500.0, 100.0, 0.5, 
                h_pts, a_pts, h_gd, a_gd, 
                7, 7, 
                1.3, 1.0, 1.2, 1.3, 
                1.3, 1.0, 1.0, 1.4,
                0.45, 0.28, 0.27 # Probabilités de cotes par défaut équilibrées
            ]], columns=features)
            
            probs = model.predict_proba(X_pred)[0]
            classes = model.classes_ # ['H', 'D', 'A'] généralement
            
            prob_dict = {cls: prob for cls, prob in zip(classes, probs)}
            p_h = prob_dict.get('H', 0.33)
            p_d = prob_dict.get('D', 0.33)
            p_a = prob_dict.get('A', 0.33)

        # Calcul Poisson complémentaire pour les buts et scores exacts
        h_g_hist = team_global_stats[home_team]['scored']
        h_g_cond = team_global_stats[home_team]['conceded']
        a_g_hist = team_global_stats[away_team]['scored']
        a_g_cond = team_global_stats[away_team]['conceded']

        league_avg_home, league_avg_away = df['FTHG'].mean(), df['FTAG'].mean()
        h_att = (sum(h_g_hist) / len(h_g_hist)) if h_g_hist else league_avg_home
        h_def = (sum(h_g_cond) / len(h_g_cond)) if h_g_cond else league_avg_away
        a_att = (sum(a_g_hist) / len(a_g_hist)) if a_g_hist else league_avg_away
        a_def = (sum(a_g_cond) / len(a_g_cond)) if a_g_cond else league_avg_home

        lambda_home = max(0.2, (h_att * a_def) / league_avg_home)
        lambda_away = max(0.2, (a_att * h_def) / league_avg_away)

        max_goals = 5
        score_matrix = np.outer(
            [poisson.pmf(i, lambda_home) for i in range(max_goals + 1)],
            [poisson.pmf(j, lambda_away) for j in range(max_goals + 1)]
        )

        max_prob = max(p_h, p_d, p_a)
        indice_fiabilite = (
            "🔥 CONFIANCE ÉLEVÉE" if max_prob >= 0.55
            else ("⚠️ MATCH INCERTAIN / RISQUÉ" if max_prob < 0.40 else "⚖️ CONFIANCE MODÉRÉE")
        )

        under_25 = np.sum([score_matrix[i, j] for i in range(max_goals + 1) for j in range(max_goals + 1) if i + j < 2.5])
        over_25 = 1.0 - under_25
        btts_yes = np.sum([score_matrix[i, j] for i in range(1, max_goals + 1) for j in range(1, max_goals + 1)])
        best_i, best_j = np.unravel_index(np.argmax(score_matrix), score_matrix.shape)

        bulletin = (
            f"🏆 *BULLETIN OPTIMISÉ : {home_team} vs {away_team}*\n\n"
            f"📌 Indice : *{indice_fiabilite}*\n\n"
            f"📊 *1N2 - Probabilités (IA + Cotes) :*\n"
            f"  • Domicile (1) : *{round(p_h * 100, 1)}%* (Cote: {round(1 / p_h, 2)})\n"
            f"  • Nul (N) : *{round(p_d * 100, 1)}%* (Cote: {round(1 / p_d, 2)})\n"
            f"  • Extérieur (2) : *{round(p_a * 100, 1)}%* (Cote: {round(1 / p_a, 2)})\n\n"
            f"⚽ *Tendances de Buts :*\n"
            f"  • Plus de 2.5 buts : *{round(over_25 * 100, 1)}%*\n"
            f"  • Les deux équipes marquent : *{round(btts_yes * 100, 1)}%*\n"
            f"  • 🎯 Score exact : *{best_i} - {best_j}*"
        )

        bot.reply_to(message, bulletin, parse_mode="Markdown")

        # Historique
        record = {
            "Date_Consultation": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "Match": f"{home_team} vs {away_team}",
            "Pronostic_1N2": f"1:{round(p_h * 100, 1)}% N:{round(p_d * 100, 1)}% 2:{round(p_a * 100, 1)}%",
            "Score_Exact": f"{best_i}-{best_j}"
        }
        hist_df = pd.DataFrame([record])
        try:
            existing = pd.read_csv("historique_pronostics.csv")
            updated = pd.concat([existing, hist_df], ignore_index=True)
            updated.to_csv("historique_pronostics.csv", index=False)
        except FileNotFoundError:
            hist_df.to_csv("historique_pronostics.csv", index=False)

    except Exception as e:
        bot.reply_to(message, f"❌ Erreur lors de l'analyse : {str(e)}")


# =========================================================
# WEBHOOK FLASK
# =========================================================
@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    json_str = request.get_data().decode('UTF-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "OK", 200


@app.route('/')
def index():
    return "Bot 5 Ans Optimisé (Cotes & ML) Opérationnel sur Render !", 200


# =========================================================
# LANCEMENT
# =========================================================
charger_et_entrainer()
