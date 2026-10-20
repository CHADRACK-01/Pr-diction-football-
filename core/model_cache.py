import psycopg2
import zlib  # ⚠️ NOUVEAU : Bibliothèque standard pour compresser

from users.db import get_connection
from core.utils.logs import log_info


def sauvegarder_modele_cache(modele_bytes, precision, nb_matchs):
    """
    Sauvegarde le modèle dans la BDD.
    ⚠️ OPTIMISATION : On compresse les bytes avant de les envoyer à la BDD (gain de 30 à 60%).
    """
    modele_compresse = zlib.compress(modele_bytes)
    
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO model_cache (id, modele, precision, nb_matchs, date_creation)
                VALUES (1, %s, %s, %s, NOW())
                ON CONFLICT (id) DO UPDATE
                SET modele = EXCLUDED.modele,
                    precision = EXCLUDED.precision,
                    nb_matchs = EXCLUDED.nb_matchs,
                    date_creation = NOW()
            """, (psycopg2.Binary(modele_compresse), precision, nb_matchs))
        conn.commit()
        
    log_info(f"Modèle sauvegardé et compressé (précision={round(precision*100, 2)}%, matchs={nb_matchs})", "CACHE")
    return True


def charger_modele_cache():
    """
    Récupère le modèle depuis la BDD et le décompresse.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT modele, precision, nb_matchs FROM model_cache WHERE id = 1")
            row = cur.fetchone()

            if row and row[0]:
                modele_compresse = bytes(row[0])
                # ⚠️ OPTIMISATION : On décompresse à la volée
                modele_decompresse = zlib.decompress(modele_compresse)
                return modele_decompresse, row[1], row[2]
            return None


def vider_modele_cache():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM model_cache WHERE id = 1")
        conn.commit()
        
    log_info("Cache modèle vidé.", "CACHE")
    return True
