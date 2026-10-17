from datetime import datetime, timezone, timedelta

from core.paris_builder import get_tous_pronostics_disponibles, _meilleure_reco


TZ_KINSHASA = timezone(timedelta(hours=1))


# Seuil minimum pour les top affiches
SEUIL_CONFIANCE_MIN = 0.75
NB_MAX_AFFICHES = 10
NB_MIN_AFFICHES = 3


def get_top_affiches(limite=10):
    """
    Retourne les affiches avec la plus forte confiance.
    Seuil minimum : 75%
    """
    matchs = get_tous_pronostics_disponibles()

    if not matchs:
        return []

    # Filtrer uniquement les matchs à 75%+
    top = [m for m in matchs if m['reco_pct'] >= SEUIL_CONFIANCE_MIN]

    if not top:
        return []

    # Trier par confiance décroissante
    top.sort(key=lambda x: x['reco_pct'], reverse=True)

    return top[:limite]


def formater_top_affiches(affiches, langue="fr", montrer_details=True):
    """Formate la liste des top affiches."""
    date_str = datetime.now(TZ_KINSHASA).strftime("%d/%m/%Y")

    if not affiches:
        return "Aucune affiche a fort potentiel aujourd'hui."

    texte = f"🎯 TOP AFFICHES - {date_str}\n"
    texte += f"_Seuil : {int(SEUIL_CONFIANCE_MIN*100)}%+_\n\n"

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
        texte += "_Passe Premium pour les details complets_\n"

    return texte
