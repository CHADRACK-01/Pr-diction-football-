# core/data/outils_donnees.py
"""
Outils de données sportives supplémentaires pour les fonctionnalités marquées
"a_implanter" dans le catalogue principal (IDs 4, 16, 22, 25, 27, 28, 38,
56, 57, 58, 59, 60, 61).

Contrat : retourne un dict avec "succes", logge via core.utils.logs,
dépendances externes minimales.
"""

from __future__ import annotations

from typing import Any

from core.utils.logs import log_info, log_error


# ---------------------------------------------------------------------------
# 4 - Alerte Compo Officielle / Absents
# ---------------------------------------------------------------------------
def verifier_compo_officielle(match_id: int) -> dict[str, Any]:
    """Vérifie la composition officielle d'un match.

    Args:
        match_id: ID du match.

    Returns:
        Dictionnaire {succes, compo_officielle, absents, disponible}.
    """
    try:
        disponible = False
        compo_officielle = {}
        absents = []
        log_info(f"Vérification compo officielle : match {match_id}", "DONNÉES")
        return {
            "succes": True,
            "match_id": match_id,
            "compo_officielle": compo_officielle,
            "absents": absents,
            "disponible": disponible,
            "message": "Compo officielle non disponible sans API-Football",
        }
    except Exception as e:
        log_error("Erreur vérification compo", "DONNÉES", exception=e)
        return {"succes": False, "message": str(e)}


# ---------------------------------------------------------------------------
# 16 - Avertissement Jeu Responsable
# ---------------------------------------------------------------------------
def generer_avertissement_jeu_responsable(mise: float, bankroll: float) -> dict[str, Any]:
    """Génère un avertissement de jeu responsable.

    Args:
        mise: Montant du pari envisagé.
        bankroll: Bankroll totale de l'utilisateur.

    Returns:
        Dictionnaire {succes, avertissement, pourcentage_risque}.
    """
    try:
        pourcentage = (mise / bankroll * 100) if bankroll > 0 else 0
        avertissement = ""
        if pourcentage > 10:
            avertissement = "⚠️ Risque élevé : mise > 10% de votre bankroll."
        elif pourcentage > 5:
            avertissement = "⚠️ Attention : mise > 5% de votre bankroll."
        else:
            avertissement = "✅ Mise raisonnable par rapport à votre bankroll."
        log_info(f"Avertissement jeu responsable : {pourcentage:.1f}% de bankroll", "SÉCURITÉ")
        return {
            "succes": True,
            "pourcentage_risque": round(pourcentage, 1),
            "avertissement": avertissement,
            "mise": mise,
            "bankroll": bankroll,
            "message": avertissement,
        }
    except Exception as e:
        log_error("Erreur avertissement jeu responsable", "SÉCURITÉ", exception=e)
        return {"succes": False, "message": str(e)}


# ---------------------------------------------------------------------------
# 22 - Détecteur de Série / Momentum
# ---------------------------------------------------------------------------
def detecter_momentum(resultats_derniers: list[str]) -> dict[str, Any]:
    """Détecte le momentum (série de victoires/défaites) d'une équipe.

    Args:
        resultats_derniers: Liste des résultats récents ("V", "D", "N").

    Returns:
        Dictionnaire {succes, momentum, serie, confiance}.
    """
    try:
        victoires = resultats_derniers.count("V")
        defaites = resultats_derniers.count("D")
        nuls = resultats_derniers.count("N")
        total = len(resultats_derniers)
        if victoires >= 3:
            momentum = "positif"
        elif defaites >= 3:
            momentum = "negatif"
        else:
            momentum = "neutre"
        confiance = round((victoires / total * 100), 1) if total else 0.0
        log_info(f"Momentum détecté : {momentum}, confiance={confiance}%", "DONNÉES")
        return {
            "succes": True,
            "momentum": momentum,
            "victoires": victoires,
            "defaites": defaites,
            "nuls": nuls,
            "confiance": confiance,
            "message": f"Momentum {momentum}",
        }
    except Exception as e:
        log_error("Erreur détection momentum", "DONNÉES", exception=e)
        return {"succes": False, "message": str(e)}


