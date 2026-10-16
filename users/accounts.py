import psycopg2.extras
from datetime import datetime, timedelta

from config import LIMITE_FREE_JOUR, LIMITE_PREMIUM_JOUR
from users.db import get_connection


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
            return False
        print(f"⭐ Utilisateur {user_id} passé en PREMIUM")
        return True
    except Exception as e:
        print(f"⚠️ Erreur set_premium : {e}")
        return False


def est_premium(user_id):
    status, expiration = get_user_status(user_id)
    if status != 'premium' or not expiration:
        return False
    try:
        return expiration > datetime.now()
    except Exception:
        return False


def get_statut_label(user_id):
    return "PREMIUM" if est_premium(user_id) else "FREE"


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
# NOTIFICATIONS
# =========================================================
def activer_notifications(user_id):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            UPDATE utilisateurs
            SET notifications_actives = TRUE
            WHERE user_id = %s
        """, (user_id,))
        conn.commit()
        rows = cur.rowcount
        cur.close()
        conn.close()
        return rows > 0
    except Exception as e:
        print(f"⚠️ Erreur activer_notifications : {e}")
        return False


def desactiver_notifications(user_id):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            UPDATE utilisateurs
            SET notifications_actives = FALSE
            WHERE user_id = %s
        """, (user_id,))
        conn.commit()
        rows = cur.rowcount
        cur.close()
        conn.close()
        return rows > 0
    except Exception as e:
        print(f"⚠️ Erreur desactiver_notifications : {e}")
        return False


def get_utilisateurs_notifies():
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT user_id FROM utilisateurs
            WHERE notifications_actives = TRUE
        """)
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return [r[0] for r in rows]
    except Exception as e:
        print(f"⚠️ Erreur get_utilisateurs_notifies : {e}")
        return []


def get_tous_utilisateurs():
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT user_id FROM utilisateurs")
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return [r[0] for r in rows]
    except Exception as e:
        print(f"⚠️ Erreur get_tous_utilisateurs : {e}")
        return []


# =========================================================
# LANGUE
# =========================================================
def get_langue(user_id):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT langue FROM utilisateurs WHERE user_id = %s", (user_id,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        return row[0] if row and row[0] else "fr"
    except Exception as e:
        print(f"⚠️ Erreur get_langue : {e}")
        return "fr"


def set_langue(user_id, langue):
    try:
        if langue not in ["fr", "en", "ln"]:
            return False
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            UPDATE utilisateurs
            SET langue = %s
            WHERE user_id = %s
        """, (langue, user_id))
        conn.commit()
        rows = cur.rowcount
        cur.close()
        conn.close()
        return rows > 0
    except Exception as e:
        print(f"⚠️ Erreur set_langue : {e}")
        return False


# =========================================================
# PARRAINAGE
# =========================================================
def get_parrain(user_id):
    """Retourne l'ID du parrain de l'utilisateur, ou None."""
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT parrain_id FROM utilisateurs WHERE user_id = %s", (user_id,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        return row[0] if row and row[0] else None
    except Exception as e:
        print(f"⚠️ Erreur get_parrain : {e}")
        return None


def set_parrain(user_id, parrain_id):
    """Enregistre le parrain d'un utilisateur."""
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            UPDATE utilisateurs
            SET parrain_id = %s
            WHERE user_id = %s AND parrain_id IS NULL
        """, (parrain_id, user_id))
        conn.commit()
        rows = cur.rowcount
        cur.close()
        conn.close()
        return rows > 0
    except Exception as e:
        print(f"⚠️ Erreur set_parrain : {e}")
        return False


def compter_filleuls(user_id):
    """Compte le nombre de filleuls d'un utilisateur."""
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM utilisateurs WHERE parrain_id = %s", (user_id,))
        result = cur.fetchone()
        cur.close()
        conn.close()
        return result[0] if result else 0
    except Exception as e:
        print(f"⚠️ Erreur compter_filleuls : {e}")
        return 0


def ajouter_jours_premium(user_id, jours):
    """Ajoute X jours de Premium à un utilisateur (cumulable)."""
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT date_expiration, status FROM utilisateurs WHERE user_id = %s", (user_id,))
        row = cur.fetchone()
        if not row:
            cur.close()
            conn.close()
            return False

        expiration_actuelle, status = row

        if status == 'premium' and expiration_actuelle and expiration_actuelle > datetime.now():
            nouvelle_date = expiration_actuelle + timedelta(days=jours)
        else:
            nouvelle_date = datetime.now() + timedelta(days=jours)

        cur.execute("""
            UPDATE utilisateurs
            SET status = 'premium', date_expiration = %s
            WHERE user_id = %s
        """, (nouvelle_date, user_id))
        conn.commit()
        cur.close()
        conn.close()
        print(f"⭐ +{jours}j Premium pour {user_id} (expire {nouvelle_date})")
        return True
    except Exception as e:
        print(f"⚠️ Erreur ajouter_jours_premium : {e}")
        return False


# =========================================================
# PARRAINAGE AVANCÉ
# =========================================================
def get_top_parrains(limite=10):
    """Retourne le classement des top parrains."""
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT 
                p.user_id,
                p.first_name,
                COUNT(f.user_id) as nb_filleuls
            FROM utilisateurs p
            INNER JOIN utilisateurs f ON f.parrain_id = p.user_id
            GROUP BY p.user_id, p.first_name
            ORDER BY nb_filleuls DESC
            LIMIT %s
        """, (limite,))
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return [dict(r) for r in rows]
    except Exception as e:
        print(f"⚠️ Erreur get_top_parrains : {e}")
        return []


def get_filleuls(user_id, limite=20):
    """Retourne la liste des filleuls d'un utilisateur."""
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT user_id, first_name, date_inscription
            FROM utilisateurs
            WHERE parrain_id = %s
            ORDER BY date_inscription DESC
            LIMIT %s
        """, (user_id, limite))
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return [dict(r) for r in rows]
    except Exception as e:
        print(f"⚠️ Erreur get_filleuls : {e}")
        return []


def get_palier_atteint(nb_filleuls):
    """Retourne le palier de récompenses atteint."""
    paliers = [
        (50, 30, "Legende"),
        (20, 15, "Or"),
        (10, 10, "Argent"),
        (5, 7, "Bronze"),
    ]
    for seuil, bonus, nom in paliers:
        if nb_filleuls >= seuil:
            return {"seuil": seuil, "bonus": bonus, "nom": nom}
    return None


def get_prochain_palier(nb_filleuls):
    """Retourne le prochain palier à atteindre."""
    paliers = [
        (5, 7, "Bronze"),
        (10, 10, "Argent"),
        (20, 15, "Or"),
        (50, 30, "Legende"),
    ]
    for seuil, bonus, nom in paliers:
        if nb_filleuls < seuil:
            return {"seuil": seuil, "bonus": bonus, "nom": nom, "restant": seuil - nb_filleuls}
    return None
