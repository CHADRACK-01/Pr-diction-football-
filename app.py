import os
os.environ['LOKY_MAX_CPU_COUNT'] = '1'

import glob
import time
import threading
import difflib
import uuid
import asyncio
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from scipy.stats import poisson
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier, VotingClassifier
from sklearn.metrics import accuracy_score
import telebot
import requests
from flask import Flask, request, jsonify

# --- NEONPAY IMPORTS ---
from neonpay import create_neonpay, PaymentStage, PaymentStatus

from config import (
    DOSSIER_PASSE, DOSSIER_ACTUEL, CHAMPIONNATS,
    FICHIER_HISTORIQUE
)
from users import (
    initialiser_tables, enregistrer_utilisateur,
    get_statut_label, peut_faire_pronostic, get_compteur_jour,
    get_limite_jour, incrementer_compteur, set_premium,
    est_premium
)

# =========================================================
# CONFIGURATION
# =========================================================
TOKEN = "8443191637:AAGcCknBZDg1o0NBeL8czLt0SsQ4c2LEMvY"
bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

global_model_data = {}

HOME_ADVANTAGE = 100
ELO_K = 32

# =========================================================
# NEONPAY (TELEGRAM STARS)
# =========================================================
print("💫 Initialisation de NeonPay (Telegram Stars)...")
neonpay = create_neonpay(bot)

# Prix en étoiles (Telegram prélève une commission d'environ 30%)
ABONNEMENTS_STARS = {
    "journalier": {
        "nom": "Journalier",
        "prix_stars": 100,   # ~2 USD
        "duree_jours": 1,
        "emoji": "📅"
    },
    "hebdomadaire": {
        "nom": "Hebdomadaire",
        "prix_stars": 300,   # ~6 USD
        "duree_jours": 7,
        "emoji": "📆"
    },
    "mensuel": {
        "nom": "Mensuel",
        "prix_stars": 500,   # ~10 USD
        "duree_jours": 30,
        "emoji": "🗓️"
    }
}

# Créer les PaymentStages pour NeonPay
for key, abo in ABONNEMENTS_STARS.items():
    stage = PaymentStage(
        title=f"Abonnement {abo['nom']}",
        description=f"Pronostics illimités pendant {abo['duree_jours']} jour(s)",
        price=abo['prix_stars'],
        label=abo['nom']
    )
    neonpay.create_payment_stage(key, stage)
    print(f"   💫 Offre créée : {abo['nom']} - {abo['prix_stars']} Stars")

# Handler de succès NeonPay
@neonpay.on_payment
async def handle_payment(result):
    """Callback appelé par NeonPay quand un paiement est complété."""
    if result.status == PaymentStatus.COMPLETED:
        user_id = result.user_id
        stage_id = result.stage_id

        duree = ABONNEMENTS_STARS[stage_id]["duree_jours"]
        nom_abo = ABONNEMENTS_STARS[stage_id]["nom"]

        expiration = (datetime.now() + timedelta(days=duree)).strftime("%Y-%m-%d %H:%M")
        set_premium(user_id, expiration)

        bot.send_message(
            user_id,
            f"🎉 *Paiement Stars confirmé !*\n\n"
            f"✅ Formule activée : *{nom_abo}*\n"
            f"⏱️ Durée : *{duree} jour(s)*\n"
            f"📅 Expire le : *{expiration}*\n\n"
            f"Profite de tes pronostics illimités 🚀",
            parse_mode="Markdown"
        )
        print(f"💫 Paiement Stars validé pour user {user_id} - {nom_abo}")


def obtenir_code_saison_actuelle():
    now = datetime.now()
    annee_d = now.year if now.month >= 7 else now.year - 1
    annee_f = annee_d + 1
    return f"{str(annee_d)[-2:]}{str(annee_f)[-2:]}"

