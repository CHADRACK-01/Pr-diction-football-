# telegram_bot/ia_dev_handlers.py
"""
Interface Telegram pour le Bot Auto-évolutif.
⚠️ MODE TEST : Toutes les sécurités sur les fichiers sont désactivées.
"""

import telebot
from telebot import types
import os

from users import est_administrateur
from ai_dev.agent import preparer_mise_a_jour
from ai_dev.tester import tester_code
from ai_dev.updater import appliquer_mise_a_jour, AI_DEV_ENABLED
from core.utils.logs import log_info, log_error

PROPOSITIONS_IA = {}

def enregistrer_ai_dev_handlers(bot):

    @bot.message_handler(commands=['demander'])
    def cmd_demander(message):
        user_id = message.from_user.id
        
        if not est_administrateur(user_id):
            bot.reply_to(message, "⛔ Commande réservée à l'administrateur.")
            return

        # 🔒 Coupure de sécurité : on refuse avant l'appel IA (aucun appel inutile)
        if not AI_DEV_ENABLED:
            bot.reply_to(message, "🚫 Auto-modification désactivée (AI_DEV_ENABLED=false).")
            return
            
        texte = message.text.replace("/demander", "").strip()
        
        if "|" not in texte:
            bot.reply_to(
                message, 
                "⚠️ **Format incorrect.**\n\n"
                "Utilise : `/demander [fichier] | [demande]`\n\n"
                "Exemple : `/demander telegram_bot/payment_handlers.py | Ajoute un bouton X`",
                parse_mode="Markdown"
            )
            return
            
        parties = texte.split("|", 1)
        fichier_cible = parties[0].strip()
        instruction = parties[1].strip()

        # ⚠️ MODE TEST : On ne vérifie plus FICHIERS_AUTORISES (tout est autorisé)
        
        bot.reply_to(message, f"🧠 L'IA réfléchit et génère le code pour `{fichier_cible}`...\n(Environ 10 à 30 secondes)", parse_mode="Markdown")
        
        # Préparation de la MAJ
        succes, message_ia, chemin_test, nouveau_code = preparer_mise_a_jour(fichier_cible, instruction)
        
        if not succes:
            bot.reply_to(message, f"❌ Échec de la génération :\n{message_ia}")
            return
            
        # Test du code généré
        test_ok, message_test = tester_code(chemin_test)
        if not test_ok:
            try: os.remove(chemin_test)
            except: pass
            bot.reply_to(message, f"❌ L'IA a généré du code invalide.\n\n{message_test}\n\n🚫 La mise à jour est annulée.")
            return
            
        # Stockage
        PROPOSITIONS_IA[user_id] = {
            "fichier": fichier_cible,
            "test_file": chemin_test,
            "explication": message_ia
        }
        
        # Boutons
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("✅ Valider et Appliquer", callback_data="ia_ok"),
            types.InlineKeyboardButton("❌ Refuser", callback_data="ia_no")
        )
        
        texte_final = (
            f"🤖 **PROPOSITION DE L'IA**\n\n"
            f"📝 **Ce que je vais changer :**\n{message_ia}\n\n"
            f"🧪 **Tests :** {message_test}\n\n"
            f"📁 Fichier cible : `{fichier_cible}`\n\n"
            f"⚠️ _Attention : Valider va modifier le code source du bot._"
        )
        bot.reply_to(message, texte_final, reply_markup=markup, parse_mode="Markdown")

    @bot.callback_query_handler(func=lambda call: call.data in ["ia_ok", "ia_no"])
    def gerer_validation_ia(call):
        user_id = call.from_user.id
        
        if not est_administrateur(user_id):
            bot.answer_callback_query(call.id, "⛔ Accès refusé.")
            return
            
        prop = PROPOSITIONS_IA.get(user_id)
        if not prop:
            bot.answer_callback_query(call.id, "⚠️ Aucune proposition en cours.")
            return
            
        if call.data == "ia_ok":
            succes, message = appliquer_mise_a_jour(prop["fichier"], prop["test_file"])
            
            if succes:
                bot.answer_callback_query(call.id, "✅ Appliqué !")
                bot.edit_message_text(
                    f"✅ **MISE À JOUR APPLIQUÉE**\n\n{message}\n\n"
                    f"🔄 Render va redémarrer le bot dans quelques secondes pour prendre en compte les changements.",
                    call.message.chat.id, call.message.message_id,
                    parse_mode="Markdown"
                )
            else:
                bot.answer_callback_query(call.id, "❌ Erreur")
                bot.edit_message_text(
                    f"❌ **ÉCHEC DE L'APPLICATION**\n\n{message}",
                    call.message.chat.id, call.message.message_id,
                    parse_mode="Markdown"
                )
        else:
            try:
                os.remove(prop["test_file"])
            except:
                pass
            bot.answer_callback_query(call.id, "❌ Annulé")
            bot.edit_message_text(
                "❌ **Modification annulée.**\nAucun changement n'a été effectué sur le bot.",
                call.message.chat.id, call.message.message_id,
                parse_mode="Markdown"
            )
            
        PROPOSITIONS_IA.pop(user_id, None)
