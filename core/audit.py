import os
import importlib
import requests

from core.utils.logs import log_info, log_error, log_warning
from users.db import get_connection


# =========================================================
# 1. AUDIT DES FICHIERS
# =========================================================
def audit_fichiers():
    log_info("--- 📁 AUDIT DES FICHIERS ---", "AUDIT")
    
    fichiers_attendus = [
        "app.py", "config.py", "requirements.txt",
        "core/__init__.py", "core/audit.py", "core/canal_manager.py",
        "core/daily_matches.py", "core/ml_model.py", "core/nouveau_prediction.py",
        "core/paris_builder.py", "core/payments.py", "core/prediction.py",
        "core/results_checker.py", "core/session.py", "core/top_matches.py",
        "core/translations.py",
        "core/utils/__init__.py", "core/utils/logs.py", "core/utils/markdown.py",
        "core/utils/error_handler.py",
        "core/api/__init__.py", "core/api/bzzoiro.py",
        "core/api/football_data.py", "core/api/manager.py", "core/api/openligadb.py",
        "telegram_bot/__init__.py", "telegram_bot/admin_handlers.py",
        "telegram_bot/payment_handlers.py", "telegram_bot/premium_handlers.py",
        "telegram_bot/prediction_handlers.py",
        "telegram_bot/handlers/__init__.py", "telegram_bot/handlers/start.py",
        "telegram_bot/handlers/notifications.py", "telegram_bot/handlers/historique.py",
        "telegram_bot/handlers/statistiques.py", "telegram_bot/handlers/parrainage.py",
        "telegram_bot/handlers/fallback.py", "telegram_bot/handlers/pronostic.py",
        "telegram_bot/handlers/premium_menu.py",
        "telegram_bot/admin/__init__.py", "telegram_bot/admin/menus.py",
        "telegram_bot/admin/actions.py",
        "users/__init__.py", "users/db.py", "users/account_base.py",
        "users/account_limits.py", "users/account_notifications.py",
        "users/account_referral.py", "users/paiements.py", "users/admin.py",
        "users/matchs.py"
    ]
    
    manquants = []
    for fichier in fichiers_attendus:
        if not os.path.exists(fichier):
            manquants.append(fichier)
            log_error(f"Fichier MANQUANT : {fichier}", "AUDIT")
            
    if not manquants:
        log_info(f"✅ Tous les {len(fichiers_attendus)} fichiers critiques sont présents.", "AUDIT")
    else:
        log_error(f"❌ {len(manquants)} fichier(s) manquant(s).", "AUDIT")


# =========================================================
# 2. AUDIT DES IMPORTS
# =========================================================
def audit_imports():
    log_info("--- 📦 AUDIT DES IMPORTS ---", "AUDIT")
    
    modules_a_tester = [
        "core.canal_manager", "core.daily_matches", "core.ml_model",
        "core.nouveau_prediction", "core.paris_builder", "core.payments",
        "core.prediction", "core.results_checker", "core.session",
        "core.top_matches", "core.translations",
        "telegram_bot.admin_handlers", "telegram_bot.payment_handlers",
        "telegram_bot.premium_handlers", "telegram_bot.prediction_handlers",
        "telegram_bot.handlers", "users"
    ]
    
    erreurs = 0
    for module in modules_a_tester:
        try:
            importlib.import_module(module)
        except ImportError as e:
            erreurs += 1
            log_error(f"Import FAILED : {module} - {e}", "AUDIT")
        except Exception as e:
            erreurs += 1
            log_error(f"Import CRASH : {module}", "AUDIT", exception=e)
            
    if erreurs == 0:
        log_info("✅ Tous les imports critiques fonctionnent.", "AUDIT")


# =========================================================
# 3. AUDIT DES APIs (Bzzoiro, Telegram)
# =========================================================
def audit_apis():
    log_info("--- 📡 AUDIT DES APIs ---", "AUDIT")
    
    import config
    
    # Test Telegram
    try:
        res = requests.get(f"https://api.telegram.org/bot{config.TOKEN}/getMe", timeout=10)
        if res.status_code == 200 and res.json().get("ok"):
            log_info("✅ API Telegram : Token valide.", "AUDIT")
        else:
            log_error(f"❌ API Telegram : Token invalide ou erreur (status {res.status_code}).", "AUDIT")
    except Exception as e:
        log_error("❌ API Telegram : impossible de se connecter", "AUDIT", exception=e)

    # Test Bzzoiro
    try:
        headers = {"Authorization": f"Token {config.BZZOIRO_API_KEY}"}
        res = requests.get("https://sports.bzzoiro.com/api/v2/coverage/", headers=headers, timeout=10)
        if res.status_code == 200:
            log_info("✅ API Bzzoiro : OK.", "AUDIT")
        else:
            log_warning(f"⚠️ API Bzzoiro : Statut {res.status_code}.", "AUDIT")
    except Exception as e:
        log_error("❌ API Bzzoiro : impossible de se connecter", "AUDIT", exception=e)