# =========================================================
# CHARGEMENT ET ENTRAÎNEMENT
# =========================================================
def charger_et_entrainer():
    global global_model_data
    print("Recherche et fusion des données (Passé + Actuel)...")

    fichiers_passe = glob.glob(os.path.join(DOSSIER_PASSE, "matchs_*.csv"))
    fichiers_actuel = glob.glob(os.path.join(DOSSIER_ACTUEL, "matchs_*.csv"))
    fichiers_csv = fichiers_passe + fichiers_actuel

    if not fichiers_csv:
        print("⚠️ Aucun fichier CSV trouvé dans les dossiers !")
        return

    dfs = []
    for fichier in fichiers_csv:
        try:
            temp_df = pd.read_csv(fichier, encoding='latin1', low_memory=False)
            cols_requises = ['Date', 'HomeTeam', 'AwayTeam', 'FTHG', 'FTAG', 'FTR']

            if not all(c in temp_df.columns for c in cols_requises):
                continue

            nom_base = os.path.basename(fichier)
            nom_comp = nom_base.replace("matchs_", "").rsplit('_', 1)[0].replace("_", " ").title()

            temp_df = temp_df[cols_requises].copy()
            temp_df['Competition'] = nom_comp

            temp_df['Date'] = pd.to_datetime(temp_df['Date'], dayfirst=True, errors='coerce')
            if temp_df['Date'].isna().sum() > len(temp_df) * 0.5:
                temp_df['Date'] = pd.to_datetime(temp_df['Date'], dayfirst=False, errors='coerce')

            temp_df = temp_df.dropna(subset=cols_requises)

            if len(temp_df) > 0:
                dfs.append(temp_df)
        except Exception as e:
            print(f"⚠️ Erreur {fichier}: {e}")

    if not dfs:
        return

    df = pd.concat(dfs, ignore_index=True)
    df = df.drop_duplicates(subset=['Date', 'HomeTeam', 'AwayTeam', 'Competition'])
    df = df.sort_values('Date').reset_index(drop=True)

    date_limite = pd.Timestamp.now() - pd.DateOffset(years=5)
    df_filtre = df[df['Date'] >= date_limite].reset_index(drop=True)

    df = df_filtre if len(df_filtre) >= len(df) * 0.3 else df

    print(f"📊 Total : {len(df)} matchs")

    teams = pd.unique(df[['HomeTeam', 'AwayTeam']].values.ravel())
    team_to_code = {team: i for i, team in enumerate(teams)}
    competitions = df['Competition'].unique()

    elo_ratings = {team: 1500.0 for team in teams}

    tables = {comp: {} for comp in competitions}
    for comp in competitions:
        comp_teams = pd.unique(df[df['Competition'] == comp][['HomeTeam', 'AwayTeam']].values.ravel())
        tables[comp] = {team: {'points': 0, 'played': 0, 'gf': 0, 'ga': 0} for team in comp_teams}

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

    for index, row in df.iterrows():
        h_team, a_team, match_date, comp = row['HomeTeam'], row['AwayTeam'], row['Date'], row['Competition']
        if h_team not in tables[comp]: tables[comp][h_team] = {'points': 0, 'played': 0, 'gf': 0, 'ga': 0}
        if a_team not in tables[comp]: tables[comp][a_team] = {'points': 0, 'played': 0, 'gf': 0, 'ga': 0}

        h_rest = (match_date - last_match_date[h_team]).days if h_team in last_match_date else 7
        a_rest = (match_date - last_match_date[a_team]).days if a_team in last_match_date else 7
        home_rest_list.append(h_rest)
        away_rest_list.append(a_rest)
        last_match_date[h_team] = match_date
        last_match_date[a_team] = match_date

        home_pts_list.append(tables[comp][h_team]['points'])
        away_pts_list.append(tables[comp][a_team]['points'])
        home_gd_list.append(tables[comp][h_team]['gf'] - tables[comp][h_team]['ga'])
        away_gd_list.append(tables[comp][a_team]['gf'] - tables[comp][a_team]['ga'])

        match_key = tuple(sorted([h_team, a_team]))
        if match_key not in h2h_history:
            h2h_history[match_key] = []
        recent_h2h = h2h_history[match_key][-5:]
        h2h_form_list.append(sum(1 for res in recent_h2h if res == h_team) / len(recent_h2h) if recent_h2h else 0.5)

        h_elo, a_elo = elo_ratings[h_team], elo_ratings[a_team]
        home_elo_list.append(h_elo)
        away_elo_list.append(a_elo)
        elo_diff_list.append((h_elo + HOME_ADVANTAGE) - a_elo)

        h_g_hist = team_global_stats[h_team]['scored']
        h_g_cond = team_global_stats[h_team]['conceded']
        a_g_hist = team_global_stats[a_team]['scored']
        a_g_cond = team_global_stats[a_team]['conceded']

        h_glob_sc.append(sum(h_g_hist) / len(h_g_hist) if h_g_hist else 1.2)
        h_glob_co.append(sum(h_g_cond) / len(h_g_cond) if h_g_cond else 1.2)
        a_glob_sc.append(sum(a_g_hist) / len(a_g_hist) if a_g_hist else 1.0)
        a_glob_co.append(sum(a_g_cond) / len(a_g_cond) if a_g_cond else 1.3)

        h_s_hist = team_home_stats[h_team]['scored'][-5:]
        h_s_cond = team_home_stats[h_team]['conceded'][-5:]
        a_s_hist = team_away_stats[a_team]['scored'][-5:]
        a_s_cond = team_away_stats[a_team]['conceded'][-5:]

        h_spec_sc.append(sum(h_s_hist) / len(h_s_hist) if h_s_hist else 1.3)
        h_spec_co.append(sum(h_s_cond) / len(h_s_cond) if h_s_cond else 1.0)
        a_spec_sc.append(sum(a_s_hist) / len(a_s_hist) if a_s_hist else 1.0)
        a_spec_co.append(sum(a_s_cond) / len(a_s_cond) if a_s_cond else 1.4)

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

        exp_h = 1 / (1 + 10 ** ((a_elo - (h_elo + HOME_ADVANTAGE)) / 400))
        exp_a = 1 / (1 + 10 ** (((h_elo + HOME_ADVANTAGE) - a_elo) / 400))
        elo_ratings[h_team] += ELO_K * ((1.0 if ftr == 'H' else (0.5 if ftr == 'D' else 0.0)) - exp_h)
        elo_ratings[a_team] += ELO_K * ((0.0 if ftr == 'H' else (0.5 if ftr == 'D' else 1.0)) - exp_a)

        team_global_stats[h_team]['scored'].append(fthg)
        team_global_stats[h_team]['conceded'].append(ftag)
        team_global_stats[a_team]['scored'].append(ftag)
        team_global_stats[a_team]['conceded'].append(fthg)

        team_home_stats[h_team]['scored'].append(fthg)
        team_home_stats[h_team]['conceded'].append(ftag)

        team_away_stats[a_team]['scored'].append(ftag)
        team_away_stats[a_team]['conceded'].append(fthg)

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
        'H_Spec_Sc', 'H_Spec_Co', 'A_Spec_Sc', 'A_Spec_Co'
    ]

    split_idx = int(len(df) * 0.8)
    X_train = df[features].iloc[:split_idx]
    X_test = df[features].iloc[split_idx:]
    y_train = df['FTR'].iloc[:split_idx]
    y_test = df['FTR'].iloc[split_idx:]

    rf_model = RandomForestClassifier(n_estimators=400, max_depth=14, min_samples_split=4, random_state=42, n_jobs=1)
    gb_model = HistGradientBoostingClassifier(max_iter=200, learning_rate=0.03, random_state=42)
    ensemble_model = VotingClassifier(estimators=[('rf', rf_model), ('gb', gb_model)], voting='soft')
    ensemble_model.fit(X_train, y_train)

    precision = accuracy_score(y_test, ensemble_model.predict(X_test))

    global_model_data['df'] = df
    global_model_data['teams'] = teams
    global_model_data['team_to_code'] = team_to_code
    global_model_data['team_global_stats'] = team_global_stats
    global_model_data['precision'] = precision
    global_model_data['model'] = ensemble_model
    global_model_data['features'] = features

    print(f"✅ Modèle entraîné sur {len(df)} matchs. Précision : {round(precision * 100, 2)}%")


