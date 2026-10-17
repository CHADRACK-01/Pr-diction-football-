import threading
import time
import telebot

def lancer_broadcast_async(bot, users, texte, admins, canal=False):
    """Lance le broadcast dans un thread séparé pour ne pas bloquer le bot."""
    def _worker():
        succes = 0
        echecs = 0
        
        # 1. Envoi aux utilisateurs
        for uid in users:
            try:
                bot.send_message(uid, f"📢 ANNONCE\n\n{texte}")
                succes += 1
                time.sleep(0.05) # Évite le flood limit de Telegram
            except Exception:
                echecs += 1

        # 2. Envoi au Canal si demandé
        if canal:
            from core.canal_manager import publier_message_custom
            publier_message_custom(bot, f"📢 **ANNONCE** 📢\n\n{texte}")

        # 3. Récapitulatif aux admins
        recap = f"📢 **Récapitulatif broadcast** :\n\n✅ Envoyés : {succes}\n❌ Échecs : {echecs}"
        if canal:
            recap += "\n📢 Envoyé sur le Canal : OUI"
            
        for a in admins:
            try:
                bot.send_message(a['user_id'], recap, parse_mode='Markdown')
            except Exception:
                pass

    thread = threading.Thread(target=_worker)
    thread.daemon = True
    thread.start()
