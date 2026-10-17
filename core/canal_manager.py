import time
from config import CANAL_ID
from core.daily_matches import get_matchs_du_jour, formater_matchs_du_jour


def _envoyer_au_canal_securise(bot, texte):
    """Envoie un message sur le canal en le découpant s'il est trop long."""
    limite = 4000
    try:
        if len(texte) <= limite:
            bot.send_message(CANAL_ID, texte, parse_mode='Markdown')
        else:
            morceaux = [texte[i:i+limite] for i in range(0, len(texte), limite)]
            for morceau in morceaux:
                bot.send_message(CANAL_ID, morceau, parse_mode='Markdown')
                time.sleep(0.5) # Pause anti-flood
        return True
    except Exception as e:
        print(f"❌ Erreur envoi canal : {e}")
        return False


def publier_matchs_sur_canal(bot):
    """Récupère les matchs du jour et les publie sur le canal Telegram."""
    print("🤖 Tentative de publication des matchs sur le canal...")
    try:
        matchs = get_matchs_du_jour()
        if not matchs:
            print("❌ Aucun match trouvé pour aujourd'hui.")
            return

        # On filtre les matchs avec une cote >= 1.30 (déjà fait dans get_matchs_du_jour, mais sécurité)
        matchs_filtres = []
        for m in matchs:
            analyse = m.get('analyse_pari')
            if analyse and analyse['cote_bot'] >= 1.30:
                matchs_filtres.append(m)
                
        if not matchs_filtres:
            print("⏸️ Aucun match avec cote ≥ 1.30 aujourd'hui. Pas de publication.")
            return

        texte = "🔥 **LES MATCHS DU JOUR** 🔥\n\n"
        texte += formater_matchs_du_jour(matchs_filtres, langue="fr", est_premium=True)
        texte += "\n\n👉 Rejoignez le bot pour vos pronostics : @MonPronosticFootball_bot"
        
        if _envoyer_au_canal_securise(bot, texte):
            print("✅ Publication des matchs sur le canal réussie !")
            
    except Exception as e:
        print(f"❌ Erreur publication canal : {e}")


def publier_message_custom(bot, texte):
    """Permet aux admins d'envoyer un message personnalisé sur le canal."""
    return _envoyer_au_canal_securise(bot, texte)


def publier_teasing(bot):
    """Publie un message de teasing à 17h pour inciter au Premium."""
    print("🤖 Tentative de publication du teasing sur le canal...")
    try:
        texte = (
            "👀 **Les matchs de ce soir approchent !**\n\n"
            "Nos experts ont analysé les rencontres du jour. "
            "Les abonnés Premium ont déjà leurs pronostics exclusifs et les analyses complètes.\n\n"
            "👉 Passe Premium sur le bot pour ne rien rater : @MonPronosticFootball_bot"
        )
        if _envoyer_au_canal_securise(bot, texte):
            print("✅ Publication du teasing réussie !")
    except Exception as e:
        print(f"❌ Erreur teasing canal : {e}")


def publier_bilan_veille(bot, texte):
    """Publie le bilan des résultats de la veille sur le canal."""
    print("🤖 Tentative de publication du bilan de la veille sur le canal...")
    try:
        if _envoyer_au_canal_securise(bot, texte):
            print("✅ Publication du bilan réussie !")
    except Exception as e:
        print(f"❌ Erreur bilan canal : {e}")