# =========================================================
# TÉLÉCHARGEMENT
# =========================================================
def tache_arriere_plan_maj(chat_id):
    try:
        now = datetime.now()
        annee_courante_debut = now.year if now.month >= 7 else now.year - 1
        saison_actuelle_code = obtenir_code_saison_actuelle()

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                          '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }

        fichiers_actuels_existants = glob.glob(os.path.join(DOSSIER_ACTUEL, "*.csv"))
        for f_path in fichiers_actuels_existants:
            nom_f = os.path.basename(f_path)
            if saison_actuelle_code not in nom_f:
                dest_path = os.path.join(DOSSIER_PASSE, nom_f)
                if os.path.exists(dest_path):
                    os.remove(dest_path)
                os.rename(f_path, dest_path)

        for i in range(1, 5):
            annee_d = annee_courante_debut - i
            annee_f = annee_d + 1
            code_saison = f"{str(annee_d)[-2:]}{str(annee_f)[-2:]}"

            for nom_propre, code in CHAMPIONNATS.items():
                nom_fichier = f"matchs_{nom_propre}_{code_saison}.csv"
                chemin_archive = os.path.join(DOSSIER_PASSE, nom_fichier)

                if not os.path.exists(chemin_archive):
                    url = f"https://www.football-data.co.uk/mmz4281/{code_saison}/{code}.csv"
                    try:
                        res = requests.get(url, headers=headers, timeout=10)
                        if res.status_code == 200 and b',' in res.content and b'<!DOCTYPE html>' not in res.content:
                            with open(chemin_archive, 'wb') as f:
                                f.write(res.content)
                        time.sleep(0.1)
                    except Exception:
                        continue

        telecharges_actuel = 0
        for nom_propre, code in CHAMPIONNATS.items():
            url = f"https://www.football-data.co.uk/mmz4281/{saison_actuelle_code}/{code}.csv"
            nom_fichier = f"matchs_{nom_propre}_{saison_actuelle_code}.csv"
            chemin_actuel = os.path.join(DOSSIER_ACTUEL, nom_fichier)
            try:
                res = requests.get(url, headers=headers, timeout=10)
                if res.status_code == 200 and b',' in res.content and b'<!DOCTYPE html>' not in res.content:
                    with open(chemin_actuel, 'wb') as f:
                        f.write(res.content)
                    telecharges_actuel += 1
                time.sleep(0.1)
            except Exception:
                continue

        annee_limite_archive = annee_courante_debut - 5
        for f_path in glob.glob(os.path.join(DOSSIER_PASSE, "*.csv")):
            nom_f = os.path.basename(f_path)
            try:
                saison_str = nom_f.split('_')[-1].replace('.csv', '')
                annee_fichier = int("20" + saison_str[:2])
                if annee_fichier < annee_limite_archive:
                    os.remove(f_path)
            except Exception:
                continue

        charger_et_entrainer()
        prec = global_model_data.get('precision', 0.5)
        nb_matchs = len(global_model_data.get('df', []))

        bot.send_message(
            chat_id,
            f"✅ *Synchronisation réussie !*\n\n"
            f"📂 Saisons passées chargées.\n"
            f"🔄 Saison actuelle ({saison_actuelle_code}) : {telecharges_actuel} fichiers.\n"
            f"📊 Total : *{nb_matchs} matchs*.\n"
            f"🎯 Précision IA : *{round(prec * 100, 2)}%*",
            parse_mode="Markdown"
        )
    except Exception as e:
        bot.send_message(chat_id, f"❌ Erreur critique : {str(e)}")


