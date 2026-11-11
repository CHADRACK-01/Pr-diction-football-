# core/audit.py
"""
Audit complet du bot :
- Fichiers attendus
- Imports critiques
- 5 APIs externes
- Toutes les tables critiques
- Modèle IA
- Configuration
"""

import os
import importlib
import requests

from core.utils.logs import log_info, log_error, log_warning
from users.db import db_fetchone, db_fetchall


# =========================================================
# 1. AUDIT DES FICHIERS
# =========================================================
FICHIERS_ATTENDUS = [
    "app.py", "config.py", "requirements.txt",
    "core/__init__.py", "core/audit.py", "core/canal_manager.py",
    "core/daily_matches.py", "core/ml_model.py", "core/nouveau_prediction.py",
    "core/paris_builder.py", "core/payments.py", "core/prediction.py",
    "core/results_checker.py", "core/session.py", "core/top_matches.py",
    "core/translations.py",
    "core/utils/__init__.py", "core/utils/logs.py",
    "core/utils/markdown.py", "core/utils/error_handler.py",
    "core/api/__init__.py", "core/api/bzzoiro.py",
    "core/api/football_data.py", "core/api/orchestrator.py",
    "core/api/openligadb.py", "core/api/api_football.py",
    "core/api/thesportsdb.py",
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
    "users/matchs.py",
    "scripts/mettre_a_jour_resultats.py", "scripts/telecharger_matchs.py",
]


def audit_fichiers():
    log_info("--- 📁 AUDIT DES FICHIERS ---", "AUDIT")
    manquants = []
    for fichier in FICHIERS_ATTENDUS:
        if not os.path.exists(fichier):
            manquants.append(fichier)
            log_error(
                message=f"Fichier MANQUANT : {fichier}",
                module="AUDIT",
                extra={"fichier": fichier},
            )

    if not manquants:
        log_info(
            f"✅ {len(FICHIERS_ATTENDUS)} fichiers critiques présents.",
            "AUDIT",
        )
    else:
        log_error(
            message=f"❌ {len(manquants)} fichier(s) manquant(s)",
            module="AUDIT",
            extra={"manquants": manquants},
        )


# =========================================================
# 2. AUDIT DES IMPORTS
# =========================================================
MODULES_A_TESTER = [
    "core.canal_manager", "core.daily_matches", "core.ml_model",
    "core.nouveau_prediction", "core.paris_builder", "core.payments",
    "core.prediction", "core.results_checker", "core.session",
    "core.top_matches", "core.translations",
    "core.api.orchestrator", "core.api.football_data",
    "core.api.bzzoiro", "core.api.openligadb", "core.api.api_football",
    "core.api.thesportsdb",
    "telegram_bot.admin_handlers", "telegram_bot.payment_handlers",
    "telegram_bot.premium_handlers", "telegram_bot.prediction_handlers",
    "telegram_bot.handlers", "users",
]


def audit_imports():
    log_info("--- 📦 AUDIT DES IMPORTS ---", "AUDIT")
    erreurs = 0
    for module in MODULES_A_TESTER:
        try:
            importlib.import_module(module)
        except ImportError as e:
            erreurs += 1
            log_error(
                message=f"Import FAILED : {module}",
                module="AUDIT",
                extra={"module": module},
                exception=e,
            )
        except Exception as e:
            erreurs += 1
            log_error(
                message=f"Import CRASH : {module}",
                module="AUDIT",
                extra={"module": module},
                exception=e,
            )
    if erreurs == 0:
        log_info("✅ Tous les imports critiques fonctionnent.", "AUDIT")


# =========================================================
# 3. AUDIT DES APIs (5 sources)
# =========================================================
def audit_apis():
    log_info("--- 📡 AUDIT DES APIs ---", "AUDIT")
    import config

    # Telegram
    try:
        res = requests.get(
            f"https://api.telegram.org/bot{config.TOKEN}/getMe", timeout=10
        )
        if res.status_code == 200 and res.json().get("ok"):
            log_info("✅ Telegram : token valide.", "AUDIT")
        else:
            log_error(
                message="❌ Telegram : token invalide",
                module="AUDIT",
                api_context={
                    "source": "telegram",
                    "http_status": res.status_code,
                },
            )
    except Exception as e:
        log_error(
            message="❌ Telegram : connexion impossible",
            module="AUDIT",
            exception=e,
        )

    # Bzzoiro
    try:
        from core.api import bzzoiro
        if bzzoiro.tester_api():
            log_info("✅ Bzzoiro : OK.", "AUDIT")
        else:
            log_warning(message="⚠️ Bzzoiro : HS", module="AUDIT")
    except Exception as e:
        log_error(
            message="❌ Bzzoiro : test échoué",
            module="AUDIT",
            exception=e,
        )

    # Football-Data
    try:
        if config.FOOTBALL_DATA_KEY:
            res = requests.get(
                "https://api.football-data.org/v4/competitions",
                headers={"X-Auth-Token": config.FOOTBALL_DATA_KEY},
                timeout=10,
            )
            if res.status_code == 200:
                log_info("✅ Football-Data : OK.", "AUDIT")
            else:
                log_warning(
                    message=f"⚠️ Football-Data : statut {res.status_code}",
                    module="AUDIT",
                    api_context={
                        "source": "football_data",
                        "http_status": res.status_code,
                    },
                )
        else:
            log_warning(
                message="⚠️ Football-Data : clé absente",
                module="AUDIT",
            )
    except Exception as e:
        log_error(
            message="❌ Football-Data : test échoué",
            module="AUDIT",
            exception=e,
        )

    # OpenLigaDB
    try:
        from core.api import openligadb
        if openligadb.tester_api():
            log_info("✅ OpenLigaDB : OK.", "AUDIT")
        else:
            log_warning(message="⚠️ OpenLigaDB : HS", module="AUDIT")
    except Exception as e:
        log_error(
            message="❌ OpenLigaDB : test échoué",
            module="AUDIT",
            exception=e,
        )

    # API-Football
    try:
        from core.api import api_football
        if api_football.tester_api():
            log_info("✅ API-Football : OK.", "AUDIT")
        else:
            log_warning(message="⚠️ API-Football : HS", module="AUDIT")
    except Exception as e:
        log_error(
            message="❌ API-Football : test échoué",
            module="AUDIT",
            exception=e,
        )

    # TheSportsDB
    try:
        from core.api import thesportsdb
        if thesportsdb.tester_api():
            log_info("✅ TheSportsDB : OK.", "AUDIT")
        else:
            log_warning(message="⚠️ TheSportsDB : HS", module="AUDIT")
    except Exception as e:
        log_error(
            message="❌ TheSportsDB : test échoué",
            module="AUDIT",
            exception=e,
        )


