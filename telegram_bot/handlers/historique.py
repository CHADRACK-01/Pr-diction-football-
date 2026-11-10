import telebot
from users import get_langue
from users.db import get_connection
from core.translations import get_text
from core.utils.logs import log_info


def enregistrer_historique_handlers(bot):
    
    @bot.message_handler(func=lambda m: m.text == "📜 Historique")
    def handle_historique(message):
        user_id = message.from_user.id
        langue = get_langue(user_id)
        
        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT date_match, home_team, away_team, pronostic_reco, score_reel, est_gagnant
                        FROM resultats_pronostics
                        ORDER BY date_creation DESC
                        LIMIT 5
                    """)
                    rows = cur.fetchall()
        except Exception as e:
            log_info(f"Erreur lecture historique : {e}", "HISTORIQUE")
            bot.reply_to(message, "❌ Impossible de charger l'historique pour le moment.")
            return
        
        if not rows:
            bot.reply_to(message, "📜 Aucun historique pour l'instant.\n\nFais ton premier pronostic avec ⚽ Faire un Pronostic !")
            return
            
        texte = "📜 **TES 5 DERNIERS PRONOSTICS**\n"
        texte += "━━━━━━━━━━━━━━━━━━━━\n\n"
        
        for i, row in enumerate(rows, 1):
            date_match, home, away, reco, score, est_gagnant = row
            
            # Format de la date
            if date_match:
                try:
                    # SQLite renvoie parfois "2026-11-10 00:00:00" ou "2026-11-10"
                    date_str = str(date_match).split(" ")[0]
                    # On inverse pour avoir JJ/MM/AAAA
                    parts = date_str.split("-")
                    if len(parts) == 3:
                        date_str = f"{parts[2]}/{parts[1]}/{parts[0]}"
                except Exception:
                    date_str = "?"
            else:
                date_str = "?"
            
            # Statut du pronostic
            if est_gagnant == 1:
                statut = "✅ GAGNÉ"
            elif est_gagnant == 0:
                statut = "❌ PERDU"
            else:
                statut = "⏳ En attente"
            
            # Affichage
            texte += f"**{i}. {home} vs {away}**\n"
            texte += f"   📅 {date_str}\n"
            texte += f"   🎯 Reco : {reco}\n"
            texte += f"   ⚽ Score : {score}\n"
            texte += f"   {statut}\n\n"
        
        texte += "━━━━━━━━━━━━━━━━━━━━\n"
        texte += "_Pour plus de pronostics, passe Premium 💎_"
            
        bot.reply_to(message, texte, parse_mode="Markdown")
