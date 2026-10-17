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

        if dry_run:
            if chat_debug:
                bot.send_message(chat_debug, f"🧪 MODE TEST (Dry Run)\n\n{texte}")
            return True

        bot.send_message(CANAL_ID, texte)
        log_info("Message publié sur le canal.", "CANAL")
        return True

    except Exception as e:
        log_error(f"ERREUR CANAL : {str(e)}", "CANAL")
        if chat_debug:
            try:
                bot.send_message(chat_debug, f"⚠️ Échec d'envoi\n\nRaison : {str(e)}")
            except Exception:
                pass
        return False


def publier_matchs_sur_canal(bot, dry_run=False, chat_debug=None):
    try:
        matchs = get_matchs_du_jour()
        if not matchs:
            if chat_debug and dry_run:
                bot.send_message(chat_debug, "❌ Aucun match trouvé.")
            return False

        matchs_filtres = [m for m in matchs if m.get('analyse_pari') and m['analyse_pari']['cote_bot'] >= 1.30]
        if not matchs_filtres:
            if chat_debug and dry_run:
                bot.send_message(chat_debug, "⏸️ Aucun match avec cote ≥ 1.30.")
            return False

        texte = "🔥 LES MATCHS DU JOUR 🔥\n\n"
        texte += formater_matchs_du_jour(matchs_filtres, langue="fr", est_premium=True)
        texte += "\n\n👉 Rejoignez le bot : @MonPronosticFootball_bot"
        
        return _envoyer_au_canal_securise(bot, texte, dry_run, chat_debug)
    except Exception as e:
        log_error(f"Erreur interne matchs : {e}", "CANAL")
        return False


def publier_coupons_sur_canal(bot, dry_run=False, chat_debug=None):
    try:
        data = generer_coupons_du_jour()
        coupons = data['coupons']
        if not coupons:
            if chat_debug and dry_run:
                bot.send_message(chat_debug, "❌ Aucun coupon généré.")
            return False

        coupon_a_publier = next((c for c in coupons if c['niveau'] == 'modere'), coupons[0])
        texte = "🎟️ COUPON DU JOUR (Gratuit) 🎟️\n\n"
        texte += formater_coupon(coupon_a_publier, langue="fr", montrer_details=False)
        texte += "\n\n⭐ Passe Premium sur le bot : @MonPronosticFootball_bot"
        
        return _envoyer_au_canal_securise(bot, texte, dry_run, chat_debug)
    except Exception as e:
        log_error(f"Erreur interne coupons : {e}", "CANAL")
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


def publier_message_custom(bot, texte):
    """
    Permet aux admins d'envoyer un message personnalisé sur le canal.
    Cette fonction est utilisée par le broadcast_manager.
    """
    try:
        bot.send_message(CANAL_ID, texte)
        log_info("Message personnalisé publié sur le canal.", "CANAL")
        return True
    except Exception as e:
        log_error(f"Erreur envoi message custom canal : {e}", "CANAL")
        return False