# =========================================================
# 4. AUDIT DE LA BASE
# =========================================================
TABLES_REQUISES = [
    "utilisateurs", "matchs", "models_cache", "parametres",
    "administrateurs", "bannis", "logs_admin", "paiements_attente",
    "codes_premium", "resultats_pronostics", "sessions_pronostic",
    "compteurs_jour",
]


def audit_base_de_donnees():
    log_info("--- 🗄️ AUDIT DE LA BASE ---", "AUDIT")
    try:
        row = db_fetchone("SELECT 1")
        if not row:
            log_error(message="❌ DB : SELECT 1 échoue", module="AUDIT")
            return

        rows = db_fetchall("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [r[0] for r in rows] if rows else []

        manquantes = [t for t in TABLES_REQUISES if t not in tables]
        if manquantes:
            log_error(
                message=f"❌ Tables manquantes : {manquantes}",
                module="AUDIT",
                extra={"manquantes": manquantes},
            )
        else:
            log_info(
                f"✅ Connexion DB OK. {len(tables)} tables détectées.",
                "AUDIT",
            )
    except Exception as e:
        log_error(
            message="❌ DB : vérification impossible",
            module="AUDIT",
            exception=e,
        )


# =========================================================
# 5. AUDIT DU MODÈLE
# =========================================================
def audit_modele():
    log_info("--- 🧠 AUDIT DU MODÈLE ---", "AUDIT")
    from core.ml_model import global_model_data, charger_et_entrainer

    modeles = global_model_data.get("modeles_par_competition")
    if not modeles:
        log_warning(
            message="⚠️ Modèle non chargé, tentative de chargement...",
            module="AUDIT",
        )
        if not charger_et_entrainer():
            log_error(
                message="❌ Impossible de charger le modèle",
                module="AUDIT",
            )
            return
        modeles = global_model_data.get("modeles_par_competition")

    if modeles:
        log_info(
            f"✅ {len(modeles)} compétitions chargées en mémoire.",
            "AUDIT",
        )

    prec = global_model_data.get("precision_moyenne")
    if prec:
        log_info(f"📊 Précision moyenne : {round(prec * 100, 2)}%.", "AUDIT")
    else:
        log_warning(
            message="⚠️ Précision non disponible dans le BLOB (pas de valeur inventée)",
            module="AUDIT",
        )

    total = global_model_data.get("total_matchs")
    if total:
        log_info(f"📊 Matchs d'entraînement : {total}.", "AUDIT")
    else:
        log_warning(
            message="⚠️ Total matchs non disponible",
            module="AUDIT",
        )


# =========================================================
# 6. AUDIT CONFIG
# =========================================================
def audit_config():
    log_info("--- ⚙️ AUDIT CONFIG ---", "AUDIT")
    import config

    if config.CANAL_ID:
        log_info(f"✅ CANAL_ID : {config.CANAL_ID}", "AUDIT")
    else:
        log_error(message="❌ CANAL_ID manquant", module="AUDIT")

    if config.CANAL_LIEN:
        log_info(f"✅ CANAL_LIEN : {config.CANAL_LIEN}", "AUDIT")
    else:
        log_error(message="❌ CANAL_LIEN manquant", module="AUDIT")

    if config.TURSO_URL:
        log_info("✅ TURSO_URL configuré.", "AUDIT")
    else:
        log_error(message="❌ TURSO_URL manquant", module="AUDIT")

    if config.TURSO_TOKEN:
        log_info("✅ TURSO_TOKEN configuré.", "AUDIT")
    else:
        log_error(message="❌ TURSO_TOKEN manquant", module="AUDIT")

    if config.ADMIN_ID:
        log_info(f"✅ ADMIN_ID : {config.ADMIN_ID}", "AUDIT")

    log_info(f"📋 Mode vitrine : {config.MODE_VITRINE}", "AUDIT")


# =========================================================
# LANCEMENT
# =========================================================
def lancer_audit_complet():
    log_info("🚀 DÉBUT AUDIT COMPLET", "AUDIT")
    try:
        audit_fichiers()
        audit_imports()
        audit_apis()
        audit_base_de_donnees()
        audit_modele()
        audit_config()
        log_info("🏁 FIN AUDIT COMPLET", "AUDIT")
    except Exception as e:
        log_error(
            message="Erreur pendant l'audit complet",
            module="AUDIT",
            exception=e,
        )
