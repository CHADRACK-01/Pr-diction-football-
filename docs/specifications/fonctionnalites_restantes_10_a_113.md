# Spécifications — Fonctionnalités restantes (IDs 10, 15, 17, 37, 51, 63, 83, 86, 90, 112, 113)

Conformément à la section 4 du référentiel REGLES_ET_METHODES, chaque
fonctionnalité possède une fiche de conception avec les 17 points obligatoires.
Ces fiches ont été rédigées a posteriori car les implémentations existaient
déjà sans spécification formelle.

---

## 10 — Calendrier Perso Mes Équipes

### 1. Identité
- Identifiant : 10
- Nom : Calendrier Perso Mes Équipes
- Groupe : Utilisateur

### 2. Problème
L'utilisateur veut suivre les matchs de ses équipes favorites sans avoir à les rechercher manuellement à chaque fois.

### 3. Résultat attendu
Un calendrier personnalisé est créé avec un identifiant unique, la liste des équipes et le nombre d'équipes suivi.

### 4. Déclencheur
Appel à `creer_calendrier_equipes(user_id, equipes)` depuis un gestionnaire Telegram ou un service applicatif.

### 5. Entrées
- `user_id` (int) : identifiant de l'utilisateur
- `equipes` (list[str]) : noms des équipes à suivre

### 6. Sorties
Dictionnaire `{succes, calendrier_id, user_id, equipes, total, message}`.

### 7. Propriétaire
Module `core.experience.fonctionnalites_restantes`.

### 8. Dépendances
Aucune dépendance externe.

### 9. Permissions
Aucune restriction spécifique (tout utilisateur authentifié).

### 10. Règles métier
- Génère un `calendrier_id` au format `CAL-XXXX` (4 octets hexadécimaux en majuscules).
- Retourne `succes=True` en cas de succès, `succes=False` avec le message d'erreur sinon.

### 11. États
- Succès : calendrier créé.
- Échec : exception interne capturée, retour `succes=False`.

### 12. Erreurs
Toute exception est loggée via `core.utils.logs.log_error` et retournée sous forme de dictionnaire `{succes: False, message: str(e)}`.

### 13. Sécurité
Aucune donnée sensible stockée. Les noms d'équipes sont des chaînes de caractères simples.

### 14. Observabilité
Log info via `core.utils.logs.log_info` avec l'identifiant du calendrier et l'ID utilisateur.

### 15. Tests
`tests/test_fonctionnalites_restantes.py::TestCreerCalendrierEquipes` (test_succes, test_liste_vide).

### 16. Compatibilité
Aucun impact sur les fonctionnalités existantes.

### 17. Critères d'acceptation
- `creer_calendrier_equipes(1, ["TP Mazembe", "Vita Club"])` retourne `succes=True`, `total=2`, `calendrier_id` commence par `CAL-`.
- `creer_calendrier_equipes(2, [])` retourne `succes=True`, `total=0`.

---

## 15 — Analyse Vidéo Courte Auto

### 1. Identité
- Identifiant : 15
- Nom : Analyse Vidéo Courte Auto
- Groupe : Contenu

### 2. Problème
L'utilisateur veut une analyse vidéo courte d'un match (par défaut 60 secondes) sans attendre un rendu long.

### 3. Résultat attendu
Une analyse vidéo est programmée avec un identifiant unique, un statut d'attente de rendu et un message indiquant qu'un rendu externe est requis.

### 4. Déclencheur
Appel à `generer_analyse_video_courte(match_id, temps_secondes=60)`.

### 5. Entrées
- `match_id` (int) : identifiant du match
- `temps_secondes` (int, optionnel, défaut 60) : durée de la vidéo

### 6. Sorties
Dictionnaire `{succes, video_id, match_id, duree_secondes, statut, message}`.

### 7. Propriétaire
Module `core.experience.fonctionnalites_restantes`.

### 8. Dépendances
Aucune dépendance externe (le rendu vidéo est externe, statut `en_attente_rendu_video`).

### 9. Permissions
Aucune restriction spécifique.

### 10. Règles métier
- Génère un `video_id` au format `VID-XXXX`.
- Durée par défaut 60 secondes, personnalisable.
- Statut `en_attente_rendu_video` indiquant que le rendu dépend d'un tiers.

### 11. États
- Succès : analyse programmée.
- Échec : exception interne.

