"""Inspection et nettoyage de la base de données."""

from core.utils.logs import log_error, log_info, log_warning
from users.database.queries import db_execute, db_fetchone


def get_taille_base():
    try:
        row = db_fetchone(
            "SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()",
            db_context={"table": "pragma"},
        )
        if row and row[0]:
            return f"{row[0] / 1024 / 1024:.2f} MB"
        return "Inconnue"
    except Exception as exc:
        log_error(
            message="Impossible de calculer la taille de la base",
            module="DATABASE",
            exception=exc,
        )
        return "Erreur"


def get_detail_tables():
    tables = [
        "utilisateurs", "matchs", "models_cache", "paiements_attente",
        "codes_premium", "logs_admin", "resultats_pronostics",
        "sessions_pronostic", "fonctionnalites_actives", "bankroll",
        "equipes_favorites", "codes_promo",
    ]
    resultats = []
    for table in tables:
        try:
            row = db_fetchone(
                f"SELECT COUNT(*) FROM {table}",
                db_context={"table": table},
            )
            count = row[0] if row else 0
            resultats.append({"table_name": table, "size": f"{count} lignes"})
        except Exception as exc:
            log_warning(
                message=f"Impossible de lire la table '{table}'",
                module="DATABASE",
                db_context={"table": table},
                exception=exc,
            )
            resultats.append({"table_name": table, "size": "❌ erreur"})
    return resultats


def nettoyer_logs_anciens(jours: int = 30) -> int:
    if not isinstance(jours, int) or jours <= 0 or jours > 3650:
        log_warning(
            message=f"Paramètre 'jours' invalide : {jours}",
            module="DATABASE",
            extra={"jours": jours},
        )
        return 0

    rowcount = db_execute(
        "DELETE FROM logs_admin WHERE date_action < datetime('now', ?)",
        params=[f"-{jours} days"],
        db_context={"table": "logs_admin", "operation": "cleanup"},
    )
    if rowcount is None:
        return 0
    log_info(f"{rowcount} logs de plus de {jours}j supprimés.", "DATABASE")
    return rowcount


def nettoyer_paiements_anciens(jours: int = 90) -> int:
    if not isinstance(jours, int) or jours <= 0 or jours > 3650:
        log_warning(
            message=f"Paramètre 'jours' invalide : {jours}",
            module="DATABASE",
            extra={"jours": jours},
        )
        return 0

    rowcount = db_execute(
        """
        DELETE FROM paiements_attente
        WHERE statut != 'en_attente'
        AND date_validation < datetime('now', ?)
        """,
        params=[f"-{jours} days"],
        db_context={"table": "paiements_attente", "operation": "cleanup"},
    )
    if rowcount is None:
        return 0
    log_info(f"{rowcount} paiements de plus de {jours}j supprimés.", "DATABASE")
    return rowcount


# =========================================================
# INITIALISATION DES TABLES (déplacé depuis users/db.py)
# =========================================================
from datetime import datetime


def _creer_table(conn, nom, sql):
    try:
        conn.execute(sql)
        conn.commit()
        log_info(f"Table '{nom}' vérifiée.", "DATABASE")
        return True
    except Exception as e:
        log_error(
            message=f"Impossible de créer la table '{nom}'",
            module="DATABASE",
            db_context={"table": nom, "query": sql[:200]},
            exception=e,
        )
        return False


def _ajouter_colonnes_manquantes(conn, table, colonnes):
    existantes = set()
    try:
        cur = conn.execute(f"PRAGMA table_info({table})")
        rows = cur.fetchall()
        existantes = {row[1] for row in rows}
        log_info(
            f"PRAGMA OK pour '{table}' : {len(existantes)} colonnes détectées.",
            "DATABASE",
        )
    except Exception as e:
        log_warning(
            message=f"PRAGMA non supporté pour '{table}', on tente ALTER en aveugle",
            module="DATABASE",
            db_context={"table": table},
            exception=e,
        )

    for nom_col, type_col in colonnes.items():
        if nom_col in existantes:
            continue
        try:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {nom_col} {type_col}")
            conn.commit()
            log_info(
                f"Colonne '{nom_col}' ajoutée à la table '{table}'.",
                "DATABASE",
            )
        except Exception as e:
            msg = str(e).lower()
            if "duplicate column" in msg or "already exists" in msg:
                log_info(
                    f"Colonne '{nom_col}' déjà présente dans '{table}'.",
                    "DATABASE",
                )
            else:
                log_error(
                    message=f"Impossible d'ajouter la colonne '{nom_col}' à '{table}'",
                    module="DATABASE",
                    db_context={"table": table, "column": nom_col, "type": type_col},
                    exception=e,
                )


