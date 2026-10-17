from config import CANAL_ID
from core.daily_matches import get_matchs_du_jour, formater_matchs_du_jour


def publier_matchs_sur_canal(bot):
    """Récupère les matchs du jour et les publie sur le canal Telegram."""
    print("🤖 Tentative de publication des matchs sur le canal...")
    try:
        matchs = get_matchs_du_jour()
        if not matchs:
            print("❌ Aucun match trouvé pour aujourd'hui.")
            return

        texte = "🔥 **LES MATCHS DU JOUR** 🔥\n\n"
        # On force est_premium=True pour avoir les recommandations sur le canal
        texte += formater_matchs_du_jour(matchs, langue="fr", est_premium=True)
        texte += "\n\n👉 Rejoignez le bot pour vos pronostics : @MonPronosticFootball_bot"
        
        bot.send_message(CANAL_ID, texte, parse_mode='Markdown')
        print("✅ Publication des matchs sur le canal réussie !")
    except Exception as e:
        print(f"❌ Erreur publication canal : {e}")


def publier_message_custom(bot, texte):
    """Permet aux admins d'envoyer un message personnalisé sur le canal."""
    try:
        bot.send_message(CANAL_ID, texte, parse_mode='Markdown')
        return True
    except Exception as e:
        print(f"❌ Erreur envoi message canal : {e}")
        return False


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
        bot.send_message(CANAL_ID, texte, parse_mode='Markdown')
        print("✅ Publication du teasing réussie !")
    except Exception as e:
        print(f"❌ Erreur teasing canal : {e}")


def publier_bilan_veille(bot, texte):
    """Publie le bilan des résultats de la veille sur le canal."""
    print("🤖 Tentative de publication du bilan de la veille sur le canal...")
    try:
        bot.send_message(CANAL_ID, texte, parse_mode='Markdown')
        print("✅ Publication du bilan réussie !")
    except Exception as e:
        print(f"❌ Erreur bilan canal : {e}")
