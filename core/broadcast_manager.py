import threading
import time
from core.utils.logs import log_info, log_error, log_warning


def lancer_broadcast_async(bot, users, texte, admins, canal=False):
    """
    Lance le broadcast dans un thread séparé pour ne pas bloquer le bot.
    - users : liste des IDs utilisateurs à qui envoyer
    - texte : le message à diffuser
    - admins : liste des admins pour le récapitulatif
    - canal : booléen, si True, envoie aussi sur le canal
    """
    def _worker():
        log_info(f"Début du broadcast pour {len(users)} utilisateurs...", "BROADCAST")
        
        succes = 0
        echecs = 0
        
        # 1. Envoi aux utilisateurs
        for uid in users:
            try:
                bot.send_message(uid, f"📢 ANNONCE\n\n{texte}")
                succes += 1
                time.sleep(0.05)  # Pause pour éviter le flood limit de Telegram
            except Exception as e:
                echecs += 1
                # On ne log pas chaque erreur individuellement pour ne pas spammer les logs
                pass

        log_info(f"Broadcast terminé : {succes} succès, {echecs} échecs.", "BROADCAST")

        # 2. Envoi au Canal si demandé
        if canal:
            try:
                from core.canal_manager import publier_message_custom
                publier_message_custom(bot, f"📢 **ANNONCE** 📢\n\n{texte}")
                log_info("Message broadcast envoyé sur le canal.", "BROADCAST")
            except Exception as e:
                log_error(f"Erreur envoi broadcast canal : {e}", "BROADCAST")

        # 3. Récapitulatif aux admins
        recap = f"📢 **Récapitulatif broadcast** :\n\n✅ Envoyés : {succes}\n❌ Échecs : {echecs}"
        if canal:
            recap += "\n📢 Envoyé sur le Canal : OUI"
            
        for a in admins:
            try:
                bot.send_message(a['user_id'], recap, parse_mode='Markdown')
            except Exception:
                pass

    # Lancement du thread
    thread = threading.Thread(target=_worker)
    thread.daemon = True
    thread.start()
