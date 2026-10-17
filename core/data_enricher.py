import pandas as pd
import soccerdata as sd
from datetime import datetime, timedelta

# Dictionnaire de correspondance pour lier les noms d'Understat avec ton bot
# (Understat utilise des noms anglais, il faut les faire correspondre à ton dataset)
MAP_EQUIPES_UNDERSTAT = {
    "Paris Saint Germain": "Paris SG",
    "Manchester City": "Man City",
    "Manchester United": "Man United",
    "Tottenham": "Tottenham",
    "Wolverhampton Wanderers": "Wolves",
    "West Ham": "West Ham",
    "Newcastle United": "Newcastle",
    "Nottingham Forest": "Nott'm Forest",
    "Brighton": "Brighton",
    "Leicester": "Leicester",
    "Leeds": "Leeds",
    "Everton": "Everton",
    "Aston Villa": "Aston Villa",
    "Fulham": "Fulham",
    "Brentford": "Brentford",
    "Crystal Palace": "Crystal Palace",
    "Bournemouth": "Bournemouth",
    "Southampton": "Southampton",
    "Ipswich": "Ipswich",
    # Liga
    "Real Madrid": "Real Madrid",
    "Barcelona": "Barcelona",
    "Atletico Madrid": "Ath Madrid",
    "Athletic Club": "Ath Bilbao",
    "Real Sociedad": "Sociedad",
    "Real Betis": "Betis",
    "Sevilla": "Sevilla",
    "Valencia": "Valencia",
    "Villarreal": "Villarreal",
    "Getafe": "Getafe",
    "Espanyol": "Espanol",
    "Rayo Vallecano": "Vallecano",
    "Celta Vigo": "Celta",
    "Mallorca": "Mallorca",
    "Osasuna": "Osasuna",
    "Granada": "Granada",
    "Alaves": "Alaves",
    "Cadiz": "Cadiz",
    "Las Palmas": "Las Palmas",
    "Girona": "Girona",
    "Valladolid": "Valladolid",
    "Levante": "Levante",
    # Bundesliga
    "Bayern Munich": "Bayern Munich",
    "Borussia Dortmund": "Dortmund",
    "Bayer Leverkusen": "Leverkusen",
    "Eintracht Frankfurt": "Ein Frankfurt",
    "VfB Stuttgart": "Stuttgart",
    "VfL Wolfsburg": "Wolfsburg",
    "Borussia Monchengladbach": "M'gladbach",
    "Union Berlin": "Union Berlin",
    "Freiburg": "Freiburg",
    "Hoffenheim": "Hoffenheim",
    "Augsburg": "Augsburg",
    "Mainz 05": "Mainz",
    "Werder Bremen": "Werder Bremen",
    "VfL Bochum": "Bochum",
    "FC Koln": "FC Koln",
    "Darmstadt": "Darmstadt",
    "Heidenheim": "Heidenheim",
    # Serie A
    "Roma": "Roma",
    "Lazio": "Lazio",
    "Juventus": "Juventus",
    "Milan": "Milan",
    "Inter": "Inter",
    "Napoli": "Napoli",
    "Fiorentina": "Fiorentina",
    "Atalanta": "Atalanta",
    "Bologna": "Bologna",
    "Torino": "Torino",
    "Udinese": "Udinese",
    "Sassuolo": "Sassuolo",
    "Empoli": "Empoli",
    "Lecce": "Lecce",
    "Verona": "Verona",
    "Cagliari": "Cagliari",
    "Genoa": "Genoa",
    "Salernitana": "Salernitana",
    "Frosinone": "Frosinone",
    "Monza": "Monza",
    # Ligue 1
    "Marseille": "Marseille",
    "Lyon": "Lyon",
    "Monaco": "Monaco",
    "Lille": "Lille",
    "Nice": "Nice",
    "Rennes": "Rennes",
    "Lens": "Lens",
    "Reims": "Reims",
    "Montpellier": "Montpellier",
    "Nantes": "Nantes",
    "Brest": "Brest",
    "Strasbourg": "Strasbourg",
    "Toulouse": "Toulouse",
    "Metz": "Metz",
    "Le Havre": "Le Havre",
    "Clermont Foot": "Clermont",
    "Lorient": "Lorient",
}

