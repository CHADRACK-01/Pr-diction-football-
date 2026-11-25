# tests/test_fonctionnalites_restantes.py
"""
Tests unitaires pour core.experience.fonctionnalites_restantes (11 fonctionnalités).

Ces tests vérifient le comportement pur de chaque fonction sans dépendance
externe (TTS, STT, Google Calendar, API tiers). Aucune clé API requise.
Conformément à la section 12 du référentiel REGLES_ET_METHODES.
"""

from __future__ import annotations

from core.experience.fonctionnalites_restantes import (
    activer_mode_expert,
    calculer_elo_live,
    creer_calendrier_equipes,
    creer_groupe_vip,
    executer_commande_vocale,
    generer_analyse_video_courte,
    generer_resume_audio,
    generer_resume_vocal_ia_30s,
    moderer_mots_interdits,
    sync_match_calendrier_google,
    verifier_anti_spam,
)

# ---------------------------------------------------------------------------
# 10 - Calendrier Perso Mes Équipes
# ---------------------------------------------------------------------------

class TestCreerCalendrierEquipes:
    def test_succes(self):
        r = creer_calendrier_equipes(1, ["TP Mazembe", "Vita Club"])
        assert r["succes"] is True
        assert r["user_id"] == 1
        assert r["equipes"] == ["TP Mazembe", "Vita Club"]
        assert r["total"] == 2
        assert r["calendrier_id"].startswith("CAL-")

    def test_liste_vide(self):
        r = creer_calendrier_equipes(2, [])
        assert r["succes"] is True
        assert r["total"] == 0


# ---------------------------------------------------------------------------
# 15 - Analyse Vidéo Courte Auto
# ---------------------------------------------------------------------------

class TestGenererAnalyseVideoCourte:
    def test_succes_defaut(self):
        r = generer_analyse_video_courte(42)
        assert r["succes"] is True
        assert r["match_id"] == 42
        assert r["duree_secondes"] == 60
        assert r["video_id"].startswith("VID-")

    def test_duree_personnalisee(self):
        r = generer_analyse_video_courte(42, temps_secondes=30)
        assert r["duree_secondes"] == 30


# ---------------------------------------------------------------------------
# 17 - Groupe VIP Auto-Modéré
# ---------------------------------------------------------------------------

class TestCreerGroupeVip:
    def test_succes(self):
        r = creer_groupe_vip("VIP Foot", 1, 5000.0)
        assert r["succes"] is True
        assert r["nom"] == "VIP Foot"
        assert r["createur_id"] == 1
        assert r["prix_abonnement"] == 5000.0
        assert r["statut"] == "actif"
        assert r["groupe_id"].startswith("VIP-")


# ---------------------------------------------------------------------------
# 37 - Résumé Vocal / Audio (partielle, TTS requis)
# ---------------------------------------------------------------------------

class TestGenererResumeAudio:
    def test_succes(self):
        r = generer_resume_audio("Victoire de TP Mazembe 2-1", langue="fr")
        assert r["succes"] is True
        assert r["audio_id"].startswith("AUDIO-")
        assert r["langue"] == "fr"
        assert r["duree_estimee"] > 0
        assert r["statut"] == "en_attente_tts"

    def test_sans_voix(self):
        r = generer_resume_audio("Test", voix=None)
        assert r["succes"] is True
        assert r["voix"] is None


# ---------------------------------------------------------------------------
# 51 - Résumé Vocal IA 30s (partielle, TTS requis)
# ---------------------------------------------------------------------------

class TestGenererResumeVocalIA30s:
    def test_succes(self):
        r = generer_resume_vocal_ia_30s(7, "Résumé du match")
        assert r["succes"] is True
        assert r["audio_id"].startswith("VOX30-")
        assert r["match_id"] == 7
        assert r["duree_ciblee"] == 30
        assert r["statut"] == "en_attente_tts"


# ---------------------------------------------------------------------------
# 63 - Élo Live qui Bouge
# ---------------------------------------------------------------------------

class TestCalculerEloLive:
    def test_victoire_equipe_a(self):
        r = calculer_elo_live("A", "B", 2, 1, elo_a=1500, elo_b=1500)
        assert r["succes"] is True
        assert r["variation_a"] > 0
        assert r["variation_b"] < 0
        assert r["elo_a_nouveau"] > 1500
        assert r["elo_b_nouveau"] < 1500
        assert r["score"] == "2-1"

    def test_nul(self):
        r = calculer_elo_live("A", "B", 1, 1, elo_a=1500, elo_b=1500)
        assert r["succes"] is True
        assert r["variation_a"] == 0
        assert r["variation_b"] == 0

    def test_victoire_equipe_b(self):
        r = calculer_elo_live("A", "B", 0, 3, elo_a=1500, elo_b=1500)
        assert r["succes"] is True
        assert r["variation_a"] < 0
        assert r["variation_b"] > 0


