import io
import joblib
import libsql

from users.db import get_connection
from core.utils.logs import log_info

CHUNK_SIZE = 1 * 1024 * 1024  # 1 Mo par morceau (Turso est plus restrictif que PostgreSQL)


def sauvegarder_modele_cache(modele_bytes, precision, nb_matchs):
    """
    Sauvegarde le modèle dans Turso par morceaux (chunks).
    """
    total_chunks = (len(modele_bytes) // CHUNK_SIZE) + 1
    
    conn = get_connection()
    conn.execute("DELETE FROM model_cache_chunks")
    
    for i in range(total_chunks):
        chunk = modele_bytes[i * CHUNK_SIZE:(i + 1) * CHUNK_SIZE]
        conn.execute("""
            INSERT INTO model_cache_chunks (chunk_index, total_chunks, chunk_data, precision, nb_matchs)
            VALUES (?, ?, ?, ?, ?)
        """, (i, total_chunks, chunk, precision, nb_matchs))
        
    conn.commit()
    conn.close()
    
    log_info(f"Modèle sauvegardé en {total_chunks} morceaux (précision={round(precision*100, 2)}%)", "CACHE")
    return True


def charger_modele_cache():
    """
    Récupère tous les morceaux de la BDD, les assemble et retourne le modèle.
    """
    conn = get_connection()
    
    cur = conn.execute("""
        SELECT chunk_data, precision, nb_matchs 
        FROM model_cache_chunks 
        ORDER BY chunk_index
    """)
    rows = cur.fetchall()
    conn.close()
    
    if not rows:
        return None
    
    # On assemble les morceaux
    modele_compresse = b"".join([bytes(r[0]) for r in rows])
    precision = rows[0][1]
    nb_matchs = rows[0][2]
    
    log_info(f"Modèle assemblé depuis {len(rows)} morceaux.", "CACHE")
    return modele_compresse, precision, nb_matchs


def vider_modele_cache():
    """Vide la table du cache modèle."""
    conn = get_connection()
    conn.execute("DELETE FROM model_cache_chunks")
    conn.commit()
    conn.close()
    log_info("Cache modèle vidé.", "CACHE")
    return True
