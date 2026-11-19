# core/cashout.py
"""
Fonctionnalité 5 : Simulateur de Cash-Out.
Calcule le montant que l'utilisateur récupérerait s'il arrêtait son pari.

Formatage : utilise core.devises.formater_prix pour cohérence avec le reste
du bot (espaces comme séparateur de milliers, symbole de devise).
"""

import os
import requests
from core.devises import formater_prix
from core.utils.logs import log_info, log_warning, log_error

ODDS_API_KEY = os.environ.get("ODDS_API_KEY", "")
BASE_URL = "https://api.the-odds-api.com/v4"


def simuler_cashout(mise, cote_initiale, cote_actuelle):
    """
    Simule le cash-out d'un pari.
    Formule simplifiée : mise * (cote_initiale / cote_actuelle)
    """
    if cote_actuelle <= 0 or cote_initiale <= 0:
        return 0.0

    cashout = mise * (cote_initiale / cote_actuelle)
    return round(cashout, 2)


def get_cote_actuelle(home_team, away_team, sport="soccer_epl", bookmaker="betwinner"):
    """
    Récupère la cote actuelle d'un match via The Odds API.
    (Note : sans API live, on utilise la cote d'avant-match).
    """
    if not ODDS_API_KEY:
        log_warning("Clé ODDS_API_KEY manquante.", "CASHOUT")
        return None

    url = f"{BASE_URL}/sports/{sport}/odds/"
    params = {
        "apiKey": ODDS_API_KEY,
        "regions": "eu",
        "markets": "h2h",
        "bookmakers": bookmaker,
        "oddsFormat": "decimal"
    }

    try:
        res = requests.get(url, params=params, timeout=15)
        if res.status_code != 200:
            return None

        data = res.json()
        for match in data:
            if (match.get("home_team", "").lower() == home_team.lower() and
                match.get("away_team", "").lower() == away_team.lower()):

                for bk in match.get("bookmakers", []):
                    for market in bk.get("markets", []):
                        if market.get("key") == "h2h":
                            for outcome in market.get("outcomes", []):
                                if outcome["name"] == home_team:
                                    return outcome["price"]
        return None

    except Exception as e:
        log_error("Erreur récupération cote actuelle", "CASHOUT", exception=e)
        return None


def formater_cashout(home_team, away_team, mise, cote_initiale, cote_actuelle, cashout):
    """Formate le résultat pour Telegram (HTML).

    Utilise formater_prix pour cohérence (séparateur espace, devise CDF).
    """
    if cashout <= 0:
        return "❌ Impossible de calculer le cash-out."

    gain_initial = mise * cote_initiale
    difference = cashout - mise

    texte = f"💸 <b>SIMULATEUR DE CASH-OUT</b>\n"
    texte += f"━━━━━━━━━━━━━━━━━━━━\n\n"
    texte += f"🏟️ {home_team} vs {away_team}\n\n"
    texte += f"💵 Mise : {formater_prix(mise, 'CDF')}\n"
    texte += f"🎯 Cote initiale : {cote_initiale}\n"
    texte += f"🎯 Cote actuelle : {cote_actuelle}\n\n"
    texte += f"💰 <b>Cash-out actuel : {formater_prix(cashout, 'CDF')}</b>\n\n"
    texte += f"📊 <b>Détail :</b>\n"
    texte += f"• Gain potentiel (si pari gagnant) : {formater_prix(gain_initial, 'CDF')}\n"

    # Différence : formater manuellement car formater_prix ne gère pas le signe
    signe = "+" if difference >= 0 else "−"
    texte += f"• Différence avec la mise : {signe}{formater_prix(abs(difference), 'CDF')}\n\n"

    if cashout > mise:
        texte += f"✅ <i>Tu es en profit. Le cash-out est intéressant.</i>\n"
    elif cashout < mise:
        texte += f"⚠️ <i>Tu perdrais de l'argent en cash-out maintenant. Patiente.</i>\n"
    else:
        texte += f"➖ <i>Tu récupérerais exactement ta mise.</i>\n"

    return texte