# =========================================================
# COMMANDES TELEGRAM
# =========================================================
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    user = message.from_user
    enregistrer_utilisateur(user.id, user.username, user.first_name)

    statut_label = get_statut_label(user.id)
    prec = global_model_data.get('precision', 0.5)
    nb_matchs = len(global_model_data.get('df', []))
    compteur = get_compteur_jour(user.id)
    limite = get_limite_jour(user.id)

    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        telebot.types.KeyboardButton("⚽ Faire un Pronostic"),
        telebot.types.KeyboardButton("📜 Historique"),
        telebot.types.KeyboardButton("📊 Statistiques du Modèle"),
        telebot.types.KeyboardButton("⭐ Passer Premium"),
    )

    welcome_text = (
        f"🤖 *Assistant Pro*\n\n"
        f"👤 Bienvenue *{user.first_name}* !\n"
        f"📊 Statut : *{statut_label}*\n"
        f"🎫 Pronostics aujourd'hui : *{compteur}/{limite}*\n\n"
        f"📈 Matchs en mémoire : *{nb_matchs}*\n"
        f"🎯 Précision IA : *{round(prec * 100, 2)}%*\n\n"
        "👇 *Utilisez les boutons ci-dessous :*"
    )
    bot.send_message(message.chat.id, welcome_text, parse_mode="Markdown", reply_markup=markup)


@bot.message_handler(commands=['update'])
def force_update_data(message):
    bot.reply_to(message, "⏳ Synchronisation en arrière-plan...")
    threading.Thread(target=tache_arriere_plan_maj, args=(message.chat.id,), daemon=True).start()


@bot.message_handler(commands=['myid'])
def cmd_myid(message):
    bot.reply_to(message, f"🆔 Ton ID : `{message.from_user.id}`", parse_mode="Markdown")


