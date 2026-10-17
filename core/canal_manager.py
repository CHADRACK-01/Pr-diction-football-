import time
from config import CANAL_ID
from core.daily_matches import get_matchs_du_jour, formater_matchs_du_jour
from core.paris_builder import generer_coupons_du_jour, formater_coupon


def _envoyer_au_canal_securise(bot, texte):
    """Envoie un message sur le canal en le découpant s'il est trop long."""
    limite = 4000
    try:
        if len(texte) <= limite:
            res = bot.send_message(CANAL_ID, texte, parse_mode='Markdown')
            print(f"✅ Message envoyé au canal (ID: {res.message_id})")
            return True
        else:
            morceaux = [texte[i:i+limite] for i in range(0, len(texte), limite)]
            for morceau in morceaux:
                bot.send_message(CANAL_ID, morceau, parse_mode='Markdown')
                time.sleep(0.5)
            print(f"✅ Message découpé et envoyé au canal en {len(morceaux)} parties")
            return True
    except Exception as e:
        print(f"❌ ERREUR CRITIQUE envoi canal : {e}")
        return False


def publier_matchs_sur_canal(bot):
    """Récupère les matchs du jour et les publie sur le canal Telegram."""
    print("🤖 Tentative de publication des matchs sur le canal...")
    try:
        matchs = get_matchs_du_jour()
        if not matchs:
            print("❌ Aucun match trouvé pour aujourd'hui.")
            return False

        matchs_filtres = [m for m in matchs if m.get('analyse_pari') and m['analyse_pari']['cote_bot'] >= 1.30]
                
        if not matchs_filtres:
            print("⏸️ Aucun match avec cote ≥ 1.30 aujourd'hui. Pas de publication.")
            return False

        texte = "🔥 **LES MATCHS DU JOUR** 🔥\n\n"
        texte += formater_matchs_du_jour(matchs_filtres, langue="fr", est_premium=True)
        texte += "\n\n👉 Rejoignez le bot pour vos pronostics : @MonPronosticFootball_bot"
        
        return _envoyer_au_canal_securise(bot, texte)
            
    except Exception as e:
        print(f"❌ Erreur publication canal : {e}")
        return False


def publier_coupons_sur_canal(bot):
    """Publie les coupons du jour sur le canal (version gratuite avec 1 coupon)."""
    print("🤖 Tentative de publication des coupons sur le canal...")
    try:
        data = generer_coupons_du_jour()
        coupons = data['coupons']
        if not coupons:
            print("❌ Aucun coupon généré.")
            return False

        coupon_a_publier = next((c for c in coupons if c['niveau'] == 'modere'), coupons[0])
        
        texte = "🎟️ **COUPON DU JOUR (Gratuit)** 🎟️\n\n"
        texte += formater_coupon(coupon_a_publier, langue="fr", montrer_details=False)
        texte += "\n\n⭐ Passe Premium sur le bot pour voir les détails et les autres coupons : @MonPronosticFootball_bot"
        
        return _envoyer_au_canal_securise(bot, texte)
    except Exception as e:
        print(f"❌ Erreur publication coupons canal : {e}")
        return False


def publier_message_custom(bot, texte):
    """Permet aux admins d'envoyer un message personnalisé sur le canal."""
    return _envoyer_au_canal_securise(bot, texte)


def publier_teasing(bot):
    """Publie un message de teasing à 17h pour inciter au Premium."""
    try:
        texte = (
            "👀 **Les matchs de ce soir approchent !**\n\n"
            "Nos experts ont analysé les rencontres du jour. "
            "Les abonnés Premium ont déjà leurs pronostics exclusifs.\n\n"
            "👉 Passe Premium sur le bot : @MonPronosticFootball_bot"
        )
        _envoyer_au_canal_securise(bot, texte)
    except Exception as e:
        print(f"❌ Erreur teasing canal : {e}")


def publier_bilan_veille(bot, texte):
    """Publie le bilan des résultats de la veille sur le canal."""
    _envoyer_au_canal_securise(bot, texte)
