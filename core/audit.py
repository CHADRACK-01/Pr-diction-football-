import os
import importlib
from core.utils.logs import log_info, log_error, log_warning


def audit_fichiers():
    """Vérifie que tous les fichiers critiques existent."""
    log_info("--- AUDIT DES FICHIERS ---", "AUDIT")
    fichiers_attendus = [
        "app.py",
        "config.py",
        "requirements.txt",
        "core/__init__.py",
        "core/audit.py",
        "core/canal_manager.py",
        "core/daily_matches.py",
        "core/ml_model.py",
        "core/paris_builder.py",
        "core/payments.py",
        "core/prediction.py",
        "core/results_checker.py",
        "core/top_matches.py",
        "core/translations.py",
        "core/utils/__init__.py",
        "core/utils/logs.py",
        "core/utils/markdown.py",
        "core/api/__init__.py",
        "core/api/api_errors.py",
        "core/api/football_data.py",
        "telegram_bot/__init__.py",
        "telegram_bot/admin_handlers.py",
        "telegram_bot/payment_handlers.py",
        "telegram_bot/premium_handlers.py",
        "telegram_bot/prediction_handlers.py",
        "telegram_bot/handlers/__init__.py",
        "telegram_bot/handlers/start.py",
        "telegram_bot/handlers/notifications.py",
        "telegram_bot/handlers/historique.py",
        "telegram_bot/handlers/statistiques.py",
        "telegram_bot/handlers/parrainage.py",
        "telegram_bot/handlers/fallback.py",
        "telegram_bot/admin/__init__.py",
        "telegram_bot/admin/menus.py",
        "telegram_bot/admin/actions.py",
        "telegram_bot/admin/tests_canal.py",
        "users/__init__.py",
        "users/db.py",
        "users/account_base.py",
        "users/account_limits.py",
        "users/account_notifications.py",
        "users/account_referral.py",
        "users/paiements.py",
        "users/admin.py",
        "users/matchs.py",
        "users/model_cache.py"
    ]
    
    manquants = []
    for fichier in fichiers_attendus:
        if not os.path.exists(fichier):
            manquants.append(fichier)
            log_error(f"Fichier MANQUANT : {fichier}", "AUDIT")
        else:
            log_info(f"Fichier OK : {fichier}", "AUDIT")
            
    if not manquants:
        log_info("✅ Tous les fichiers critiques sont présents.", "AUDIT")
    return manquants


def audit_imports():
    """Vérifie que les modules critiques peuvent être importés sans erreur."""
    log_info("--- AUDIT DES IMPORTS ---", "AUDIT")
    modules_a_tester = [
        "core.canal_manager",
        "core.daily_matches",
        "core.ml_model",
        "core.paris_builder",
        "core.payments",
        "core.prediction",
        "core.results_checker",
        "core.top_matches",
        "core.translations",
        "telegram_bot.admin_handlers",
        "telegram_bot.payment_handlers",
        "telegram_bot.premium_handlers",
        "telegram_bot.prediction_handlers",
        "telegram_bot.handlers.__init__",
        "users.__init__"
    ]
    
    for module in modules_a_tester:
        try:
            importlib.import_module(module)
            log_info(f"Import OK : {module}", "AUDIT")
        except Exception as e:
            log_error(f"Import FAILED : {module} - {e}", "AUDIT", e)


def audit_fonctions():
    """Vérifie que les fonctions clés existent dans les modules."""
    log_info("--- AUDIT DES FONCTIONS ---", "AUDIT")
    
    from core import canal_manager
    from core import daily_matches
    from core import prediction
    from core import paris_builder
    from telegram_bot.admin import menus
    
    fonctions_attendues = {
        "canal_manager": ["publier_matchs_sur_canal", "publier_coupons_sur_canal", "publier_message_custom", "publier_teasing"],
        "daily_matches": ["get_matchs_du_jour", "formater_matchs_du_jour"],
        "prediction": ["predire_match", "sauvegarder_historique"],
        "paris_builder": ["generer_coupons_du_jour", "formater_coupon"],
        "menus": ["menu_principal_admin", "menu_admin_bas", "menu_premium", "menu_codes", "menu_parametres", "menu_bdd"]
    }
    
    for module_name, fonctions in fonctions_attendues.items():
        module = locals()[module_name]
        for f in fonctions:
            if hasattr(module, f):
                log_info(f"Fonction OK : {module_name}.{f}", "AUDIT")
            else:
                log_error(f"Fonction MANQUANTE : {module_name}.{f}", "AUDIT")


def audit_base_de_donnees():
    """Vérifie que la base de données répond."""
    log_info("--- AUDIT DE LA BASE DE DONNÉES ---", "AUDIT")
    try:
        from users.db import get_connection
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.fetchone()
        cur.close()
        conn.close()
        log_info("✅ Connexion à la base de données OK.", "AUDIT")
    except Exception as e:
        log_error(f"❌ Connexion à la base de données ÉCHEC : {e}", "AUDIT", e)


def audit_modele():
    """Vérifie que le modèle IA est chargé."""
    log_info("--- AUDIT DU MODÈLE IA ---", "AUDIT")
    try:
        from core.ml_model import global_model_data
        if global_model_data.get('model') is not None:
            log_info(f"✅ Modèle chargé en mémoire ({type(global_model_data['model']).__name__}).", "AUDIT")
        else:
            log_warning("⚠️ Modèle non chargé en mémoire. Tentative de chargement...", "AUDIT")
            from users import charger_modele_cache
            cache = charger_modele_cache()
            if cache:
                log_info("✅ Modèle trouvé dans le cache BDD.", "AUDIT")
            else:
                log_error("❌ Aucun modèle trouvé dans le cache.", "AUDIT")
    except Exception as e:
        log_error(f"❌ Erreur lors de la vérification du modèle : {e}", "AUDIT", e)


def audit_canal():
    """Vérifie la configuration du canal."""
    log_info("--- AUDIT DU CANAL ---", "AUDIT")
    try:
        import config
        if hasattr(config, "CANAL_ID") and config.CANAL_ID:
            log_info(f"✅ CANAL_ID configuré : {config.CANAL_ID}", "AUDIT")
        else:
            log_error("❌ CANAL_ID manquant ou vide.", "AUDIT")
            
        if hasattr(config, "CANAL_LIEN") and config.CANAL_LIEN:
            log_info(f"✅ CANAL_LIEN configuré : {config.CANAL_LIEN}", "AUDIT")
        else:
            log_error("❌ CANAL_LIEN manquant ou vide.", "AUDIT")
    except Exception as e:
        log_error(f"❌ Erreur lors de la vérification du canal : {e}", "AUDIT", e)


def lancer_audit_complet():
    """Lance tous les audits et retourne un résumé."""
    log_info("🚀 DÉBUT DE L'AUDIT COMPLET", "AUDIT")
    
    audit_fichiers()
    audit_imports()
    audit_fonctions()
    audit_base_de_donnees()
    audit_modele()
    audit_canal()
    
    log_info("🏁 FIN DE L'AUDIT COMPLET", "AUDIT")