# =========================================================
# MENU PRINCIPAL
# =========================================================
@bot.message_handler(func=lambda message: True)
def handle_menu_clicks(message):
    text = message.text
    user_id = message.from_user.id

    if text == "📊 Statistiques du Modèle":
        prec = global_model_data.get('precision', 0.5)
        length = len(global_model_data.get('df', []))
        bot.reply_to(message, f"📊 Matchs analysés : {length}\n🎯 Précision : {round(prec * 100, 2)}%")

    elif text == "📜 Historique":
        try:
            hist = pd.read_csv(FICHIER_HISTORIQUE)
            last_5 = hist.tail(5)
            texte = "📜 *Vos 5 derniers pronostics :*\n\n"
            for _, row in last_5.iterrows():
                texte += (
                    f"⚽ *{row['Match']}*\n"
                    f"📅 {row['Date_Consultation']}\n"
                    f"💡 {row['Pronostic_1N2']} | 🎯 {row['Score_Exact']}\n\n"
                )
            bot.reply_to(message, texte, parse_mode="Markdown")
        except FileNotFoundError:
            bot.reply_to(message, "⚠️ Aucun historique.")

    elif text == "⭐ Passer Premium":
        if est_premium(user_id):
            bot.reply_to(
                message,
                "✅ *Tu es déjà Premium !*\n\nProfite bien de tes pronostics illimités 🚀",
               es[comp][h_team]['played'] += 1
        tables[comp][h_team]['gf'] += fthg
        tables[comp][h_team]['ga'] += ftag
        tables[comp][a_team]['played'] += 1
        tables[comp][a_team]['gf'] += ftag
        tables[comp][a_team]['ga'] += fthg

        winner = h_team if ftr == 'H' else ("Draw" if ftr == 'D' else a_team)
        h2h_history[match_key].append(winner)

        exp_h = 1 / (1 + 10 ** ((a_elo - (h_elo + HOME_ADVANTAGE)) / 400))
        exp_a = 1 / (1 + 10 ** (((h_elo + HOME_ADVANTAGE) - a_elo) / 400))
        elo_ratings[h_team] += ELO_K * ((1.0 if ftr == 'H' else (0.5 if ftr == 'D' else 0.0)) - exp_h)
        elo_ratings[a_team] += ELO_K * ((0.0 if ftr == 'H' else (0.5 if ftr == 'D' else 1.0)) - exp_a)

        team_global_stats[h_team]['scored'].append(fthg)
        team_global_stats[h_team]['conceded'].append(ftag)
        team_global_stats[a_team]['scored'].append(ftag)
        team_global_stats[a_team]['conceded'].append(fthg)

        team_home_stats[h_team]['scored'].append(fthg)
        team_home_stats[h_team]['conceded'].append(ftag)

        team_away_stats[a_team]['scored'].append(ftag)
        team_away_stats[a_team]['conceded'].append(fthg)

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
        'H_Spec_Sc', 'H_Spec_Co', 'A_Spec_Sc', 'A_Spec_Co'
    ]

    split_idx = int(len(df) * 0.8)
    X_train = df[features].iloc[:split_idx]
    X_test = df[features].iloc[split_idx:]
    y_train = df['FTR'].iloc[:split_idx]
    y_test = df['FTR'].iloc[split_idx:]

    rf_model = RandomForestClassifier(n_estimators=400, max_depth=14, min_samples_split=4, random_state=42, n_jobs=1)
    gb_model = HistGradientBoostingClassifier(max_iter=200, learning_rate=0.03, random_state=42)
    ensemble_model = VotingClassifier(estimators=[('rf', rf_model), ('gb', gb_model)], voting='soft')
    ensemble_model.fit(X_train, y_train)

    precision = accuracy_score(y_test, ensemble_model.predict(X_test))

    global_model_data['df'] = df
    global_model_data['teams'] = teams
    global_model_data['team_to_code'] = team_to_code
    global_model_data['team_global_stats'] = team_global_stats
    global_model_data['precision'] = precision
    global_model_data['model'] = ensemble_model
    global_model_data['features'] = features

    print(f"✅ Modèle entraîné sur {len(df)} matchs. Précision : {round(precision * 100, 2)}%")

