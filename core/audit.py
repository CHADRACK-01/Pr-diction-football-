# core/audit.py
"""
Script d'audit pour vérifier l'intégrité du projet.
- Vérifie la présence des fichiers critiques
- Vérifie que les modules s'importent sans erreur
- Vérifie la connexion à la base de données
"""

import os
import importlib

from core.utils.logs import log_info, log_error, log_warning

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

FICHIERS_ATTENDUS = [
    "config.py",
    "app.py",
    "core/consultation.py",
    "core/ml_model.py",
    "core/nouveau_prediction.py",
    "core/prediction.py",
    "core/value_bet.py",
    "core/session.py",
    "core/urgence.py",
    "core/audit.py",
    "core/utils/logs.py",
    "users/db.py",
    "users/account_base.py",
    "users/account_limits.py",
    "telegram_bot/consultation_handlers.py",
    "telegram_bot/admin_handlers.py",
    "telegram_bot/payment_handlers.py",
    "telegram_bot/prediction_handlers.py",
    "telegram_bot/handlers/start.py",
    "telegram_bot/handlers/pronostic.py",
    "telegram_bot/handlers/fallback.py",
    "telegram_bot/admin/menus.py",
    "telegram_bot/admin/actions.py",
    "telegram_bot/admin/selection.py",
    "telegram_bot/admin/callbacks.py",
]

MODULES_A_TESTER = [
    "config",
    "core.consultation",
    "core.ml_model",
    "core.nouveau_prediction",
    "core.value_bet",
    "core.session",
    "core.utils.logs",
    "users.db",
    "users.account_base",
    "telegram_bot.consultation_handlers",
    "telegram_bot.admin_handlers",
    "telegram_bot.payment_handlers",
    "telegram_bot.prediction_handlers",
    "telegram_bot.handlers.start",
    "telegram_bot.handlers.pronostic",
    "telegram_bot.handlers.fallback",
    "telegram_bot.handlers",
]


def verifier_fichiers():
    """Vérifie que tous les fichiers critiques existent."""
    manquants = []
    for fichier in FICHIERS_ATTENDUS:
        chemin = os.path.join(RACINE, fichier)
        if not os.path.exists(chemin):
            manquants.append(fichier)
    
    if manquants:
        log_error(f"Fichiers manquants : {', '.join(manquants)}", "AUDIT")
        return False
    log_info("✅ Tous les fichiers critiques sont présents.", "AUDIT")
    return True


def verifier_imports():
    """Vérifie que tous les modules s'importent sans erreur."""
    erreurs = []
    for module in MODULES_A_TESTER:
        try:
            importlib.import_module(module)
        except Exception as e:
            erreurs.append(f"{module} : {e}")
            log_error(f"Échec d'import du module {module}", "AUDIT", exception=e)
    
    if erreurs:
        return False
    log_info("✅ Tous les modules s'importent correctement.", "AUDIT")
    return True


def verifier_base_de_donnees():
    """Vérifie la connexion à la base de données."""
    try:
        from users.db import db_fetchone
        row = db_fetchone("SELECT 1")
        if row and row[0] == 1:
            log_info("✅ Connexion base de données OK.", "AUDIT")
            return True
    except Exception as e:
        log_error("Échec de connexion à la base de données", "AUDIT", exception=e)
    return False


def lancer_audit_complet():
    """Lance l'audit complet du projet."""
    log_info("=== DÉBUT DE L'AUDIT ===", "AUDIT")
    
    res_fichiers = verifier_fichiers()
    res_imports = verifier_imports()
    res_db = verifier_base_de_donnees()
    
    if res_fichiers and res_imports and res_db:
        log_info("✅ AUDIT RÉUSSI : Le projet est sain.", "AUDIT")
        return True
    else:
        log_error("❌ AUDIT ÉCHOUÉ : Des problèmes ont été détectés.", "AUDIT")
        return False