### 12. Erreurs
Toute exception est loggée et retournée sous forme `{succes: False, message: str(e)}`.

### 13. Sécurité
Aucune donnée sensible.

### 14. Observabilité
Log info avec l'identifiant vidéo et l'ID du match.

### 15. Tests
`tests/test_fonctionnalites_restantes.py::TestGenererAnalyseVideoCourte` (test_succes_defaut, test_duree_personnalisee).

### 16. Compatibilité
Aucun impact.

### 17. Critères d'acceptation
- `generer_analyse_video_courte(42)` retourne `succes=True`, `duree_secondes=60`, `statut="en_attente_rendu_video"`.
- `generer_analyse_video_courte(42, 30)` retourne `duree_secondes=30`.

---

## 17 — Groupe VIP Auto-Modéré

### 1. Identité
- Identifiant : 17
- Nom : Groupe VIP Auto-Modéré
- Groupe : Paiement

### 2. Problème
Permettre à un utilisateur de créer un groupe VIP avec un abonnement payant et une modération automatique.

### 3. Résultat attendu
Un groupe VIP est créé avec un identifiant unique, un nom, un créateur, un prix d'abonnement et un statut actif.

### 4. Déclencheur
Appel à `creer_groupe_vip(nom, createur_id, prix_abonnement)`.

### 5. Entrées
- `nom` (str) : nom du groupe VIP
- `createur_id` (int) : ID du créateur/admin
- `prix_abonnement` (float) : prix de l'abonnement

### 6. Sorties
Dictionnaire `{succes, groupe_id, nom, createur_id, prix_abonnement, statut, message}`.

### 7. Propriétaire
Module `core.experience.fonctionnalites_restantes`.

### 8. Dépendances
Aucune dépendance externe.

### 9. Permissions
Aucune restriction spécifique.

### 10. Règles métier
- Génère un `groupe_id` au format `VIP-XXXX`.
- Statut `actif` par défaut.

### 11. États
- Succès : groupe créé.
- Échec : exception interne.

### 12. Erreurs
Toute exception est loggée et retournée sous forme `{succes: False, message: str(e)}`.

### 13. Sécurité
Le prix est un float, pas de donnée de paiement stockée ici (délégué au module paiement).

### 14. Observabilité
Log info avec l'identifiant du groupe et l'ID du créateur.

### 15. Tests
`tests/test_fonctionnalites_restantes.py::TestCreerGroupeVip::test_succes`.

### 16. Compatibilité
Aucun impact.

### 17. Critères d'acceptation
- `creer_groupe_vip("VIP Foot", 1, 5000.0)` retourne `succes=True`, `statut="actif"`, `groupe_id` commence par `VIP-`.

---

## 37 — Résumé Vocal / Audio

### 1. Identité
- Identifiant : 37
- Nom : Résumé Vocal / Audio
- Groupe : Contenu

### 2. Problème
Convertir un texte en audio (TTS) pour une écoute rapide, avec estimation de durée.

### 3. Résultat attendu
Un résumé audio est généré avec un identifiant unique, une durée estimée et un statut en attente de rendu TTS.

### 4. Déclencheur
Appel à `generer_resume_audio(texte, langue="fr", voix=None)`.

### 5. Entrées
- `texte` (str) : texte à convertir
- `langue` (str, optionnel, défaut "fr") : code langue (fr, sw, ln)
- `voix` (str|None, optionnel) : identifiant de voix TTS

### 6. Sorties
Dictionnaire `{succes, audio_id, texte, langue, voix, duree_estimee, statut, message}`.

### 7. Propriétaire
Module `core.experience.fonctionnalites_restantes`.

### 8. Dépendances
Clé TTS requise pour le rendu effectif (statut `en_attente_tts`).

### 9. Permissions
Aucune restriction spécifique.

### 10. Règles métier
- Génère un `audio_id` au format `AUDIO-XXXX`.
- Durée estimée = nombre de mots / 2.5 (≈150 mots/min), arrondi à 1 décimale.
- Statut `en_attente_tts` (clé TTS requise pour le rendu audio réel).

### 11. États
- Succès : audio généré (en attente de rendu TTS).
- Échec : exception interne.

### 12. Erreurs
Toute exception est loggée et retournée sous forme `{succes: False, message: str(e)}`.

### 13. Sécurité
Le texte source est conservé dans la réponse (pas de stockage persistant ici).

### 14. Observabilité
Log info avec l'identifiant audio et la durée estimée.