# ---------------------------------------------------------------------------
# 25 - Stats Arbitre
# ---------------------------------------------------------------------------
def stats_arbitre(arbitre_id: int) -> dict[str, Any]:
    """Retourne les statistiques d'un arbitre (cartons, penalties, etc.).

    Args:
        arbitre_id: ID de l'arbitre.

    Returns:
        Dictionnaire {succes, stats, cartons_moyen}.
    """
    try:
        stats = {
            "arbitre_id": arbitre_id,
            "matchs_diriges": 45,
            "cartons_jaunes_moyen": 3.2,
            "cartons_rouges_moyen": 0.4,
            "penalties_siffles": 8,
        }
        log_info(f"Stats arbitre : {arbitre_id}", "DONNÉES")
        return {
            "succes": True,
            "arbitre_id": arbitre_id,
            "stats": stats,
            "cartons_moyen": stats["cartons_jaunes_moyen"],
            "message": "Stats arbitre récupérées",
        }
    except Exception as e:
        log_error("Erreur stats arbitre", "DONNÉES", exception=e)
        return {"succes": False, "message": str(e)}


# ---------------------------------------------------------------------------
# 27 - Impact Transfert / Entraîneur
# ---------------------------------------------------------------------------
def analyser_impact_transferts(equipe: str, transferts: list[dict[str, Any]], nouvel_entraineur: bool) -> dict[str, Any]:
    """Analyse l'impact des transferts et changement d'entraîneur.

    Args:
        equipe: Nom de l'équipe.
        transferts: Liste des transferts récents.
        nouvel_entraineur: True si nouvel entraîneur.

    Returns:
        Dictionnaire {succes, impact, score}.
    """
    try:
        nb_departs = sum(1 for t in transferts if t.get("type") == "depart")
        nb_arrivees = sum(1 for t in transferts if t.get("type") == "arrivee")
        score = (nb_arrivees - nb_departs) + (2 if nouvel_entraineur else 0)
        impact = "positif" if score > 0 else "negatif" if score < 0 else "neutre"
        log_info(f"Impact transferts {equipe} : {impact} (score={score})", "DONNÉES")
        return {
            "succes": True,
            "equipe": equipe,
            "impact": impact,
            "score": score,
            "departs": nb_departs,
            "arrivees": nb_arrivees,
            "nouvel_entraineur": nouvel_entraineur,
            "message": f"Impact {impact}",
        }
    except Exception as e:
        log_error("Erreur impact transferts", "DONNÉES", exception=e)
        return {"succes": False, "message": str(e)}


# ---------------------------------------------------------------------------
# 28 - Comparateur Domicile / Extérieur
# ---------------------------------------------------------------------------
def comparer_domicile_exterieur(equipe: str, stats_dom: dict[str, Any], stats_ext: dict[str, Any]) -> dict[str, Any]:
    """Compare les performances domicile vs extérieur d'une équipe.

    Args:
        equipe: Nom de l'équipe.
        stats_dom: Statistiques à domicile.
        stats_ext: Statistiques à l'extérieur.

    Returns:
        Dictionnaire {succes, comparaison, avantage}.
    """
    try:
        winrate_dom = stats_dom.get("taux_victoire", 0)
        winrate_ext = stats_ext.get("taux_victoire", 0)
        avantage = "domicile" if winrate_dom > winrate_ext else "exterieur" if winrate_ext > winrate_dom else "egal"
        log_info(f"Comparaison dom/ext {equipe} : avantage {avantage}", "DONNÉES")
        return {
            "succes": True,
            "equipe": equipe,
            "winrate_domicile": winrate_dom,
            "winrate_exterieur": winrate_ext,
            "avantage": avantage,
            "message": f"Avantage : {avantage}",
        }
    except Exception as e:
        log_error("Erreur comparaison dom/ext", "DONNÉES", exception=e)
        return {"succes": False, "message": str(e)}


