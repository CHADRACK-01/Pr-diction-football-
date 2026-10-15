import os
import psycopg2
import psycopg2.extras
from datetime import datetime

from config import (
    DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME,
    LIMITE_FREE_JOUR, LIMITE_PREMIUM_JOUR
)


# =========================================================
# CONNEXION
# =========================================================
def get_connection():
    """Retourne une connexion PostgreSQL."""
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        dbname=DB_NAME,
        sslmode="require"
    )


# =========================================================
# INITIALISATION DES TABLES
# =========================================================
def initialiser_tables():
    """Crée les tables si elles n'existent pas."""
    try:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS utilisateurs (
                user_id BIGINT PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                status TEXT DEFAULT 'free',
                date_inscription TIMESTAMP DEFAULT NOW(),
                date_expiration TIMESTAMP
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS compteurs_jour (
                user_id BIGINT,
                date DATE,
                compteur INTEGER DEFAULT 0,
                PRIMARY KEY (user_id, date)
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                deposit_id TEXT PRIMARY KEY,
                user_id BIGINT,
                abonnement TEXT,
                montant TEXT,
                statut TEXT DEFAULT 'pending',
                date_creation TIMESTAMP DEFAULT NOW()
            )
        """)

        conn.commit()
        cur.close()
        conn.close()
        print("✅ Tables PostgreSQL prêtes.")
    except Exception as e:
        print(f"❌ Erreur init tables : {e}")


# =========================================================
# LECTURE UTILISATEUR
# =========================================================
def utilisateur_existe(user_id):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM utilisateurs WHERE user_id = %s", (user_id,))
        result = cur.fetchone()
        cur.close()
        conn.close()
        return result is not None
    except Exception as e:
        print(f"⚠️ Erreur utilisateur_existe : {e}")
        return False


def get_user_info(user_id):
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM utilisateurs WHERE user_id = %s", (user_id,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        return dict(row) if row else None
    except Exception as e:
        print(f"⚠️ Erreur get_user_info : {e}")
        return None


def get_user_status(user_id):
    info = get_user_info(user_id)
    if not info:
        return 'free', None
    return info['status'], info['date_expiration']


# =========================================================
# ÉCRITURE UTILISATEUR
# =========================================================
def enregistrer_utilisateur(user_id, username, first_name):
    try:
        if utilisateur_existe(user_id):
            return False

        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO utilisateurs (user_id, username, first_name, status)
            VALUES (%s, %s, %s, 'free')
            ON CONFLICT (user_id) DO NOTHING
        """, (user_id, username or "", first_name or ""))
        conn.commit()
        cur.close()
        conn.close()
        print(f"👤 Nouvel utilisateur : {first_name} ({user_id})")
        return True
    except Exception as e:
        print(f"⚠️ Erreur enregistrer_utilisateur : {e}")
        return False


def set_premium(user_id, date_expiration):
    """
    Passe un utilisateur en premium.
    Accepte soit un datetime, soit une string 'YYYY-MM-DD HH:MM'.
    """
    try:
        if isinstance(date_expiration, str):
            date_expiration = datetime.strptime(date_expiration, "%Y-%m-%d %H:%M")

        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            UPDATE utilisateurs
            SET status = 'premium', date_expiration = %s
            WHERE user_id = %s
        """, (date_expiration, user_id))
        conn.commit()
        rows = cur.rowcount
        cur.close()
        conn.close()

        if rows == 0:
            print(f"⚠️ Utilisateur {user_id} introuvable pour set_premium.")
            return False

        print(f"⭐ Utilisateur {user_id} passé en PREMIUM jusqu'au {date_expiration}")
        return True
    except Exception as e:
        print(f"⚠️ Erreur set_premium : {e}")
        return False


# =========================================================
# STATUT
# =========================================================
def est_premium(user_id):
    status, expiration = get_user_status(user_id)
    if status != 'premium':
        return False
    if not expiration:
        return False
    try:
        return expiration > datetime.now()
    except Exception:
        return False


def get_statut_label(user_id):
    return "⭐ PREMIUM" if est_premium(user_id) else "🆓 FREE"


# =========================================================
# COMPTEURS JOURNALIERS
# =========================================================
def incrementer_compteur(user_id):
    try:
        today = datetime.now().date()
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO compteurs_jour (user_id, date, compteur)
            VALUES (%s, %s, 1)
            ON CONFLICT (user_id, date)
            DO UPDATE SET compteur = compteurs_jour.compteur + 1
        """, (user_id, today))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"⚠️ Erreur incrementer_compteur : {e}")


def get_compteur_jour(user_id):
    try:
        today = datetime.now().date()
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT compteur FROM compteurs_jour WHERE user_id = %s AND date = %s",
            (user_id, today)
        )
        result = cur.fetchone()
        cur.close()
        conn.close()
        return result[0] if result else 0
    except Exception as e:
        print(f"⚠️ Erreur get_compteur_jour : {e}")
        return 0


def get_limite_jour(user_id):
    return LIMITE_PREMIUM_JOUR if est_premium(user_id) else LIMITE_FREE_JOUR


def peut_faire_pronostic(user_id):
    return get_compteur_jour(user_id) < get_limite_jour(user_id)


# =========================================================
# TRANSACTIONS PAWAPAY
# =========================================================
def enregistrer_transaction(deposit_id, user_id, abonnement, montant):
    """Enregistre une nouvelle transaction avant l'appel PawaPay."""
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO transactions (deposit_id, user_id, abonnement, montant, statut)
            VALUES (%s, %s, %s, %s, 'pending')
            ON CONFLICT (deposit_id) DO NOTHING
        """, (deposit_id, user_id, abonnement, montant))
        conn.commit()
        cur.close()
        conn.close()
        print(f"💾 Transaction enregistrée : {deposit_id}")
        return True
    except Exception as e:
        print(f"⚠️ Erreur enregistrer_transaction : {e}")
        return False


def get_transaction(deposit_id):
    """Récupère une transaction par son deposit_id."""
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM transactions WHERE deposit_id = %s", (deposit_id,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        return dict(row) if row else None
    except Exception as e:
        print(f"⚠️ Erreur get_transaction : {e}")
        return None


def update_transaction_statut(deposit_id, statut):
    """Met à jour le statut d'une transaction."""
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "UPDATE transactions SET statut = %s WHERE deposit_id = %s",
            (statut, deposit_id)
        )
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"⚠️ Erreur update_transaction_statut : {e}")
        return False
