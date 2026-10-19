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

    top = [m for m in matchs if m['reco_pct'] >= SEUIL_CONFIANCE_MIN]

    if not top:
        log_warning(f"Aucun match avec confiance >= {SEUIL_CONFIANCE_MIN*100}%.", "TOP")
        return []

    top = [m for m in top if round(1/m['reco_pct'], 2) >= 1.30]

    if not top:
        log_warning("Aucun match avec cote >= 1.30.", "TOP")
        return []

    top.sort(key=lambda x: x['reco_pct'], reverse=True)

    log_info(f"{len(top)} top affiches trouvées (limite : {limite}).", "TOP")
    return top[:limite]


def formater_top_affiches(affiches, langue="fr", montrer_details=True):
    """Formate la liste des top affiches pour Telegram."""
    date_str = datetime.now(TZ_KINSHASA).strftime("%d/%m/%Y")

    if not affiches:
        return "Aucune affiche à fort potentiel aujourd'hui."

    texte = f"🎯 TOP AFFICHES - {date_str}\n"
    texte += f"Seuil : {int(SEUIL_CONFIANCE_MIN*100)}%+ | Cote : ≥ 1.30\n\n"

    for i, m in enumerate(affiches, 1):
        texte += f"{i}. {m['home']} vs {m['away']}\n"
        texte += f"   🏆 {m['competition'].replace('_', ' ').title()}\n"

        if montrer_details:
            texte += f"   🎯 Reco : {m['reco_label']}\n"
            texte += f"   📊 Confiance : {round(m['reco_pct']*100, 1)}%\n"
            cote = round(1/m['reco_pct'], 2) if m['reco_pct'] > 0 else 0
            texte += f"   💰 Cote : {cote}\n"
        else:
            texte += f"   🎯 Reco : {m['reco_label']}\n"

        texte += "\n"

    if not montrer_details:
        texte += "_Passe Premium pour les détails complets_\n"

    return texte
