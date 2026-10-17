import pandas as pd
import soccerdata as sd

# Dictionnaire de correspondance pour lier les noms d'Understat avec ton bot
MAP_EQUIPES_UNDERSTAT = {
    "Paris Saint Germain": "Paris SG", "Manchester City": "Man City", "Manchester United": "Man United",
    "Tottenham": "Tottenham", "Wolverhampton Wanderers": "Wolves", "West Ham": "West Ham",
    "Newcastle United": "Newcastle", "Nottingham Forest": "Nott'm Forest", "Brighton": "Brighton",
    "Leicester": "Leicester", "Leeds": "Leeds", "Everton": "Everton", "Aston Villa": "Aston Villa",
    "Fulham": "Fulham", "Brentford": "Brentford", "Crystal Palace": "Crystal Palace",
    "Bournemouth": "Bournemouth", "Southampton": "Southampton", "Ipswich": "Ipswich",
    "Real Madrid": "Real Madrid", "Barcelona": "Barcelona", "Atletico Madrid": "Ath Madrid",
    "Athletic Club": "Ath Bilbao", "Real Sociedad": "Sociedad", "Real Betis": "Betis",
    "Sevilla": "Sevilla", "Valencia": "Valencia", "Villarreal": "Villarreal", "Getafe": "Getafe",
    "Espanyol": "Espanol", "Rayo Vallecano": "Vallecano", "Celta Vigo": "Celta", "Mallorca": "Mallorca",
    "Osasuna": "Osasuna", "Granada": "Granada", "Alaves": "Alaves", "Cadiz": "Cadiz",
    "Las Palmas": "Las Palmas", "Girona": "Girona", "Valladolid": "Valladolid", "Levante": "Levante",
    "Bayern Munich": "Bayern Munich", "Borussia Dortmund": "Dortmund", "Bayer Leverkusen": "Leverkusen",
    "Eintracht Frankfurt": "Ein Frankfurt", "VfB Stuttgart": "Stuttgart", "VfL Wolfsburg": "Wolfsburg",
    "Borussia Monchengladbach": "M'gladbach", "Union Berlin": "Union Berlin", "Freiburg": "Freiburg",
    "Hoffenheim": "Hoffenheim", "Augsburg": "Augsburg", "Mainz 05": "Mainz", "Werder Bremen": "Werder Bremen",
    "VfL Bochum": "Bochum", "FC Koln": "FC Koln", "Darmstadt": "Darmstadt", "Heidenheim": "Heidenheim",
    "Roma": "Roma", "Lazio": "Lazio", "Juventus": "Juventus", "Milan": "Milan", "Inter": "Inter",
    "Napoli": "Napoli", "Fiorentina": "Fiorentina", "Atalanta": "Atalanta", "Bologna": "Bologna",
    "Torino": "Torino", "Udinese": "Udinese", "Sassuolo": "Sassuolo", "Empoli": "Empoli", "Lecce": "Lecce",
    "Verona": "Verona", "Cagliari": "Cagliari", "Genoa": "Genoa", "Salernitana": "Salernitana",
    "Frosinone": "Frosinone", "Monza": "Monza", "Marseille": "Marseille", "Lyon": "Lyon", "Monaco": "Monaco",
    "Lille": "Lille", "Nice": "Nice", "Rennes": "Rennes", "Lens": "Lens", "Reims": "Reims",
    "Montpellier": "Montpellier", "Nantes": "Nantes", "Brest": "Brest", "Strasbourg": "Strasbourg",
    "Toulouse": "Toulouse", "Metz": "Metz", "Le Havre": "Le Havre", "Clermont Foot": "Clermont", "Lorient": "Lorient",
}

