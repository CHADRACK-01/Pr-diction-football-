import telebot
from users import get_langue
from users.db import get_connection
from core.translations import get_text
from core.utils.logs import log_info


def enregistrer_historique_handlers(bot):
    
    @bot.message_handler(func=lambda m: m.text == "#HISTO")
    def handle_historique(message):
        user_id = message.from_user.id
        langue = get_langue(user_id)
        
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT date_match, home_team, away_team, pronostic_reco, score_reel, est_gagnant
                    FROM resultats_pronostics
                    ORDER BY date_creation DESC
                    LIMIT 5
                """)
                rows = cur.fetchall()
        
        if not rows:
            bot.reply_to(message, get_text("historique_vide", langue))
            return
            
        texte = get_text("historique_titre", langue)
        
        for i, row in enumerate(rows, 1):
            date_match, home, away, reco, score, est_gagnant = row
            
            # Format de la date
            date_str = date_match.strftime("%d/%m/%Y") if date_match else "?"
            
            # Statut du pronostic
            if est_gagnant is True:
                statut = "✅ GAGNÉ"
            elif est_gagnant is False:
                statut = "❌ PERDU"
            else:
                statut = "⏳ En attente"
            
            texte += (
                f"{i}. {home} vs {away}\n"
                f"   📅 {date_str}\n"
                f"   🎯 {reco}\n"
                f"   ⚽ Score : {score}\n"
                f"   {statut}\n\n"
            )
            
        bot.reply_to(message, texte)
