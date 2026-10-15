from datetime import datetime, timedelta
import pandas as pd

from core.ml_model import global_model_data
from core.prediction import predire_match


def get_matchs_du_jour(date_cible=None, limite=10):
    """
    Retourne la liste des matchs du jour avec leur pronostic.
    - date_cible : datetime.date (défaut = aujourd'hui)
    - limite : nombre max de matchs retournés
    """
    if not global_model_data:
        return []

    df = global_model_data.get('df')
    if df is None or len(df) == 0:
        return []

    if date_cible is None:
        date_cible = datetime.now().date()

    df_jour = df[df['Date'].dt.date == date_cible].copy()

    if len(df_jour) == 0:
        return []

    df_jour = df_jour.sort_values('Date').head(limite)

    resultats = []
    for _, row in df_jour.iterrows():
        home = row['HomeTeam']
        away = row['AwayTeam']
        competition = row.get('Competition', 'Inconnu')

        try:
            prono = predire_match(home, away)
            if "erreur" in prono:
                continue
        except Exception:
            continue

        resultats.append({
            "home": home,
            "away": away,
            "competition": competition,
            "p_h": prono['p_h'],
            "p_d": prono['p_d'],
            "p_a": prono['p_a'],
            "best_score": prono['best_score'],
            "fiabilite": prono['fiabilite']
        })

    return resultats


def formater_matchs_du_jour(matchs):
    """Formate la liste des matchs pour Telegram."""
    if not matchs:
        return "📅 *Aucun match aujourd'hui* dans nos championnats suivis."

    date_str = datetime.now().strftime("%d/%m/%Y")
    texte = f"📅 *Matchs du jour — {date_str}*\n"
    texte += f"_{len(matchs)} match(s) trouvé(s)_\n\n"

    for i, m in enumerate(matchs, 1):
        p_h = round(m['p_h'] * 100)
        p_d = round(m['p_d'] * 100)
        p_a = round(m['p_a'] * 100)
        best_i, best_j = m['best_score']

        # Déterminer le favori
        max_p = max(p_h, p_d, p_a)
        if max_p == p_h:
            favori = f"🏠 {m['home']}"
        elif max_p == p_a:
            favori = f"✈️ {m['away']}"
        else:
            favori = "⚖️ Match nul"

        texte += (
            f"*{i}. {m['home']} vs {m['away']}*\n"
            f"🏆 _{m['competition']}_\n"
            f"🎯 1: *{p_h}%* | N: *{p_d}%* | 2: *{p_a}%*\n"
            f"⭐ Favori : {favori}\n"
            f"⚽ Score probable : *{best_i}-{best_j}*\n"
            f"📊 {m['fiabilite']}\n\n"
        )

    texte += "💡 _Tapez une affiche pour plus de détails_"
    return texte
