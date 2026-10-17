import time
from config import CANAL_ID
from core.daily_matches import get_matchs_du_jour, formater_matchs_du_jour
from core.paris_builder import generer_coupons_du_jour, formater_coupon
from core.utils.logs import log_info, log_error


def _envoyer_au_canal_securise(bot, texte, dry_run=False, chat_debug=None):
    """Envoie un message sur le canal SANS AUCUN Markdown."""
    try:
        if len(texte) > 4000:
            texte = texte[:3990] + "\n\n[...Message tronqué...]"

        # Mode Test (Dry Run)
        if dry_run:
            if chat_debug:
                bot.send_message(chat_debug, f"🧪 MODE TEST (Dry Run)\n\nVoici le message qui sera envoyé :\n\n{texte}")
            return True

        # Mode Production (Envoi réel)
        bot.send_message(CANAL_ID, texte)
        return True

    except Exception as e:
        log_error(f"ERREUR CANAL : {str(e)}", "CANAL")
        if chat_debug:
            try:
                bot.send_message(chat_debug, f"⚠️ Échec d'envoi\n\nRaison : {str(e)}")
            except Exception:
                pass
        return False


def publier_coupons_sur_canal(bot, dry_run=False, chat_debug=None):
    try:
        data = generer_coupons_du_jour()
        coupons = data['coupons']
        
        # ⚠️ DIAGNOSTIC : Si aucun coupon n'est généré, on prévient l'admin
        if not coupons:
            msg = "❌ Aucun coupon généré (pas assez de matchs avec cote ≥ 1.30 aujourd'hui)."
            log_error(msg, "CANAL")
            if chat_debug and dry_run:
                bot.send_message(chat_debug, msg)
            return False

        # On cherche le coupon "modéré" en priorité
        coupon_a_publier = next((c for c in coupons if c['niveau'] == 'modere'), coupons[0])
        
        texte = "🎟️ COUPON DU JOUR (Gratuit) 🎟️\n\n"
        texte += formater_coupon(coupon_a_publier, langue="fr", montrer_details=False)
        texte += "\n\n⭐ Passe Premium sur le bot : @MonPronosticFootball_bot"
        
        return _envoyer_au_canal_securise(bot, texte, dry_run, chat_debug)
    except Exception as e:
        log_error(f"Erreur interne coupons : {e}", "CANAL")
        if chat_debug:
            bot.send_message(chat_debug, f"❌ Erreur interne : {e}")
        return False


def publier_matchs_sur_canal(bot, dry_run=False, chat_debug=None):
    try:
        matchs = get_matchs_du_jour()
        if not matchs:
            msg = "❌ Aucun match trouvé pour aujourd'hui."
            log_error(msg, "CANAL")
            if chat_debug and dry_run:
                bot.send_message(chat_debug, msg)
            return False

        matchs_filtres = [m for m in matchs if m.get('analyse_pari') and m['analyse_pari']['cote_bot'] >= 1.30]
        if not matchs_filtres:
            msg = "⏸️ Aucun match avec cote ≥ 1.30 aujourd'hui."
            log_error(msg, "CANAL")
            if chat_debug and dry_run:
                bot.send_message(chat_debug, msg)
            return False

        texte = "🔥 LES MATCHS DU JOUR 🔥\n\n"
        texte += formater_matchs_du_jour(matchs_filtres, langue="fr", est_premium=True)
        texte += "\n\n👉 Rejoignez le bot : @MonPronosticFootball_bot"
        
        return _envoyer_au_canal_securise(bot, texte, dry_run, chat_debug)
    except Exception as e:
        log_error(f"Erreur interne matchs : {e}", "CANAL")
        if chat_debug:
            bot.send_message(chat_debug, f"❌ Erreur interne : {e}")
        return False


def publier_bilan_veille(bot, texte, dry_run=False, chat_debug=None):
    return _envoyer_au_canal_securise(bot, texte, dry_run, chat_debug)


def publier_teasing(bot):
    try:
        texte = (
            "👀 Les matchs de ce soir approchent !\n\n"
            "Nos experts ont analysé les rencontres du jour. "
            "Les abonnés Premium ont déjà leurs pronostics exclusifs.\n\n"
            "👉 Passe Premium : @MonPronosticFootball_bot"
        )
        _envoyer_au_canal_securise(bot, texte, dry_run=False)
    except Exception as e:
        log_error(f"Erreur teasing : {e}", "CANAL")