# ---------------------------------------------------------------------------
# 83 - Commande Vocale (partielle, STT requis)
# ---------------------------------------------------------------------------

class TestExecuterCommandeVocale:
    def test_prono(self):
        r = executer_commande_vocale("donne moi un prono", 1)
        assert r["succes"] is True
        assert r["action"] == "demander_pronostic"

    def test_resultat(self):
        r = executer_commande_vocale("quel est le score", 2)
        assert r["succes"] is True
        assert r["action"] == "consulter_resultat"

    def test_bankroll(self):
        r = executer_commande_vocale("ma bankroll", 3)
        assert r["succes"] is True
        assert r["action"] == "consulter_bankroll"

    def test_aide(self):
        r = executer_commande_vocale("aide", 4)
        assert r["succes"] is True
        assert r["action"] == "aide"

    def test_inconnu(self):
        r = executer_commande_vocale("blablabla", 5)
        assert r["succes"] is True
        assert r["action"] == "inconnu"


# ---------------------------------------------------------------------------
# 86 - Sync Calendrier Google (partielle, credentials requis)
# ---------------------------------------------------------------------------

class TestSyncMatchCalendrierGoogle:
    def test_succes(self):
        r = sync_match_calendrier_google(100, "TP Mazembe vs Vita", "2024-01-15T15:00:00")
        assert r["succes"] is True
        assert r["evenement_id"].startswith("GCAL-")
        assert r["match_id"] == 100
        assert r["statut"] == "en_attente_credentials_google"

    def test_avec_calendrier_id(self):
        r = sync_match_calendrier_google(100, "Match", "2024-01-15", calendrier_id="cal_123")
        assert r["calendrier_id"] == "cal_123"


# ---------------------------------------------------------------------------
# 90 - Mode Expert Débloquable
# ---------------------------------------------------------------------------

class TestActiverModeExpert:
    def test_debloque_anciennete_suffisante(self):
        r = activer_mode_expert(1, jours_anciennete=30)
        assert r["succes"] is True
        assert r["debloque"] is True
        assert r["mode_expert"] is True

    def test_pas_debloque_anciennete_insuffisante(self):
        r = activer_mode_expert(2, jours_anciennete=10)
        assert r["succes"] is True
        assert r["debloque"] is False
        assert r["mode_expert"] is False


# ---------------------------------------------------------------------------
# 112 - Modération Mots Interdits
# ---------------------------------------------------------------------------

class TestModererMotsInterdits:
    def test_texte_propre(self):
        r = moderer_mots_interdits("Bonjour le monde")
        assert r["succes"] is True
        assert r["propre"] is True
        assert r["mots_detectes"] == []

    def test_texte_avec_mots_interdits(self):
        r = moderer_mots_interdits("C'est une arnaque spam")
        assert r["succes"] is True
        assert r["propre"] is False
        assert "arnaque" in r["mots_detectes"]
        assert "spam" in r["mots_detectes"]
        assert "[***]" in r["texte_nettoye"]

    def test_liste_personnalisee(self):
        r = moderer_mots_interdits("motsecret", liste_mots_interdits=["motsecret"])
        assert r["propre"] is False
        assert "motsecret" in r["mots_detectes"]


# ---------------------------------------------------------------------------
# 113 - Anti-Spam Auto
# ---------------------------------------------------------------------------

class TestVerifierAntiSpam:
    def test_message_normal_pas_spam(self):
        r = verifier_anti_spam(1, "Bonjour tout le monde")
        assert r["succes"] is True
        assert r["est_spam"] is False
        assert r["action"] == "autoriser"

    def test_message_duplique_est_spam(self):
        r = verifier_anti_spam(1, "même message", historique_messages=["même message"])
        assert r["est_spam"] is True
        assert r["action"] == "bloquer"
        assert "message_duplique" in r["raisons"]

    def test_majuscules_excessives_sont_spam(self):
        r = verifier_anti_spam(1, "HTTP://EXAMPLE.COM")
        assert r["est_spam"] is True
        assert "majuscules_excessives" in r["raisons"]
        assert "lien_detecte" in r["raisons"]

    def test_lien_suspect_est_spam(self):
        r = verifier_anti_spam(1, "HTTP://EXAMPLE.COM")
        assert r["est_spam"] is True
        assert "lien_detecte" in r["raisons"]
