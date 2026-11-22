# telegram_bot/admin/revenus_admin.py
"""
Affichage du tableau de bord des revenus dans le panneau admin (fonctionnalités 103 et 129).

- Résumé du mois en cours (total, nombre de paiements, détail par jour)
- Fichier CSV du mois, prêt pour la comptabilité
"""

import io
from datetime import datetime, timedelta, timezone

from core.revenus import revenus_par_jour, total_revenus, exporter_revenus_csv
from core.utils.logs import log_error

TZ_KINSHASA = timezone(timedelta(hours=1))


def _periode_du_mois():
    aujourd_hui = datetime.now(TZ_KINSHASA).date()
    return aujourd_hui.replace(day=1), aujourd_hui


def construire_resume_revenus():
    """Retourne le texte HTML du résumé du mois en cours."""
    debut, fin = _periode_du_mois()
    nb, total = total_revenus(debut, fin)
    details = revenus_par_jour(debut, fin)

    lignes = [
        "💰 <b>Revenus du mois</b>",
        f"Période : {debut.strftime('%d/%m/%Y')} au {fin.strftime('%d/%m/%Y')}",
        f"Paiements validés : <b>{nb}</b>",
        f"Total : <b>{total:,} CDF</b>".replace(",", " "),
    ]
    if details:
        lignes.append("")
        lignes.append("<b>Détail par jour</b>")
        for d in details[-31:]:
            jour = datetime.strptime(d["jour"], "%Y-%m-%d").strftime("%d/%m")
            lignes.append(f"• {jour} : {d['nb_paiements']} paiement(s), {d['total_cdf']:,} CDF".replace(",", " "))
    else:
        lignes.append("")
        lignes.append("Aucun paiement validé sur cette période.")
    return "\n".join(lignes)


def envoyer_revenus_mois(bot, chat_id):
    """Envoie le résumé du mois puis le fichier CSV. Ne lève jamais d'exception."""
    try:
        bot.send_message(chat_id, construire_resume_revenus(), parse_mode="HTML")
        debut, fin = _periode_du_mois()
        contenu = exporter_revenus_csv(debut, fin).encode("utf-8")
        fichier = io.BytesIO(contenu)
        fichier.name = f"revenus_{debut.strftime('%Y_%m')}.csv"
        bot.send_document(chat_id, fichier, caption="📄 Export comptable du mois (séparateur ;)")
    except Exception as e:
        log_error(message="Impossible d'afficher les revenus", module="ADMIN", exception=e)
        try:
            bot.send_message(chat_id, "❌ Impossible de calculer les revenus pour le moment.")
        except Exception:
            pass
