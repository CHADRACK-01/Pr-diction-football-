# core/comparateur.py
"""
Fonctionnalité 28 : Comparateur Domicile / Extérieur.
Analyse les performances d'une équipe à domicile et à l'extérieur.
"""

from users.db import db_fetchall
from core.utils.logs import log_info, log_error


def analyser_domicile_exterieur(nom_equipe):
    """
    Analyse les performances d'une équipe à domicile et à l'extérieur.
    Retourne un dictionnaire avec les stats des deux configurations.
    """
    try:
        # Stats à domicile
        rows_dom = db_fetchall(
            """
            SELECT fthg, ftag FROM matchs
            WHERE home_team = ? AND fthg IS NOT NULL
            ORDER BY date DESC LIMIT 20
            """,
            params=[nom_equipe],
        )
        
        # Stats à l'extérieur
        rows_ext = db_fetchall(
            """
            SELECT fthg, ftag FROM matchs
            WHERE away_team = ? AND fthg IS NOT NULL
            ORDER BY date DESC LIMIT 20
            """,
            params=[nom_equipe],
        )
    except Exception as e:
        log_error(f"Erreur analyse domicile/extérieur pour {nom_equipe}", "COMPARATEUR", exception=e)
        return None

    # Calcul des stats à domicile
    dom_victoires = 0
    dom_nuls = 0
    dom_defaites = 0
    for fthg, ftag in rows_dom:
        if fthg > ftag: dom_victoires += 1
        elif fthg == ftag: dom_nuls += 1
        else: dom_defaites += 1

    # Calcul des stats à l'extérieur
    ext_victoires = 0
    ext_nuls = 0
    ext_defaites = 0
    for fthg, ftag in rows_ext:
        if ftag > fthg: ext_victoires += 1
        elif ftag == fthg: ext_nuls += 1
        else: ext_defaites += 1

    total_dom = len(rows_dom)
    total_ext = len(rows_ext)

    return {
        "nom": nom_equipe,
        "domicile": {
            "total": total_dom,
            "victoires": dom_victoires,
            "nuls": dom_nuls,
            "defaites": dom_defaites,
            "taux_victoire": round((dom_victoires / total_dom * 100), 1) if total_dom > 0 else 0
        },
        "exterieur": {
            "total": total_ext,
            "victoires": ext_victoires,
            "nuls": ext_nuls,
            "defaites": ext_defaites,
            "taux_victoire": round((ext_victoires / total_ext * 100), 1) if total_ext > 0 else 0
        }
    }


def formater_comparateur(stats):
    """Formate les stats en texte lisible."""
    if not stats:
        return "❌ Impossible d'analyser cette équipe."

    texte = f"🏟️ <b>COMPARATEUR DOMICILE / EXTÉRIEUR</b>\n"
    texte += f"━━━━━━━━━━━━━━━━━━━━\n\n"
    texte += f"⚽ <b>{stats['nom']}</b>\n\n"

    # Domicile
    dom = stats["domicile"]
    texte += f"🏠 <b>À DOMICILE</b> ({dom['total']} matchs)\n"
    texte += f"   ✅ Victoires : {dom['victoires']}\n"
    texte += f"   ➖ Nuls : {dom['nuls']}\n"
    texte += f"   ❌ Défaites : {dom['defaites']}\n"
    texte += f"   🎯 Taux de victoire : {dom['taux_victoire']}%\n\n"

    # Extérieur
    ext = stats["exterieur"]
    texte += f"✈️ <b>À L'EXTÉRIEUR</b> ({ext['total']} matchs)\n"
    texte += f"   ✅ Victoires : {ext['victoires']}\n"
    texte += f"   ➖ Nuls : {ext['nuls']}\n"
    texte += f"   ❌ Défaites : {ext['defaites']}\n"
    texte += f"   🎯 Taux de victoire : {ext['taux_victoire']}%\n\n"

    # Conclusion
    diff = dom['taux_victoire'] - ext['taux_victoire']
    if diff > 20:
        texte += f"💡 <i>Cette équipe est beaucoup plus forte à domicile.</i>\n"
    elif diff < -20:
        texte += f"💡 <i>Cette équipe est étonnamment plus forte à l'extérieur.</i>\n"
    else:
        texte += f"💡 <i>Cette équipe a des performances équilibrées.</i>\n"

    return texte
