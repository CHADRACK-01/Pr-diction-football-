# core/top_matches.py
"""
Top affiches (confiance >= 75%).
"""

from datetime import datetime, timezone, timedelta

from core.paris_builder import get_tous_pronostics_disponibles
from core.utils.logs import log_info, log_warning, log_error

TZ_KINSHASA = timezone(timedelta(hours=1))

SEUIL_CONFIANCE_MIN = 0.75
NB_MAX_AFFICHES = 10


def get_top_affiches(limite=10):
    """Retourne les affiches à forte confiance."""
    try:
        matchs = get_tous_pronostics_disponibles()
    except Exception as e:
        log_error(
            message="Impossible de récupérer les pronostics pour top affiches",
            module="TOP",
            exception=e,
        )
        return []

    if not matchs:
        log_warning(message="Aucun match pour top affiches", module="TOP")
        return []

    top = [m for m in matchs if (m.get("reco_pct") or 0) >= SEUIL_CONFIANCE_MIN]
    if not top:
        log_warning(
            message=f"Aucun match avec confiance >= {SEUIL_CONFIANCE_MIN * 100}%",
            module="TOP",
        )
        return []

    try:
        top.sort(key=lambda x: x.get("reco_pct", 0), reverse=True)
    except Exception as e:
        log_error(
            message="Erreur tri top affiches",
            module="TOP",
            exception=e,
        )
        return []

    log_info(
        f"{len(top)} top affiches trouvées",
        module="TOP",
        extra={"total": len(top), "limite": limite},
    )
    return top[:limite]


def formater_top_affiches(affiches, langue="fr", montrer_details=True):
    """Formate les top affiches."""
    date_str = datetime.now(TZ_KINSHASA).strftime("%d/%m/%Y")

    if not affiches:
        return "🏆 Aucune affiche à fort potentiel aujourd'hui."

    texte = f"🎯 **TOP AFFICHES - {date_str}**\n"
    texte += f"Seuil : {int(SEUIL_CONFIANCE_MIN * 100)}%+ | Cote : ≥ 1.30\n\n"

    for i, m in enumerate(affiches, 1):
        try:
            nom_comp = m.get("nom_competition", m.get("competition", "?"))
            texte += f"{i}. **{m.get('home', '?')} vs {m.get('away', '?')}**\n"
            texte += f"   🏆 {nom_comp}\n"

            if montrer_details:
                reco_pct = m.get("reco_pct", 0)
                texte += f"   🛡️ DC : {m.get('reco_label', '?')} ({round(reco_pct * 100, 1)}%)\n"
                texte += (
                    f"   🎯 BTTS : {round(m.get('btts', 0.5) * 100, 1)}% | "
                    f"🥅 Over 2.5 : {round(m.get('over_25', 0.5) * 100, 1)}%\n"
                )
                cote = round(1 / reco_pct, 2) if reco_pct > 0 else 0
                texte += f"   💰 Cote estimée : {cote}\n"
                analyse = m.get("analyse_pari")
                if analyse and analyse.get("cote_book"):
                    texte += f"   🏢 Cote Book : {analyse['cote_book']}\n"
                    if analyse.get("is_value"):
                        texte += "   🔥 VALUE BET !\n"
            else:
                texte += f"   🎯 Reco : {m.get('reco_label', '?')}\n"

            texte += "\n"
        except Exception as e:
            log_warning(
                message="Erreur formatage top affiche",
                module="TOP",
                exception=e,
            )
            continue

    if not montrer_details:
        texte += "_Passe Premium pour les détails complets_\n"

    return texte
