import time
from config import CANAL_ID
from core.daily_matches import get_matchs_du_jour, formater_matchs_du_jour
from core.paris_builder import generer_coupons_du_jour, formater_coupon


def _envoyer_au_canal_securise(bot, texte, dry_run=False, chat_debug=None):
    """
    Envoie un message sur le canal.
    - dry_run=True : n'envoie pas sur le canal, mais renvoie le texte à l'admin.
    - chat_debug : ID du chat admin pour recevoir les erreurs.
    """
    try:
        # 1. Vérification de la taille (Telegram limite à 4096)
        if len(texte) > 4000:
            texte = texte[:3990] + "\n\n[...Message tronqué...]"

        # 2. Mode Test (Dry Run) - On n'envoie rien sur le canal
        if dry_run:
            if chat_debug:
                msg = f"🧪 **MODE TEST (Dry Run)**\n\nVoici ce qui aurait été envoyé sur le canal :\n\n{texte}"
                # On envoie le texte à l'admin pour vérifier le rendu Markdown
                bot.send_message(chat_debug, msg, parse_mode='Markdown')
            return True

        # 3. Mode Production (Envoi réel)
        bot.send_message(CANAL_ID, texte, parse_mode='Markdown')
        return True

    except Exception as e:
        # En cas d'erreur, on log proprement et on prévient l'admin
        erreur_msg = f"❌ ERREUR CANAL : {str(e)}"
        print(erreur_msg)
        if chat_debug:
            try:
                bot.send_message(chat_debug, f"⚠️ *Échec d'envoi sur le canal*\n\nRaison : `{str(e)}`", parse_mode='Markdown')
            except Exception:
                pass
        return False


def publier_matchs_sur_canal(bot, dry_run=False, chat_debug=None):
    try:
        matchs = get_matchs_du_jour()
        if not matchs:
            if chat_debug and dry_run: bot.send_message(chat_debug, "❌ Aucun match trouvé.")
            return False

        matchs_filtres = [m for m in matchs if m.get('analyse_pari') and m['analyse_pari']['cote_bot'] >= 1.30]
        if not matchs_filtres:
            if chat_debug and dry_run: bot.send_message(chat_debug, "⏸️ Aucun match avec cote ≥ 1.30.")
            return False

        texte = "🔥 **LES MATCHS DU JOUR** 🔥\n\n"
        texte += formater_matchs_du_jour(matchs_filtres, langue="fr", est_premium=True)
        texte += "\n\n👉 Rejoignez le bot : @MonPronosticFootball_bot"
        
        return _envoyer_au_canal_securise(bot, texte, dry_run, chat_debug)
    except Exception as e:
        print(f"❌ Erreur interne matchs : {e}")
        return False


def publier_coupons_sur_canal(bot, dry_run=False, chat_debug=None):
    try:
        data = generer_coupons_du_jour()
        coupons = data['coupons']
        if not coupons:
            if chat_debug and dry_run: bot.send_message(chat_debug, "❌ Aucun coupon généré.")
            return False

        coupon_a_publier = next((c for c in coupons if c['niveau'] == 'modere'), coupons[0])
        texte = "🎟️ **COUPON DU JOUR (Gratuit)** 🎟️\n\n"
        texte += formater_coupon(coupon_a_publier, langue="fr", montrer_details=False)
        texte += "\n\n⭐ Passe Premium sur le bot : @MonPronosticFootball_bot"
        
        return _envoyer_au_canal_securise(bot, texte, dry_run, chat_debug)
    except Exception as e:
        print(f"❌ Erreur interne coupons : {e}")
        return False


def publier_bilan_veille(bot, texte, dry_run=False, chat_debug=None):
    return _envoyer_au_canal_securise(bot, texte, dry_run, chat_debug)