def _assurer_schema_catalogue(conn):
    """Crée et migre les tables du catalogue des fonctionnalités."""
    colonnes_features = {
        "libelle": "TEXT",
        "categorie": "TEXT",
        "priorite": "INTEGER",
        "proprietaire": "TEXT",
        "date_creation": "TEXT",
        "date_expiration": "TEXT",
    }
    try:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS fonctionnalites_actives ("
            "feature_id TEXT PRIMARY KEY, "
            "actif INTEGER NOT NULL DEFAULT 0, "
            "libelle TEXT, "
            "categorie TEXT, "
            "priorite INTEGER, "
            "proprietaire TEXT, "
            "date_creation TEXT, "
            "date_expiration TEXT)"
        )
        conn.execute(
            "CREATE TABLE IF NOT EXISTS historique_features ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "feature_id TEXT NOT NULL, "
            "actif INTEGER NOT NULL, "
            "auteur_id INTEGER, "
            "date_bascule TEXT DEFAULT CURRENT_TIMESTAMP)"
        )
        conn.commit()
    except Exception as e:
        log_error(
            message="Impossible de créer les tables du catalogue des fonctionnalités",
            module="DATABASE",
            exception=e,
        )
    _ajouter_colonnes_manquantes(conn, "fonctionnalites_actives", colonnes_features)


