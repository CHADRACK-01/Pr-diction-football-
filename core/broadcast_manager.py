# core/broadcast_manager.py
"""
Broadcast asynchrone.
- try/except autour de la boucle utilisateurs
- parse_mode cohérent (Markdown partout)
- Récap toujours envoyé même en cas d'erreur
"""

import threading
import time

from core.utils.logs import log_info, log_error, log_warning


def lancer_broadcast_async(bot, users, texte, admins, canal=False):
    """Lance le broadcast dans un thread séparé."""
    def _worker():
        log_info(f"Broadcast vers {len(users)} utilisateurs...", "BROADCAST")

        succes = 0
        echecs = 0
        echecs_details = []

        # 1. Envoi aux utilisateurs
        for uid in users:
            try:
                bot.send_message(uid, f"📢 ANNONCE\n\n{texte}", parse_mode="Markdown")
                succes += 1
            except Exception as e:
                echecs += 1
                if len(echecs_details) < 5:
                    echecs_details.append(f"User {uid} : {str(e)[:100]}")
            time.sleep(0.05)

        log_info(
            f"Broadcast terminé : {succes} succès, {echecs} échecs",
            "BROADCAST",
            extra={"succes": succes, "echecs": echecs},
        )

        # 2. Envoi au canal
        erreur_canal = None
        if canal:
            try:
                from core.canal_manager import publier_message_custom
                if publier_message_custom(bot, f"📢 ANNONCE\n\n{texte}"):
                    log_info("Message broadcast envoyé sur le canal.", "BROADCAST")
                else:
                    erreur_canal = "publier_message_custom a échoué (voir logs)"
                    log_error(erreur_canal, "BROADCAST")
            except Exception as e:
                erreur_canal = f"Exception canal : {str(e)[:100]}"
                log_error(
                    message="Erreur envoi broadcast canal",
                    module="BROADCAST",
                    exception=e,
                )

        # 3. Récap admins
        recap = (
            f"📢 **RÉCAPITULATIF BROADCAST**\n\n"
            f"✅ Envoyés : {succes}\n"
            f"❌ Échecs : {echecs}\n"
        )
        if echecs_details:
            recap += "\n⚠️ **Détails échecs** :\n"
            for d in echecs_details:
                recap += f"• {d}\n"
            if echecs > 5:
                recap += f"... et {echecs - 5} autres\n"

        if canal:
            if erreur_canal:
                recap += f"\n⚠️ **Canal** : ÉCHEC\nRaison : {erreur_canal}"
            else:
                recap += "\n📢 **Canal** : Envoyé avec succès"

        for a in admins:
            try:
                bot.send_message(a["user_id"], recap, parse_mode="Markdown")
            except Exception as e:
                log_warning(
                    message="Impossible d'envoyer le récap à l'admin",
                    module="BROADCAST",
                    extra={"admin_id": a["user_id"]},
                    exception=e,
                )

        log_info(f"Broadcast terminé (canal={canal})", "BROADCAST")

    thread = threading.Thread(target=_worker, daemon=True)
    thread.start()