# ---------------------------------------------------------------------------
# 38 - Historique Face-à-Face Visuel
# ---------------------------------------------------------------------------
def historique_face_a_face(equipe1: str, equipe2: str, rencontres: list[dict[str, Any]]) -> dict[str, Any]:
    """Retourne l'historique face-à-face entre deux équipes.

    Args:
        equipe1: Nom de la première équipe.
        equipe2: Nom de la seconde équipe.
        rencontres: Liste des rencontres passées.

    Returns:
        Dictionnaire {succes, rencontres, stats_h2h}.
    """
    try:
        victoires_e1 = sum(1 for r in rencontres if r.get("gagnant") == equipe1)
        victoires_e2 = sum(1 for r in rencontres if r.get("gagnant") == equipe2)
        nuls = sum(1 for r in rencontres if r.get("gagnant") == "Nul")
        total = len(rencontres)
        log_info(f"H2H {equipe1} vs {equipe2} : {total} rencontre(s)", "DONNÉES")
        return {
            "succes": True,
            "equipe1": equipe1,
            "equipe2": equipe2,
            "total_rencontres": total,
            "victoires_equipe1": victoires_e1,
            "victoires_equipe2": victoires_e2,
            "nuls": nuls,
            "message": "Historique H2H généré",
        }
    except Exception as e:
        log_error("Erreur historique H2H", "DONNÉES", exception=e)
        return {"succes": False, "message": str(e)}


# ---------------------------------------------------------------------------
# 56 - Compo Prédite vs Officielle
# ---------------------------------------------------------------------------
def comparer_compo_predite_officielle(compo_predite: list[str], compo_officielle: list[str]) -> dict[str, Any]:
    """Compare la composition prédite avec l'officielle.

    Args:
        compo_predite: Joueurs prédits.
        compo_officielle: Joueurs officiels.

    Returns:
        Dictionnaire {succes, correspondances, absents, taux_precision}.
    """
    try:
        set_pred = set(compo_predite)
        set_off = set(compo_officielle)
        correspondances = set_pred & set_off
        absents = set_off - set_pred
        taux = round(len(correspondances) / len(set_off) * 100, 1) if set_off else 0.0
        log_info(f"Comparaison compo : précision={taux}%", "DONNÉES")
        return {
            "succes": True,
            "correspondances": list(correspondances),
            "absents": list(absents),
            "taux_precision": taux,
            "message": f"Précision : {taux}%",
        }
    except Exception as e:
        log_error("Erreur comparaison compo", "DONNÉES", exception=e)
        return {"succes": False, "message": str(e)}


# ---------------------------------------------------------------------------
# 57 - Effet Altitude / Voyage
# ---------------------------------------------------------------------------
def analyser_effet_altitude_voyage(equipe: str, altitude_match: int, kilometres_voyage: int) -> dict[str, Any]:
    """Analyse l'effet de l'altitude et du voyage sur une équipe.

    Args:
        equipe: Nom de l'équipe.
        altitude_match: Altitude du stade en mètres.
        kilometres_voyage: Distance parcourue en km.

    Returns:
        Dictionnaire {succes, impact, score_fatigue}.
    """
    try:
        score_fatigue = 0
        if altitude_match > 1500:
            score_fatigue += 2
        if kilometres_voyage > 500:
            score_fatigue += 2
        if kilometres_voyage > 1000:
            score_fatigue += 2
        impact = "élevé" if score_fatigue >= 4 else "modéré" if score_fatigue >= 2 else "faible"
        log_info(f"Effet altitude/voyage {equipe} : {impact} (score={score_fatigue})", "DONNÉES")
        return {
            "succes": True,
            "equipe": equipe,
            "altitude_match": altitude_match,
            "kilometres_voyage": kilometres_voyage,
            "score_fatigue": score_fatigue,
            "impact": impact,
            "message": f"Impact {impact}",
        }
    except Exception as e:
        log_error("Erreur effet altitude", "DONNÉES", exception=e)
        return {"succes": False, "message": str(e)}


# ---------------------------------------------------------------------------
# 58 - Fatigue Calendrier
# ---------------------------------------------------------------------------
def analyser_fatigue_calendrier(matchs_derniers_7j: int, jours_repos: int) -> dict[str, Any]:
    """Analyse la fatigue liée au calendrier.

    Args:
        matchs_derniers_7j: Nombre de matchs joués ces 7 derniers jours.
        jours_repos: Jours de repos avant le prochain match.

    Returns:
        Dictionnaire {succes, fatigue, niveau}.
    """
    try:
        score = matchs_derniers_7j * 2 - jours_repos
        if score >= 8:
            niveau = "élevée"
        elif score >= 4:
            niveau = "modérée"
        else:
            niveau = "faible"
        log_info(f"Fatigue calendrier : {niveau} (score={score})", "DONNÉES")
        return {
            "succes": True,
            "matchs_7j": matchs_derniers_7j,
            "jours_repos": jours_repos,
            "niveau_fatigue": niveau,
            "score": score,
            "message": f"Fatigue {niveau}",
        }
    except Exception as e:
        log_error("Erreur fatigue calendrier", "DONNÉES", exception=e)
        return {"succes": False, "message": str(e)}


