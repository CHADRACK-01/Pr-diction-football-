# users/schema.py
"""Schéma SQL centralisé : source unique de vérité.

``TABLES`` regroupe tous les ``CREATE TABLE`` et ``COLONNES_A_MIGRER`` les
colonnes à ajouter aux tables existantes. ``synchroniser_schema`` est appelé par
``users.db.initialiser_tables``.
"""

TABLES = {
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
    # Gestion des fonctionnalités (Feature Flags) : schéma riche attendu par
    # core/feature_flags.py (libelle, categorie, priorite, proprietaire,
    # date_creation, date_expiration).
    "fonctionnalites_actives": """
        CREATE TABLE IF NOT EXISTS fonctionnalites_actives (
            feature_id TEXT PRIMARY KEY,
            actif INTEGER NOT NULL DEFAULT 0,
            libelle TEXT,
            categorie TEXT,
            priorite INTEGER,
            proprietaire TEXT,
            date_creation TEXT,
            date_expiration TEXT
        )
    """,
    "historique_features": """
        CREATE TABLE IF NOT EXISTS historique_features (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            feature_id TEXT NOT NULL,
            actif INTEGER NOT NULL,
            auteur_id INTEGER,
            date_bascule TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """,
    # Bankroll (core/bankroll.py)
    "bankroll": """
        CREATE TABLE IF NOT EXISTS bankroll (
            user_id INTEGER PRIMARY KEY,
            montant_total REAL DEFAULT 0,
            strategie TEXT DEFAULT 'kelly_fractionne',
            pourcentage_mise REAL DEFAULT 2.0
        )
    """,
    # Équipes favorites (core/equipes_favorites.py)
    "equipes_favorites": """
        CREATE TABLE IF NOT EXISTS equipes_favorites (
            user_id INTEGER,
            equipe TEXT,
            date_ajout TEXT DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, equipe)
        )
    """,
    # Codes promo (core/codes_promo.py)
    "codes_promo": """
        CREATE TABLE IF NOT EXISTS codes_promo (
            code TEXT PRIMARY KEY,
            type_reduction TEXT,
            valeur REAL,
            limite_utilisation INTEGER DEFAULT 0,
            deja_utilise INTEGER DEFAULT 0,
            date_creation TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """,
}

COLONNES_A_MIGRER = {
    "matchs": {
        "hs": "INTEGER", "as_shots": "INTEGER",
        "hst": "INTEGER", "ast": "INTEGER",
        "hc": "INTEGER", "ac": "INTEGER",
        "hf": "INTEGER", "af": "INTEGER",
        "hy": "INTEGER", "ay": "INTEGER",
        "hr": "INTEGER", "ar": "INTEGER",
        "b365h": "REAL", "b365d": "REAL", "b365a": "REAL",
    },
    "resultats_pronostics": {
        "competition": "TEXT",
        "score_predit": "TEXT",
        "tentatives_verification": "INTEGER DEFAULT 0",
    },
    "sessions_pronostic": {
        "etape": "TEXT",
        "equipe_dom": "TEXT",
        "equipe_ext": "TEXT",
        "equipes_dispo": "TEXT",
        "date_creation": "TEXT",
        "date_maj": "TEXT",
    },
    "fonctionnalites_actives": {
        "libelle": "TEXT",
        "categorie": "TEXT",
        "priorite": "INTEGER",
        "proprietaire": "TEXT",
        "date_creation": "TEXT",
        "date_expiration": "TEXT",
    },
}


def synchroniser_schema(conn, ajouter_colonnes):
    """Crée toutes les tables puis applique les colonnes manquantes.

    ``ajouter_colonnes`` est ``users.db._ajouter_colonnes_manquantes`` : elle est
    fournie par l'appelant pour éviter un import circulaire
    (``users.db -> users.schema``) et pour conserver la journalisation.
    """
    for sql in TABLES.values():
        conn.execute(sql)
    conn.commit()

    for table, colonnes in COLONNES_A_MIGRER.items():
        ajouter_colonnes(conn, table, colonnes)
