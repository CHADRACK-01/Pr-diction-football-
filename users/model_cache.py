import psycopg2

from users.db import get_connection


def sauvegarder_modele_cache(modele_bytes, precision, nb_matchs):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO model_cache (id, modele, precision, nb_matchs, date_creation)
            VALUES (1, %s, %s, %s, NOW())
            ON CONFLICT (id) DO UPDATE
            SET modele = EXCLUDED.modele,
                precision = EXCLUDED.precision,
                nb_matchs = EXCLUDED.nb_matchs,
                date_creation = NOW()
        """, (psycopg2.Binary(modele_bytes), precision, nb_matchs))
        conn.commit()
        cur.close()
        conn.close()
        print(f"💾 Modèle sauvegardé (précision={round(precision*100, 2)}%, matchs={nb_matchs})")
        return True
    except Exception as e:
        print(f"⚠️ Erreur sauvegarder_modele_cache : {e}")
        return False


def charger_modele_cache():
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT modele, precision, nb_matchs FROM model_cache WHERE id = 1")
        row = cur.fetchone()
        cur.close()
        conn.close()

        if row and row[0]:
            return bytes(row[0]), row[1], row[2]
        return None
    except Exception as e:
        print(f"⚠️ Erreur charger_modele_cache : {e}")
        return None


def vider_modele_cache():
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM model_cache WHERE id = 1")
        conn.commit()
        cur.close()
        conn.close()
        print("🗑 Cache modèle vidé.")
        return True
    except Exception as e:
        print(f"⚠️ Erreur vider_modele_cache : {e}")
        return False