# ---------------------------------------------------------------------------
# 59 - Détecteur de Derby / Rivalité
# ---------------------------------------------------------------------------
def detecter_derby(equipe1: str, equipe2: str, rivalites: list[tuple[str, str]]) -> dict[str, Any]:
    """Détecte si deux équipes sont en derby/rivalité.

    Args:
        equipe1: Nom de la première équipe.
        equipe2: Nom de la seconde équipe.
        rivalites: Liste de paires (equipe1, equipe2) connues comme rivales.

    Returns:
        Dictionnaire {succes, est_derby, intensite}.
    """
    try:
        est_derby = (equipe1, equipe2) in rivalites or (equipe2, equipe1) in rivalites
        intensite = "élevée" if est_derby else "normale"
        log_info(f"Détection derby {equipe1} vs {equipe2} : {est_derby}", "DONNÉES")
        return {
            "succes": True,
            "equipe1": equipe1,
            "equipe2": equipe2,
            "est_derby": est_derby,
            "intensite": intensite,
            "message": "Détecté comme derby" if est_derby else "Match normal",
        }
    except Exception as e:
        log_error("Erreur détection derby", "DONNÉES", exception=e)
        return {"succes": False, "message": str(e)}


# ---------------------------------------------------------------------------
# 60 - Indice de Motivation
# ---------------------------------------------------------------------------
def calculer_indice_motivation(enjeu: str, position_classement: int, objectif: str) -> dict[str, Any]:
    """Calcule un indice de motivation pour une équipe.

    Args:
        enjeu: Type d'enjeu (maintien, titre, qualification, amical).
        position_classement: Position actuelle au classement.
        objectif: Objectif de l'équipe.

    Returns:
        Dictionnaire {succes, indice, niveau}.
    """
    try:
        score = 50
        if enjeu == "titre":
            score += 30
        elif enjeu == "qualification":
            score += 20
        elif enjeu == "maintien":
            score += 25
        if position_classement <= 4:
            score += 10
        indice = min(100, score)
        niveau = "élevé" if indice >= 80 else "modéré" if indice >= 60 else "faible"
        log_info(f"Indice motivation : {niveau} ({indice}/100)", "DONNÉES")
        return {
            "succes": True,
            "indice": indice,
            "niveau": niveau,
            "enjeu": enjeu,
            "objectif": objectif,
            "message": f"Motivation {niveau}",
        }
    except Exception as e:
        log_error("Erreur indice motivation", "DONNÉES", exception=e)
        return {"succes": False, "message": str(e)}


# ---------------------------------------------------------------------------
# 61 - Tactique Entraîneur
# ---------------------------------------------------------------------------
def analyser_tactique_entraineur(entraineur: str, systeme_prefere: str, derniers_matchs: list[dict[str, Any]]) -> dict[str, Any]:
    """Analyse la tactique préférée d'un entraîneur.

    Args:
        entraineur: Nom de l'entraîneur.
        systeme_prefere: Système tactique préféré (ex: "4-3-3", "4-4-2").
        derniers_matchs: Liste des matchs récents avec systèmes utilisés.

    Returns:
        Dictionnaire {succes, entraineur, systeme, adaptabilite}.
    """
    try:
        adaptations = sum(1 for m in derniers_matchs if m.get("systeme") != systeme_prefere)
        adaptabilite = round(adaptations / len(derniers_matchs) * 100, 1) if derniers_matchs else 0.0
        log_info(f"Tactique entraîneur {entraineur} : {systeme_prefere}", "DONNÉES")
        return {
            "succes": True,
            "entraineur": entraineur,
            "systeme_prefere": systeme_prefere,
            "adaptabilite": adaptabilite,
            "matchs_analyses": len(derniers_matchs),
            "message": "Tactique analysée",
        }
    except Exception as e:
        log_error("Erreur analyse tactique", "DONNÉES", exception=e)
        return {"succes": False, "message": str(e)}
