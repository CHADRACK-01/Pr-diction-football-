# core/audit.py
"""
Audit complet et dynamique du bot.
- Vérifie la présence réelle des fichiers
- Teste les imports
- Teste les APIs externes
- Vérifie les tables Turso
- Vérifie la présence et le chargement du modèle IA
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
    "app.py", "config.py", "requirements.txt", "runtime.txt",
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
    "scripts/__init__.py", "scripts/mettre_a_jour_resultats.py", 
    "scripts/telecharger_matchs.py",
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
    "scripts.mettre_a_jour_resultats", "scripts.telecharger_matchs",
]


def audit_imports():
    log_info("--- 📦 AUDIT DES IMPORTS ---", "AUDIT")
    erreurs = 0
    for module in MODULES_A_TESTER:
        try:
            importlib.import_module(module)
        except Exception as e:
            erreurs += 1
            log_error(
                message=f"Import FAILED : {module}",
                module="AUDIT",
                extra={"module": module},
                exception=e,
            )
    if erreurs == 0:
        log_info("✅ Tous les imports critiques fonctionnent.", "AUDIT")


# =========================================================
# 3. AUDIT DES APIs
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
                api_context={"source": "telegram", "http_status": res.status_code},
            )
    except Exception as e:
        log_error("❌ Telegram : connexion impossible", "AUDIT", exception=e)

    # Bzzoiro
    try:
        from core.api import bzzoiro
        if bzzoiro.tester_api():
            log_info("✅ Bzzoiro : OK.", "AUDIT")
        else:
            log_warning("⚠️ Bzzoiro : HS", "AUDIT")
    except Exception as e:
        log_error("❌ Bzzoiro : test échoué", "AUDIT", exception=e)

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
                    f"⚠️ Football-Data : statut {res.status_code}",
                    "AUDIT",
                    api_context={"source": "football_data", "http_status": res.status_code},
                )
        else:
            log_warning("⚠️ Football-Data : clé absente", "AUDIT")
    except Exception as e:
        log_error("❌ Football-Data : test échoué", "AUDIT", exception=e)

    # OpenLigaDB
    try:
        from core.api import openligadb
        if openligadb.tester_api():
            log_info("✅ OpenLigaDB : OK.", "AUDIT")
        else:
            log_warning("⚠️ OpenLigaDB : HS", "AUDIT")
    except Exception as e:
        log_error("❌ OpenLigaDB : test échoué", "AUDIT", exception=e)

    # API-Football
    try:
        from core.api import api_football
        if api_football.tester_api():
            log_info("✅ API-Football : OK.", "AUDIT")
        else:
            log_warning("⚠️ API-Football : HS", "AUDIT")
    except Exception as e:
        log_error("❌ API-Football : test échoué", "AUDIT", exception=e)

    # TheSportsDB (Optionnel, souvent HS)
    try:
        from core.api import thesportsdb
        if thesportsdb.tester_api():
            log_info("✅ TheSportsDB : OK.", "AUDIT")
        else:
            log_warning("⚠️ TheSportsDB : HS (Normal si API gratuite)", "AUDIT")
    except Exception as e:
        log_error("❌ TheSportsDB : test échoué", "AUDIT", exception=e)


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
            log_error("❌ DB : SELECT 1 échoue", "AUDIT")
            return

        rows = db_fetchall("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [r[0] for r in rows] if rows else []

        manquantes = [t for t in TABLES_REQUISES if t not in tables]
        if manquantes:
            log_error(
                f"❌ Tables manquantes : {manquantes}",
                "AUDIT",
                extra={"manquantes": manquantes},
            )
        else:
            log_info(
                f"✅ Connexion DB OK. {len(tables)} tables détectées.",
                "AUDIT",
            )
            
        # Vérification du contenu de matchs
        try:
            row_count = db_fetchone("SELECT COUNT(*) FROM matchs")
            nb_matchs = row_count[0] if row_count else 0
            if nb_matchs > 0:
                log_info(f"📊 {nb_matchs} matchs trouvés dans la base.", "AUDIT")
            else:
                log_warning("⚠️ La table 'matchs' est vide.", "AUDIT")
        except Exception as e:
            log_warning("⚠️ Impossible de compter les matchs", "AUDIT", exception=e)

    except Exception as e:
        log_error("❌ DB : vérification impossible", "AUDIT", exception=e)


# =========================================================
# 5. AUDIT DU MODÈLE
# =========================================================
def audit_modele():
    log_info("--- 🧠 AUDIT DU MODÈLE ---", "AUDIT")
    from core.ml_model import global_model_data, charger_et_entrainer

    # 1. On vérifie d'abord dans Turso (source de vérité)
    try:
        row = db_fetchone(
            "SELECT length(data) FROM models_cache ORDER BY id DESC LIMIT 1",
            db_context={"table": "models_cache"}
        )
        if not row or not row[0]:
            log_error("❌ Aucun modèle trouvé dans models_cache (table vide)", "AUDIT")
            return
        taille = row[0]
        log_info(f"✅ Modèle présent en base Turso : {taille} caractères.", "AUDIT")
    except Exception as e:
        log_error("❌ Impossible de vérifier models_cache", "AUDIT", exception=e)
        return

    # 2. On vérifie le chargement en RAM
    modeles = global_model_data.get("models")
    if not modeles:
        log_warning("⚠️ Modèle non chargé en RAM, tentative de chargement...", "AUDIT")
        if not charger_et_entrainer():
            log_error("❌ Impossible de charger le modèle en RAM", "AUDIT")
            return
        modeles = global_model_data.get("models")

    if modeles:
        log_info(f"✅ {len(modeles)} marchés chargés en mémoire.", "AUDIT")

    # 3. On affiche les métriques
    prec = global_model_data.get("precision_moyenne")
    if prec:
        log_info(f"📊 Précision moyenne (DC_1X) : {round(prec * 100, 2)}%.", "AUDIT")
    else:
        log_warning("⚠️ Précision non disponible dans le bundle", "AUDIT")


# =========================================================
# 6. AUDIT CONFIG
# =========================================================
def audit_config():
    log_info("--- ⚙️ AUDIT CONFIG ---", "AUDIT")
    import config

    if config.CANAL_ID:
        log_info(f"✅ CANAL_ID : {config.CANAL_ID}", "AUDIT")
    else:
        log_error("❌ CANAL_ID manquant", "AUDIT")

    if config.CANAL_LIEN:
        log_info(f"✅ CANAL_LIEN : {config.CANAL_LIEN}", "AUDIT")
    else:
        log_error("❌ CANAL_LIEN manquant", "AUDIT")

    if config.TURSO_URL:
        log_info("✅ TURSO_URL configuré.", "AUDIT")
    else:
        log_error("❌ TURSO_URL manquant", "AUDIT")

    if config.TURSO_TOKEN:
        log_info("✅ TURSO_TOKEN configuré.", "AUDIT")
    else:
        log_error("❌ TURSO_TOKEN manquant", "AUDIT")

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
        log_error("Erreur pendant l'audit complet", "AUDIT", exception=e)