# =========================================================
# TÉLÉCHARGEMENT (identique)
# =========================================================
def tache_arriere_plan_maj(chat_id):
    try:
        now = datetime.now()
        annee_courante_debut = now.year if now.month >= 7 else now.year - 1
        saison_actuelle_code = obtenir_code_saison_actuelle()

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                          '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }

        fichiers_actuels_existants = glob.glob(os.path.join(DOSSIER_ACTUEL, "*.csv"))
        for f_path in fichiers_actuels_existants:
            nom_f = os.path.basename(f_path)
            if saison_actuelle_code not in nom_f:
                dest_path = os.path.join(DOSSIER_PASSE, nom_f)
                if os.path.exists(dest_path):
                    os.remove(dest_path)
                os.rename(f_path, dest_path)

        for i in range(1, 5):
            annee_d = annee_courante_debut - i
            annee_f = annee_d + 1
            code_saison = f"{str(annee_d)[-2:]}{str(annee_f)[-2:]}"

            for nom_propre, code in CHAMPIONNATS.items():
                nom_fichier = f"matchs_{nom_propre}_{code_saison}.csv"
                chemin_archive = os.path.join(DOSSIER_PASSE, nom_fichier)

                if not os.path.exists(chemin_archive):
                    url = f"https://www.football-data.co.uk/mmz4281/{code_saison}/{code}.csv"
                    try:
                        res = requests.get(url, headers=headers, timeout=10)
                        if res.status_code == 200 and b',' in res.content and b'<!DOCTYPE html>' not in res.content:
                            with open(chemin_archive, 'wb') as f:
                                f.write(res.content)
                        time.sleep(0.1)
                    except Exception:
                        continue

        telecharges_actuel = 0
        for nom_propre, code in CHAMPIONNATS.items():
            url = f"https://www.football-data.co.uk/mmz4281/{saison_actuelle_code}/{code}.csv"
            nom_fichier = f"matchs_{nom_propre}_{saison_actuelle_code}.csv"
            chemin_actuel = os.path.join(DOSSIER_ACTUEL, nom_fichier)
            try:
                res = requests.get(url, headers=headers, timeout=10)
                if res.status_code == 200 and b',' in res.content and b'<!DOCTYPE html>' not in res.content:
                    with open(chemin_actuel, 'wb') as f:
                        f.write(res.content)
                    telecharges_actuel += 1
                time.sleep(0.1)
            except Exception:
                continue

        annee_limite_archive = annee_courante_debut - 5
        for f_path in glob.glob(os.path.join(DOSSIER_PASSE, "*.csv")):
            nom_f = os.path.basename(f_path)
            try:
                saison_str = nom_f.split('_')[-1].replace('.csv', '')
                annee_fichier = int("20" + saison_str[:2])
                if annee_fichier < annee_limite_archive:
                    os.remove(f_path)
            except Exception:
                continue

        charger_et_entrainer()
        prec = global_model_data.get('precision', 0.5)
        nb_matchs = len(global_model_data.get('df', []))

        bot.send_message(
            chat_id,
            f"✅ *Synchronisation réussie !*\n\n"
            f"📂 Saisons passées chargées.\n"
            f"🔄 Saison actuelle ({saison_actuelle_code}) : {telecharges_actuel} fichiers.\n"
            f"📊 Total : *{nb_matchs} matchs*.\n"
            f"🎯 Précision IA : *{round(prec * 100, 2)}%*",
            parse_mode="Markdown"
        )
    except Exception as e:
        bot.send_message(chat_id, f"❌ Erreur critique : {str(e)}")

# =========================================================
# COMMANDES TELEGRAM
# =========================================================
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    user = message.from_user
    enregistrer_utilisateur(user.id, user.username, user.first_name)

    statut_label = get_statut_label(user.id)
    prec = global_model_data.get('precision', 0.5)
    nb_matchs = len(global_model_data.get('df', []))
    compteur = get_compteur_jour(user.id)
    limite = get_limite_jour(user.id)

    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        telebot.types.KeyboardButton("⚽ Faire un Pronostic"),
        telebot.types.KeyboardButton("📜 Historique"),
        telebot.types.KeyboardButton("📊 Statistiques du Modèle"),
        telebot.types.KeyboardButton("⭐ Passer Premium"),
    )

    welcome_text = (
        f"🤖 *Assistant Pro*\n\n"
        f"👤 Bienvenue *{user.first_name}* !\n"
        f"📊 Statut : *{statut_label}*\n"
        f"🎫 Pronostics aujourd'hui : *{compteur}/{limite}*\n\n"
        f"📈 Matchs en mémoire : *{nb_matchs}*\n"
        f"🎯 Précision IA : *{round(prec * 100, 2)}%*\n\n"
        "👇 *Utilisez les boutons ci-dessous :*"
    )
    bot.send_message(message.chat.id, welcome_text, parse_mode="Markdown", reply_markup=markup)