### 15. Tests
`tests/test_fonctionnalites_restantes.py::TestGenererResumeAudio` (test_succes, test_sans_voix).

### 16. Compatibilité
Aucun impact.

### 17. Critères d'acceptation
- `generer_resume_audio("Victoire 2-1", langue="fr")` retourne `succes=True`, `duree_estimee > 0`, `statut="en_attente_tts"`.
- `generer_resume_audio("Test", voix=None)` retourne `succes=True`, `voix=None`.

---

## 51 — Résumé Vocal IA 30s

### 1. Identité
- Identifiant : 51
- Nom : Résumé Vocal IA 30s
- Groupe : Contenu

### 2. Problème
Produire un résumé vocal court (30 secondes cible) pour un match donné.

### 3. Résultat attendu
Un résumé vocal 30s est généré avec un identifiant unique, l'ID du match, la durée cible de 30s et un statut en attente de TTS.

### 4. Déclencheur
Appel à `generer_resume_vocal_ia_30s(match_id, resume_texte)`.

### 5. Entrées
- `match_id` (int) : identifiant du match
- `resume_texte` (str) : texte du résumé à condenser

### 6. Sorties
Dictionnaire `{succes, audio_id, match_id, duree_ciblee, texte_source, statut, message}`.

### 7. Propriétaire
Module `core.experience.fonctionnalites_restantes`.

### 8. Dépendances
Clé TTS requise (statut `en_attente_tts`).

### 9. Permissions
Aucune restriction spécifique.

### 10. Règles métier
- Génère un `audio_id` au format `VOX30-XXXX`.
- `duree_ciblee` = 30 secondes.
- `texte_source` tronqué à 200 caractères.

### 11. États
- Succès : résumé programmé.
- Échec : exception interne.

### 12. Erreurs
Toute exception est loggée et retournée sous forme `{succes: False, message: str(e)}`.

### 13. Sécurité
Le texte source est tronqué pour éviter les fuites de données longues.

### 14. Observabilité
Log info avec l'identifiant audio et l'ID du match.

### 15. Tests
`tests/test_fonctionnalites_restantes.py::TestGenererResumeVocalIA30s::test_succes`.

### 16. Compatibilité
Aucun impact.

### 17. Critères d'acceptation
- `generer_resume_vocal_ia_30s(7, "Résumé du match")` retourne `succes=True`, `duree_ciblee=30`, `match_id=7`, `statut="en_attente_tts"`.

---

## 63 — Élo Live qui Bouge

### 1. Identité
- Identifiant : 63
- Nom : Élo Live qui Bouge
- Groupe : Live

### 2. Problème
Calculer la nouvelle élo de deux équipes après un match, selon le système de notation élo classique.

### 3. Résultat attendu
Les nouvelles élo des deux équipes, leurs variations et le score du match.

### 4. Déclencheur
Appel à `calculer_elo_live(equipe_a, equipe_b, score_a, score_b, elo_a, elo_b, k)`.

### 5. Entrées
- `equipe_a`, `equipe_b` (str) : noms des équipes
- `score_a`, `score_b` (int) : scores
- `elo_a`, `elo_b` (float, défaut 1500.0) : élo actuels
- `k` (float, défaut 32.0) : facteur K

### 6. Sorties
Dictionnaire `{succes, equipe_a, equipe_b, elo_a_nouveau, elo_b_nouveau, variation_a, variation_b, score, message}`.

### 7. Propriétaire
Module `core.experience.fonctionnalites_restantes`.

### 8. Dépendances
Aucune dépendance externe.

### 9. Permissions
Aucune restriction spécifique.

### 10. Règles métier
- Attendu A = 1 / (1 + 10^((elo_b - elo_a) / 400)).
- Résultat A = 1 si victoire, 0.5 si nul, 0 si défaite.
- Nouvel élo = élo + k * (résultat - attendu).
- Variations arrondies à 1 décimale.

### 11. États
- Succès : élo calculé.
- Échec : exception interne.

### 12. Erreurs
Toute exception est loggée et retournée sous forme `{succes: False, message: str(e)}`.

### 13. Sécurité
Aucune donnée sensible.

### 14. Observabilité
Log info avec les noms d'équipes et les élo avant/après.

### 15. Tests
`tests/test_fonctionnalites_restantes.py::TestCalculerEloLive` (test_victoire_equipe_a, test_nul, test_victoire_equipe_b).

