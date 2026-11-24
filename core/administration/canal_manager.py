# core/canal_manager.py
"""
Publication sur le canal.
- Cache CPU : évite de recalculer les pronostics 2x/jour
- Logs enrichis
"""

import time
from datetime import datetime, timezone, timedelta

from config import CANAL_ID
from core.data.daily_matches import get_matchs_du_jour, formater_matchs_du_jour
from core.betting.paris_builder import generer_coupons_du_jour, formater_coupon
from core.utils.logs import log_info, log_error, log_warning

TZ_KINSHASA = timezone(timedelta(hours=1))

# Cache : date (YYYY-MM-DD) -> matchs calculés
_CACHE_MATCHS = {"date": None, "matchs": []}
_CACHE_COUPONS = {"date": None, "data": None}


def _invalider_si_nouveau_jour():
    """Invalide le cache si on change de jour."""
    aujourd_hui = datetime.now(TZ_KINSHASA).strftime("%Y-%m-%d")
    if _CACHE_MATCHS["date"] != aujourd_hui:
        _CACHE_MATCHS["date"] = aujourd_hui
        _CACHE_MATCHS["matchs"] = []
    if _CACHE_COUPONS["date"] != aujourd_hui:
        _CACHE_COUPONS["date"] = aujourd_hui
        _CACHE_COUPONS["data"] = None


def _get_matchs_avec_cache():
    """Retourne les matchs du jour (avec cache par date)."""
    _invalider_si_nouveau_jour()
    if _CACHE_MATCHS["matchs"]:
        return _CACHE_MATCHS["matchs"]
    try:
        matchs = get_matchs_du_jour()
        _CACHE_MATCHS["matchs"] = matchs or []
        return _CACHE_MATCHS["matchs"]
    except Exception as e:
        log_error(
            message="Erreur récupération matchs pour canal",
            module="CANAL",
            exception=e,
        )
        return []


def _get_coupons_avec_cache():
    """Retourne les coupons du jour (avec cache par date)."""
    _invalider_si_nouveau_jour()
    if _CACHE_COUPONS["data"] is not None:
        return _CACHE_COUPONS["data"]
    try:
        data = generer_coupons_du_jour()
        _CACHE_COUPONS["data"] = data
        return data
    except Exception as e:
        log_error(
            message="Erreur génération coupons pour canal",
            module="CANAL",
            exception=e,
        )
        return {"weekend": False, "coupons": []}


def _envoyer_au_canal_securise(bot, texte, dry_run=False, chat_debug=None):
    """Envoie un message au canal (tronqué si besoin)."""
    if not texte:
        log_warning(message="Message vide ignoré", module="CANAL")
        return False

    if len(texte) > 4000:
        texte = texte[:3990] + "\n\n[...Message tronqué...]"

    if dry_run:
        if chat_debug:
            try:
                bot.send_message(chat_debug, f"🧪 MODE TEST (Dry Run)\n\n{texte}")
            except Exception as e:
                log_error(
                    message="Impossible d'envoyer le test",
                    module="CANAL",
                    extra={"chat_id": chat_debug},
                    exception=e,
                )
        return True

    try:
        bot.send_message(CANAL_ID, texte)
        log_info("Message publié sur le canal.", "CANAL")
        return True
    except Exception as e:
        log_error(
            message=f"Impossible de publier sur le canal {CANAL_ID}",
            module="CANAL",
            extra={"chat_id": CANAL_ID},
            exception=e,
        )
        return False


def publier_matchs_sur_canal(bot, dry_run=False, chat_debug=None):
    """Publie les matchs du jour (confiance >= 60%)."""
    matchs = _get_matchs_avec_cache()
    if not matchs:
        log_info("Aucun match à publier sur le canal.", "CANAL")
        if chat_debug and dry_run:
            try:
                bot.send_message(chat_debug, "❌ Aucun match trouvé.")
            except Exception:
                pass
        return False

    matchs_filtres = [m for m in matchs if m.get("dc_pct", 0) >= 0.60]
    if not matchs_filtres:
        log_info("Aucun match avec confiance ≥ 60%.", "CANAL")
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
        log_error(
            message="Erreur formatage matchs canal",
            module="CANAL",
            exception=e,
        )
        return False

    return _envoyer_au_canal_securise(bot, texte, dry_run, chat_debug)


def publier_coupons_sur_canal(bot, dry_run=False, chat_debug=None):
    """Publie un coupon gratuit (modéré de préférence)."""
    data = _get_coupons_avec_cache()
    coupons = data.get("coupons", [])
    if not coupons:
        log_info("Aucun coupon à publier.", "CANAL")
        if chat_debug and dry_run:
            try:
                bot.send_message(chat_debug, "❌ Aucun coupon généré.")
            except Exception:
                pass
        return False

    coupon = next((c for c in coupons if c["niveau"] == "modere"), coupons[0])

    try:
        texte = "🎟️ COUPON DU JOUR (Gratuit) 🎟️\n\n"
        texte += formater_coupon(coupon, langue="fr", montrer_details=False)
        texte += "\n\n⭐ Passe Premium : @MonPronosticFootball_bot"
    except Exception as e:
        log_error(
            message="Erreur formatage coupon canal",
            module="CANAL",
            exception=e,
        )
        return False

    return _envoyer_au_canal_securise(bot, texte, dry_run, chat_debug)


def publier_bilan_veille(bot, texte, dry_run=False, chat_debug=None):
    """Publie le bilan de la veille."""
    if not texte:
        log_warning(message="Bilan vide", module="CANAL")
        return False
    return _envoyer_au_canal_securise(bot, texte, dry_run, chat_debug)


def publier_teasing(bot):
    """Teasing de soirée."""
    texte = (
        "👀 Les matchs de ce soir approchent !\n\n"
        "Nos experts ont analysé les rencontres du jour. "
        "Les abonnés Premium ont déjà leurs pronostics exclusifs.\n\n"
        "👉 Passe Premium : @MonPronosticFootball_bot"
    )
    return _envoyer_au_canal_securise(bot, texte)


def publier_message_custom(bot, texte):
    """Message personnalisé (broadcast admin)."""
    if not texte:
        log_warning(message="Message custom vide", module="CANAL")
        return False

    if len(texte) > 4000:
        texte = texte[:3990] + "\n\n[...Message tronqué...]"

    try:
        bot.send_message(CANAL_ID, texte)
        log_info("Message custom publié sur le canal.", "CANAL")
        return True
    except Exception as e:
        log_error(
            message=f"Impossible de publier message custom sur {CANAL_ID}",
            module="CANAL",
            exception=e,
        )
        return False
