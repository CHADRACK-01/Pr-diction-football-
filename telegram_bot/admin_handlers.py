import telebot
import io
import csv

from users import est_administrateur, compter_codes_disponibles, get_tous_utilisateurs

from telegram_bot.admin.menus import (
    menu_principal_admin, menu_premium, menu_codes,
    menu_parametres, menu_bdd,
    menu_admin_bas, menu_premium_bas, menu_codes_bas,
    menu_parametres_bas, menu_bdd_bas
)
from telegram_bot.admin.actions import executer_action, executer_action_bas, ADMIN_SESSIONS
from core.utils.logs import log_info, log_error, log_warning


def enregistrer_admin_handlers(bot):

    # =========================================================
    # OUVERTURE DU PANNEAU (Bouton 👑 Panneau Admin et commande /admin)
    # =========================================================
    @bot.message_handler(commands=['admin'])
    @bot.message_handler(func=lambda m: m.text == "👑 Panneau Admin" and est_administrateur(m.from_user.id))
    def cmd_admin(message):
        try:
            if not est_administrateur(message.from_user.id):
                bot.reply_to(message, "Accès refusé.")
                return
        except Exception as e:
            log_error(f"Impossible de vérifier si {message.from_user.id} est admin", "ADMIN", exception=e)
            return
            
        try:
            bot.send_message(
                message.chat.id, 
                "🎛️ PANNEAU ADMIN\n\nChoisis une action :", 
                reply_markup=menu_admin_bas()
            )
        except Exception as e:
            log_error(f"Impossible d'ouvrir le panneau admin pour {message.from_user.id}", "ADMIN", exception=e)

    # =========================================================
    # OUVERTURE DU PANNEAU (Bouton Inline)
    # =========================================================
    @bot.callback_query_handler(func=lambda call: call.data == "open_admin_panel")
    def open_admin_panel_callback(call):
        try:
            if not est_administrateur(call.from_user.id):
                bot.answer_callback_query(call.id, "Accès refusé")
                return
            bot.answer_callback_query(call.id)
            bot.send_message(call.message.chat.id, "🎛️ PANNEAU ADMIN\n\nChoisis une action :", reply_markup=menu_principal_admin())
        except Exception as e:
            log_error(f"Erreur ouverture panneau inline pour {call.from_user.id}", "ADMIN", exception=e)

    # =========================================================
    # GESTIONNAIRE DES BOUTONS INLINE
    # =========================================================
    @bot.callback_query_handler(func=lambda call: call.data.startswith(("admin_", "param_", "bcast_")))
    def handle_admin_callbacks(call):
        try:
            if not est_administrateur(call.from_user.id):
                bot.answer_callback_query(call.id, "Accès refusé")
                return
        except Exception as e:
            log_error(f"Impossible de vérifier admin {call.from_user.id}", "ADMIN", exception=e)
            return
            
        data = call.data
        user_id = call.from_user.id
        
        try:
            bot.answer_callback_query(call.id)
        except Exception as e:
            log_warning(f"Impossible de répondre au callback {call.id} : {e}", "ADMIN")

        try:
            if data == "admin_back":
                ADMIN_SESSIONS.pop(user_id, None)
                bot.edit_message_text("🎛️ PANNEAU ADMIN\n\nChoisis une action :", call.message.chat.id, call.message.message_id, reply_markup=menu_principal_admin())
            elif data == "admin_close":
                ADMIN_SESSIONS.pop(user_id, None)
                bot.delete_message(call.message.chat.id, call.message.message_id)
            elif data == "admin_premium":
                ADMIN_SESSIONS.pop(user_id, None)
                bot.edit_message_text("💎 GESTION PREMIUM", call.message.chat.id, call.message.message_id, reply_markup=menu_premium())
            elif data == "admin_codes":
                ADMIN_SESSIONS.pop(user_id, None)
                try:
                    dispo = compter_codes_disponibles()
                except Exception as e:
                    log_error(f"Impossible de compter les codes disponibles", "ADMIN", exception=e)
                    dispo = "?"
                bot.edit_message_text(f"🎟️ CODES PREMIUM\n\nCodes disponibles : {dispo}", call.message.chat.id, call.message.message_id, reply_markup=menu_codes())
            elif data == "admin_bdd":
                ADMIN_SESSIONS.pop(user_id, None)
                bot.edit_message_text("🗄️ BASE DE DONNÉES", call.message.chat.id, call.message.message_id, reply_markup=menu_bdd())
            elif data == "admin_params":
                ADMIN_SESSIONS.pop(user_id, None)
                bot.edit_message_text("⚙️ PARAMÈTRES", call.message.chat.id, call.message.message_id, reply_markup=menu_parametres())
            else:
                executer_action(bot, call, data, user_id)
        except Exception as e:
            log_error(f"Erreur exécution action '{data}' par {user_id}", "ADMIN", exception=e)

    # =========================================================
    # GESTIONNAIRE DES BOUTONS DU CLAVIER ADMIN (Texte)
    # =========================================================
    @bot.message_handler(func=lambda m: est_administrateur(m.from_user.id) and m.text in [
        "📊 Stats", "👥 Utilisateurs", "💳 Paiements", "🎟️ Codes Premium",
        "🗄️ Base de données", "👑 Admins", "⚙️ Paramètres", "📝 Logs",
        "🚫 Bannis", "📢 Broadcast", "💎 Premium", "🔙 Quitter Admin",
        "🔍 Lancer l'Audit", "📋 Exporter la liste",
        "➕ Ajouter Premium", "➖ Retirer Premium", "🔙 Retour Admin",
        "Gen 10 jours", "Gen 30 jours", "Gen 90 jours", "Gen custom", "👁️ Voir codes dispo",
        "Heure notifs", "Limite Free", "Prix Stars", "Message accueil", "Mode maintenance", "👁️ Voir parametres",
        "Taille BDD", "Detail tables", "🧹 Nettoyer"
    ])
    def handle_admin_buttons_text(message):
        text = message.text
        user_id = message.from_user.id

        try:
            # --- Quitter Admin ---
            if text == "🔙 Quitter Admin":
                from telegram_bot.handlers.start import envoyer_menu_principal
                envoyer_menu_principal(message.chat.id, user_id, bot)
                return

            # --- Retour Admin ---
            if text == "🔙 Retour Admin":
                bot.send_message(message.chat.id, "🎛️ PANNEAU ADMIN", reply_markup=menu_admin_bas())
                return

            # --- Exporter la liste des utilisateurs ---
            if text == "📋 Exporter la liste":
                try:
                    from users import get_liste_utilisateurs
                    liste_complete = get_liste_utilisateurs(limite=100000)
                except Exception as e:
                    log_error("Impossible de récupérer la liste des utilisateurs pour l'export", "ADMIN", exception=e)
                    bot.send_message(message.chat.id, "❌ Impossible de générer le fichier. L'admin a été prévenu.")
                    return

                try:
                    output = io.StringIO()
                    writer = csv.writer(output)
                    writer.writerow(["user_id", "first_name", "username", "status", "date_inscription"])
                    
                    for u in liste_complete:
                        # Nettoyage basique pour éviter les injections CSV
                        first_name = str(u.get('first_name', '') or '').replace('"', "'")
                        username = str(u.get('username', '') or '').replace('"', "'")
                        writer.writerow([u.get('user_id', ''), first_name, username, u.get('status', ''), u.get('date_inscription', '')])
                    
                    fichier_bytes = io.BytesIO(output.getvalue().encode('utf-8'))
                    fichier_bytes.name = "utilisateurs.csv"
                    
                    bot.send_document(message.chat.id, fichier_bytes, caption="📋 Liste complète de tes utilisateurs.")
                except Exception as e:
                    log_error("Impossible de générer le fichier CSV", "ADMIN", exception=e)
                    bot.send_message(message.chat.id, "❌ Erreur lors de la génération du fichier.")
                return

            # --- Audit (SÉCURISÉ) ---
            if text == "🔍 Lancer l'Audit":
                bot.send_message(message.chat.id, "⏳ Lancement de l'audit en arrière-plan... Regarde les logs Render.")
                
                import threading
                def run_audit():
                    try:
                        from core.audit import lancer_audit_complet
                        lancer_audit_complet()
                        bot.send_message(message.chat.id, "✅ Audit terminé ! Regarde les logs Render pour les détails.")
                    except Exception as e:
                        log_error("Erreur pendant l'audit", "ADMIN", exception=e)
                        try:
                            bot.send_message(message.chat.id, "❌ L'audit a échoué. Regarde les logs Render.")
                        except Exception:
                            pass
                        
                threading.Thread(target=run_audit, daemon=True).start()
                return

            # --- Navigation vers les sous-menus (Bascule de clavier) ---
            if text == "⚙️ Paramètres":
                bot.send_message(message.chat.id, "⚙️ PARAMÈTRES", reply_markup=menu_parametres_bas())
                return
            if text == "🎟️ Codes Premium":
                try:
                    dispo = compter_codes_disponibles()
                except Exception as e:
                    log_error("Impossible de compter les codes disponibles", "ADMIN", exception=e)
                    dispo = "?"
                bot.send_message(message.chat.id, f"🎟️ CODES PREMIUM (Dispo : {dispo})", reply_markup=menu_codes_bas())
                return
            if text == "🗄️ Base de données":
                bot.send_message(message.chat.id, "🗄️ BASE DE DONNÉES", reply_markup=menu_bdd_bas())
                return
            if text == "💎 Premium":
                bot.send_message(message.chat.id, "💎 GESTION PREMIUM", reply_markup=menu_premium_bas())
                return

            # --- Exécution des actions ---
            executer_action_bas(bot, message, text, user_id)
            
        except Exception as e:
            log_error(f"Erreur traitement bouton admin '{text}' par {user_id}", "ADMIN", exception=e)

    # =========================================================
    # COMMANDE /annuler
    # =========================================================
    @bot.message_handler(commands=['annuler'])
    def cmd_annuler(message):
        try:
            if not est_administrateur(message.from_user.id): 
                return
            ADMIN_SESSIONS.pop(message.from_user.id, None)
            bot.reply_to(message, "Action annulée.")
        except Exception as e:
            log_error(f"Erreur annulation admin {message.from_user.id}", "ADMIN", exception=e)