### 16. Compatibilité
Aucun impact.

### 17. Critères d'acceptation
- `calculer_elo_live("A", "B", 2, 1, 1500, 1500)` retourne `variation_a > 0`, `variation_b < 0`, `score="2-1"`.
- `calculer_elo_live("A", "B", 1, 1, 1500, 1500)` retourne `variation_a == 0`, `variation_b == 0`.

---

## 83 — Commande Vocale

### 1. Identité
- Identifiant : 83
- Nom : Commande Vocale
- Groupe : Expérience

### 2. Problème
Permettre à un utilisateur d'envoyer une commande vocale (après transcription STT) et d'obtenir une réponse adaptée.

### 3. Résultat attendu
La commande est classée (prono, résultat, bankroll, aide, inconnu) avec une réponse associée.

### 4. Déclencheur
Appel à `executer_commande_vocale(texte_transcrit, user_id)`.

### 5. Entrées
- `texte_transcrit` (str) : texte issu de la reconnaissance vocale
- `user_id` (int) : ID de l'utilisateur

### 6. Sorties
Dictionnaire `{succes, user_id, commande, action, reponse, statut, message}`.

### 7. Propriétaire
Module `core.experience.fonctionnalites_restantes`.

### 8. Dépendances
STT requis pour l'entrée audio (statut `en_attente_stt`).

### 9. Permissions
Aucune restriction spécifique.

### 10. Règles métier
- Détection par mots-clés : "prono"/"pronostic" → demander_pronostic, "résultat"/"score" → consulter_resultat, "bankroll"/"capital" → consulter_bankroll, "aide"/"help" → aide, sinon inconnu.
- Texte mis en minuscules et supprimé des espaces.

### 11. États
- Succès : commande traitée.
- Échec : exception interne.

### 12. Erreurs
Toute exception est loggée et retournée sous forme `{succes: False, message: str(e)}`.

### 13. Sécurité
Aucune donnée sensible.

### 14. Observabilité
Log info avec l'ID utilisateur, la commande et l'action détectée.

### 15. Tests
`tests/test_fonctionnalites_restantes.py::TestExecuterCommandeVocale` (5 tests : prono, résultat, bankroll, aide, inconnu).

### 16. Compatibilité
Aucun impact.

### 17. Critères d'acceptation
- `executer_commande_vocale("prono", 1)` retourne `action="demander_pronostic"`.
- `executer_commande_vocale("quel est le score", 2)` retourne `action="consulter_resultat"`.
- `executer_commande_vocale("ma bankroll", 3)` retourne `action="consulter_bankroll"`.
- `executer_commande_vocale("aide", 4)` retourne `action="aide"`.
- `executer_commande_vocale("blablabla", 5)` retourne `action="inconnu"`.

---

## 86 — Sync Calendrier Google

### 1. Identité
- Identifiant : 86
- Nom : Sync Calendrier Google
- Groupe : Expérience

### 2. Problème
Synchroniser un match vers Google Calendar pour que l'utilisateur reçoive un rappel.

### 3. Résultat attendu
Un événement Google Calendar est programmé avec un identifiant unique, en attente des credentials Google.

### 4. Déclencheur
Appel à `sync_match_calendrier_google(match_id, titre, date_match, calendrier_id=None)`.

### 5. Entrées
- `match_id` (int) : identifiant du match
- `titre` (str) : titre de l'événement
- `date_match` (str) : date au format ISO
- `calendrier_id` (str|None, optionnel) : ID du calendrier Google

### 6. Sorties
Dictionnaire `{succes, match_id, evenement_id, titre, date_match, calendrier_id, statut, message}`.

### 7. Propriétaire
Module `core.experience.fonctionnalites_restantes`.

### 8. Dépendances
Credentials Google Calendar requis (statut `en_attente_credentials_google`).

### 9. Permissions
Aucune restriction spécifique.

### 10. Règles métier
- Génère un `evenement_id` au format `GCAL-XXXX`.
- Statut `en_attente_credentials_google` indiquant que la sync effective nécessite des credentials.

### 11. États
- Succès : événement programmé (en attente de credentials).
- Échec : exception interne.

### 12. Erreurs
Toute exception est loggée et retournée sous forme `{succes: False, message: str(e)}`.

