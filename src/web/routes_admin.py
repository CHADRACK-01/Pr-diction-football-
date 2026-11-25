"""Routes Flask d'administration protégées."""

from core.utils.logs import log_error
from web.security import admin_required


def register_admin_routes(app, *, config, initialiser_bdd_si_necessaire):
    @app.route("/debug_env")
    @admin_required
    def debug_env():
        return (
            f"TURSO_URL : {'✅' if config.TURSO_URL else '❌'}\n"
            f"TURSO_TOKEN : {'✅' if config.TURSO_TOKEN else '❌'}\n"
            f"TELEGRAM_TOKEN : {'✅' if config.TOKEN else '❌'}\n"
            f"MODE_VITRINE : {config.MODE_VITRINE}\n"
            f"MODE_TEST : {config.MODE_TEST}\n"
            f"ADMIN_ID : {config.ADMIN_ID}"
        ), 200

    @app.route("/init_db")
    @admin_required
    def init_db():
        try:
            from users.db import initialiser_tables
            from users.database import db_fetchall

            initialiser_tables()
            initialiser_bdd_si_necessaire()
            rows = db_fetchall("SELECT name FROM sqlite_master WHERE type='table'")
            noms = [row[0] for row in rows] if rows else []
            return f"✅ Tables ({len(noms)}) :\n" + "\n".join(noms), 200
        except Exception as exc:
            log_error("Erreur /init_db", "FLASK", exception=exc)
            return "❌ Impossible d’initialiser la base de données", 500

    @app.route("/telecharger")
    @admin_required
    def telecharger():
        try:
            from scripts.telecharger_matchs import telecharger_tout

            total = telecharger_tout()
            return f"✅ {total} matchs traités.", 200
        except Exception as exc:
            log_error("Erreur /telecharger", "FLASK", exception=exc)
            return "❌ Impossible de télécharger les matchs", 500

    @app.route("/maj_resultats")
    @admin_required
    def maj_resultats():
        try:
            from scripts.mettre_a_jour_resultats import mettre_a_jour_resultats

            total = mettre_a_jour_resultats()
            return f"✅ {total} matchs mis à jour.", 200
        except Exception as exc:
            log_error("Erreur /maj_resultats", "FLASK", exception=exc)
            return "❌ Impossible de mettre à jour les résultats", 500

    @app.route("/nettoyer")
    @admin_required
    def nettoyer():
        try:
            from users.matchs import nettoyer_vieilles_donnees

            total = nettoyer_vieilles_donnees(annees=5)
            return f"✅ {total} matchs > 5 ans supprimés.", 200
        except Exception:
            return "❌ Erreur lors du nettoyage", 500

    @app.route("/debug_model")
    @admin_required
    def debug_model():
        try:
            from users.database import get_connection

            conn = get_connection()
            try:
                rows = conn.execute("SELECT id, length(data) FROM models_cache").fetchall()
            finally:
                conn.close()

            if not rows:
                return "❌ La table models_cache est VIDE.", 200
            output = f"✅ {len(rows)} ligne(s) trouvée(s) :\n"
            output += "".join(f"ID: {row[0]}, Taille: {row[1]} caractères\n" for row in rows)
            return output, 200
        except Exception as exc:
            log_error("Erreur /debug_model", "FLASK", exception=exc)
            return "❌ Impossible de lire le cache du modèle", 500
