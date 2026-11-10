import time
from config import CANAL_ID
from core.daily_matches import get_matchs_du_jour, formater_matchs_du_jour
from core.paris_builder import generer_coupons_du_jour, formater_coupon
from core.utils.logs import log_info, log_error, log_warning


def _envoyer_au_canal_securise(bot, texte, dry_run=False, chat_debug=None):
    """
    Envoie un message sur le canal.
    - Tronque si le texte dépasse 4000 caractères
    - En dry_run : envoie à chat_debug au lieu du canal
    - Logge les erreurs
    """
    if not texte:
        log_warning("Tentative d'envoi d'un message vide sur le canal", "CANAL")
        return False

    if len(texte) > 4000:
        texte = texte[:3990] + "\n\n[...Message tronqué...]"

    if dry_run:
        if chat_debug:
            try:
                bot.send_message(chat_debug, f"🧪 MODE TEST (Dry Run)\n\n{texte}")
            except Exception as e:
                log_error(f"Impossible d'envoyer le message test à {chat_debug}", "CANAL", exception=e)
        return True

    try:
        bot.send_message(CANAL_ID, texte)
        log_info("Message publié sur le canal.", "CANAL")
        return True
    except Exception as e:
        log_error(f"Impossible de publier sur le canal {CANAL_ID}", "CANAL", exception=e)
        return False


def publier_matchs_sur_canal(bot, dry_run=False, chat_debug=None):
    """Publie les matchs du jour sur le canal."""
    try:
        matchs = get_matchs_du_jour()
    except Exception as e:
        log_error("Erreur lors de la récupération des matchs pour le canal", "CANAL", exception=e)
        return False

    if not matchs:
        log_info("Aucun match à publier sur le canal.", "CANAL")
        if chat_debug and dry_run:
            try:
                bot.send_message(chat_debug, "❌ Aucun match trouvé.")
            except Exception:
                pass
        return False

    # On filtre sur la confiance de la Double Chance
    matchs_filtres = [m for m in matchs if m.get('dc_pct', 0) >= 0.60]
    
    if not matchs_filtres:
        log_info("Aucun match avec confiance ≥ 60% à publier.", "CANAL")
        if chat_debug and dry_run:
            try:
                bot.send_message(chat_debug, "⏸️ Aucun match avec confiance ≥ 60%.")
            except Exception:
                pass
        return False

    try:
        texte = "🔥 LES MATCHS DU JOUR 🔥\n\n"
        texte += formater_matchs_du_jour(matchs_filtres, langue="fr", est_premium=True)
        texte += "\n\n👉 Rejoignez le bot : @MonPronosticFootball_bot"
    except Exception as e:
        log_error("Erreur lors du formatage des matchs pour le canal", "CANAL", exception=e)
        return False
    
    return _envoyer_au_canal_securise(bot, texte, dry_run, chat_debug)


def publier_coupons_sur_canal(bot, dry_run=False, chat_debug=None):
    """Publie un coupon gratuit sur le canal."""
    try:
        data = generer_coupons_du_jour()
        coupons = data['coupons']
    except Exception as e:
        log_error("Erreur lors de la génération des coupons pour le canal", "CANAL", exception=e)
        return False

    if not coupons:
        log_info("Aucun coupon à publier sur le canal.", "CANAL")
        if chat_debug and dry_run:
            try:
                bot.send_message(chat_debug, "❌ Aucun coupon généré.")
            except Exception:
                pass
        return False

    # On prend le coupon modéré en priorité (ou le premier disponible)
    coupon_a_publier = next((c for c in coupons if c['niveau'] == 'modere'), None)
    if not coupon_a_publier:
        coupon_a_publier = coupons[0]

    try:
        texte = "🎟️ COUPON DU JOUR (Gratuit) 🎟️\n\n"
        texte += formater_coupon(coupon_a_publier, langue="fr", montrer_details=False)
        texte += "\n\n⭐ Passe Premium sur le bot : @MonPronosticFootball_bot"
    except Exception as e:
        log_error("Erreur lors du formatage du coupon pour le canal", "CANAL", exception=e)
        return False
    
    return _envoyer_au_canal_securise(bot, texte, dry_run, chat_debug)


def publier_bilan_veille(bot, texte, dry_run=False, chat_debug=None):
    """Publie le bilan de la veille sur le canal."""
    if not texte:
        log_warning("Tentative de publier un bilan vide sur le canal", "CANAL")
        return False
    return _envoyer_au_canal_securise(bot, texte, dry_run, chat_debug)


def publier_teasing(bot):
    """Publie un teasing en soirée pour rappeler les pronostics."""
    texte = (
        "👀 Les matchs de ce soir approchent !\n\n"
        "Nos experts ont analysé les rencontres du jour. "
        "Les abonnés Premium ont déjà leurs pronostics exclusifs.\n\n"
        "👉 Passe Premium : @MonPronosticFootball_bot"
    )
    return _envoyer_au_canal_securise(bot, texte, dry_run=False)


def publier_message_custom(bot, texte):
    """
    Permet aux admins d'envoyer un message personnalisé sur le canal.
    Cette fonction est utilisée par le broadcast_manager.
    """
    if not texte:
        log_warning("Tentative d'envoyer un message vide sur le canal", "CANAL")
        return False

    if len(texte) > 4000:
        texte = texte[:3990] + "\n\n[...Message tronqué...]"
    
    try:
        bot.send_message(CANAL_ID, texte)
        log_info("Message personnalisé publié sur le canal.", "CANAL")
        return True
    except Exception as e:
        log_error(f"Impossible d'envoyer le message custom sur le canal {CANAL_ID}", "CANAL", exception=e)
        return False
