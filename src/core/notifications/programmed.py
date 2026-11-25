"""Préparation et envoi des notifications quotidiennes."""

import time
from datetime import datetime, timezone, timedelta

from core.utils.logs import log_error, log_info, log_warning

TZ_KINSHASA = timezone(timedelta(hours=1))


def formater_conseils_matchs(matchs, maintenant=None):
    maintenant = maintenant or datetime.now(TZ_KINSHASA)
    top_3 = sorted(matchs, key=lambda item: item.get("dc_pct", 0), reverse=True)[:3]
    if not top_3:
        return None

    date_str = maintenant.strftime("%d/%m/%Y")
    lignes = ["👋 <b>BONJOUR ! VOICI MES 3 CONSEILS DU JOUR</b>", f"Date : {date_str}", ""]

    for index, match in enumerate(top_3, start=1):
        label = match.get("dc_label", "1X")
        if label == "1X":
            conseil = f"<b>{match['home']}</b> gagne ou fait match nul"
        elif label == "X2":
            conseil = f"<b>{match['away']}</b> gagne ou fait match nul"
        else:
            conseil = "Il n'y aura pas de match nul"

        fiabilite = round(match.get("dc_pct", 0) * 100, 1)
        lignes.extend([
            f"{index}. <b>{match['home']} vs {match['away']}</b>",
            f"   👉 Mon conseil : {conseil}",
            f"   📊 (Fiabilité : {fiabilite}%)",
            "",
        ])

    lignes.extend(["━━━━━━━━━━━━━━━━━━━━", "💡 <i>Misez max 2% de votre capital par pari.</i>"])
    return "\n".join(lignes)


def envoyer_notifications_matinales(*, bot, mode_test=False, charger_modele=None,
                                   recuperer_matchs=None, recuperer_users=None,
                                   envoyer_message=None, sleep_seconds=0.1):
    if mode_test:
        log_info("Mode Test : envoi de notifications ignoré.", "NOTIFS")
        return 0

    try:
        if charger_modele is not None and not charger_modele():
            return 0

        matchs = recuperer_matchs() if recuperer_matchs else []
        texte = formater_conseils_matchs(matchs)
        if texte is None:
            log_warning("Aucun match pour les notifications du matin.", "NOTIFS")
            return 0

        users = recuperer_users() if recuperer_users else []
        succes = 0
        for user_id in users:
            try:
                if envoyer_message:
                    ok = envoyer_message(user_id, texte)
                else:
                    bot.send_message(user_id, texte, parse_mode="HTML")
                    ok = True
                if ok:
                    succes += 1
            except Exception as e:
                log_error("Impossible d'envoyer une notification quotidienne", "NOTIFS", extra={"user_id": user_id}, exception=e)
            time.sleep(sleep_seconds)

        log_info(f"Notifications du matin envoyées : {succes}", "NOTIFS")
        return succes
    except Exception as e:
        log_error("Erreur envoi notifications quotidiennes", "NOTIFS", exception=e)
        return 0