def initialiser_tables():
    """Crée toutes les tables de l'application si elles n'existent pas."""
    log_info("Début de l'initialisation des tables...", "DATABASE")

    conn = None
    try:
        conn = get_connection()

        tables = {
            "utilisateurs": """
                CREATE TABLE IF NOT EXISTS utilisateurs (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    status TEXT DEFAULT 'free',
                    date_inscription TEXT DEFAULT CURRENT_TIMESTAMP,
                    date_expiration TEXT,
                    notifications_actives INTEGER DEFAULT 1,
                    langue TEXT DEFAULT 'fr',
                    parrain_id INTEGER,
                    methode_paiement TEXT
                )
            """,
            "compteurs_jour": """
                CREATE TABLE IF NOT EXISTS compteurs_jour (
                    user_id INTEGER,
                    date TEXT,
                    compteur INTEGER DEFAULT 0,
                    PRIMARY KEY (user_id, date)
                )
            """,
            "matchs": """
                CREATE TABLE IF NOT EXISTS matchs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT,
                    home_team TEXT,
                    away_team TEXT,
                    fthg INTEGER, ftag INTEGER, ftr TEXT,
                    hthg INTEGER, htag INTEGER, htr TEXT,
                    hs INTEGER, as_shots INTEGER, hst INTEGER, ast INTEGER,
                    hc INTEGER, ac INTEGER, hf INTEGER, af INTEGER,
                    hy INTEGER, ay INTEGER, hr INTEGER, ar INTEGER,
                    b365h REAL, b365d REAL, b365a REAL,
                    competition TEXT,
                    UNIQUE(date, home_team, away_team, competition)
                )
            """,
            "models_cache": """
                CREATE TABLE IF NOT EXISTS models_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    data BLOB,
                    date_creation TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """,
            "parametres": """
                CREATE TABLE IF NOT EXISTS parametres (
                    cle TEXT PRIMARY KEY,
                    valeur TEXT,
                    description TEXT,
                    modifie_le TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """,
            "administrateurs": """
                CREATE TABLE IF NOT EXISTS administrateurs (
                    user_id INTEGER PRIMARY KEY,
                    nom TEXT,
                    ajoute_le TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """,
            "bannis": """
                CREATE TABLE IF NOT EXISTS bannis (
                    user_id INTEGER PRIMARY KEY,
                    raison TEXT,
                    banni_le TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """,
            "logs_admin": """
                CREATE TABLE IF NOT EXISTS logs_admin (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    admin_id INTEGER,
                    action TEXT,
                    details TEXT,
                    date_action TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """,
            "paiements_attente": """
                CREATE TABLE IF NOT EXISTS paiements_attente (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    abonnement TEXT,
                    montant INTEGER,
                    preuve_photo_id TEXT,
                    statut TEXT DEFAULT 'en_attente',
                    date_demande TEXT DEFAULT CURRENT_TIMESTAMP,
                    date_validation TEXT,
                    admin_id INTEGER
                )
            """,
            "codes_premium": """
                CREATE TABLE IF NOT EXISTS codes_premium (
                    code TEXT PRIMARY KEY,
                    jours INTEGER,
                    utilise INTEGER DEFAULT 0,
                    utilise_par INTEGER,
                    date_creation TEXT DEFAULT CURRENT_TIMESTAMP,
                    date_utilisation TEXT
                )
            """,
            "resultats_pronostics": """
                CREATE TABLE IF NOT EXISTS resultats_pronostics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date_match TEXT,
                    home_team TEXT,
                    away_team TEXT,
                    competition TEXT,
                    pronostic_reco TEXT,
                    score_predit TEXT,
                    score_reel TEXT,
                    est_gagnant INTEGER,
                    tentatives_verification INTEGER DEFAULT 0,
                    date_creation TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """,
            "sessions_pronostic": """
                CREATE TABLE IF NOT EXISTS sessions_pronostic (
                    user_id INTEGER PRIMARY KEY,
                    competition TEXT,
                    etape TEXT,
                    equipe_dom TEXT,
                    equipe_ext TEXT,
                    equipes_dispo TEXT,
                    date_creation TEXT DEFAULT CURRENT_TIMESTAMP,
                    date_maj TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """,
            "fonctionnalites_actives": """
                CREATE TABLE IF NOT EXISTS fonctionnalites_actives (
                    feature_id TEXT PRIMARY KEY,
                    actif INTEGER DEFAULT 0
                )
            """,
            "bankroll": """
                CREATE TABLE IF NOT EXISTS bankroll (
                    user_id INTEGER PRIMARY KEY,
                    montant_total REAL DEFAULT 0,
                    strategie TEXT DEFAULT 'kelly_fractionne',
                    pourcentage_mise REAL DEFAULT 2.0
                )
            """,
            "equipes_favorites": """
                CREATE TABLE IF NOT EXISTS equipes_favorites (
                    user_id INTEGER,
                    equipe TEXT,
                    date_ajout TEXT DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (user_id, equipe)
                )
            """,
            "codes_promo": """
                CREATE TABLE IF NOT EXISTS codes_promo (
                    code TEXT PRIMARY KEY,
                    type_reduction TEXT,
                    valeur REAL,
                    limite_utilisation INTEGER DEFAULT 0,
                    deja_utilise INTEGER DEFAULT 0,
                    date_creation TEXT DEFAULT CURRENT_TIMESTAMP,
                    date_utilisation TEXT
                )
            """,
        }

        for nom, sql in tables.items():
            _creer_table(conn, nom, sql)

        colonnes_matchs = {
            "hs": "INTEGER", "as_shots": "INTEGER",
            "hst": "INTEGER", "ast": "INTEGER",
            "hc": "INTEGER", "ac": "INTEGER",
            "hf": "INTEGER", "af": "INTEGER",
            "hy": "INTEGER", "ay": "INTEGER",
            "hr": "INTEGER", "ar": "INTEGER",
            "b365h": "REAL", "b365d": "REAL", "b365a": "REAL",
        }
        _ajouter_colonnes_manquantes(conn, "matchs", colonnes_matchs)

        colonnes_resultats = {
            "competition": "TEXT",
            "score_predit": "TEXT",
            "tentatives_verification": "INTEGER DEFAULT 0",
        }
        _ajouter_colonnes_manquantes(conn, "resultats_pronostics", colonnes_resultats)

        colonnes_sessions = {
            "etape": "TEXT",
            "equipe_dom": "TEXT",
            "equipe_ext": "TEXT",
            "equipes_dispo": "TEXT",
            "date_creation": "TEXT",
            "date_maj": "TEXT",
        }
        _ajouter_colonnes_manquantes(conn, "sessions_pronostic", colonnes_sessions)

        try:
            result = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
            noms = [r[0] for r in result]
            log_info(f"Tables existantes ({len(noms)}) : {noms}", "DATABASE")
        except Exception as e:
            log_warning(
                message="Impossible de lister les tables",
                module="DATABASE",
                exception=e,
            )
    except Exception as e:
        log_error(
            message="Erreur critique lors de l'initialisation des tables",
            module="DATABASE",
            exception=e,
        )
        raise
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception as e:
                log_warning(
                    message="Impossible de fermer la connexion après init",
                    module="DATABASE",
                    exception=e,
                )

    log_info("Initialisation terminée.", "DATABASE")