def recuperer_xg_understat(ligues=None):
    """Récupère les données xG d'Understat via soccerdata."""
    if ligues is None:
        ligues = ['ENG-Premier League', 'ESP-La Liga', 'GER-Bundesliga', 'ITA-Serie A', 'FRA-Ligue 1']
    
    print(f"📥 Récupération des xG pour : {ligues}...")
    try:
        understat = sd.Understat(leagues=ligues, seasons=range(2019, 2025))
        df_xg = understat.read_team_match_stats().reset_index()
        
        cols = ['date', 'home_team', 'away_team', 'home_xg', 'away_xg']
        df_xg = df_xg[[c for c in cols if c in df_xg.columns]]
        
        df_xg['home_team'] = df_xg['home_team'].map(lambda x: MAP_EQUIPES_UNDERSTAT.get(x, x))
        df_xg['away_team'] = df_xg['away_team'].map(lambda x: MAP_EQUIPES_UNDERSTAT.get(x, x))
        df_xg['date'] = pd.to_datetime(df_xg['date']).dt.date
        
        print(f"✅ {len(df_xg)} matchs avec xG récupérés.")
        return df_xg
    except Exception as e:
        print(f"❌ Erreur lors de la récupération des xG : {e}")
        return pd.DataFrame()

def calculer_xg_moyens(df_matchs, df_xg, fenetre=5):
    """
    Calcule la moyenne des xG et xGA sur les N derniers matchs 
    (Optimisé avec Pandas, ultra rapide).
    """
    if df_xg.empty or df_matchs.empty:
        return df_matchs
    
    df_matchs = df_matchs.copy()
    df_matchs['Date'] = pd.to_datetime(df_matchs['Date']).dt.date
    df_xg['date'] = pd.to_datetime(df_xg['date']).dt.date

    # 1. Création d'un historique complet par équipe (Domicile + Extérieur)
    hist_home = df_xg[['date', 'home_team', 'home_xg', 'away_xg']].rename(
        columns={'home_team': 'Equipe', 'home_xg': 'xG', 'away_xg': 'xGA'}
    )
    hist_away = df_xg[['date', 'away_team', 'away_xg', 'home_xg']].rename(
        columns={'away_team': 'Equipe', 'away_xg': 'xG', 'home_xg': 'xGA'}
    )
    historique = pd.concat([hist_home, hist_away]).sort_values('date')

    # 2. Calcul de la moyenne glissante pour chaque équipe
    historique['xG_Avg'] = historique.groupby('Equipe')['xG'].transform(
        lambda x: x.shift(1).rolling(window=fenetre, min_periods=1).mean()
    )
    historique['xGA_Avg'] = historique.groupby('Equipe')['xGA'].transform(
        lambda x: x.shift(1).rolling(window=fenetre, min_periods=1).mean()
    )
    
    # On remplit les valeurs manquantes par la moyenne de ligue (1.2)
    historique['xG_Avg'] = historique['xG_Avg'].fillna(1.2)
    historique['xGA_Avg'] = historique['xGA_Avg'].fillna(1.2)

    # 3. Fusion avec le dataset de matchs
    # On fusionne pour l'équipe à domicile
    df_matchs = pd.merge(
        df_matchs, 
        historique[['date', 'Equipe', 'xG_Avg', 'xGA_Avg']], 
        left_on=['Date', 'HomeTeam'], 
        right_on=['date', 'Equipe'], 
        how='left'
    ).rename(columns={'xG_Avg': 'Home_xG_Avg', 'xGA_Avg': 'Home_xGA_Avg'}).drop(columns=['date', 'Equipe'])

    # On fusionne pour l'équipe à l'extérieur
    df_matchs = pd.merge(
        df_matchs, 
        historique[['date', 'Equipe', 'xG_Avg', 'xGA_Avg']], 
        left_on=['Date', 'AwayTeam'], 
        right_on=['date', 'Equipe'], 
        how='left'
    ).rename(columns={'xG_Avg': 'Away_xG_Avg', 'xGA_Avg': 'Away_xGA_Avg'}).drop(columns=['date', 'Equipe'])

    # On remplit les NaN restants (matchs très anciens)
    for col in ['Home_xG_Avg', 'Home_xGA_Avg', 'Away_xG_Avg', 'Away_xGA_Avg']:
        df_matchs[col] = df_matchs[col].fillna(1.2)

    print("✅ Calcul des xG terminé (optimisé).")
    return df_matchs
