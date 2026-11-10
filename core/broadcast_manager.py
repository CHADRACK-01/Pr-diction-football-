import threading
import time
from core.utils.logs import log_info, log_error, log_warning


def lancer_broadcast_async(bot, users, texte, admins, canal=False):
    """
    Lance le broadcast dans un thread séparé.
    - users : liste des user_id à qui envoyer
    - texte : le message à envoyer
    - admins : liste des admins à qui envoyer le récapitulatif
    - canal : True si on doit aussi publier sur le canal
    """
    def _worker():
        log_info(f"Début du broadcast pour {len(users)} utilisateurs...", "BROADCAST")
        
        succes = 0
        echecs = 0
        echecs_details = []
        
        # 1. Envoi aux utilisateurs
        for uid in users:
            try:
                bot.send_message(uid, f"📢 ANNONCE\n\n{texte}")
                succes += 1
                time.sleep(0.05)  # Éviter de se faire rate-limit par Telegram
            except Exception as e:
                echecs += 1
                echecs_details.append(f"User {uid} : {e}")
                # On ne logge pas chaque échec pour éviter de spammer l'admin
                # Mais on garde la trace pour le récapitulatif

        log_info(f"Broadcast utilisateurs terminé : {succes} succès, {echecs} échecs.", "BROADCAST")

        # 2. Envoi au Canal si demandé
        erreur_canal = None
        if canal:
            try:
                from core.canal_manager import publier_message_custom
                resultat = publier_message_custom(bot, f"📢 ANNONCE\n\n{texte}")
                if resultat:
                    log_info("Message broadcast envoyé sur le canal.", "BROADCAST")
                else:
                    erreur_canal = "La fonction publier_message_custom a échoué (voir logs)."
                    log_error(erreur_canal, "BROADCAST")
            except Exception as e:
                erreur_canal = f"Exception lors de l'envoi canal : {e}"
                log_error(erreur_canal, "BROADCAST", exception=e)

        # 3. Récapitulatif aux admins
        recap = f"📢 **RÉCAPITULATIF BROADCAST**\n\n"
        recap += f"✅ Envoyés : {succes}\n"
        recap += f"❌ Échecs : {echecs}\n"
        
        if echecs > 0:
            recap += f"\n⚠️ **Détails des échecs (5 max)** :\n"
            for detail in echecs_details[:5]:
                recap += f"• {detail}\n"
            if len(echecs_details) > 5:
                recap += f"... et {len(echecs_details) - 5} autres\n"
        
        if canal:
            if erreur_canal:
                recap += f"\n⚠️ **Canal** : ÉCHEC\nRaison : {erreur_canal}"
            else:
                recap += "\n📢 **Canal** : Envoyé avec succès"
        
        # Envoi du récapitulatif aux admins
        for a in admins:
            try:
                bot.send_message(a['user_id'], recap, parse_mode="Markdown")
            except Exception as e:
                log_error(f"Impossible d'envoyer le récapitulatif à l'admin {a['user_id']}", "BROADCAST", exception=e)

        log_info(f"Broadcast terminé (canal={canal}, erreur_canal={erreur_canal})", "BROADCAST")

    # Lancement du thread
    thread = threading.Thread(target=_worker, daemon=True)
    thread.start()
