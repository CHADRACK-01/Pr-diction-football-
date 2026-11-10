import telebot
from users import get_langue
from users.db import get_connection
from core.utils.logs import log_info, log_error, log_warning


def _formater_date(date_match):
    """Formate une date SQLite (YYYY-MM-DD) en JJ/MM/AAAA."""
    if not date_match:
        return "?"
    try:
        # SQLite renvoie parfois "2026-11-10 00:00:00" ou "2026-11-10"
        date_str = str(date_match).split(" ")[0]
        parts = date_str.split("-")
        if len(parts) == 3:
            return f"{parts[2]}/{parts[1]}/{parts[0]}"
        return date_str
    except Exception:
        return str(date_match)


def enregistrer_historique_handlers(bot):
    
    @bot.message_handler(func=lambda m: m.text == "📜 Historique")
    def handle_historique(message):
        user_id = message.from_user.id
        langue = get_langue(user_id)
        
        # Lecture de la BDD
        try:
            conn = get_connection()
            cur = conn.execute("""
                SELECT date_match, home_team, away_team, pronostic_reco, score_reel, est_gagnant
                FROM resultats_pronostics
                ORDER BY date_creation DESC
                LIMIT 5
            """)
            rows = cur.fetchall()
            conn.close()
        except Exception as e:
            log_error(f"Impossible de lire l'historique pour {user_id}", "HISTORIQUE", exception=e)
            bot.reply_to(message, "❌ Impossible de charger l'historique pour le moment. L'admin a été prévenu.")
            return
        
        # Si vide
        if not rows:
            bot.reply_to(message, "📜 Aucun historique pour l'instant.\n\nFais ton premier pronostic avec ⚽ Faire un Pronostic !")
            return
            
        # Formatage
        texte = "📜 **TES 5 DERNIERS PRONOSTICS**\n"
        texte += "━━━━━━━━━━━━━━━━━━━━\n\n"
        
        for i, row in enumerate(rows, 1):
            try:
                date_match, home, away, reco, score, est_gagnant = row
            except Exception as e:
                log_warning(f"Ligne d'historique invalide pour {user_id} : {e}", "HISTORIQUE")
                continue
            
            date_str = _formater_date(date_match)
            
            # Statut
            if est_gagnant == 1:
                statut = "✅ GAGNÉ"
            elif est_gagnant == 0:
                statut = "❌ PERDU"
            else:
                statut = "⏳ En attente"
            
            # Valeurs par défaut si manquantes
            home = home or "?"
            away = away or "?"
            reco = reco or "?"
            score = score or "?"
            
            texte += f"**{i}. {home} vs {away}**\n"
            texte += f"   📅 {date_str}\n"
            texte += f"   🎯 Reco : {reco}\n"
            texte += f"   ⚽ Score : {score}\n"
            texte += f"   {statut}\n\n"
        
        texte += "━━━━━━━━━━━━━━━━━━━━\n"
        texte += "_Pour plus de pronostics, passe Premium 💎_"
        
        try:
            bot.reply_to(message, texte, parse_mode="Markdown")
        except Exception as e:
            log_error(f"Impossible d'envoyer l'historique à {user_id}", "HISTORIQUE", exception=e)
            # Fallback sans Markdown si le Markdown cause une erreur
            try:
                bot.reply_to(message, texte.replace("**", "").replace("_", ""))
            except Exception as e2:
                log_error(f"Impossible d'envoyer l'historique (fallback) à {user_id}", "HISTORIQUE", exception=e2)