@bot.message_handler(commands=['update'])
def force_update_data(message):
    bot.reply_to(message, "⏳ Synchronisation en arrière-plan...")
    threading.Thread(target=tache_arriere_plan_maj, args=(message.chat.id,), daemon=True).start()

@bot.message_handler(commands=['myid'])
def cmd_myid(message):
    bot.reply_to(message, f"🆔 Ton ID : `{message.from_user.id}`", parse_mode="Markdown")

@bot.message_handler(commands=['annuler'])
def cmd_annuler(message):
    bot.reply_to(message, "❌ Action annulée.")

# =========================================================
# MENU PRINCIPAL
# =========================================================
@bot.message_handler(func=lambda message: True)
def handle_menu_clicks(message):
    text = message.text
    user_id = message.from_user.id

    if text == "📊 Statistiques du Modèle":
        prec = global_model_data.get('precision', 0.5)
        length = len(global_model_data.get('df', []))
        bot.reply_to(message, f"📊 Matchs analysés : {length}\n🎯 Précision : {round(prec * 100, 2)}%")

    elif text == "📜 Historique":
        try:
            hist = pd.read_csv(FICHIER_HISTORIQUE)
            last_5 = hist.tail(5)
            texte = "📜 *Vos 5 derniers pronostics :*\n\n"
            for _, row in last_5.iterrows():
                texte += (
                    f"⚽ *{row['Match']}*\n"
                    f"📅 {row['Date_Consultation']}\n"
                    f"💡 {row['Pronostic_1N2']} | 🎯 {row['Score_Exact']}\n\n"
                )
            bot.reply_to(message, texte, parse_mode="Markdown")
        except FileNotFoundError:
            bot.reply_to(message, "⚠️ Aucun historique.")

    # ------- PASSER PREMIUM (NEONPAY) -------
    elif text == "⭐ Passer Premium":
        if est_premium(user_id):
            bot.reply_to(
                message,
                "✅ *Tu es déjà Premium !*\n\nProfite bien de tes pronostics illimités 🚀",
                parse_mode="Markdown"
            )
            return

        texte = (
            "⭐ *Abonnement Premium*\n\n"
            "🎁 *Avantages Premium :*\n"
            "  • Pronostics illimités\n"
            "  • Score exact + Over/BTTS\n"
            "  • Support prioritaire\n\n"
            "💳 *Choisis ta formule (Paiement par Telegram Stars 🌟) :*\n\n"
        )
        for key, abo in ABONNEMENTS_STARS.items():
            texte += (
                f"{abo['emoji']} *{abo['nom']}* : "
                f"`{abo['prix_stars']} Stars` "
                f"({abo['duree_jours']} jour(s))\n"
            )

        markup = telebot.types.InlineKeyboardMarkup(row_width=1)
        for key, abo in ABONNEMENTS_STARS.items():
            markup.add(telebot.types.InlineKeyboardButton(
                f"{abo['emoji']} {abo['nom']} - {abo['prix_stars']} Stars",
                callback_data=f"abo_stars|{key}"
            ))

        bot.reply_to(message, texte, parse_mode="Markdown", reply_markup=markup)

    elif text == "⚽ Faire un Pronostic":
        if not peut_faire_pronostic(user_id):
            bot.reply_to(
                message,
                f"⚠️ *Limite atteinte* ({get_limite_jour(user_id)}/jour).\n\n"
                "Passe en ⭐ *Premium* pour des pronostics illimités.",
                parse_mode="Markdown"
            )
            return
        bot.reply_to(message, "✍️ Tapez l'affiche :\n\n`EquipeDom vs EquipeExt`", parse_mode="Markdown")

    elif 'vs' in text.lower():
        if not peut_faire_pronostic(user_id):
            bot.reply_to(
                message,
                f"⚠️ *Limite atteinte* ({get_limite_jour(user_id)}/jour).\n\n"
                "Passe en ⭐ *Premium* !",
                parse_mode="Markdown"
            )
            return
        traiter_prediction(message)

    else:
        bot.reply_to(message, "💡 Utilisez les boutons.")

# =========================================================
# CALLBACK : CHOIX DE L'ABONNEMENT (NEONPAY)
# =========================================================
@bot.callback_query_handler(func=lambda call: call.data.startswith("abo_stars|"))
def traiter_choix_abonnement(call):
    user_id = call.from_user.id
    abo_key = call.data.split("|")[1]

    if abo_key not in ABONNEMENTS_STARS:
        bot.answer_callback_query(call.id, "Formule inconnue.")
        return

    abo = ABONNEMENTS_STARS[abo_key]
    bot.answer_callback_query(call.id, f"{abo['nom']} sélectionné")

    # Envoyer l'invoice Telegram Stars via NeonPay
    import asyncio
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    loop.create_task(neonpay.send_payment(user_id=user_id, stage_id=abo_key))