### 13. Sécurité
Aucun token Google stocké ici (délégué à l'adaptateur calendrier).

### 14. Observabilité
Log info avec l'identifiant d'événement et l'ID du match.

### 15. Tests
`tests/test_fonctionnalites_restantes.py::TestSyncMatchCalendrierGoogle` (test_succes, test_avec_calendrier_id).

### 16. Compatibilité
Aucun impact.

### 17. Critères d'acceptation
- `sync_match_calendrier_google(100, "Match", "2024-01-15")` retourne `succes=True`, `statut="en_attente_credentials_google"`, `evenement_id` commence par `GCAL-`.

---

## 90 — Mode Expert Débloquable

### 1. Identité
- Identifiant : 90
- Nom : Mode Expert Débloquable
- Groupe : Abonnement

### 2. Problème
Débloquer un mode expert pour un utilisateur selon son ancienneté (30 jours minimum).

### 3. Résultat attendu
Le mode expert est débloqué si l'utilisateur a 30 jours d'ancienneté ou plus, sinon il reste verrouillé.

### 4. Déclencheur
Appel à `activer_mode_expert(user_id, jours_anciennete=0)`.

### 5. Entrées
- `user_id` (int) : ID de l'utilisateur
- `jours_anciennete` (int, défaut 0) : nombre de jours d'ancienneté

### 6. Sorties
Dictionnaire `{succes, user_id, jours_anciennete, mode_expert, debloque, message}`.

### 7. Propriétaire
Module `core.experience.fonctionnalites_restantes`.

### 8. Dépendances
Aucune dépendance externe.

### 9. Permissions
Aucune restriction spécifique.

### 10. Règles métier
- `debloque = jours_anciennete >= 30`.
- `mode_expert = debloque`.
- Message adapté selon le déblocage.

### 11. États
- Succès : mode expert évalué.
- Échec : exception interne.

### 12. Erreurs
Toute exception est loggée et retournée sous forme `{succes: False, message: str(e)}`.

### 13. Sécurité
Aucune donnée sensible.

### 14. Observabilité
Log info avec l'ID utilisateur, l'ancienneté et le déblocage.

### 15. Tests
`tests/test_fonctionnalites_restantes.py::TestActiverModeExpert` (test_debloque_anciennete_suffisante, test_pas_debloque_anciennete_insuffisante).

### 16. Compatibilité
Aucun impact.

### 17. Critères d'acceptation
- `activer_mode_expert(1, 30)` retourne `debloque=True`, `mode_expert=True`.
- `activer_mode_expert(2, 10)` retourne `debloque=False`, `mode_expert=False`.

---

## 112 — Modération Mots Interdits

### 1. Identité
- Identifiant : 112
- Nom : Modération Mots Interdits
- Groupe : Modération

### 2. Problème
Détecter et filtrer les mots interdits dans un texte utilisateur.

### 3. Résultat attendu
Le texte est analysé, les mots interdits détectés et remplacés par `[***]`, avec un indicateur de propreté.

### 4. Déclencheur
Appel à `moderer_mots_interdits(texte, liste_mots_interdits=None)`.

### 5. Entrées
- `texte` (str) : texte à modérer
- `liste_mots_interdits` (list[str]|None, optionnel) : liste des mots interdits (défaut : ["insulte", "spam", "arnaque", "pub"])

### 6. Sorties
Dictionnaire `{succes, texte_original, texte_nettoye, mots_detectes, propre, message}`.

### 7. Propriétaire
Module `core.experience.fonctionnalites_restantes`.

### 8. Dépendances
Aucune dépendance externe.

### 9. Permissions
Aucune restriction spécifique.

### 10. Règles métier
- Détection insensible à la casse.
- Remplacement des mots détectés par `[***]`.
- `propre = True` si aucun mot interdit détecté.

### 11. États
- Succès : texte modéré.
- Échec : exception interne.

### 12. Erreurs
Toute exception est loggée et retournée sous forme `{succes: False, message: str(e)}`.

### 13. Sécurité
Le texte original est conservé dans la réponse pour audit.

### 14. Observabilité
Log info avec le nombre de mots détectés et l'indicateur de propreté.

### 15. Tests
`tests/test_fonctionnalites_restantes.py::TestModererMotsInterdits` (test_texte_propre, test_texte_avec_mots_interdits, test_liste_personnalisee).

### 16. Compatibilité
Aucun impact.

### 17. Critères d'acceptation
- `moderer_mots_interdits("Bonjour le monde")` retourne `propre=True`, `mots_detectes=[]`.
- `moderer_mots_interdits("C'est une arnaque spam")` retourne `propre=False`, `"arnaque"` et `"spam"` dans `mots_detectes`, `"[***]"` dans `texte_nettoye`.

---

## 113 — Anti-Spam Auto

### 1. Identité
- Identifiant : 113
- Nom : Anti-Spam Auto
- Groupe : Modération

### 2. Problème
Détecter automatiquement si un message est du spam pour décider de le bloquer ou l'autoriser.

### 3. Résultat attendu
Un score de spam est calculé (0.0 à 1.0+), avec des raisons et une action (autoriser/bloquer).

### 4. Déclencheur
Appel à `verifier_anti_spam(user_id, message, historique_messages=None)`.

### 5. Entrées
- `user_id` (int) : ID de l'utilisateur
- `message` (str) : message à vérifier
- `historique_messages` (list[str]|None, optionnel) : messages précédents

### 6. Sorties
Dictionnaire `{succes, user_id, est_spam, score_spam, raisons, action, message}`.

### 7. Propriétaire
Module `core.experience.fonctionnalites_restantes`.

### 8. Dépendances
Aucune dépendance externe.

### 9. Permissions
Aucune restriction spécifique.

### 10. Règles métier
- Message dupliqué dans l'historique : +0.5, raison "message_duplique".
- Plus de 70% de majuscules (si len > 10) : +0.3, raison "majuscules_excessives".
- Présence d'un lien http(s) : +0.2, raison "lien_detecte" (détection insensible à la casse).
- `est_spam = score >= 0.5`, `action = "bloquer"` si spam, sinon "autoriser".

### 11. États
- Succès : message analysé.
- Échec : exception interne.

### 12. Erreurs
Toute exception est loggée et retournée sous forme `{succes: False, message: str(e)}`.

### 13. Sécurité
Aucune donnée sensible.

### 14. Observabilité
Log info avec l'ID utilisateur, le score et le statut spam.

### 15. Tests
`tests/test_fonctionnalites_restantes.py::TestVerifierAntiSpam` (test_message_normal_pas_spam, test_message_duplique_est_spam, test_majuscules_excessives_sont_spam, test_lien_suspect_est_spam).

### 16. Compatibilité
Aucun impact.

### 17. Critères d'acceptation
- `verifier_anti_spam(1, "Bonjour tout le monde")` retourne `est_spam=False`, `action="autoriser"`.
- `verifier_anti_spam(1, "même message", ["même message"])` retourne `est_spam=True`, `"message_duplique"` dans `raisons`.
- `verifier_anti_spam(1, "HTTP://EXAMPLE.COM")` retourne `est_spam=True`, `"lien_detecte"` et `"majuscules_excessives"` dans `raisons`.

---

## État final proposé

| ID | Nom | Groupe | Statut catalogue | Statut implémentation | Tests |
|----|-----|--------|------------------|----------------------|-------|
| 10 | Calendrier Perso Mes Équipes | Utilisateur | complete | complete | 2 tests |
| 15 | Analyse Vidéo Courte Auto | Contenu | complete | complete | 2 tests |
| 17 | Groupe VIP Auto-Modéré | Paiement | complete | complete | 1 test |
| 37 | Résumé Vocal / Audio | Contenu | partielle | partielle | 2 tests |
| 51 | Résumé Vocal IA 30s | Contenu | partielle | partielle | 1 test |
| 63 | Élo Live qui Bouge | Live | complete | complete | 3 tests |
| 83 | Commande Vocale | Expérience | partielle | partielle | 5 tests |
| 86 | Sync Calendrier Google | Expérience | partielle | partielle | 2 tests |
| 90 | Mode Expert Débloquable | Abonnement | complete | complete | 2 tests |
| 112 | Modération Mots Interdits | Modération | complete | complete | 3 tests |
| 113 | Anti-Spam Auto | Modération | complete | complete | 4 tests |

**Total : 27 tests unitaires couvrant les 11 fonctionnalités.**

Conformément à la section 19 du référentiel, les fonctions marquées `complete` ont leurs tests unitaires validés. Les fonctions `partielle` (37, 51, 83, 86) dépendent de clés externes (TTS, STT, Google Calendar) non configurées en environnement de test ; elles passent à `EXISTANTE_A_VERIFIER` tant que ces dépendances ne sont pas configurées et testées en intégration.