def recuperer_xg_understat(ligues=None):
    """
    Récupère les données xG d'Understat via soccerdata.
    Ligues dispo: 'ENG-Premier League', 'ESP-La Liga', 'GER-Bundesliga', 'ITA-Serie A', 'FRA-Ligue 1'
    """
    if ligues is None:
        ligues = ['ENG-Premier League', 'ESP-La Liga', 'GER-Bundesliga', 'ITA-Serie A', 'FRA-Ligue 1']
    
    print(f"📥 Récupération des xG pour : {ligues}...")
    
    try:
        # On demande les 5 dernières saisons (2019-2024 environ)
        understat = sd.Understat(leagues=ligues, seasons=range(2019, 2025))
        df_xg = understat.read_team_match_stats()
        
        # Understat retourne un MultiIndex, on le remet à plat
        df_xg = df_xg.reset_index()
        
        # On garde seulement les colonnes utiles
        cols = ['date', 'home_team', 'away_team', 'home_xg', 'away_xg']
        df_xg = df_xg[[c for c in cols if c in df_xg.columns]]
        
        # Normalisation des noms d'équipes
        df_xg['home_team'] = df_xg['home_team'].map(lambda x: MAP_EQUIPES_UNDERSTAT.get(x, x))
        df_xg['away_team'] = df_xg['away_team'].map(lambda x: MAP_EQUIPES_UNDERSTAT.get(x, x))
        
        # Conversion de la date au format YYYY-MM-DD
        df_xg['date'] = pd.to_datetime(df_xg['date']).dt.date
        
        print(f"✅ {len(df_xg)} matchs avec xG récupérés.")
        return df_xg
        
    except Exception as e:
        print(f"❌ Erreur lors de la récupération des xG : {e}")
        return pd.DataFrame()

def calculer_xg_moyens(df_matchs, df_xg, fenetre=5):
    """
    Calcule la moyenne des xG et xGA (Expected Goals Against) sur les N derniers matchs
    pour chaque équipe avant chaque match.
    """
    if df_xg.empty or df_matchs.empty:
        return df_matchs
    
    df_matchs = df_matchs.copy()
    df_matchs['Date'] = pd.to_datetime(df_matchs['Date']).dt.date
    
    # On trie les données xG par date
    df_xg = df_xg.sort_values('date')
    
    # Initialisation des colonnes
    df_matchs['Home_xG_Avg'] = 0.0
    df_matchs['Home_xGA_Avg'] = 0.0
    df_matchs['Away_xG_Avg'] = 0.0
    df_matchs['Away_xGA_Avg'] = 0.0
    
    # Fonction pour calculer la moyenne d'une équipe
    def get_moyenne(equipe, date_match, est_domicile):
        # On récupère les matchs de l'équipe AVANT la date du match
        if est_domicile:
            hist = df_xg[(df_xg['home_team'] == equipe) & (df_xg['date'] < date_match)]
            xg = hist['home_xg'].tail(fenetre).mean()
            xga = hist['away_xg'].tail(fenetre).mean()
        else:
            hist = df_xg[(df_xg['away_team'] == equipe) & (df_xg['date'] < date_match)]
            xg = hist['away_xg'].tail(fenetre).mean()
            xga = hist['home_xg'].tail(fenetre).mean()
        
        return (xg if pd.notna(xg) else 1.2, xga if pd.notna(xga) else 1.2)
    
    print("🧮 Calcul des moyennes xG glissantes (cela peut prendre quelques minutes)...")
    for idx, row in df_matchs.iterrows():
        h_xg, h_xga = get_moyenne(row['HomeTeam'], row['Date'], True)
        a_xg, a_xga = get_moyenne(row['AwayTeam'], row['Date'], False)
        
        df_matchs.at[idx, 'Home_xG_Avg'] = h_xg
        df_matchs.at[idx, 'Home_xGA_Avg'] = h_xga
        df_matchs.at[idx, 'Away_xG_Avg'] = a_xg
        df_matchs.at[idx, 'Away_xGA_Avg'] = a_xga
    
    print("✅ Calcul des xG terminé.")
    return df_matchs