# =========================================================
# PRÉDICTION (identique)
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

        def trouver_nom_exact(nom_partiel):
            lower_teams = {t.lower(): t for t in teams}
            matches = difflib.get_close_matches(nom_partiel.lower(), lower_teams.keys(), n=1, cutoff=0.4)
            return lower_teams[matches[0]] if matches else nom_partiel

        home_team = trouver_nom_exact(home_input)
        away_team = trouver_nom_exact(away_input)

        if home_team not in team_to_code or away_team not in team_to_code:
            bot.reply_to(message, f"❌ Impossible de trouver '{home_input}' ou '{away_input}' dans la base.")
            return

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

        prob_home_win = np.sum(np.tril(score_matrix, -1))
        prob_draw = np.sum(np.diag(score_matrix))
        prob_away_win = np.sum(np.triu(score_matrix, 1))
        total_prob = prob_home_win + prob_draw + prob_away_win
        p_h, p_d, p_a = prob_home_win / total_prob, prob_draw / total_prob, prob_away_win / total_prob

        max_prob = max(p_h, p_d, p_a)
        if max_prob >= 0.50:
            indice_fiabilite = "🔥 CONFIANCE ÉLEVÉE"
        elif max_prob < 0.40:
            indice_fiabilite = "⚠️ MATCH INCERTAIN / RISQUÉ"
        else:
            indice_fiabilite = "⚖️ CONFIANCE MODÉRÉE"

        under_25 = np.sum([score_matrix[i, j] for i in range(max_goals + 1) for j in range(max_goals + 1) if i + j < 2.5])
        over_25 = 1.0 - under_25
        btts_yes = np.sum([score_matrix[i, j] for i in range(1, max_goals + 1) for j in range(1, max_goals + 1)])
        best_i, best_j = np.unravel_index(np.argmax(score_matrix), score_matrix.shape)

        bulletin = (
            f"🏆 *BULLETIN : {home_team} vs {away_team}*\n\n"
            f"📌 Indice : *{indice_fiabilite}*\n\n"
            f"📊 *1N2 - Probabilités :*\n"
            f"  • Domicile (1) : *{round(p_h * 100, 1)}%* (Cote: {round(1 / p_h, 2)})\n"
            f"  • Nul (N) : *{round(p_d * 100, 1)}%* (Cote: {round(1 / p_d, 2)})\n"
            f"  • Extérieur (2) : *{round(p_a * 100, 1)}%* (Cote: {round(1 / p_a, 2)})\n\n"
            f"⚽ *Tendances de Buts :*\n"
            f"  • Plus de 2.5 buts : *{round(over_25 * 100, 1)}%*\n"
            f"  • Les deux équipes marquent : *{round(btts_yes * 100, 1)}%*\n"
            f"  • 🎯 Score exact : *{best_i} - {best_j}*"
        )

        bot.reply_to(message, bulletin, parse_mode="Markdown")

        record = {
            "Date_Consultation": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "Match": f"{home_team} vs {away_team}",
            "Pronostic_1N2": f"1:{round(p_h * 100, 1)}% N:{round(p_d * 100, 1)}% 2:{round(p_a * 100, 1)}%",
            "Score_Exact": f"{best_i}-{best_j}"
        }
        hist_df = pd.DataFrame([record])
        try:
            existing = pd.read_csv(FICHIER_HISTORIQUE)
            updated = pd.concat([existing, hist_df], ignore_index=True)
            updated.to_csv(FICHIER_HISTORIQUE, index=False)
        except FileNotFoundError:
            hist_df.to_csv(FICHIER_HISTORIQUE, index=False)

        incrementer_compteur(message.from_user.id)

    except Exception as e:
        bot.reply_to(message, f"❌ Erreur lors de l'analyse : {str(e)}")

# =========================================================
# WEBHOOK TELEGRAM
# =========================================================
@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    json_str = request.get_data().decode('UTF-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "OK", 200

# =========================================================
# ROUTE DE BASE
# =========================================================
@app.route('/')
def index():
    return "Bot opérationnel (NeonPay) !", 200

# =========================================================
# LANCEMENT AU BOOT (Render)
# =========================================================
initialiser_tables()
charger_et_entrainer()