# =========================================================
# 4. AUDIT DE LA BASE DE DONNÉES (Turso/SQLite)
# =========================================================
def audit_base_de_donnees():
    log_info("--- 🗄️ AUDIT DE LA BASE DE DONNÉES ---", "AUDIT")
    
    try:
        conn = get_connection()
        try:
            # Test simple
            conn.execute("SELECT 1").fetchone()
            
            # Vérification des tables critiques (SQLite/Turso)
            cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cur.fetchall()]
            tables_requises = ["utilisateurs", "models_cache", "paiements_attente", "codes_premium"]
            
            manquantes = [t for t in tables_requises if t not in tables]
            if manquantes:
                log_error(f"❌ Tables manquantes en BDD : {manquantes}", "AUDIT")
            else:
                log_info(f"✅ Connexion BDD OK. {len(tables)} tables détectées.", "AUDIT")
        finally:
            conn.close()
    except Exception as e:
        log_error("Impossible de vérifier la base de données", "AUDIT", exception=e)


# =========================================================
# 5. AUDIT DU MODÈLE IA
# =========================================================
def audit_modele():
    log_info("--- 🧠 AUDIT DU MODÈLE IA ---", "AUDIT")
    
    from core.ml_model import global_model_data
    
    modeles = global_model_data.get('modeles_par_competition')
    if modeles:
        log_info(f"✅ {len(modeles)} modèles par compétition chargés en mémoire.", "AUDIT")
    else:
        log_warning("⚠️ Modèle non chargé en mémoire. Tentative de chargement depuis Turso...", "AUDIT")
        from core.ml_model import charger_et_entrainer
        if charger_et_entrainer():
            modeles = global_model_data.get('modeles_par_competition')
            log_info(f"✅ Modèle chargé : {len(modeles)} compétitions.", "AUDIT")
        else:
            log_error("❌ Impossible de charger le modèle depuis Turso.", "AUDIT")
            
    # Vérification de la précision
    prec = global_model_data.get('precision_moyenne')
    if prec:
        log_info(f"📊 Précision moyenne : {round(prec*100, 2)}%.", "AUDIT")
    
    # Vérification du nombre de matchs
    nb_matchs = global_model_data.get('total_matchs')
    if nb_matchs:
        log_info(f"📊 Matchs d'entraînement : {nb_matchs}.", "AUDIT")


# =========================================================
# 6. AUDIT DE LA CONFIGURATION
# =========================================================
def audit_config():
    log_info("--- ⚙️ AUDIT DE LA CONFIGURATION ---", "AUDIT")
    
    import config
    
    if config.CANAL_ID:
        log_info(f"✅ CANAL_ID configuré : {config.CANAL_ID}", "AUDIT")
    else:
        log_error("❌ CANAL_ID manquant ou vide.", "AUDIT")
        
    if config.CANAL_LIEN:
        log_info(f"✅ CANAL_LIEN configuré : {config.CANAL_LIEN}", "AUDIT")
    else:
        log_error("❌ CANAL_LIEN manquant ou vide.", "AUDIT")
    
    if config.TURSO_URL:
        log_info(f"✅ TURSO_URL configuré ({len(config.TURSO_URL)} caractères).", "AUDIT")
    else:
        log_error("❌ TURSO_URL manquant.", "AUDIT")
    
    if config.TURSO_TOKEN:
        log_info(f"✅ TURSO_TOKEN configuré ({len(config.TURSO_TOKEN)} caractères).", "AUDIT")
    else:
        log_error("❌ TURSO_TOKEN manquant.", "AUDIT")
    
    log_info(f"📋 Mode vitrine : {config.MODE_VITRINE}", "AUDIT")


# =========================================================
# LANCEMENT DE L'AUDIT COMPLET
# =========================================================
def lancer_audit_complet():
    log_info("🚀 DÉBUT DE L'AUDIT COMPLET", "AUDIT")
    
    try:
        audit_fichiers()
        audit_imports()
        audit_apis()
        audit_base_de_donnees()
        audit_modele()
        audit_config()
        log_info("🏁 FIN DE L'AUDIT COMPLET", "AUDIT")
    except Exception as e:
        log_error("Erreur pendant l'audit complet", "AUDIT", exception=e)
