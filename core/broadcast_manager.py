import threading
import time
from core.utils.logs import log_info, log_error


def lancer_broadcast_async(bot, users, texte, admins, canal=False):
    """Lance le broadcast dans un thread séparé."""
    def _worker():
        log_info(f"Début du broadcast pour {len(users)} utilisateurs...", "BROADCAST")
        
        succes = 0
        echecs = 0
        
        # 1. Envoi aux utilisateurs
        for uid in users:
            try:
                bot.send_message(uid, f"📢 ANNONCE\n\n{texte}")
                succes += 1
                time.sleep(0.05)
            except Exception as e:
                echecs += 1

        log_info(f"Broadcast utilisateurs terminé : {succes} succès, {echecs} échecs.", "BROADCAST")

        # 2. Envoi au Canal si demandé
        erreur_canal = None
        if canal:
            try:
                from core.canal_manager import publier_message_custom
                # On récupère le résultat de la fonction
                resultat = publier_message_custom(bot, f"📢 ANNONCE\n\n{texte}")
                if resultat:
                    log_info("Message broadcast envoyé sur le canal.", "BROADCAST")
                else:
                    erreur_canal = "La fonction publier_message_custom a échoué (voir logs)."
                    log_error(erreur_canal, "BROADCAST")
            except Exception as e:
                erreur_canal = str(e)
                log_error(f"Erreur envoi broadcast canal : {e}", "BROADCAST")

        # 3. Récapitulatif aux admins
        recap = f"📢 Récapitulatif broadcast :\n\n✅ Envoyés : {succes}\n❌ Échecs : {echecs}"
        if canal:
            if erreur_canal:
                recap += f"\n⚠️ Canal : ÉCHEC\nRaison : {erreur_canal}"
            else:
                recap += "\n📢 Envoyé sur le Canal : OUI"
            
        for a in admins:
            try:
                bot.send_message(a['user_id'], recap)
            except Exception:
                pass

    thread = threading.Thread(target=_worker)
    thread.daemon = True
    thread.start()
