from datetime import datetime, timezone, timedelta
from core.paris_builder import get_tous_pronostics_disponibles, _meilleure_reco
from core.utils.logs import log_info, log_warning

TZ_KINSHASA = timezone(timedelta(hours=1))

SEUIL_CONFIANCE_MIN = 0.75
NB_MAX_AFFICHES = 10
NB_MIN_AFFICHES = 3


def get_top_affiches(limite=10):
    """
    Retourne les affiches avec la plus forte confiance.
    Filtre : Confiance >= 75% ET Cote >= 1.30.
    """
    matchs = get_tous_pronostics_disponibles()

    if not matchs:
        log_warning("Aucun match disponible pour les top affiches.", "TOP")
        return []

    # Filtre 1 : Confiance >= 75% (sur la Double Chance)
    top = [m for m in matchs if m['reco_pct'] >= SEUIL_CONFIANCE_MIN]

    if not top:
        log_warning(f"Aucun match avec confiance >= {SEUIL_CONFIANCE_MIN*100}%.", "TOP")
        return []

    # Filtre 2 : Cote >= 1.30
    top = [m for m in top if round(1/m['reco_pct'], 2) >= 1.30]

    if not top:
        log_warning("Aucun match avec cote >= 1.30.", "TOP")
        return []

    # Tri par confiance décroissante
    top.sort(key=lambda x: x['reco_pct'], reverse=True)

    log_info(f"{len(top)} top affiches trouvées (limite : {limite}).", "TOP")
    return top[:limite]


def formater_top_affiches(affiches, langue="fr", montrer_details=True):
    """Formate la liste des top affiches pour Telegram avec les 5 marchés."""
    date_str = datetime.now(TZ_KINSHASA).strftime("%d/%m/%Y")

    if not affiches:
        return "Aucune affiche à fort potentiel aujourd'hui."

    texte = f"🎯 **TOP AFFICHES - {date_str}**\n"
    texte += f"Seuil : {int(SEUIL_CONFIANCE_MIN*100)}%+ | Cote : ≥ 1.30\n\n"

    for i, m in enumerate(affiches, 1):
        nom_comp = m.get('nom_competition', m['competition'])
        texte += f"{i}. **{m['home']} vs {m['away']}**\n"
        texte += f"   🏆 {nom_comp}\n"

        if montrer_details:
            texte += f"   🛡️ DC : {m['reco_label']} ({round(m['reco_pct']*100, 1)}%)\n"
            texte += f"   🎯 BTTS : {round(m['btts']*100, 1)}% | 🥅 Over 2.5 : {round(m['over_25']*100, 1)}%\n"
            
            cote = round(1/m['reco_pct'], 2) if m['reco_pct'] > 0 else 0
            texte += f"   💰 Cote estimée : {cote}\n"
            
            analyse = m.get('analyse_pari')
            if analyse and analyse.get('cote_book'):
                texte += f"   🏢 Cote Book : {analyse['cote_book']}\n"
                if analyse.get('is_value'):
                    texte += f"   🔥 VALUE BET !\n"
        else:
            texte += f"   🎯 Reco : {m['reco_label']}\n"

        texte += "\n"

    if not montrer_details:
        texte += "_Passe Premium pour les détails complets (BTTS, Over, Mi-temps, Value Bets)_\n"

    return texte
