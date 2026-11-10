from datetime import datetime, timedelta
from users.db import get_connection
from core.utils.logs import log_info, log_error, log_warning


def inserer_matchs(liste_matchs):
    """Insère une liste de matchs dans la base Turso (avec protection par ligne)."""
    if not liste_matchs:
        return 0

    conn = get_connection()
    inseres = 0
    TAILLE_LOT = 500

    for i in range(0, len(liste_matchs), TAILLE_LOT):
        lot = liste_matchs[i:i + TAILLE_LOT]
        
        valeurs = []
        for m in lot:
            valeurs.append((
                m.get('date'), m.get('home_team'), m.get('away_team'),
                m.get('fthg'), m.get('ftag'), m.get('ftr'),
                m.get('hthg'), m.get('htag'), m.get('htr'),
                m.get('hs'), m.get('as_shots'), m.get('hst'), m.get('ast'),
                m.get('hc'), m.get('ac'), m.get('hf'), m.get('af'),
                m.get('hy'), m.get('ay'), m.get('hr'), m.get('ar'),
                m.get('b365h'), m.get('b365d'), m.get('b365a'),
                m.get('competition')
            ))
        
        query = """
            INSERT INTO matchs (
                date, home_team, away_team,
                fthg, ftag, ftr,
                hthg, htag, htr,
                hs, as_shots, hst, ast,
                hc, ac, hf, af,
                hy, ay, hr, ar,
                b365h, b365d, b365a,
                competition
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (date, home_team, away_team, competition) DO NOTHING
        """
        
        for vals in valeurs:
            try:
                conn.execute(query, vals)
                inseres += 1
            except Exception as e:
                log_error(
                    message=f"Erreur d'insertion pour {vals[1]} vs {vals[2]} ({vals[0]})",
                    module="MATCHS",
                    exception=e
                )
        
        conn.commit()

    conn.close()
    log_info(f"{inseres} match(s) traité(s).", "MATCHS")
    return inseres


def compter_matchs():
    """Compte le nombre total de matchs dans la base."""
    try:
        conn = get_connection()
        result = conn.execute("SELECT COUNT(*) FROM matchs").fetchone()
        conn.close()
        return result[0] if result else 0
    except Exception as e:
        log_error("Impossible de compter les matchs", "MATCHS", exception=e)
        return 0


def get_equipes_saison_en_cours(competition):
    """
    Récupère les équipes de la saison en cours (matchs des 365 derniers jours).
    Cela inclut les matchs futurs (calendrier déjà téléchargé).
    """
    try:
        conn = get_connection()
        
        date_limite = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
        
        cur = conn.execute("""
            SELECT DISTINCT home_team FROM matchs 
            WHERE competition = ? AND date >= ?
            UNION
            SELECT DISTINCT away_team FROM matchs 
            WHERE competition = ? AND date >= ?
            ORDER BY home_team ASC
        """, (competition, date_limite, competition, date_limite))
        
        equipes = [row[0] for row in cur.fetchall()]
        conn.close()
        
        log_info(f"{len(equipes)} équipes trouvées pour {competition} (saison en cours).", "MATCHS")
        return equipes
    except Exception as e:
        log_error(f"Impossible de récupérer les équipes de {competition}", "MATCHS", exception=e)
        return []


def nettoyer_vieilles_donnees(annees=5):
    """
    Supprime les matchs de plus de X années (5 ans par défaut).
    C'est la norme en modélisation football.
    """
    try:
        conn = get_connection()
        
        date_limite = (datetime.now() - timedelta(days=annees * 365)).strftime("%Y-%m-%d")
        
        cur = conn.execute("SELECT COUNT(*) FROM matchs WHERE date < ?", (date_limite,))
        nb_a_supprimer = cur.fetchone()[0]
        
        if nb_a_supprimer == 0:
            log_info(f"Aucun match de plus de {annees} ans à supprimer.", "MATCHS")
            conn.close()
            return 0
        
        conn.execute("DELETE FROM matchs WHERE date < ?", (date_limite,))
        conn.commit()
        conn.close()
        
        log_info(f"{nb_a_supprimer} matchs de plus de {annees} ans supprimés.", "MATCHS")
        return nb_a_supprimer
    except Exception as e:
        log_error(f"Impossible de nettoyer les données de plus de {annees} ans", "MATCHS", exception=e)
        return 0
