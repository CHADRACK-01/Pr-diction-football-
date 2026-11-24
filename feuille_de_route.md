# Feuille de route complète du bot de pronostics

Ce document remplace la revue précédente. Il regroupe les 700 fonctionnalités du catalogue et les 239 nouvelles idées, décide des doublons, les range par phase, et décrit les situations réelles que le bot doit gérer.

## 1. Comment lire ce document

- **Phase** : l’ordre dans lequel on fait les choses. Phase 0 d’abord : un bot qui ne démarre pas ne sert à rien.
- **Décision** : pour les doublons seulement. « SUPPRIMER », « FUSIONNER→N » (intégrer à la fonction N), « GARDER SÉPARÉ », « À VÉRIFIER ».
- **Statut** : « À auditer/tester » veut dire que la fonction n’est pas confirmée dans le code. « Fait » ne concerne que 7 entrées, toutes liées à la QA.

## 2. Principes non négociables

1. **Ne jamais présenter un pari comme gagnant.** Chaque recommandation affiche son incertitude et la possibilité de perdre.
2. **Protéger le joueur avant de l’engager.** Les limites, pauses et ressources d’aide passent avant les fonctions d’engagement.
3. **Ne pas inciter à parier davantage.** Concours, tirages au sort, loteries, roues et récompenses de connexion sont retirés (décision 145, 146, 264, 265 et équivalents).
4. **Publier les résultats, y compris les mauvais.** La transparence vaut mieux qu’un historique embelli.
5. **Ne jamais montrer une donnée non fiable comme certaine.** En cas de panne ou de donnée manquante, le bot dit ce qu’il ne sait pas.
6. **Vérifier la légalité avant chaque marché.** Âge, pays, paiements et publicité dépendent de la réglementation locale.

## 3. Décisions sur les doublons

| # | Titre | Décision | Raison |
|---|---|---|---|
| 51 | Résumé Vocal IA 30s | FUSIONNER→37 | Résumé vocal : garder 37 ; la version « IA 30 s » devient un format de 37. |
| 98 | Vérification Paiement Mobile Money Auto | FUSIONNER→31 | Mobile Money : une intégration, la vérification du paiement en est une étape. |
| 103 | Tableau de Bord Revenus | GARDER SÉPARÉ | Tableau de bord revenus : public admin. |
| 120 | Gestion des Ligues Actives | À VÉRIFIER | Ligues actives : vérifier si distinct de 251 avant de décider. |
| 143 | Tableau de Bord Revendeur | GARDER SÉPARÉ | Tableau de bord revendeur : public différent de 103. |
| 145 | Gestion des Concours | SUPPRIMER | Concours : retiré pour protéger les joueurs (incitation à parier). |
| 146 | Tirage au Sort Auto | SUPPRIMER | Tirage au sort : même logique d’incitation, retiré. |
| 216 | Journal d’Actions Admin | SUPPRIMER | Doublon du journal admin 114. |
| 227 | Blacklist Numéros | FUSIONNER→147 | Blacklist numéros : garder 147 qui est plus complète. |
| 229 | Limite de Comptes par Téléphone | FUSIONNER→148 | Limite de comptes : une seule règle, appliquée par numéro ET par téléphone. |
| 251 | Gestion des Ligues | GARDER 251 | Gestion des ligues : fonction principale. |
| 264 | Gestion des Concours | SUPPRIMER | Doublon de 145 et concours : retiré. |
| 265 | Tirage au Sort Auto | SUPPRIMER | Doublon de 146 et tirage au sort : retiré. |
| 279 | Page Facebook Auto-Post | FUSIONNER→76 | Même besoin (publication Facebook) : garder 76, ajouter sa version « page » comme paramètre. |
| 281 | Story Instagram Sondage | GARDER SÉPARÉ | Story Instagram sondage et template : deux besoins distincts. |
| 299 | Giveaway WhatsApp Statut | GARDER SÉPARÉ | Giveaway WhatsApp : retiré car concours. (Statut WhatsApp 274 gardé.) |
| 383 | Statistiques Arbitre VAR | FUSIONNER→575 | Statistiques arbitre VAR : données intégrées dans 575. |
| 420 | Paiement Automatisé des Commissions Partenaires | FUSIONNER→262 | Commissions partenaires : une seule logique de paiement partenaire. |
| 457 | Gestion des équipes promues | FUSIONNER→252 | Équipes promues : sous-cas de la gestion des équipes. |
| 458 | Gestion des équipes renommées | FUSIONNER→252 | Équipes renommées : sous-cas de la gestion des équipes. |
| 466 | Score de Brier par marché | FUSIONNER→583 | Score de Brier : une seule métrique de calibration. |
| 467 | Log-loss par compétition | FUSIONNER→584 | Log-loss : une seule métrique. |
| 474 | Détection de surconfiance | FUSIONNER→590 | Détection de surconfiance : doublon de 590. |
| 493 | Rapport par niveau de confiance | FUSIONNER→473 | Rapport par niveau de confiance : intégré au rapport documenté. |
| 528 | Politique de conservation des données | FUSIONNER→682 | Durée de conservation : une politique unique. |
| 547 | Tableau de bord de disponibilité | GARDER SÉPARÉ | Disponibilité : distinct des tableaux de bord de revenus. |
| 575 | Arbitre et VAR | GARDER 575 | Arbitre et VAR : garder 575 comme fiche complète. |
| 585 | Courbe de fiabilité des probabilités | FUSIONNER→465 | Courbe de fiabilité : une seule fonction. |
| 589 | Calibration par marché et par compétition | FUSIONNER→464 | Calibration par marché et compétition : même fonction. |
| 590 | Détection de surconfiance du modèle | GARDER 590 | Surconfiance : garder 590 ; 435 (dérive) reste séparé. |
| 591 | Détection de sous-confiance du modèle | GARDER SÉPARÉ | Sous-confiance : opposé de 590, à garder séparé. |
| 597 | Score de calibration par segment | FUSIONNER→583 | Calibration par segment : une seule fonction de calibration. |
| 606 | Fiabilité des sources de composition | FUSIONNER→557 | Sources médicales et composition : une fiche « fiabilité des sources ». |
| 607 | Horodatage de la composition probable | FUSIONNER→598 | Composition probable : horodatage intégré à 598. |
| 608 | Composition probable et blessures | FUSIONNER→598 | Composition et blessures : intégré à 598. |
| 613 | Mise selon Kelly fractionné | FUSIONNER→482 | Kelly : une seule fonction, paramétrée en fraction. |
| 640 | Métadonnées de modèle | FUSIONNER→26 | Métadonnées de modèle : partie du versionnage du modèle xG. |
| 651 | Interrupteurs avec date d'expiration | FUSIONNER→102 | Expiration : même mécanisme pour codes et interrupteurs. |
| 667 | Limitation de débit par utilisateur | FUSIONNER→538 | Limitation de débit : une seule règle centralisée. |
| 669 | Rapport mensuel de consommation | FUSIONNER→79 | Rapports mensuels : garder 79 et y ajouter le rapport de consommation. |
| 687 | Accès restreint aux données sensibles | FUSIONNER→529 | Accès aux données sensibles : un journal et une restriction. |

Les autres paires détectées (faux positifs : deux modèles ou fonctions distincts portant un nom proche) sont conservées séparément.

## 4. Les phases

- **Phase 0 — Réparer et sécuriser le bot** : 60 fonctionnalités
- **Phase 1 — Protéger les joueurs et prouver la fiabilité** : 92 fonctionnalités
- **Phase 2 — Cœur prédictif et marchés** : 194 fonctionnalités
- **Phase 3 — Expérience et engagement** : 264 fonctionnalités
- **Phase 4 — Croissance et monétisation** : 52 fonctionnalités
- **Phase 5 — Intégrations externes (dépendent de tiers)** : 29 fonctionnalités
- **À écarter (incitation au jeu ou hors périmètre)** : 9 fonctionnalités
- **Nouvelles idées** : 239 à trier dans ces mêmes phases.

## 5. Situations que le bot doit gérer

### Premier passage du parieur
Accueil simple, tutoriel, mode démo sans paiement, glossaire, questions fréquentes.
Fonctionnalités liées : 124 Message de Bienvenue Personnalisable ; 125 FAQ Dynamique Admin ; 175 Code Promo Montant Fixe ; 315 Offre de Bienvenue Limitée ; 327 Vocal de Bienvenue Personnalisé ; 339 Apprentissage Auto-Adaptatif des Alias d’Équipes.

### Le parieur perd plusieurs fois de suite
Stop-loss, pause suggérée, réduction de mise, mode prudent, soutien non médical.
Fonctionnalités liées : 16 Avertissement Jeu Responsable ; 47 Plan Anti-Perte ; 351 Profils de Parieurs Personnalisés ; 353 Coffre-Fort à Codes (🎟️ Mes codes achetés) ; 396 Verrou Émotionnel (Conseiller Financier) ; 482 Kelly fractionné prudent.

### Le parieur gagne une série
Bilan positif, mais rappel que la variance existe ; pas d’encouragement à augmenter les mises.
Fonctionnalités liées : 22 Détecteur de Série / Momentum ; 118 Corriger un Résultat ; 251 Gestion des Ligues ; 301 Série “7 Jours, 7 Tickets” ; 352 Suivi de Bankroll & Bilan Financier ; 378 Infographie Bilan du Week-end.

### Le parieur veut tout miser sur un match
Plafond de mise journalier, avertissement, calcul de Kelly fractionnaire.
Fonctionnalités liées : 5 Simulateur de Cash-Out ; 41 Gestion Kelly Automatique ; 42 Plan de Mise Fixe / Progressif ; 54 Checklist Avant de Parier ; 148 Limite de Comptes par Numéro ; 169 Appareils Utilisés.

### Le parieur demande un conseil financier
Rappel clair que le bot ne garantit rien, information factuelle sans recommandation personnalisée de placement.
Fonctionnalités liées : 16 Avertissement Jeu Responsable ; 43 Constructeur de Combiné par Risque ; 186 Modération des Pronos IA ; 234 Score de Risque ; 362 Intégration IA Multimodale (Analyse de Photo de Coupon) ; 483 Exposition cumulée par match.

### Le parieur veut arrêter ou s’auto-exclure
Auto-exclusion, ressources d’aide, pause, désactivation des notifications.
Fonctionnalités liées : 16 Avertissement Jeu Responsable ; 121 Gestion des Marchés Actifs ; 144 Bannir un Revendeur Tricheur ; 183 Gestion des Opérateurs ; 251 Gestion des Ligues ; 335 Circuit Breaker sur les APIs Externes.

### Un match est reporté ou annulé
Mise à jour automatique, annulation des alertes, information de l’utilisateur.
Fonctionnalités liées : 1 Alertes Live / But en direct ; 3 Tracker de Chute de Cotes ; 4 Alerte Compo Officielle / Absents ; 24 Alerte But Tardif ; 35 Alerte Météo Pelouse ; 39 Alerte Underdog.

### La composition change à la dernière minute
Alerte, mise à jour de la prédiction, horodatage.
Fonctionnalités liées : 550 Détection des blessures non annoncées ; 562 Alerte de composition médicale incomplète ; 586 Décomposition de Brier (fiabilité, résolution) ; 598 Composition probable par équipe ; 601 Incertitude de composition ; 602 Impact de la composition sur les marchés.

### Le fournisseur de données tombe
Mode dégradé, message clair, alerte admin, pas de prédiction fausse présentée comme fiable.
Fonctionnalités liées : 11 Ticket de la Semaine en PDF ; 40 Export TikTok / Statut en 1 Clic ; 92 Gestion Utilisateurs par Statut ; 116 Panneau Pronos Manuel ; 125 FAQ Dynamique Admin ; 126 Tickets Support avec Statut.

### La cote bouge après la prédiction
Historique des cotes, valeur recalculée, alerte si l’avantage disparaît.
Fonctionnalités liées : 2 Détecteur de Value Bet ; 3 Tracker de Chute de Cotes ; 14 Comparateur de Bookmakers RDC ; 23 Spécialiste Match Nul ; 39 Alerte Underdog ; 43 Constructeur de Combiné par Risque.

### Le bookmaker limite le compte
Information, conseil de diversifier, comparaison de bookmakers.
Fonctionnalités liées : 2 Détecteur de Value Bet ; 14 Comparateur de Bookmakers RDC ; 28 Comparateur Domicile / Extérieur ; 256 Gestion des Bookmakers ; 399 Couverture Spéciale Petites Ligues Africaines ; 419 Affiliation Bookmakers & Tracking Campagnes.

### Un paiement échoue ou est contesté
Relance, remboursement selon règles, facture.
Fonctionnalités liées : 17 Groupe VIP Auto-Modéré ; 31 Paiement Auto Airtel / M-Pesa / Orange ; 91 Dashboard Admin Temps Réel ; 97 Historique Paiements par Utilisateur ; 98 Vérification Paiement Mobile Money Auto ; 107 Offre de Relance Auto.

### Un utilisateur demande la suppression de ses données
Export puis suppression, confirmation.
Fonctionnalités liées : 40 Export TikTok / Statut en 1 Clic ; 128 Export Utilisateurs CSV / Excel ; 129 Export Revenus pour Compta ; 206 Export des Logs Admin ; 222 Export CSV Segment ; 529 Journal d’accès aux données sensibles.

### Un admin fait une erreur
Journal d’audit, sauvegarde, restauration, rôles limités.
Fonctionnalités liées : 115 Rôles Admin ; 130 Sauvegarde Manuelle en 1 Clic ; 131 Restauration Backup ; 135 Contrôle Consommation API ; 149 Mode Audit Complet ; 205 Sauvegarde des Paramètres.

### Une prédiction se trompe
Explication après match, rapport d’erreurs, transparence des résultats.
Fonctionnalités liées : 65 Explication du Prono ; 132 Logs d’Erreurs Lisibles ; 134 Alerte si Pic d’Erreurs ; 161 Résumé Quotidien Admin à 07h00 ; 228 Whitelist VIP ; 340 Health Score Dynamique des Sources.

### Le modèle se dégrade
Détection de dérive, rollback, comparaison A/B.
Fonctionnalités liées : 202 Rollback en 1 Clic ; 342 Calibration Adaptative des Seuils (Top Affiches) ; 430 Modèles spécialisés par marché ; 435 Détection de dérive du modèle ; 464 Calibration par marché ; 469 Détection de prédictions incohérentes.

### Un utilisateur tente de contourner une limite
Journal, blocage, détection d’abus.
Fonctionnalités liées : 89 Détecteur de Match Truqué Suspect ; 147 Blacklist Numéros / Appareils ; 148 Limite de Comptes par Numéro ; 199 Gestion des Signalements ; 227 Blacklist Numéros ; 229 Limite de Comptes par Téléphone.

### Un utilisateur vulnérable est détecté (signes de dépendance)
Message de soutien, pause proposée, aide, pas de pronostic supplémentaire pendant la pause.
Fonctionnalités liées : 16 Avertissement Jeu Responsable ; 334 Verrouillage des Dépendances & Format Natif ML ; 509 Marchés combinés cohérents ; 653 Interrupteurs dépendants ; 655 Rôle et propriétaire d'un interrupteur ; 695 Mise à jour des dépendances obsolètes.

## 6. Feuille de route par phase

### Phase 0 — Réparer et sécuriser le bot (60)

#### Gouvernance du catalogue et des interrupteurs (11)
> **Réalité parieur :** Le parieur ne voit pas les interrupteurs, mais leur mauvaise gestion peut activer une fonction non prête devant lui.

- **647. Source de vérité du catalogue de fonctionnalités** — Définir une source unique décrivant chaque fonctionnalité et son état.
- **648. Métadonnées d'interrupteur (propriétaire, date)** — Enrichir chaque interrupteur avec un propriétaire, une date de création et un motif.
- **649. Historique des bascules d'interrupteurs** — Journaliser chaque activation ou désactivation d'un interrupteur avec horodatage.
- **650. Interrupteurs par environnement** — Permettre un état d'activation distinct selon l'environnement (dev, recette, prod).
- **651. Interrupteurs avec date d'expiration** — **FUSIONNER→102** — Prévoir une date d'expiration pour éviter les interrupteurs oubliés.
- **652. Validation des identifiants de fonctionnalité** — Vérifier le format et l'unicité des feature_id avant enregistrement.
- **653. Interrupteurs dépendants** — Gérer les dépendances entre fonctionnalités pour éviter des états incohérents.
- **654. Audit des interrupteurs orphelins** — Repérer les feature_id présents en base mais plus utilisés dans le code.
- **656. Documentation générée depuis le catalogue** — Générer automatiquement une documentation listant les fonctionnalités et leur état.
- **657. Interrupteurs par segment d'utilisateurs** — Activer une fonctionnalité pour un sous-ensemble d'utilisateurs seulement.
- **658. Alerte sur interrupteur inactif depuis longtemps** — Signaler les interrupteurs désactivés depuis longtemps et probablement supprimables.

#### Performance, cache et maîtrise des coûts (10)
> **Réalité parieur :** Le parieur veut une réponse immédiate, surtout avant un coup d’envoi. Un bot lent perd l’utilisateur au moment critique.

- **536. Cache prédictif avec expiration** — Mettre en cache les prédictions avec version du modèle, version des données et expiration.
- **537. Cache par fournisseur** — Éviter les appels API répétés lorsque les données sont encore valides.
- **539. File de tâches persistante** — Exécuter notifications et traitements lourds avec reprise après redémarrage.
- **540. Verrous distribués des tâches** — Empêcher plusieurs instances de lancer le même traitement planifié.
- **541. Traitement par lots** — Regrouper les opérations de base et les appels compatibles pour réduire les coûts.
- **542. Mesure du coût par prédiction** — Suivre appels API, temps CPU, mémoire et coût estimé par prédiction.
- **543. Optimisation des requêtes** — Ajouter des index selon les requêtes réelles et suivre leur latence.
- **545. Arrêt gracieux** — Terminer les tâches en cours et libérer les ressources lors d’un redémarrage.
- **546. Circuit breaker configurable** — Mettre temporairement en pause une source défaillante et tester sa reprise.
- **547. Tableau de bord de disponibilité** — **GARDER SÉPARÉ** — Suivre latence, erreurs, fraîcheur, files d’attente et taux de succès.

#### Coûts, quotas et exploitation des fournisseurs (10)
> **Réalité parieur :** Un fournisseur qui tombe ou dépasse son quota coupe le service. Le parieur ne comprend pas pourquoi ses données manquent.

- **659. Suivi du coût par appel fournisseur** — Enregistrer le coût estimé de chaque appel à un fournisseur externe.
- **661. Alerte de dépassement de budget** — Notifier lorsqu'un seuil de dépense mensuel est atteint.
- **662. Répartition des coûts par fonctionnalité** — Attribuer les coûts aux fonctionnalités qui les génèrent.
- **663. Mesure de la latence par fournisseur** — Mesurer le temps de réponse de chaque fournisseur.
- **664. Repli automatique entre fournisseurs** — Basculer vers un fournisseur de secours lorsqu'un autre est indisponible.
- **665. Fenêtre de disponibilité des fournisseurs** — Déclarer les plages horaires de maintenance ou d'indisponibilité connues.
- **666. Journal des erreurs fournisseur** — Consigner les erreurs renvoyées par les fournisseurs pour analyse.
- **668. Estimation préalable du coût d'une requête** — Estimer le coût d'une requête avant de l'envoyer au fournisseur.
- **669. Rapport mensuel de consommation** — **FUSIONNER→79** — Produire un récapitulatif mensuel des appels et coûts par fournisseur.
- **670. Priorisation des requêtes en cas de saturation** — Définir un ordre de priorité lorsque les quotas sont proches d'être atteints.

#### Fiabilité, sécurité et gouvernance des données (9)
> **Réalité parieur :** Le parieur confie son argent et ses données. Une panne ou une fuite détruit la confiance plus vite que n’importe quelle mauvaise prédiction.

- **524. Authentification des webhooks** — Vérifier signature, secret, origine et horodatage des callbacks entrants.
- **525. Idempotence des événements** — Ignorer proprement les événements reçus plusieurs fois sans dupliquer les écritures.
- **527. Restauration testée** — Tester régulièrement la restauration plutôt que de vérifier uniquement l’existence des sauvegardes.
- **528. Politique de conservation des données** — **FUSIONNER→682** — Définir des durées adaptées aux données financières, sportives et de diagnostic.
- **529. Journal d’accès aux données sensibles** — Tracer les accès administratifs et les exports contenant des informations sensibles.
- **530. Gestion des secrets centralisée** — Retirer les secrets du code et contrôler leur rotation.
- **532. Validation des entrées externes** — Valider types, tailles, plages et encodages des données reçues.
- **533. Protection contre l’injection** — Utiliser des requêtes paramétrées et un encodage de sortie adapté au contexte.
- **534. Plan de réponse aux incidents** — Documenter détection, confinement, restauration et communication en cas d’incident.

#### Hygiène du dépôt et dette technique (9)
> **Réalité parieur :** Invisible pour le parieur, mais une dette technique élevée ralentit toutes les corrections et augmente le risque de bug en production.

- **691. Suppression du paquet mort core/betting/** — Retirer le paquet core/betting/, plus référencé, et vérifier l'absence d'imports résiduels.
- **692. Inventaire des modules non importés** — Lister les modules Python jamais importés dans le dépôt.
- **693. Nettoyage des scripts obsolètes** — Supprimer ou archiver les scripts qui ne sont plus utilisés.
- **694. Détection du code dupliqué** — Repérer les blocs de code répétés pouvant être factorisés.
- **696. Normalisation de l'arborescence** — Définir une organisation cohérente des dossiers et fichiers.
- **697. Vérification des fichiers volumineux versionnés** — Détecter les fichiers volumineux ou binaires versionnés par erreur.
- **698. Documentation des modules sans docstring** — Repérer les modules et fonctions dépourvus de docstring.
- **699. Suppression des migrations inutiles** — Nettoyer les migrations obsolètes ou jamais appliquées.
- **700. Tableau de bord de la dette technique** — Regrouper les indicateurs de dette technique dans un tableau de bord unique.

#### QA et non-régression (8)
> **Réalité parieur :** Le parieur ne voit jamais les tests, mais une régression silencieuse peut lui faire recevoir de mauvaises prédictions pendant des jours.

- **626. Tests de bout en bout du parcours utilisateur** — Simuler le parcours complet d'un utilisateur, de la commande Discord à la réponse finale.
- **628. Vérification des contrats d'API internes** — Contrôler que les modules respectent les formats d'échange attendus entre eux.
- **629. Tests de charge légère du service de prédiction** — Mesurer le temps de réponse sous un volume modéré de requêtes simultanées.
- **630. Contrôle de stabilité des réponses aux commandes Discord** — Vérifier que chaque commande renvoie une réponse formatée et stable.
- **631. Détection des sorties non déterministes** — Identifier les fonctions qui produisent des résultats variables sans graine fixée.
- **632. Rapport de couverture par module** — Produire un rapport de couverture de tests par module et par thème.
- **635. Vérification des valeurs par défaut des configurations** — Contrôler que chaque paramètre dispose d'une valeur par défaut sûre.
- **636. Journal de santé des tests en intégration continue** — Suivre l'évolution du taux de réussite et de la durée des tests dans le temps.

#### Catalogue initial (2)
> **Réalité parieur :** Le parieur veut une réponse simple et rapide : quel pari, pour quelle raison, et combien mettre. Il ne lit pas les statistiques en détail ; il attend une recommandation claire et honnête sur l’incertitude.

- **333. Garbage Collection Nocturne (03h15)** — Nettoyage auto des logs (>30j), paiements échoués (>90j) et fenêtre glissante de 5 ans sur la table matchs.
- **345. Health Check Externe (/ping + UptimeRobot)** — Surveillance HTTP toutes les 5 minutes avec alerte SMS/Email avant les plaintes clients.

#### Confidentialité et données personnelles (1)
> **Réalité parieur :** Le parieur veut savoir ce qui est collecté, pourquoi, et comment le supprimer. C’est une obligation légale et une condition de confiance.

- **686. Journalisation minimale par défaut** — Ne journaliser que le strict nécessaire par défaut.

### Phase 1 — Protéger les joueurs et prouver la fiabilité (92)

#### Probabilités, calibration et incertitude (27)
> **Réalité parieur :** Un parieur qui voit « 60 % » s’attend à gagner 6 fois sur 10. Si le modèle dit 60 % et qu’il gagne 40 % du temps, il perd son argent sans comprendre pourquoi. La calibration est donc ce qui rend la confiance légitime.

- **464. Calibration par marché** — Calibrer séparément les probabilités de chaque marché à partir de prédictions hors échantillon.
- **465. Courbes de fiabilité** — Comparer les fréquences observées aux probabilités annoncées par tranches.
- **466. Score de Brier par marché** — **FUSIONNER→583** — Mesurer l’erreur quadratique des probabilités pour suivre leur qualité.
- **467. Log-loss par compétition** — **FUSIONNER→584** — Mesurer la qualité probabiliste avec pénalisation des prédictions trop confiantes.
- **468. Intervalle d’incertitude** — Afficher une plage ou un niveau d’incertitude plutôt qu’un pourcentage isolé.
- **469. Détection de prédictions incohérentes** — Vérifier que les marchés dérivés restent compatibles avec les distributions sous-jacentes.
- **470. Seuil d’abstention adaptatif** — Ne pas publier lorsque la qualité des données ou l’incertitude dépasse les limites acceptées.
- **471. Calibration après changement de saison** — Vérifier la stabilité des probabilités au début d’une nouvelle saison.
- **472. Comparaison modèle et fréquence de base** — Comparer les performances à des références simples pour éviter la complexité inutile.
- **473. Rapport de confiance documenté** — Distinguer probabilité, confiance dans les données et qualité du modèle.
- **474. Détection de surconfiance** — **FUSIONNER→590** — Identifier les segments où les probabilités élevées se réalisent moins souvent qu’annoncé.
- **475. Contrôle de cohérence inter-marchés** — Vérifier les relations logiques entre 1N2, double chance, buts et scores exacts.
- **580. xG avancé par tir (post-shot xG)** — Estimer la qualité de chaque tir selon sa localisation et sa trajectoire.
- **581. xG contre par match** — Mesurer la qualité des occasions concédées par une équipe.
- **582. Écart xG et buts réels** — Suivre l’écart entre buts attendus et buts marqués.
- **583. Calibration par Brier score** — Évaluer la précision probabiliste avec le score de Brier.
- **584. Calibration par log-loss** — Pénaliser davantage les probabilités confiantes et fausses.
- **585. Courbe de fiabilité des probabilités** — **FUSIONNER→465** — Comparer probabilités annoncées et fréquences observées.
- **586. Décomposition de Brier (fiabilité, résolution)** — Séparer la fiabilité et la résolution du score global.
- **587. Recalibration isotonique** — Ajuster les probabilités par régression isotonique.
- **588. Recalibration par Platt scaling** — Recalibrer les sorties par une transformation logistique.
- **589. Calibration par marché et par compétition** — **FUSIONNER→464** — Contrôler la calibration séparément par segment.
- **590. Détection de surconfiance du modèle** — **GARDER 590** — Identifier les segments où le modèle est trop confiant.
- **592. xG ajusté à la qualité de l’adversaire** — Corriger le xG selon le niveau défensif adverse.
- **595. xG et finition au-dessus de la moyenne** — Repérer les finisseurs durablement au-dessus de leur xG.
- **596. Suivi de la dérive de calibration** — Alerter lorsque la calibration se dégrade dans le temps.
- **597. Score de calibration par segment** — **FUSIONNER→583** — Attribuer un score de calibration à chaque segment de prédiction.

#### Catalogue initial (17)
> **Réalité parieur :** Le parieur veut une réponse simple et rapide : quel pari, pour quelle raison, et combien mettre. Il ne lit pas les statistiques en détail ; il attend une recommandation claire et honnête sur l’incertitude.

- **16. Avertissement Jeu Responsable** — Après 3 pertes d’affilée, il propose une pause de 24h.
- **42. Plan de Mise Fixe / Progressif** — Tu choisis mise fixe, Martingale douce ou Fibonacci, le bot suit. ⚠ Un plan de mise progressif peut pousser à miser davantage après une perte : garde-fous obligatoires (plafond et pause).
- **47. Plan Anti-Perte** — Après 3 pertes, il bloque les gros combinés et ne propose que des sûrs. ⚠ Le nom « Plan Anti-Perte » promet une protection qui n’existe pas : à reformuler en « Plan de gestion des pertes » et à présenter comme une aide, pas une garantie.
- **130. Sauvegarde Manuelle en 1 Clic** — Bouton Backup = envoie la DB sur ton Telegram.
- **131. Restauration Backup** — Choisis une sauvegarde et restaure en 1 clic.
- **148. Limite de Comptes par Numéro** — 1 numéro = 1 compte Premium max.
- **153. Double Authentification Admin** — Code Telegram à chaque connexion.
- **176. Limite d’Utilisation Code Promo** — “Ce code ne marche que 100 fois”.
- **198. Limite de Partage** — 1 compte Premium ne peut pas être sur 5 téléphones.
- **205. Sauvegarde des Paramètres** — Tes réglages sont sauvegardés même si le serveur redémarre.
- **221. Segments Sauvegardés** — Sauvegarde ton filtre “VIP inactifs” pour le réutiliser chaque semaine.
- **229. Limite de Comptes par Téléphone** — **FUSIONNER→148** — 1 numéro = 1 compte max.
- **334. Verrouillage des Dépendances & Format Natif ML** — requirements.txt figé + double sauvegarde .pkl et format natif JSON/TXT LightGBM/XGBoost.
- **335. Circuit Breaker sur les APIs Externes** — Mise en pause 24h d’une API après 5 échecs consécutifs et plafond d’alertes Admin à 15/jour.
- **379. Mode “Copilote de Paris”** — Note de sécurité sur 10 attribuée au ticket composé par l’utilisateur avant validation.
- **396. Verrou Émotionnel (Conseiller Financier)** — Blocage temporaire des mises élevées après une série de pertes.
- **426. Blacklist Dynamique de Matchs Suspects** — Exclusion immédiate des rencontres signalées pour anomalies de cotes.

#### Validation scientifique et surveillance (12)
> **Réalité parieur :** Le parieur veut savoir si le bot est fiable. Des résultats publiés honnêtement, y compris les mauvais mois, construisent une confiance durable.

- **488. Backtesting chronologique** — Tester les stratégies sur des périodes successives en respectant l’information disponible à chaque date.
- **489. Séparation entraînement validation test** — Empêcher les données de test de participer à la sélection ou au réglage du modèle.
- **490. Registre des expériences** — Conserver paramètres, métriques, données et code de chaque expérience.
- **491. Rapport de performance par saison** — Comparer les performances sur plusieurs saisons sans agréger les périodes incompatibles.
- **492. Rapport par tranche de cote** — Mesurer les résultats selon le niveau de cote et la disponibilité des prix.
- **493. Rapport par niveau de confiance** — **FUSIONNER→473** — Vérifier empiriquement les groupes de prédictions selon leur probabilité annoncée.
- **494. Détection de fuite de données** — Repérer les variables qui contiennent indirectement des informations postérieures au match.
- **495. Test de robustesse** — Mesurer la sensibilité des résultats aux paramètres, aux périodes et aux sources.
- **496. Bootstrap des métriques** — Estimer l’incertitude statistique autour des taux et rendements observés.
- **497. Surveillance de dérive des performances** — Déclencher une alerte lorsque les métriques se dégradent sur une fenêtre suffisante.
- **498. Publication de bilans vérifiables** — Publier toutes les recommandations admissibles, y compris les pertes et les abstentions.
- **499. Audit de reproductibilité** — Permettre de recalculer une métrique à partir des prédictions, cotes et résultats archivés.

#### Confidentialité et données personnelles (9)
> **Réalité parieur :** Le parieur veut savoir ce qui est collecté, pourquoi, et comment le supprimer. C’est une obligation légale et une condition de confiance.

- **681. Inventaire des données personnelles traitées** — Recenser les données personnelles collectées, stockées et utilisées.
- **682. Durée de conservation des données** — Définir et appliquer une durée de conservation pour chaque type de donnée.
- **683. Droit à l'effacement des données utilisateur** — Permettre la suppression des données d'un utilisateur sur demande.
- **684. Anonymisation des journaux** — Retirer ou masquer les identifiants personnels des journaux techniques.
- **685. Consentement explicite au stockage** — Recueillir l'accord de l'utilisateur avant tout stockage durable.
- **687. Accès restreint aux données sensibles** — **FUSIONNER→529** — Limiter l'accès aux données sensibles aux seuls composants autorisés.
- **688. Export des données d'un utilisateur** — Fournir à un utilisateur l'ensemble des données le concernant sur demande.
- **689. Purge automatique des données expirées** — Supprimer automatiquement les données ayant dépassé leur durée de conservation.
- **690. Registre des traitements** — Documenter la finalité de chaque traitement de données.

#### Versionnage et évaluation de variantes de modèle (8)
> **Réalité parieur :** Le parieur ne doit pas être utilisé comme cobaye. Tester une variante sur un petit groupe, et seulement si elle est meilleure, protège tout le monde.

- **637. Registre des versions de modèle** — Tenir un registre des versions de modèle avec identifiant, date et description.
- **638. Comparaison A/B de deux variantes** — Comparer deux variantes sur un même échantillon et mesurer l'écart de performance.
- **639. Évaluation hors échantillon d'une variante** — Mesurer la performance d'une variante sur des données non vues à l'entraînement.
- **641. Promotion d'une variante en production** — Promouvoir une variante validée comme version active de production.
- **642. Retour arrière vers une version antérieure** — Revenir rapidement à une version de modèle précédente en cas de problème.
- **643. Mesure de l'écart entre variantes** — Quantifier la différence de prédictions entre deux variantes sur un même lot.
- **644. Évaluation de la robustesse aux données manquantes** — Tester le comportement d'une variante lorsque des champs attendus sont absents.
- **645. Historique des métriques par version** — Conserver l'évolution des métriques clés pour chaque version de modèle.

#### Cotes, value betting et risque (6)
> **Réalité parieur :** Le parieur compare des cotes qui bougent sans cesse. Il lui faut la meilleure cote disponible, la marge du bookmaker, et la certitude qu’une recommandation n’est pas un conseil garanti.

- **481. Gestion de bankroll plafonnée** — Appliquer des limites absolues et relatives de mise et éviter les mises automatiques agressives.
- **482. Kelly fractionné prudent** — Proposer une fraction limitée de Kelly uniquement avec probabilités calibrées et plafonds stricts.
- **483. Exposition cumulée par match** — Limiter le risque total sur plusieurs marchés corrélés d’une même rencontre.
- **485. Simulation de scénarios de pertes** — Montrer les séries négatives plausibles et le risque de ruine selon la mise.
- **611. Mise fixe plafonnée** — Limiter la mise à un montant fixe maximal par pari.
- **624. Alerte de perte de bankroll** — Prévenir lorsque les pertes dépassent un seuil défini.

#### Fiabilité, sécurité et gouvernance des données (3)
> **Réalité parieur :** Le parieur confie son argent et ses données. Une panne ou une fuite détruit la confiance plus vite que n’importe quelle mauvaise prédiction.

- **526. Chiffrement des sauvegardes** — Chiffrer les sauvegardes et limiter strictement les accès aux clés.
- **531. Contrôle d’accès par rôle** — Limiter chaque action selon le rôle et appliquer le principe du moindre privilège.
- **535. Conformité et transparence des prédictions** — Présenter les limites, les probabilités et les règles de publication de manière vérifiable.

#### Données et ingénierie (2)
> **Réalité parieur :** Le parieur ne voit pas les données, mais il voit leurs effets : une fiche joueur fausse ou une composition en retard fait perdre confiance. La qualité des données est invisible mais décisive.

- **440. Catalogue central des sources** — Décrire chaque fournisseur, ses compétitions, champs disponibles, limites, fraîcheur et conditions d’utilisation.
- **553. Suspensions pour carton rouge** — Gérer les matchs de suspension et le retour après exclusion.

#### Performance, cache et maîtrise des coûts (2)
> **Réalité parieur :** Le parieur veut une réponse immédiate, surtout avant un coup d’envoi. Un bot lent perd l’utilisateur au moment critique.

- **538. Limitation de débit centralisée** — Appliquer des limites par fournisseur, utilisateur et type de tâche.
- **544. Surveillance de la mémoire** — Mesurer l’utilisation mémoire et limiter les chargements simultanés de modèles.

#### QA et non-régression (2)
> **Réalité parieur :** Le parieur ne voit jamais les tests, mais une régression silencieuse peut lui faire recevoir de mauvaises prédictions pendant des jours.

- **627. Couverture des cas limites de saisie** — Tester les entrées vides, malformées ou hors bornes des commandes.
- **634. Tests de compatibilité des migrations de base** — Vérifier que les migrations s'appliquent sur une base existante sans perte de données.

#### Coûts, quotas et exploitation des fournisseurs (2)
> **Réalité parieur :** Un fournisseur qui tombe ou dépasse son quota coupe le service. Le parieur ne comprend pas pourquoi ses données manquent.

- **660. Quota journalier par fournisseur** — Fixer et contrôler un plafond d'appels par jour et par fournisseur.
- **667. Limitation de débit par utilisateur** — **FUSIONNER→538** — Limiter le nombre de requêtes qu'un utilisateur peut déclencher.

#### Prédictions en direct (1)
> **Réalité parieur :** Pendant le match, le parieur réagit vite et sous pression. Une alerte tardive ou fausse peut le conduire à parier sur une situation déjà dépassée.

- **512. Collecte live à fréquence adaptative** — Ajuster la fréquence de collecte selon l’état du match et les limites des fournisseurs.

#### Gouvernance du catalogue et des interrupteurs (1)
> **Réalité parieur :** Le parieur ne voit pas les interrupteurs, mais leur mauvaise gestion peut activer une fonction non prête devant lui.

- **655. Rôle et propriétaire d'un interrupteur** — Associer chaque interrupteur à un responsable pouvant décider de sa bascule.

### Phase 2 — Cœur prédictif et marchés (194)

#### Catalogue initial (65)
> **Réalité parieur :** Le parieur veut une réponse simple et rapide : quel pari, pour quelle raison, et combien mettre. Il ne lit pas les statistiques en détail ; il attend une recommandation claire et honnête sur l’incertitude.

- **1. Alertes Live / But en direct** — Le bot t’envoie un message dès qu’un but tombe et te dit si ton pari est validé.
- **2. Détecteur de Value Bet** — Il compare la proba IA et la cote du bookmaker. Si la cote est trop haute, il te dit “VALUE”.
- **3. Tracker de Chute de Cotes** — Alerte quand une cote chute vite, ex: 2.40 -> 1.85, signe d’une info importante.
- **5. Simulateur de Cash-Out** — Tu entres ta mise, il te dit combien tu gagnes si tu arrêtes ton pari maintenant.
- **7. Historique Vérifiable Public** — Commande /preuves, tu vois les 30 derniers jours gagnés/perdus, impossible à modifier.
- **14. Comparateur de Bookmakers RDC** — Montre la cote Winner.bet vs 1xBet vs BetWinner pour le même match.
- **23. Spécialiste Match Nul** — Filtre pour les nuls à grosse cote 3.30+ avec proba IA >32%.
- **24. Alerte But Tardif** — Détecte les équipes qui marquent après la 75e, propose un pari live.
- **26. Modèle xG** — Montre les buts attendus selon les occasions, pas seulement les scores.
- **38. Historique Face-à-Face Visuel** — “Sur 5 derniers Real-Barça: 4x BTTS Oui”, en tableau.
- **39. Alerte Underdog** — “Petite équipe 35% de chance mais cote 5.00”, petit billet fun.
- **41. Gestion Kelly Automatique** — Calcule la mise idéale selon ta bankroll, ex: 2% = 2.000 FC.
- **43. Constructeur de Combiné par Risque** — Tu dis “Je veux cote 3.00”, il construit le combiné seul.
- **44. Double Sûr du Jour** — 2 matchs ultra-sûrs combinés, cote 1.80-2.20.
- **52. Commentaire Live IA** — Pendant le match “Arsenal pousse, 8 tirs en 15 min, but imminent”.
- **54. Checklist Avant de Parier** — “As-tu vérifié compo ? Météo ? Mise ?” avant de valider.
- **63. Elo Live qui Bouge** — Classement Elo qui change après chaque but en live.
- **66. Backtest de Ta Stratégie** — “Si tu avais suivi Over 2.5 depuis 3 mois, tu serais à +34%”.
- **87. Graphique Évolution des Cotes** — Courbe “Cote passée de 2.50 à 1.90 en 24h”.
- **89. Détecteur de Match Truqué Suspect** — “Cotes bizarres + gros argent sur petit match = DANGER”.
- **93. Recherche Utilisateur** — Par ID / nom / numéro, tu vois tout son historique.
- **118. Corriger un Résultat** — Corrige le score et recalcule les bilans.
- **137. Planificateur de Tâches** — “Réentraîner le modèle chaque 1er du mois à 03h00”.
- **155. Historique de Connexion Admin** — “Connecté le 15/11 à 14h depuis Kinshasa”.
- **169. Appareils Utilisés** — Android 85%, iPhone 10%, PC 5%, optimise pour Android.
- **186. Modération des Pronos IA** — Tu proposes 5 pronos, tu en supprimes 1 risqué.
- **190. Historique des Pronos Envoyés** — Tous les pronos envoyés, heure, par qui, à combien de personnes.
- **192. Gestion des Canaux** — Canal Gratuit / VIP / Résultats, chacun ses règles.
- **193. Auto-Post Résultats** — À la fin du match, le bot poste le résultat seul.
- **201. Gestion des Mises à Jour** — Bouton “Mettre à jour” sans couper le service.
- **234. Score de Risque** — “Cet utilisateur partage ses pronos, risque élevé”.
- **236. Historique de Messages** — Tous les messages envoyés à un utilisateur.
- **242. Dupliquer un Prono** — “Reprends le prono d’hier et change juste la cote”.
- **248. Gestion des Cotes Manuelles** — Modifie une cote à la main si l’API se trompe.
- **256. Gestion des Bookmakers** — Ajoute un nouveau bookmaker avec ses cotes.
- **268. Gestion des Modèles IA** — Vois quel modèle est actif, son score, change en 1 clic.
- **269. Entraînement Manuel du Modèle** — Lance un réentraînement quand tu veux.
- **301. Série “7 Jours, 7 Tickets”** — Chaque jour pendant 7 jours, tu postes ton résultat, comme une série.
- **319. Groupe “Résultats du Jour”** — Groupe public où tu postes QUE les résultats, pas les pronos.
- **336. Fallback Mathématique Pur (Loi de Poisson)** — Bascule automatique sur calcul probabiliste pur si le modèle ML est corrompu ou indisponible.
- **338. Auto-Réentraînement Semestriel du Modèle** — Réentraînement fin août et fin janvier avec validation comparative par Brier Score.
- **343. Backup Hebdomadaire Automatique** — Envoi chaque dimanche à 04h00 du modèle IA et d’un dump de la base sur le Telegram de l’Admin.
- **351. Profils de Parieurs Personnalisés** — Filtre Prudent (>75%), Équilibré (>60%) ou Aventurier (Value Bets >3.00).
- **352. Suivi de Bankroll & Bilan Financier** — Simulation de capital de départ, taux de réussite et ROI personnel.
- **356. Pari du Jour Gratuit (Produit d’Appel)** — 1 prono haute fiabilité (>80%, cote >= 1.50) offert chaque jour aux comptes gratuits.
- **358. Défi Quotidien “Challenger vs IA”** — Mini-jeu quotidien où l’utilisateur affronte l’IA sur le match phare pour gagner de l’XP.
- **362. Intégration IA Multimodale (Analyse de Photo de Coupon)** — Envoie la photo d’un billet Winner.bet au bot pour obtenir une évaluation de risque.
- **367. Détecteur de Compo Inédite / Rotation** — Alerte immédiate si un coach aligne une équipe bis ou des jeunes.
- **368. Indice de Pression Psychologique** — Évaluation de l’enjeu mental (coach menacé, maintien, titre).
- **369. Historique Arbitres Spécial Derbys** — Statistiques dédiées aux matchs à haute tension.
- **371. Système de Badges de Profil** — “Expert Premier League”, “Maître du 1N2”, “Sniper de Cotes”.
- **375. Mini-Jeu de Penalty Virtuel dans le Chat** — Animation interactive pour gagner des points XP.
- **376. Mode “Chasseur de Value Bets”** — Scan automatique global pour isoler la plus grosse anomalie de cote du jour.
- **377. Alerte Live “But en Approche”** — Détection de forte pression offensive (tirs, corners) sur les 10 dernières minutes.
- **382. Analyseur de Billet Papier Kiosque** — Photo du ticket physique pour activer le suivi live automatique des scores.
- **386. Alerte Changement Brutal de Cote Pré-Match** — Notification en cas de hausse ou baisse soudaine à H-1.
- **389. Impact Pelouse (Synthétique vs Naturelle)** — Ajustement des probabilités de buts et blessures selon le terrain.
- **399. Couverture Spéciale Petites Ligues Africaines** — Base de données dédiée aux championnats locaux souvent mal cotés par les bookmakers.
- **401. Ticket “Frisson du Week-end” (Cote 10.00+)** — Suggestion fun à faible mise pour le divertissement.
- **402. Analyseur de Forme Mentale & Enjeu** — Pondération selon la position au classement (course au titre / maintien).
- **403. Simulateur de Classement Live** — Projection du classement en temps réel à chaque but inscrit.
- **409. Courbe de Progression Financière** — Graphique d’évolution de la bankroll façon trading.
- **412. Alerte “Match Piège Identifié”** — Mise en garde contre les favoris en déplacement difficile avant une coupe d’Europe.
- **414. Accès Pro aux Matrices de Poisson & Monte Carlo** — Transparence totale sur les probabilités mathématiques brutes.
- **423. Comparateur de Modèles IA en Production (Shadow Testing)** — Test silencieux d’un nouveau modèle avant bascule officielle.

#### Données et ingénierie (30)
> **Réalité parieur :** Le parieur ne voit pas les données, mais il voit leurs effets : une fiche joueur fausse ou une composition en retard fait perdre confiance. La qualité des données est invisible mais décisive.

- **441. Identifiants sportifs canoniques** — Relier les identifiants d’équipes, joueurs, matchs et compétitions entre fournisseurs.
- **442. Historique des changements d’équipe** — Conserver les renommages, fusions, promotions et alias sans perdre les anciennes correspondances.
- **443. Score de qualité des données** — Calculer un score par donnée selon fraîcheur, complétude, cohérence et provenance.
- **444. Détection de doublons de matchs** — Repérer les doublons multi-fournisseurs à partir des identifiants et des attributs temporels.
- **445. Réconciliation multi-sources** — Comparer les valeurs concurrentes et appliquer des règles de priorité documentées.
- **446. Historisation des instantanés** — Enregistrer les données disponibles à l’heure de la prédiction pour éviter les fuites temporelles.
- **447. Pipeline d’import incrémental** — Ne télécharger que les nouveaux événements et les modifications détectées.
- **448. Contrôle de fraîcheur des données** — Refuser ou dégrader explicitement une prédiction lorsque les données dépassent leur durée de validité.
- **449. Validation de schéma fournisseur** — Détecter les changements de format d’API avant qu’ils ne corrompent les traitements.
- **450. Journal de provenance des statistiques** — Conserver la source, l’heure de collecte et la transformation de chaque statistique importante.
- **451. Jeux de données de référence** — Créer des jeux de validation stables pour tester les imports et les transformations.
- **548. Registre des blessures par joueur** — Centraliser l’état médical de chaque joueur avec type de blessure, date et source.
- **549. Suivi des retours de blessure** — Suivre la reprise progressive et le temps de jeu après une blessure.
- **550. Détection des blessures non annoncées** — Repérer les absences implicites via les compositions et les rotations.
- **551. Impact des absences sur la force d’équipe** — Quantifier la baisse de niveau estimée selon les absents clés.
- **552. Suspensions par accumulation de cartons** — Recenser les joueurs sous le coup d’une suspension à venir.
- **554. Retour de suspension et remise en forme** — Estimer la forme réelle au retour d’une suspension.
- **555. Absences pour sélection nationale** — Prendre en compte les convocations et les retours tardifs.
- **556. Joueurs incertains et doutes d’avant-match** — Lister les joueurs incertains et la probabilité de participation.
- **557. Fiabilité des sources médicales** — Pondérer chaque source selon son historique de justesse.
- **558. Fraîcheur des informations de blessure** — Horodater les statuts pour éviter d’utiliser une donnée périmée.
- **559. Historique des indisponibilités** — Conserver l’historique complet des absences par joueur.
- **560. Durée moyenne d’indisponibilité par type de blessure** — Estimer la durée de retour selon la nature de la blessure.
- **561. Rotation et gestion de la charge** — Détecter les risques liés à la surcharge et à la rotation.
- **562. Alerte de composition médicale incomplète** — Signaler les cas où les absents ne sont pas documentés.
- **563. Corrélation blessures et calendrier chargé** — Relier la fréquence des blessures à la densité du calendrier.
- **564. Contradiction entre fournisseurs sur les absents** — Détecter et arbitrer les désaccords entre sources.
- **565. Pondération des absents clés** — Attribuer un poids d’influence à chaque joueur absent.
- **566. Prévision de disponibilité à court terme** — Estimer la probabilité de disponibilité au prochain match.
- **567. Journal des changements de statut médical** — Tracer chaque changement de statut pour audit et reproductibilité.

#### Couverture compétitions et équipes (24)
> **Réalité parieur :** Le parieur suit ses équipes et ses championnats. Une couverture irrégulière est frustrante : il quitte le bot si son championnat n’est pas traité ou si ses équipes sont mal renseignées.

- **452. Référentiel mondial des compétitions** — Maintenir un catalogue des ligues, coupes, pays, niveaux et saisons.
- **453. Couverture des divisions inférieures** — Ajouter les divisions secondaires seulement lorsque la couverture et la qualité des données sont suffisantes.
- **454. Gestion des formats de compétition** — Gérer saisons calendaires, saisons chevauchantes, groupes, play-offs et éliminations directes.
- **455. Indice de fiabilité par championnat** — Mesurer la disponibilité et la qualité historique des données par compétition.
- **456. Profil statistique d’équipe** — Construire des profils distincts domicile, extérieur et terrain neutre.
- **457. Gestion des équipes promues** — **FUSIONNER→252** — Initialiser prudemment les équipes promues avec incertitude élevée et références de niveau comparables.
- **458. Gestion des équipes renommées** — **FUSIONNER→252** — Relier les alias validés à une identité sportive stable.
- **459. Détection des matchs sur terrain neutre** — Éviter d’attribuer automatiquement l’avantage domicile lorsque le match est déplacé.
- **460. Calendrier et congestion** — Mesurer les jours de repos, déplacements et séquences de matchs rapprochés.
- **461. Contexte de classement** — Intégrer titre, maintien, qualification et phase de saison sans supposer la motivation subjective.
- **462. Contexte des coupes** — Tenir compte des matchs aller-retour, prolongations et règles de qualification.
- **463. Couverture géographique contrôlée** — Activer de nouvelles ligues après tests de qualité et validation de leurs identifiants.
- **598. Composition probable par équipe** — Estimer les onze titulaires probables avant l’annonce officielle.
- **599. Probabilité de titularisation par joueur** — Calculer la probabilité de débuter pour chaque joueur.
- **600. Schéma tactique probable** — Deviner le dispositif tactique le plus probable.
- **601. Incertitude de composition** — Mesurer le degré d’incertitude de la composition estimée.
- **602. Impact de la composition sur les marchés** — Relier les choix de composition aux marchés de paris.
- **603. Détection des changements de dispositif** — Repérer les changements tactiques récents d’une équipe.
- **604. Rotation probable selon le calendrier** — Anticiper la rotation liée à la densité des matchs.
- **605. Première composition et banc** — Estimer la répartition entre titulaires et remplaçants.
- **606. Fiabilité des sources de composition** — **FUSIONNER→557** — Pondérer les sources qui annoncent les compositions.
- **607. Horodatage de la composition probable** — **FUSIONNER→598** — Suivre l’évolution de la composition estimée jusqu’au coup d’envoi.
- **608. Composition probable et blessures** — **FUSIONNER→598** — Croiser la composition estimée avec les absents connus.
- **609. Confrontation des compositions (duel tactique)** — Comparer les dispositifs des deux équipes et leurs duels clés.

#### Marchés spécialisés (23)
> **Réalité parieur :** Au-delà du 1X2, le parieur joue les buts, corners, cartons, mi-temps, handicaps. Ces marchés sont moins liquides et souvent mal compris : une explication claire évite les erreurs de règles.

- **500. Modèle corners équipe** — Estimer séparément les corners attendus de chaque équipe et le total du match.
- **501. Modèle cartons équipe** — Estimer les cartons selon équipe, arbitre, compétition et contexte documenté.
- **502. Modèle tirs cadrés** — Prédire les volumes de tirs cadrés lorsque les fournisseurs offrent une couverture suffisante.
- **503. Modèle fautes** — Estimer les fautes avec prudence et validation spécifique à chaque compétition.
- **504. Modèle hors-jeu** — Prédire les hors-jeu lorsque l’historique est assez complet.
- **505. Modèle mi-temps** — Construire des distributions distinctes pour première et seconde période.
- **506. Modèle premier but** — Estimer quelle équipe marque en premier et la probabilité d’absence de but.
- **507. Modèle joueur buteur** — Évaluer les probabilités de buteur avec titularisation, minutes attendues et rôle.
- **508. Modèle joueur passeur** — Estimer les probabilités de passe décisive avec temps de jeu et rôle offensif.
- **509. Marchés combinés cohérents** — Calculer les probabilités conjointes en tenant compte de la dépendance entre sélections.
- **511. Validation des règlements de marché** — Documenter les règles de règlement, prolongations et annulations avant toute publication.
- **568. Profil de cartons de l’arbitre désigné** — Moyenne de cartons par match de l’arbitre, par compétition et par période.
- **569. Tendance de l’arbitre aux penaltys** — Fréquence de penaltys accordés par l’arbitre désigné.
- **570. Moyenne de fautes sifflées par arbitre** — Volume moyen de fautes sifflées selon l’arbitre.
- **571. Sévérité de l’arbitre selon la compétition** — Comparer la sévérité d’un arbitre d’une compétition à l’autre.
- **572. Historique des cartons rouges directs** — Suivre les expulsions directes et les profils d’arbitres stricts.
- **573. Avantage maison de l’arbitre** — Mesurer un éventuel biais de l’arbitre en faveur du domicile.
- **574. Temps additionnel moyen selon l’arbitre** — Estimer le temps additionnel habituel de l’arbitre.
- **575. Arbitre et VAR** — **GARDER 575** — Taux de décisions annulées ou modifiées après recours à la VAR.
- **576. Style de gestion des contestations** — Observer la propension de l’arbitre à sanctionner les contestations.
- **577. Stabilité du profil arbitral dans le temps** — Vérifier que le profil reste stable saison après saison.
- **578. Comparaison arbitre contre moyenne de la ligue** — Situer l’arbitre par rapport à la moyenne de sa compétition.
- **579. Alerte de changement d’arbitre** — Prévenir lorsque l’arbitre désigné change avant le match.

#### Cotes, value betting et risque (21)
> **Réalité parieur :** Le parieur compare des cotes qui bougent sans cesse. Il lui faut la meilleure cote disponible, la marge du bookmaker, et la certitude qu’une recommandation n’est pas un conseil garanti.

- **476. Normalisation de la marge bookmaker** — Retirer la marge implicite des cotes avant de comparer les probabilités du marché.
- **477. Calcul de valeur espérée** — Calculer l’espérance théorique à partir de la probabilité calibrée et de la cote disponible.
- **478. Historique des cotes horodaté** — Conserver les cotes et leur source à plusieurs moments avant le coup d’envoi.
- **479. Suivi Closing Line Value** — Comparer la cote prise à la cote de clôture pour évaluer la qualité du prix obtenu.
- **480. Détection d’écarts inter-bookmakers** — Comparer les prix disponibles en tenant compte des règles et de l’heure de collecte.
- **484. Exposition par compétition** — Surveiller la concentration du risque sur une ligue ou une journée.
- **486. Journal des recommandations de cotes** — Enregistrer le prix disponible au moment exact de chaque recommandation.
- **487. Alerte de cote périmée** — Retirer une recommandation lorsque la cote a changé ou n’est plus vérifiable.
- **610. Bankroll réelle synchronisée** — Suivre le capital réel engagé et disponible en temps réel.
- **612. Mise proportionnelle au risque** — Adapter la mise à la confiance et au risque estimé.
- **613. Mise selon Kelly fractionné** — **FUSIONNER→482** — Calculer une mise prudente avec un Kelly fractionné.
- **614. ROI réel par compétition** — Mesurer le retour sur investissement compétition par compétition.
- **615. ROI ajusté de la marge** — Corriger le ROI de la marge bookmaker.
- **616. Rendement par marché** — Comparer la performance selon le marché joué.
- **617. Rendement par type de pari** — Distinguer simples, combinés et paris système.
- **618. Suivi du drawdown maximal** — Mesurer la pire baisse de capital enregistrée.
- **619. Courbe de capital vérifiable** — Reconstituer la courbe de capital à partir de l’historique.
- **620. Espérance de gain nette** — Estimer l’espérance de gain après marge et incertitude.
- **621. Comparaison ROI modèle contre marché** — Comparer la performance du modèle à la cote du marché.
- **622. Seuil de rentabilité par cote** — Déterminer la cote minimale pour être rentable.
- **623. Répartition des mises par compétition** — Visualiser la concentration des mises par compétition.

#### IA, modèles et apprentissage (12)
> **Réalité parieur :** Le parieur attend que le bot s’améliore. Il faut lui montrer quand un modèle change et pourquoi, sans lui donner l’impression qu’on joue avec son argent.

- **428. Ensemble probabiliste multi-modèles** — Combiner plusieurs modèles indépendants et pondérer leur contribution selon leurs performances hors échantillon.
- **429. Modèles spécialisés par compétition** — Entraîner et sélectionner un modèle adapté à chaque ligue lorsque le volume de données le permet.
- **430. Modèles spécialisés par marché** — Séparer les modèles 1N2, buts, corners et cartons pour éviter de transférer les biais d’un marché à l’autre.
- **431. Méta-modèle de combinaison** — Apprendre à combiner les sorties de modèles de base à partir de prédictions historiques strictement hors échantillon.
- **432. Registre des modèles versionné** — Conserver version, date, données, variables, métriques et empreinte de chaque modèle déployé.
- **433. Entraînement reproductible** — Rejouer exactement un entraînement à partir d’un jeu de données versionné et d’une configuration enregistrée.
- **434. Validation temporelle automatisée** — Évaluer les modèles par fenêtres chronologiques sans mélanger le futur et le passé.
- **435. Détection de dérive du modèle** — Détecter les changements de distribution et la dégradation des scores probabilistes.
- **436. Déploiement progressif des modèles** — Comparer une nouvelle version en mode silencieux avant de lui confier les prédictions publiques.
- **437. Explication locale des prédictions** — Présenter les facteurs réellement utilisés par le modèle sans transformer une corrélation en certitude.
- **438. Surveillance des variables d’entrée** — Détecter valeurs absentes, extrêmes, incohérentes et changements de définition des variables.
- **439. Retour arrière du modèle** — Revenir à une version précédente si les contrôles automatiques de qualité échouent.

#### Prédictions en direct (10)
> **Réalité parieur :** Pendant le match, le parieur réagit vite et sous pression. Une alerte tardive ou fausse peut le conduire à parier sur une situation déjà dépassée.

- **513. État du match normalisé** — Représenter minute, score, période, cartons, remplacements et interruptions dans un format commun.
- **514. Détection d’événements live** — Détecter but, carton rouge, penalty et changement de période avec contrôle de cohérence.
- **515. Recalcul après événement majeur** — Recalculer uniquement après réception et validation d’un événement pertinent.
- **516. Contrôle de latence live** — Afficher l’heure de dernière mise à jour et suspendre les alertes trop tardives.
- **517. Détection de flux live bloqué** — Identifier les scores qui ne changent plus malgré un match en cours.
- **518. Probabilité conditionnelle au score** — Estimer les probabilités en tenant compte du score et du temps restant.
- **519. Gestion des interruptions** — Suspendre les calculs lors d’une pause, d’un report ou d’une interruption inconnue.
- **521. Limitation des alertes live** — Éviter les notifications répétitives pour un même événement ou une même recommandation.
- **522. Mode dégradé live** — Afficher clairement l’indisponibilité ou l’incertitude au lieu d’inventer une mise à jour.
- **523. Validation rétrospective live** — Mesurer les prédictions live avec l’heure et les données réellement disponibles.

#### Probabilités, calibration et incertitude (3)
> **Réalité parieur :** Un parieur qui voit « 60 % » s’attend à gagner 6 fois sur 10. Si le modèle dit 60 % et qu’il gagne 40 % du temps, il perd son argent sans comprendre pourquoi. La calibration est donc ce qui rend la confiance légitime.

- **591. Détection de sous-confiance du modèle** — **GARDER SÉPARÉ** — Identifier les segments où le modèle est trop prudent.
- **593. xG ajusté au temps de jeu** — Normaliser le xG par les minutes réellement jouées.
- **594. xG par situation de jeu** — Décomposer le xG par jeu ouvert, coup de pied arrêté et contre.

#### QA et non-régression (2)
> **Réalité parieur :** Le parieur ne voit jamais les tests, mais une régression silencieuse peut lui faire recevoir de mauvaises prédictions pendant des jours.

- **625. Jeu de tests de non-régression des prédictions** — Constituer un corpus figé de matchs et rejouer les prédictions pour comparer les sorties attendues.
- **633. Rejeu des incidents passés comme tests** — Transformer les incidents corrigés en tests de non-régression dédiés.

#### Versionnage et évaluation de variantes de modèle (2)
> **Réalité parieur :** Le parieur ne doit pas être utilisé comme cobaye. Tester une variante sur un petit groupe, et seulement si elle est meilleure, protège tout le monde.

- **640. Métadonnées de modèle** — **FUSIONNER→26** — Associer à chaque modèle sa date d'entraînement, son jeu de données et son auteur.
- **646. Critères d'acceptation d'une nouvelle variante** — Définir les seuils de performance à atteindre avant toute mise en production.

#### Contenu éditorial et pédagogie (1)
> **Réalité parieur :** Le parieur débutant a besoin d’apprendre avant de parier. Un contenu clair réduit les erreurs de compréhension et les pertes évitables.

- **677. Révision éditoriale des libellés** — Uniformiser le ton et l'orthographe des libellés visibles.

#### Hygiène du dépôt et dette technique (1)
> **Réalité parieur :** Invisible pour le parieur, mais une dette technique élevée ralentit toutes les corrections et augmente le risque de bug en production.

- **695. Mise à jour des dépendances obsolètes** — Identifier et mettre à jour les dépendances dépassées.

### Phase 3 — Expérience et engagement (264)

#### Catalogue initial (255)
> **Réalité parieur :** Le parieur veut une réponse simple et rapide : quel pari, pour quelle raison, et combien mettre. Il ne lit pas les statistiques en détail ; il attend une recommandation claire et honnête sur l’incertitude.

- **4. Alerte Compo Officielle / Absents** — 1h avant le match, il te dit qui est absent et il recalcule le prono.
- **6. Mode Lingala + Français** — Bouton /langue pour mettre tout le bot en Lingala simple.
- **8. Filtre Anti-Piège** — Badge rouge sur les matchs dangereux comme les derbys avec beaucoup de cartons.
- **9. Prono Spécial Corners / Cartons** — En plus du 1N2, il propose Over corners/cartons pour les matchs offensifs.
- **10. Calendrier Perso “Mes Équipes”** — Tu choisis 5 équipes favorites, tu ne reçois que leurs pronos.
- **11. Ticket de la Semaine en PDF** — Belle image/PDF du combiné à partager sur Statut WhatsApp.
- **12. Quiz / Sondage Avant Match** — “Qui va marquer en premier ?” Bonne réponse = points XP.
- **13. Mode Sans Internet / SMS Résumé** — Version ultra-courte “ARS 1-0, O2.5 62%”, très peu de data.
- **17. Groupe VIP Auto-Modéré** — Paiement = ajout auto au groupe VIP, expiration = retrait auto.
- **18. Prono Championnats Africains** — Linafoot, CAN, Ligue des Champions CAF, Afrique du Sud.
- **19. Mode “Copier le Ticket en 1 Clic”** — Code à coller direct sur Winner.bet / 1xBet, pas de recherche manuelle.
- **20. Statistiques de l’IA en Temps Réel** — /stats_ia montre “Cette semaine 68% sur Over 2.5”.
- **21. Coach IA en Chat Libre** — Tu écris “Que penses-tu de Real-Barça ?” et il répond avec une analyse.
- **22. Détecteur de Série / Momentum** — Repère les équipes en feu, ex: “7 victoires d’affilée à domicile”.
- **25. Stats Arbitre** — “Arbitre X: 5.8 cartons / match”, utile pour jouer Over cartons.
- **27. Impact Transfert / Entraîneur** — “Nouvel entraîneur: +2 buts / match”, explique le changement de forme.
- **28. Comparateur Domicile / Extérieur** — “Chelsea 78% à domicile, 22% à l’extérieur”, évite les pièges.
- **29. Prono Buteur + Passeur** — “Saka buteur 55%, Palmer passeur 48%”, pour les paris buteurs.
- **30. Mini App Telegram Visuelle** — Tableau de bord avec cartes jolies, pas de longs textes.
- **33. Programme Revendeur** — Des gens vendent tes codes et touchent 20% en automatique.
- **34. Classement par Quartier / Ville** — Top Gombe, Bandal, Lubumbashi, fierté locale.
- **35. Alerte Météo Pelouse** — “Pluie + pelouse synthétique = favorise Under et fautes”.
- **36. Mode Duo / Pari à 2** — 2 amis combinent leurs pronos, bonus si les 2 ont raison.
- **45. Assurance Combiné** — “Si 4/5 passent, tu récupères ton bonus”, calcul auto.
- **46. Cash-Out Partiel Simulé** — “Encaisse 50% maintenant, laisse 50% tourner”.
- **48. Filtre Réussite par Ligue** — “Ligue 1 71%, Premier League 54%”, tu choisis la meilleure ligue.
- **49. Dashboard ROI Personnel** — Graphique “Tu as +28% ce mois”, tu vois si tu gagnes vraiment.
- **50. Notifications Heure Kinshasa** — Pronos envoyés à 09h00 heure Kinshasa, pas heure Europe.
- **53. Débrief Auto Après-Match** — “Prono passé parce que…” ou “Raté à cause du rouge 23e”.
- **55. Base Blessés / Suspendus** — Liste chaque matin: qui est absent et pour combien de temps.
- **56. Compo Prédite vs Officielle** — Compare sa compo prédite à l’officielle et ajuste le prono.
- **57. Effet Altitude / Voyage** — “Lubumbashi 1.200m + 3h de vol pour l’adversaire”, fatigue.
- **58. Fatigue Calendrier** — “3e match en 7 jours, rotation probable”.
- **59. Détecteur de Derby / Rivalité** — Badge rouge DERBY, les derbys cassent les stats.
- **60. Indice de Motivation** — “Équipe A joue le titre 9/10, Équipe B plus rien à jouer 3/10”.
- **61. Tactique Entraîneur** — “Entraîneur défensif: 70% de Under 2.5”, le style influence le score.
- **62. xG + xA + xPoints** — Buts attendus + passes attendues + points attendus, niveau analyste TV.
- **64. Simulation Monte Carlo 10.000x** — Simule le match 10.000 fois, ex: “Arsenal gagne 6.200 fois”.
- **65. Explication du Prono** — “Pourquoi ce choix ? 1) Forme, 2) xG, 3) Absents”, en 3 puces.
- **67. Paris Virtuels Argent Fictif** — Tu testes avec 100.000 FC fictifs, sans argent réel.
- **68. Ligue Privée Entre Amis** — Crée “Les gars de Bandal” et affrontez-vous.
- **69. Bataille IA vs Humains** — Chaque jour: qui a le meilleur prono, toi ou l’IA ?
- **70. Boutique XP** — Avec tes points, achète 1 jour Premium, 1 analyse VIP.
- **71. Bonus Connexion Quotidienne** — Jour 1: 10 XP, Jour 7 d’affilée: 1 jour Premium.
- **73. Classement Parrains** — Top 5 parrains du mois avec récompense.
- **74. Lien d’Affiliation Suivi** — Chaque utilisateur a son lien et voit combien il a gagné.
- **79. Rapport Mensuel PDF** — “Ton mois: 68% réussite, +45.000 FC”, en PDF.
- **81. Notifications Silencieuses** — Option “Ne me réveille pas, envoie à 7h00”.
- **82. Mode Swahili** — En plus de Français + Lingala, Swahili pour l’Est du Congo.
- **84. Recherche par Emoji** — Tape ballon + nom d’équipe, le bot comprend.
- **85. Alertes Équipe Favorite Ultra-Ciblée** — “Mazembe joue dans 1h, voici ton prono”, zéro spam.
- **86. Sync Calendrier Google** — “Ajouter ce match à mon agenda” en 1 clic.
- **88. Mode Nuit / Économie Data** — Version texte ultra-légère, 2 Ko par message.
- **90. Mode Expert Débloquable** — Après 30 jours d’abonnement, débloque xG, Elo, Monte Carlo.
- **92. Gestion Utilisateurs par Statut** — Filtre Gratuit / Premium / Expiré / Bloqué / VIP / Revendeur.
- **94. Bannir / Débannir en 1 Clic** — Bouton rouge avec raison et durée 1j / 7j / définitif.
- **99. Générateur de Codes en Masse** — Génère 100 / 500 / 1000 codes d’un coup.
- **100. Codes par Lot / Campagne** — Lot “PROMO CAN” / “BANDAL”, tu sais quel lot vend le mieux.
- **101. Codes Usage Unique / Multi-Usage** — Code pour 1 personne ou pour 50 personnes.
- **102. Codes avec Date d’Expiration** — Code auto-détruit après 7 jours si non utilisé.
- **104. Graphique Croissance Abonnés** — Courbe nouveaux, churn, actifs, Premium.
- **108. Broadcast Ciblé** — Envoie seulement aux Expirés / Gratuit depuis 7j / Fan de Mazembe.
- **109. Broadcast Programmé** — “Envoie demain à 08h00 heure Kinshasa”.
- **110. Broadcast avec Boutons** — Boutons “Je m’abonne / Voir le ticket”, 3x plus de clics.
- **111. Statistiques de Broadcast** — Vu / Cliqué / Abonné après ce message.
- **112. Modération Mots Interdits** — Supprime auto liens, insultes, numéros dans le groupe VIP.
- **113. Anti-Spam Auto** — 5 messages en 10 sec = mute 1h automatique.
- **114. Journal d’Activité Admin** — Qui a fait quoi et quand.
- **115. Rôles Admin** — Super-Admin / Modérateur / Support / Revendeur, chacun voit son périmètre.
- **116. Panneau Pronos Manuel** — Ajoute un prono à la main si l’IA est en panne.
- **117. Validation Pronos Avant Envoi** — Tu vois les pronos du jour, tu cliques Valider avant envoi.
- **120. Gestion des Ligues Actives** — **À VÉRIFIER** — Coche / décoche les ligues actives cette semaine.
- **121. Gestion des Marchés Actifs** — Active / désactive Corners, Cartons, BTTS par jour.
- **122. Seuils de Confiance Réglables** — Change le seuil Premium 75% -> 70% sans code.
- **123. Mode Maintenance** — “Bot en maintenance 30 min”, message auto pour tous.
- **124. Message de Bienvenue Personnalisable** — Change le texte d’accueil sans redéployer.
- **125. FAQ Dynamique Admin** — Ajoute / modifie les questions fréquentes depuis le panneau.
- **126. Tickets Support avec Statut** — Nouveau / En cours / Résolu, avec assignation.
- **128. Export Utilisateurs CSV / Excel** — Télécharge toute ta base pour analyses / pubs.
- **129. Export Revenus pour Compta** — Fichier mensuel propre pour ton comptable.
- **132. Logs d’Erreurs Lisibles** — “API en panne à 10h12”, pas du code incompréhensible.
- **133. Alerte Admin si API Morte** — “API X morte depuis 2h, bascule sur API Y”.
- **134. Alerte si Pic d’Erreurs** — “50 erreurs en 10 min, regarde ça”.
- **135. Contrôle Consommation API** — “Tu as utilisé 850 / 1000 appels aujourd’hui”.
- **136. Gestion des Sources Prioritaires** — Glisse-dépose pour ordonner les API.
- **138. Test A/B des Messages** — Version A à 50%, Version B à 50%, garde la gagnante.
- **139. Gestion des Prix** — Change le prix Premium depuis le panneau, sans développeur.
- **140. Promo Flash Admin** — “Promo -50% pendant 3h”, le bot change les prix et prévient tous.
- **141. Gestion Revendeurs** — Vois ventes, commission, solde de chaque revendeur.
- **143. Tableau de Bord Revendeur** — **GARDER SÉPARÉ** — Chaque revendeur voit ses codes et ses ventes.
- **144. Bannir un Revendeur Tricheur** — 1 clic = ses codes désactivés.
- **147. Blacklist Numéros / Appareils** — Fraudeur bloqué même s’il recrée un compte.
- **151. Admin sur Mobile Web** — Panneau qui marche parfaitement sur téléphone, pas besoin de PC.
- **152. Connexion Admin par Code PIN** — Code à 6 chiffres pour entrer, pas de mot de passe.
- **154. Session Admin Expirable** — Déconnexion auto après 30 min d’inactivité.
- **156. Mode Admin Fantôme** — Vois le bot comme un utilisateur Gratuit / Premium sans changer de compte.
- **157. Créer des Comptes Test** — 10 faux utilisateurs pour tester sans casser les vrais comptes.
- **159. Centre de Notifications Admin** — Toutes les alertes au même endroit.
- **160. Notifications Admin par Priorité** — Rouge = urgent, Orange = à voir, Vert = info.
- **161. Résumé Quotidien Admin à 07h00** — “Hier: +42 utilisateurs, +85.000 FC, 3 erreurs”.
- **162. Résumé Hebdo PDF Admin** — Chaque lundi, rapport complet en PDF sur ton Telegram.
- **163. Comparaison Mois vs Mois** — “Novembre +25% vs Octobre en revenus”.
- **164. Prévision Revenus IA** — “Si tu continues, tu feras 450.000 FC ce mois”.
- **165. Cohorte Utilisateurs** — “Utilisateurs d’Octobre encore 60% actifs”.
- **166. Analyse d’Abandon** — “70% partent après 3 jours gratuits, à cause de…”.
- **167. Carte des Utilisateurs** — Kinshasa, Lubumbashi, Goma, Bukavu, d’où viennent-ils ?
- **168. Heures de Pointe** — “Tes utilisateurs sont actifs 18h-21h”, envoie tes broadcasts à ce moment.
- **170. Langue des Utilisateurs** — 60% Français, 30% Lingala, 10% Swahili.
- **174. Code Promo Pourcentage** — “CAN2026 = -30%”.
- **175. Code Promo Montant Fixe** — “BIENVENUE = -2.000 FC”.
- **181. Réconciliation Manuelle** — “J’ai reçu 10.000 FC mais le bot n’a pas vu”, tu valides à la main.
- **183. Gestion des Opérateurs** — Active / désactive Airtel, M-Pesa, Orange selon les pannes.
- **184. Frais Opérateurs** — “Sur 10.000 FC, Airtel prend 500 FC, reste 9.500 FC”.
- **185. Seuil d’Alerte Solde** — “Ton solde Airtel est bas, recharge avant demain”.
- **187. Boost Manuel d’un Prono** — “Mets ce match en avant, il est très sûr”.
- **188. Masquer un Marché** — “Aujourd’hui, pas de paris sur les cartons”.
- **189. Ajouter une Note Admin sur un Match** — “Pelouse en mauvais état à Kamalondo”, visible Premium seul.
- **191. Taux de Réussite par Admin** — Si 2 admins font des pronos, qui est le meilleur ?
- **194. Nettoyage Auto des Anciens Messages** — Supprime les pronos de plus de 7 jours.
- **195. Gestion des Épinglés** — Épingle / désépingle le ticket du jour automatiquement.
- **196. Anti-Fuite Pronos Premium** — Filigrane avec l’ID de l’utilisateur sur chaque image Premium.
- **197. Détection de Capture d’Écran** — Avertit “Captures Premium interdites”.
- **199. Gestion des Signalements** — File des bugs / abus signalés par les utilisateurs.
- **200. Sondage Admin** — “Vous voulez plus de Linafoot ou plus de Premier League ?”
- **202. Rollback en 1 Clic** — “Reviens à l’ancienne version” si la MAJ casse le bot.
- **203. Environnement Test / Prod** — Tu testes sur un bot test, puis tu bascules sur le vrai bot.
- **204. Gestion des Variables** — Change token, clés API, prix sans toucher au code.
- **206. Export des Logs Admin** — Télécharge les logs pour les envoyer à un développeur.
- **207. Quota d’Envoi Telegram** — “Tu as envoyé 8.500 / 10.000 messages aujourd’hui”.
- **209. Priorité d’Envoi** — Les VIP reçoivent d’abord, les gratuits après.
- **210. Mode Catastrophe** — Si Render tombe, bascule sur serveur de secours en 2 min.
- **212. Alertes Telegram Admin Silencieuses** — Discrète la nuit, bruyante le jour.
- **213. Gestion des Fuseaux Horaires** — Tous les horaires affichés en heure de Kinshasa.
- **214. Mode Vacances Admin** — “Je suis absent 3 jours”, le bot gère tout seul avec message auto.
- **215. Délégation Temporaire** — Donne les clés à un ami pour 48h, puis ça se coupe seul.
- **216. Journal d’Actions Admin** — **SUPPRIMER** — “Jean a banni 2 utilisateurs à 14h32”.
- **217. Annuler une Action Admin** — “Oups, j’ai banni le mauvais”, bouton Annuler.
- **218. Corbeille Admin** — Supprimés restent 30 jours, tu peux tout récupérer.
- **222. Export CSV Segment** — Exporte uniquement tes VIP inactifs en CSV.
- **223. Import CSV Utilisateurs** — Importe une liste de numéros depuis Excel.
- **224. Fusion de Doublons** — “Ce numéro a 2 comptes”, bouton Fusionner.
- **225. Nettoyage Auto Comptes Fantômes** — Supprime les comptes jamais ouverts depuis 90 jours.
- **226. Vérification Numéro Téléphone OTP** — Vérifie que le numéro existe via code SMS.
- **227. Blacklist Numéros** — **FUSIONNER→147** — Bloque un numéro définitivement, même s’il recrée un compte.
- **228. Whitelist VIP** — Ces utilisateurs ne peuvent jamais être bannis par erreur.
- **230. Gestion des Langues par Utilisateur** — Vois qui parle quelle langue, change à la main.
- **231. Notes Privées sur Utilisateur** — “Ce client paie en retard mais fidèle”, visible que par toi.
- **232. Tags Utilisateurs** — Tags #fidèle #retardataire #gros_parieur #influenceur, comme un CRM.
- **237. Gestion des Réclamations** — File Nouvelle / En cours / Résolue, avec temps de réponse.
- **238. Réponses Types Admin** — 10 réponses prêtes en 1 clic, tu réponds 10x plus vite.
- **239. Traduction Auto Support** — Message en Lingala traduit en Français pour toi.
- **241. Création de Pronos Manuels** — Crée un prono à la main sans IA, en 30 sec, pour Linafoot.
- **244. Calendrier des Pronos** — Vue calendrier: quel jour, quel match, quel prono.
- **245. Validation en 2 Étapes des Pronos** — Un admin propose, un autre valide avant envoi.
- **246. Aperçu Avant Envoi** — Vois exactement comment le message va s’afficher sur téléphone.
- **247. Test d’Envoi à Toi-Même** — Envoie le prono d’abord à toi seul pour vérifier.
- **249. Verrouillage des Pronos** — Une fois envoyé, impossible de modifier, personne ne dit que tu as triché.
- **250. Archivage des Pronos** — Pronos de plus de 6 mois archivés, mais consultables.
- **251. Gestion des Ligues** — **GARDER 251** — Active / désactive une ligue “Cette semaine, pas de Serie A”.
- **252. Gestion des Équipes** — Renomme, fusionne, corrige une équipe en 1 clic.
- **253. Gestion des Saisons** — Crée la saison 2026-2027 en 1 clic, archive l’ancienne.
- **254. Gestion des Stades** — Infos stade: pelouse, capacité, altitude.
- **255. Gestion des Arbitres** — Base arbitres avec leurs stats de cartons.
- **257. Taux de Change FC / USD** — “1 USD = 2.850 FC aujourd’hui”, modifiable.
- **258. Gestion des Taxes** — Calcule la taxe sur chaque vente si besoin.
- **261. Gestion des Partenaires** — Liste influenceurs, revendeurs, avec leurs commissions.
- **263. Contrats Partenaires** — Stocke “Jean touche 20% pendant 6 mois”, zéro dispute.
- **266. Gestion des Badges** — Crée des badges “Expert”, “Ancien”, “Parrain Or”.
- **267. Gestion des Notifications Push** — Choisis qui reçoit quelle notif, à quelle heure.
- **270. Bouton STOP D’Urgence** — Gros bouton rouge “Stop tout, ne plus envoyer de messages”.
- **282. Shorts YouTube** — 30 sec “3 matchs à ne pas jouer aujourd’hui”.
- **287. Influenceur Micro Kinshasa** — Tu donnes 7 jours Premium à un influenceur 5k abonnés, il en parle.
- **288. Influenceur Football Local** — Un journaliste sportif local parle de ton bot, crédibilité.
- **289. Joueur de Linafoot Ambassadeur** — Un joueur connu de Mazembe / Vita poste ton lien.
- **290. Bar / Nganda Partenaire** — QR code dans 10 bars où on regarde les matchs.
- **291. Boutique Paris Sportif Partenaire** — QR code dans les agences Winner.bet / 1xBet.
- **292. Cybercafé Partenaire** — Affiche A4 dans 20 cybercafés “Scanne, reçois ton 1er prono gratuit”.
- **293. Flyer QR Code Marché** — Flyer simple à Gambela, Zando “Gagne avec ton téléphone”.
- **294. Affiche Taxi / Moto** — Petite affiche derrière les taxis “Bot Pronos Kinshasa”.
- **295. Parrainage Double Récompense** — Parrain + Filleul gagnent tous les 2 “1 jour Premium chacun”.
- **300. Preuve de Gain Floutée** — Tu postes un gain avec montant flouté “Devine combien ? Lien en bio”.
- **302. Défi Public “100.000 FC en 30 Jours”** — Tu montres ton évolution chaque jour avec 100.000 FC fictifs.
- **303. Comparaison “Sans Bot vs Avec Bot”** — “Sans bot 2/10, Avec bot 7/10”, argument simple.
- **304. Témoignage Vidéo Utilisateur** — Un utilisateur filme “Grâce au bot j’ai payé mon loyer”.
- **305. Capture d’Écran Avis Telegram** — Tu postes “Merci frère, ton prono est passé !”, preuve sociale.
- **306. Nom de Bot Facile à Retenir** — Nom court + @ facile @PronoKinshasaBot.
- **307. Bio TikTok / Insta Optimisée** — “Pronos gratuits chaque jour 🇨🇩 👇 Clique ici”.
- **309. QR Code Personnalisé avec Logo** — QR joli avec logo, les gens scannent plus.
- **310. Carte de Visite Numérique** — 1 image avec QR + prix + “1er prono gratuit” à partager.
- **314. Retargeting** — Ceux qui ont cliqué mais pas payé revoient ta pub, ce sont les plus chauds.
- **317. Prono Gratuit du Jour Public** — 1 prono gratuit chaque jour, visible par tous, sans inscription.
- **318. Prono Gratuit du Week-End** — Le samedi, 3 pronos gratuits pour attirer le max de monde.
- **320. Podcast Audio 2 Min** — “L’analyse du jour en 2 min” sur WhatsApp / TikTok.
- **321. Collaboration avec Page Meme Football** — Page meme 50k abonnés poste ton lien contre Premium.
- **322. Collaboration avec Page Linafoot** — Page Mazembe / Vita partage ton prono Linafoot.
- **323. SEO Telegram** — Description avec mots “Pronostic, Football, Kinshasa, RDC, Winner.bet”.
- **324. Annuaire de Bots Telegram** — Inscris ton bot sur les sites de bots, trafic gratuit passif.
- **325. Forum / Reddit RDC** — Tu réponds aux questions pronos avec ton lien, trafic qualifié.
- **326. Signature Email / WhatsApp** — “Pronos gratuits chaque jour 👉 @tonbot” en signature.
- **327. Vocal de Bienvenue Personnalisé** — Vocal “Merci frère, bienvenue”, il se sent spécial et reste.
- **328. Anniversaire Utilisateur** — “Joyeux anniversaire, 3 jours Premium offerts”, il en parle à tous.
- **329. Programme “Ambassadeur de Quartier”** — 1 ambassadeur par quartier Gombe, Bandal, Matete, il gagne 30%.
- **331. Fuzzy Matching Dynamique des Noms d’Équipes** — difflib.get_close_matches(cutoff=0.75) pour absorber les promotions/relégations de clubs.
- **332. Calcul 100 % Dynamique des Saisons et Années** — Fonction get_saison_actuelle() (basculement en juillet) sans année codée en dur.
- **337. Échappement HTML Strict (nettoyer_html)** — Protection anti-crash Telegram (&, <, >) dans _envoyer_message_securise.
- **339. Apprentissage Auto-Adaptatif des Alias d’Équipes** — Table alias_equipes qui apprend automatiquement les nouveaux noms via (date + score exact).
- **340. Health Score Dynamique des Sources** — Notation dynamique des APIs (score 100, -20 par erreur, +5 par succès) pour prioriser les plus fiables.
- **341. Pré-génération Nocturne (predictions_cache)** — Pré-calcul à 04h00 des 20 plus grosses affiches du jour pour des réponses instantanées.
- **344. Hachage SHA-256 des Codes Premium** — Stockage sécurisé par empreinte hashlib.sha256() uniquement.
- **346. Watchdog Interne & Auto-Guérison** — Thread de contrôle des heartbeats toutes les 10 min avec redémarrage propre (os._exit(1)) si gelé.
- **347. Verrou Distribué Anti-Doublons (cron_locks)** — Contrainte SQL ON CONFLICT DO NOTHING pour éviter les doubles envois lors des redémarrages Render.
- **349. Optimisation RAM (512 Mo Render) & Mode Survie Read-Only** — Typage int8/float32 + gc.collect() + bascule lecture seule si Turso échoue en écriture + désactivation auto erreur Telegram 403.
- **350. Mode Dégradé Intelligent (/status)** — Bannière d’état en direct dans le menu principal (“🟢 Opérationnel” / “🟠 API lente”).
- **354. Mode Expert (Analyse Tactique Humaine)** — Génération de phrases naturelles à partir des stats Elo et de forme.
- **355. Bouton d’Urgence / Support Intégré (🆘 Support)** — Ticket direct vers l’Admin avec contexte ID utilisateur.
- **357. Classement Mensuel des Parieurs (🏆 Top 10)** — 7 jours Premium offerts au meilleur pronostiqueur du mois.
- **359. Indice Météo Tactique** — Vérification météo du stade (pluie/vent -> alerte Under 2.5).
- **360. Bouton “⚡ Flash Prono” & Générateur de Combinés Magiques** — Génération en 1 clic du meilleur pari ou d’un ticket combiné de 3 à 5 matchs.
- **364. Mode Prono entre IA (Duel d’Algorithmes)** — Confrontation en direct entre XGBoost et Random Forest sur les grosses affiches.
- **365. Analyse Tactique Détaillée** — Description du schéma attendu (ex: bloc bas, contre-attaque, pressing haut).
- **366. Simulateur de Match Virtuel Minute par Minute** — Narration simulée des temps forts avant le coup d’envoi.
- **370. Analyse des Conférences de Presse** — Extraction du sentiment et des indices de forme via NLP.
- **372. Duels Quotidiens 1v1 entre Abonnés** — Affrontement aléatoire sur 3 pronos du jour.
- **373. Tournoi Hebdomadaire à Élimination Directe** — Tableau style Ligue des Champions entre les meilleurs joueurs du bot.
- **374. Cagnotte Communautaire Mensuelle** — Redistribution d’une part des revenus aux meilleurs pronostiqueurs vérifiés.
- **378. Infographie Bilan du Week-end** — Génération automatique d’une image récapitulative des victoires du week-end.
- **381. Parrainage Multi-Niveaux & QR Code Personnel** — Commissions sur filleuls directs/indirects avec QR code prêt à partager.
- **383. Statistiques Arbitre VAR** — **FUSIONNER→575** — Taux d’intervention et d’annulation de buts de l’arbitre VAR désigné.
- **384. Indice de Fatigue des Voyages (Vols & Décalage)** — Calcul de l’impact des déplacements intercontinentaux (CAF / Coupes d’Europe).
- **385. Salons “Fan Zone” par Club** — Espaces communautaires dédiés (Mazembe, Vita Club, Real Madrid, Barça, Arsenal).
- **387. Prono Spécial “Remontada”** — Identification des équipes statistiques capables de renverser un score après la pause.
- **388. Alerte “Cash-Out Conseillé” en Direct** — Signal tactique lorsque le scénario du match devient défavorable.
- **390. Graphique Visuel des Confrontations Directes (H2H)** — Mini-charte générée à la volée pour les 5 derniers duels.
- **391. Combiné avec Couverture Mutuelle** — Sélection de matchs équilibrés réduisant la variance globale.
- **392. Indicateur Visuel de Série (🟢🔴🟢🟢🟡)** — Affichage instantané de la dynamique des 5 derniers matchs.
- **393. Alerte “Coup de Sûr Hebdomadaire” (Confiance > 90%)** — Le match le plus fiable de la semaine mis en avant.
- **394. Analyse Fine des Tirs Cadrés & Conversion** — Ratio occasions créées vs buts réels.
- **395. Prono Spécial “Clean Sheet”** — Ciblage des défenses hermétiques à domicile.
- **397. Prédiction de Cartons Rouges** — Croisement agressivité équipes + sévérité arbitre.
- **398. Impact Absences Longue Durée** — Ajustement de la force offensive/défensive sur toute la période d’indisponibilité.
- **404. Statistiques Spéciales “Money Time” (75e - 90e min)** — Ciblage des équipes décisives en fin de rencontre.
- **405. Mode “Chasseur de Matchs Nuls”** — Algorithme dédié aux championnats fermés (Ligue 2, Serie B, Linafoot).
- **406. Facteur “Stade à Guichets Fermés”** — Pondération de l’avantage domicile lors des grandes affluences.
- **407. Détecteur d’Équipes Vernies / Malchanceuses (xG vs Réel)** — Identification des retours à la normale imminents.
- **408. Génération de Ticket Express en 2 Secondes** — Raccourci clavier persistant pour un ticket immédiat.
- **410. Comparaison Saison Actuelle vs Saison Précédente** — Analyse comparative à la même journée de championnat.
- **411. Détection Automatique de la Langue** — Adaptation fluide entre Français, Lingala, Swahili et Anglais.
- **413. Module Spécial 1ère Mi-Temps** — Prédictions dédiées exclusivement aux 45 premières minutes.
- **415. Le Grand Livre d’Or Infalsifiable** — Archive publique et permanente de tous les bilans vérifiés sur 10 ans.
- **416. Gestion des Devises Multiples (CDF / USD / EUR)** — Conversion automatique selon le taux configuré en Admin.
- **421. Score de Satisfaction Support (CSAT 1 à 5)** — Évaluation automatique après chaque ticket d’assistance résolu.
- **422. Diagnostics Serveur & Alerte RAM Critique** — Surveillance proactive (alerte si RAM > 450 Mo / 512 Mo).
- **424. Interrupteur Dynamique des Features ML** — Désactivation à chaud d’une variable (ex: météo) si sa source tombe en panne.
- **425. Mode Trêve Internationale** — Bascule automatique des algorithmes et messages lors des fenêtres FIFA/CAF.
- **427. Module Jackpot Winner.bet** — grille 14 matchs principaux + 3 réserves, saisie/import de la grille et pré-remplissage Flash Grille IA

#### Contenu éditorial et pédagogie (9)
> **Réalité parieur :** Le parieur débutant a besoin d’apprendre avant de parier. Un contenu clair réduit les erreurs de compréhension et les pertes évitables.

- **671. Fiches pédagogiques des fonctionnalités** — Rédiger une fiche simple expliquant chaque fonctionnalité et son usage.
- **672. Glossaire des termes métier** — Définir les termes métier utilisés dans les messages et la documentation.
- **673. Exemples d'utilisation par commande** — Fournir des exemples concrets pour chaque commande utilisateur.
- **674. Messages d'aide contextuels** — Adapter le message d'aide au contexte de la commande invoquée.
- **675. Tutoriel de prise en main** — Proposer un parcours guidé pas à pas pour les nouveaux utilisateurs.
- **676. FAQ intégrée** — Regrouper les questions fréquentes et leurs réponses directement accessibles.
- **678. Localisation des messages utilisateur** — Préparer les messages pour une traduction éventuelle en plusieurs langues.
- **679. Notes de version lisibles** — Rédiger des notes de version compréhensibles par les utilisateurs.
- **680. Aide à la lecture des statistiques** — Expliquer comment interpréter les statistiques affichées à l'utilisateur.

### Phase 4 — Croissance et monétisation (52)

#### Catalogue initial (50)
> **Réalité parieur :** Le parieur veut une réponse simple et rapide : quel pari, pour quelle raison, et combien mettre. Il ne lit pas les statistiques en détail ; il attend une recommandation claire et honnête sur l’incertitude.

- **31. Paiement Auto Airtel / M-Pesa / Orange** — Vérifie le paiement seul, débloque Premium en 10 sec.
- **32. Essai Premium 24h Automatique** — 1 fois par utilisateur, test gratuit sans code.
- **91. Dashboard Admin Temps Réel** — 1 écran: utilisateurs en ligne, pronos envoyés, paiements du jour.
- **95. Offrir Premium Manuellement** — “Offrir 7 jours à @user” sans code, pour concours.
- **96. Prolonger / Raccourcir Abonnement** — Change la date d’expiration manuellement.
- **97. Historique Paiements par Utilisateur** — Date, montant, opérateur, code, preuve en cas de litige.
- **103. Tableau de Bord Revenus** — **GARDER SÉPARÉ** — Revenu jour / semaine / mois, par opérateur, par abonnement.
- **105. Taux de Conversion Gratuit -> Premium** — % qui passent Premium après l’essai.
- **106. Alerte Churn** — “15 utilisateurs expirent demain, envoie-leur une offre”.
- **107. Offre de Relance Auto** — À J-1: “Renouvelle avec -20% aujourd’hui”, vente auto.
- **119. Annuler / Reporter un Match** — Bouton reporté = remboursement points + alerte utilisateurs.
- **127. Réponses Rapides Admin** — Boutons “Ton paiement est en cours”, “Voici ton code”.
- **142. Paiement Commission Revendeur Auto** — Calcule et paie chaque lundi.
- **149. Mode Audit Complet** — Enregistre TOUT: clics, paiements, gains, preuve en cas de problème.
- **150. Bouton Panique Admin** — STOP TOUT, coupe envois, paiements, pronos en 1 clic.
- **158. Simulateur de Paiement** — Simule paiement réussi / échoué, sans dépenser d’argent.
- **171. Gestion des Abonnements par Durée** — 1j / 7j / 30j / 90j / 1 an, chacun son prix.
- **172. Abonnement Famille / Groupe** — 1 paiement pour 5 comptes.
- **173. Abonnement Cadeau** — “Offre 30 jours à un ami”, l’utilisateur paie pour un autre.
- **177. Remboursement en 1 Clic** — Rembourse un mécontent et coupe son Premium.
- **178. Crédit / Avoir Utilisateur** — Donne 5.000 FC de crédit au lieu d’un remboursement.
- **179. Facture / Reçu Auto** — Reçu propre avec logo après chaque paiement.
- **180. Litiges Paiements** — Liste en attente / contesté / échoué avec bouton résoudre.
- **182. Taux de Paiement Échoué** — “12% échouent à cause du réseau”.
- **208. File d’Attente d’Envoi** — Envoie 5.000 messages petit à petit sans planter.
- **211. Tableau de Bord Temps Réel V2** — Utilisateurs en ligne, pronos, paiements de la dernière heure en direct.
- **219. Recherche Globale Admin** — Tape nom, numéro, ID, paiement, tu trouves tout en 1 sec.
- **220. Filtres Avancés Utilisateurs** — “Premium qui n’a pas ouvert depuis 7 jours + à Kinshasa”.
- **233. Score de Fidélité** — 0 à 100: ancienneté + paiements + activité, tu sais qui chouchouter.
- **235. Historique de Paiement Complet** — Tous les paiements avec preuves, en ordre.
- **243. Planification de Pronos** — Prépare les pronos de demain à 22h, envoi auto à 08h.
- **259. Budget Pub** — “J’ai dépensé 50.000 FC en pub TikTok, j’ai gagné 12 clients”. ⚠ Budget publicitaire pour un service de paris : vérifier les règles des plateformes et de la réglementation.
- **260. ROI par Canal d’Acquisition** — TikTok 40 clients, WhatsApp 25, Bouche-à-oreille 30.
- **262. Paiement des Partenaires** — Calcule et paie les commissions en 1 clic.
- **308. Lien Unique dans Toutes les Bios** — Même lien partout TikTok, Insta, WhatsApp, Facebook.
- **311. Pub TikTok 5.000 FC / Jour** — Petite pub ciblée Hommes 18-35 ans, Kinshasa, intérêt Football. ⚠ Une publicité promettant un gain journalier est trompeuse : à interdire ou à reformuler. Vérifier la réglementation des publicités de paris.
- **312. Pub Facebook 10.000 FC** — Pub “Pronos Football RDC” avec bouton Envoyer message. ⚠ Publicité de paris : vérifier la réglementation et les plateformes avant toute diffusion.
- **313. Pub WhatsApp Click-to-Chat** — Pub qui ouvre direct ton bot WhatsApp / Telegram. ⚠ Publicité de paris : vérifier la réglementation et les plateformes avant toute diffusion.
- **315. Offre de Bienvenue Limitée** — “Les 100 premiers: 7 jours Premium à 2.000 FC au lieu de 5.000 FC”.
- **316. Compte à Rebours** — “Il reste 12 places pour l’offre”, urgence = vente.
- **330. Événement “Soirée Match”** — Soirée foot dans un bar, tu montres ton bot en live, abonnement sur place.
- **342. Calibration Adaptative des Seuils (Top Affiches)** — Ajustement dynamique du seuil de confiance (plancher 65%) pour ne jamais avoir de rubrique vide.
- **348. Idempotence Stricte des Paiements & Rate-Limit** — Clé UNIQUE sur telegram_payment_charge_id et anti-spam 3s sur les boutons.
- **353. Coffre-Fort à Codes (🎟️ Mes codes achetés)** — Conservation des codes validés dans le profil utilisateur anti-perte.
- **380. Paiement Crypto (USDT / Toncoin) & Cartes Internationales** — Ouverture à la diaspora congolaise (Europe, Amérique). ⚠ Paiement en crypto : réglementation très variable selon les pays. Ne pas implémenter sans avis juridique.
- **400. Planification Horaire Personnalisée des Alertes** — Choix exact de l’heure de réception par utilisateur.
- **417. Suivi des Frais de Retrait Mobile Money** — Calcul de la marge nette réelle après commissions opérateurs. Frais de retrait Mobile Money : dépend de l’intégration de la fonction 31.
- **418. Calculateur de Seuil de Rentabilité Serveur** — Suivi automatique coûts hébergement vs revenus abonnements.
- **419. Affiliation Bookmakers & Tracking Campagnes** — Suivi des conversions par lien (TikTok, Facebook, WhatsApp, Influenceurs).
- **420. Paiement Automatisé des Commissions Partenaires** — **FUSIONNER→262** — Règlement périodique transparent des revendeurs et ambassadeurs.

#### Marchés spécialisés (1)
> **Réalité parieur :** Au-delà du 1X2, le parieur joue les buts, corners, cartons, mi-temps, handicaps. Ces marchés sont moins liquides et souvent mal compris : une explication claire évite les erreurs de règles.

- **510. Catalogue de disponibilité par fournisseur** — N’activer un marché que si les données nécessaires sont réellement disponibles.

#### Prédictions en direct (1)
> **Réalité parieur :** Pendant le match, le parieur réagit vite et sous pression. Une alerte tardive ou fausse peut le conduire à parier sur une situation déjà dépassée.

- **520. Historique des états live** — Conserver les instantanés nécessaires à l’audit des prédictions en direct.

### Phase 5 — Intégrations externes (dépendent de tiers) (29)

#### Catalogue initial (29)
> **Réalité parieur :** Le parieur veut une réponse simple et rapide : quel pari, pour quelle raison, et combien mettre. Il ne lit pas les statistiques en détail ; il attend une recommandation claire et honnête sur l’incertitude.

- **15. Analyse Vidéo Courte Auto** — Texte prêt pour TikTok “3 raisons de jouer Under 2.5 ce soir”.
- **37. Résumé Vocal / Audio** — Vocal 30 sec “Voici les 3 matchs à jouer ce soir”.
- **40. Export TikTok / Statut en 1 Clic** — Image carrée prête avec logo + ticket du jour.
- **51. Résumé Vocal IA 30s** — **FUSIONNER→37** — Audio “Voici les 3 matchs à jouer ce soir”, pour ceux qui travaillent.
- **75. Sync Auto Canal WhatsApp** — Prono posté sur Telegram = posté aussi sur WhatsApp.
- **76. Post Auto Facebook** — Ticket du jour posté seul sur ta page Facebook.
- **77. Générateur Légende TikTok** — Écrit “3 raisons de jouer ce ticket… #kinshasa”.
- **78. Template Story Instagram** — Image 9:16 prête avec logo + ticket du jour.
- **80. Résumé Email Hebdo** — Dimanche, tes stats de la semaine par email.
- **83. Commande Vocale** — Envoie un vocal “Donne-moi le prono de Mazembe”.
- **98. Vérification Paiement Mobile Money Auto** — **FUSIONNER→31** — Vérifie Airtel / M-Pesa / Orange seul.
- **240. Support par Vocal** — Écoute les vocaux des utilisateurs direct dans le panneau.
- **271. TikTok 15s “Ticket du Jour”** — Tu filmes ton écran “Voici mon ticket à 2.10 aujourd’hui”.
- **272. TikTok “Avant / Après”** — Avant “J’ai mis 5.000 FC” / Après “J’ai gagné 12.000 FC”.
- **273. TikTok Réaction Live But** — Tu te filmes quand ton prono passe en live, émotion = partages.
- **274. Statut WhatsApp Quotidien** — Chaque matin, 1 image du ticket dans ton statut.
- **275. Statut WhatsApp Résultats** — Le soir “3/4 pronos passés hier” avec capture.
- **276. Canal WhatsApp Public** — Canal gratuit 1 prono / jour + lien vers Telegram.
- **277. Groupe WhatsApp “Pronos Gratuits”** — Groupe de 500 personnes, 1 prono gratuit, reste en Premium.
- **278. Groupe Facebook “Parieurs RDC”** — Tu crées le groupe, tu es l’admin, tu postes tes pronos.
- **279. Page Facebook Auto-Post** — **FUSIONNER→76** — Le bot poste le ticket du jour seul sur ta page.
- **280. Reels Instagram Ticket** — Même vidéo TikTok, repostée sur Reels.
- **281. Story Instagram Sondage** — **GARDER SÉPARÉ** — “Real va gagner ? Oui / Non”, ceux qui votent voient ton lien.
- **283. Commentaires TikTok Stratégiques** — Tu commentes sous les vidéos de parieurs connus.
- **284. Duo TikTok avec Parieur Connu** — Tu fais un duo, son audience te découvre.
- **285. Live TikTok Avant Match** — 20 min avant le match “On analyse ensemble”.
- **286. Live TikTok Après Victoire** — “On a gagné ! On montre le ticket”, meilleur moment pour vendre.
- **296. Parrainage WhatsApp 1 Clic** — Bouton “Invite tes amis”, message déjà écrit, juste Envoyer.
- **363. Assistant Vocal Telegram (STT/TTS Lingala & Français)** — Pose une question en vocal et reçois la réponse audio personnalisée du Coach.

### À écarter (incitation au jeu ou hors périmètre) (9)

#### Catalogue initial (9)
> **Réalité parieur :** Le parieur veut une réponse simple et rapide : quel pari, pour quelle raison, et combien mettre. Il ne lit pas les statistiques en détail ; il attend une recommandation claire et honnête sur l’incertitude.

- **72. Roue Quotidienne Gratuite** — 1 spin par jour: XP, analyse gratuite ou -10%.
- **145. Gestion des Concours** — **SUPPRIMER** — Crée “Top parrain du mois gagne 30 jours” en 2 min.
- **146. Tirage au Sort Auto** — **SUPPRIMER** — Tire un gagnant au hasard, transparent.
- **264. Gestion des Concours** — **SUPPRIMER** — Crée “Pronostique le score, gagne 7 jours Premium”.
- **265. Tirage au Sort Auto** — **SUPPRIMER** — Tire un gagnant au hasard, transparent et juste.
- **297. Concours “Invite 5 Amis”** — Celui qui invite 5 amis gagne 30 jours Premium.
- **298. Giveaway TikTok** — “Abonne-toi + Commente PRONO = je t’envoie 1 jour Premium”.
- **299. Giveaway WhatsApp Statut** — **GARDER SÉPARÉ** — “Mets mon lien en statut 24h = 3 jours Premium”.
- **361. Parrainage à Paliers & Roue de la Fortune Telegram** — Lancer de dé/machine à sous native (🎲/🎰) offrant de 1 à 30 jours Premium par filleul.

## 7. Nouvelles idées à trier

### Paris Et Prédictions (18)
- **Prédiction du nombre exact de buts** — affiche la probabilité de chaque total de buts ; marché peu exploité.
- **Pari sur la première équipe à marquer** — estime qui ouvre le score ; marché souvent sous-analysé.
- **Pari sur le nombre de corners** — prédit le volume de corners à partir du style de jeu des équipes.
- **Pari sur le nombre de cartons jaunes** — s'appuie sur l'historique des fautes et sur l'arbitre désigné.
- **Pari buteur probable selon xG** — classe les joueurs par chance de marquer, à partir des occasions créées.
- **Pari sur la mi-temps à la fin du match** — estime le résultat combiné mi-temps/fin de match.
- **Double chance automatique selon cote** — propose la double chance quand elle offre une meilleure valeur.
- **Pari système multi-sélections** — calcule les gains et risques d'un système, pour mieux gérer les combinés.
- **Calculateur de pari combiné avec marge** — tient compte de la marge du bookmaker dans le gain attendu.
- **Scores exacts les plus probables** — liste les scores les plus probables pour les parieurs qui visent ce marché.
- **Prono sur la différence de buts** — prédit l'écart de buts, plus fin qu'un simple résultat.
- **Pronostics de handicap asiatique** — estime les issues des handicaps, marché populaire chez les parieurs expérimentés.
- **Pronostics de totaux asiatiques** — évalue les totaux avec demi-issues, utile pour réduire le risque.
- **Explication des marchés asiatiques** — détaille les règles des handicaps et totaux, pour éviter les erreurs de compréhension.
- **Buteur et passeur prédits** *(proche de #29)* — identifie les passeurs probables, complément des prédictions de buteurs.
- **Top buteurs par journée** — classement hebdomadaire des buteurs probables, contenu régulier qui fidélise.
- **Cashout automatique selon seuil** — encaisse ou limite la perte dès qu'un seuil défini est atteint.
- **Pari live selon statistiques en cours** — adapte la recommandation pendant le match, à partir des stats actuelles.

### Gestion De Bankroll Et Jeu Responsable (23)
- **Simulateur de Kelly fractionnaire** — calcule une mise prudente selon la valeur estimée ; réduit le risque de ruine.
- **Gestion de bankroll par unités** *(proche de #481)* — exprime les mises en unités, plus simple à suivre qu'en montants.
- **Suivi du ROI par marché** — montre quels marchés sont rentables, pour concentrer les efforts.
- **Suivi du ROI par ligue** — compare la rentabilité des championnats, utile pour choisir où parier.
- **Stop-loss sur série perdante** — suggère une pause après plusieurs pertes, pour éviter la poursuite des pertes.
- **Limite de mise journalière** — plafonne automatiquement les mises du jour ; outil de protection essentiel.
- **Plafond de perte mensuel** — bloque les nouvelles mises quand la perte mensuelle atteint un montant fixé.
- **Objectif de bankroll et suivi** — fixe un objectif et montre la progression, pour garder une vision claire.
- **Mode prudent après perte** — réduit les recommandations de mise après une perte importante.
- **Mode réduction de mise** — baisse automatiquement les mises conseillées pendant une période difficile.
- **Rappel de jeu après un certain temps** — invite à faire une pause après une durée d'utilisation ; prévention simple.
- **Auto-exclusion temporaire** — permet de suspendre l'accès pendant une durée choisie ; protection importante.
- **Test de dépendance au jeu** — questionnaire qui aide l'utilisateur à évaluer son rapport au jeu.
- **Ressources d'aide au jeu responsable** — oriente vers des services d'aide ; indispensable pour un bot de paris.
- **Partenariat avec associations de prévention** — renforce la crédibilité et la protection des utilisateurs.
- **Profil de risque du parieur** — classe l'utilisateur selon sa tolérance au risque, pour adapter les conseils.
- **Questionnaire de profil de risque** — collecte les réponses qui servent à établir le profil de risque.
- **Recommandation de mise personnalisée** — propose une mise adaptée au profil et à la bankroll de l'utilisateur.
- **Alerte objectif atteint** — félicite l'utilisateur quand son objectif est atteint ; renforce l'engagement sain.
- **Rappel de bilan après série** — propose un bilan après une série de paris, pour analyser sans émotion.
- **Historique de l'humeur liée aux pertes** — note l'état émotionnel après les pertes, pour repérer les mauvaises périodes.
- **Soutien psychologique non médical** — oriente vers une aide adaptée sans prétendre remplacer un professionnel.
- **Ressources de sortie de dépendance** — fournit des contacts pour les personnes qui veulent arrêter.

### Analyse Statistique Et Modèle (47)
- **Forme récente sur 10 matchs** — résume les résultats récents d'une équipe ; indicateur simple et lisible.
- **Série d'invincibilité d'une équipe** — suit les séries sans défaite ; signal utile de dynamique.
- **Analyse des coups de pied arrêtés** — mesure l'efficacité sur corners et coups francs ; facteur souvent négligé.
- **Carte de chaleur des tirs** — visualise les zones de tir ; lecture rapide du style offensif.
- **Carte de passes par équipe** — montre les connexions entre joueurs ; utile pour comprendre le jeu.
- **Analyse du pressing** — mesure l'intensité défensive ; indicateur clé de la tactique.
- **Distance parcourue par match** — compare l'effort physique ; utile pour repérer la fatigue.
- **Impact de l'arbitre sur les résultats** — mesure le lien entre arbitre et penalties ou cartons.
- **Influence du public à domicile** — quantifie l'avantage du terrain ; facteur important des prédictions.
- **Effet des voyages sur la performance** — mesure les effets de longs déplacements sur les équipes.
- **Impact du décalage horaire** — estime l'influence des fuseaux horaires sur les matchs internationaux.
- **Calendrier chargé** *(proche de #563)* — détecte les équipes enchaînant les matchs ; risque de baisse de forme.
- **Impact des blessures sur la prédiction** — ajuste la prédiction selon les absents clés.
- **Suivi des suspensions** — prend en compte les joueurs absents pour cause de cartons.
- **Effectif disponible probable** — estime les joueurs disponibles ; base de prédictions fiables.
- **Compositions probables** — anticipe l'équipe de départ ; facteur majeur avant coup d'envoi.
- **Alerte changement de composition** *(proche de #579)* — signale les modifications de dernière minute ; fort impact sur les cotes.
- **Valeur marchande de l'effectif** — compare la valeur des équipes ; indicateur de moyens.
- **Changement d'entraîneur et effet** — mesure la réaction des équipes après un changement de coach.
- **Analyse du coach et tactique** *(proche de #365)* — étudie le style de l'entraîneur ; facteur de prédiction.
- **Performance selon la météo** — analyse l'effet de la pluie, du vent et de la chaleur sur les résultats.
- **Motivation et enjeu du match** — pondère les matchs à enjeu, souvent plus imprévisibles.
- **Matchs à enjeu de qualification** — signale les rencontres décisives pour les places européennes ou la survie.
- **Probabilité de relégation par journée** — suit le risque de relégation au fil de la saison.
- **Simulation de fin de saison** — projette le classement final ; contenu très consulté.
- **Scénarios de titre et de qualification** — détaille les chemins possibles pour chaque équipe.
- **Calendrier restant pour chaque équipe** — liste les matchs à venir ; base de l'analyse de fin de saison.
- **Difficulté du calendrier restant** — mesure la difficulté des prochains matchs.
- **Calibration des probabilités** — vérifie que les pourcentages annoncés correspondent aux résultats réels.
- **Graphique d'importance des variables** — montre les facteurs qui pèsent le plus, pour comprendre le modèle.
- **Rapport d'erreurs par ligue** — identifie les championnats où le modèle se trompe le plus.
- **Rapport d'erreurs par type de match** — repère les situations difficiles pour le modèle.
- **Suivi de la précision par semaine** — mesure l'évolution du modèle dans le temps.
- **Versioning des modèles** — conserve chaque version du modèle, pour comparer et revenir en arrière.
- **Rollback d'un modèle** *(proche de #26)* — restaure une version précédente en cas de régression ; sécurité essentielle.
- **Mode bac à sable pour tester un modèle** — permet de tester sans toucher aux données réelles.
- **Comparaison de modèles A/B** — compare deux modèles sur les mêmes matchs, pour choisir le meilleur.
- **Validation croisée temporelle** *(proche de #434)* — évalue le modèle sans utiliser les données du futur.
- **Détection de biais du modèle** *(proche de #435)* — repère les dérives systématiques, par ligue ou par équipe.
- **Entraînement automatique hebdomadaire** *(proche de #343)* — met à jour le modèle régulièrement avec les nouveaux résultats.
- **Score de confiance par prédiction** — indique la fiabilité de chaque prédiction ; aide à décider.
- **Décomposition des facteurs de la prédiction** — détaille ce qui pousse le modèle vers son résultat.
- **Justification avec les trois facteurs principaux** — résume les raisons clés, lisible en un coup d'œil.
- **Comparaison de deux saisons** *(proche de #638)* — met en parallèle les performances, pour repérer les tendances.
- **Évolution du classement en graphique** *(proche de #87)* — visualise la course au titre ou au maintien.
- **Tableau de bord par championnat** *(proche de #103)* — regroupe les indicateurs d'un championnat au même endroit.
- **Vue comparative de plusieurs équipes** — compare plusieurs équipes côte à côte.

### Cotes Et Marchés (16)
- **Détection des anomalies de cotes** — repère les cotes qui s'écartent fortement du marché ; signal intéressant.
- **Alerte arbitrage de cotes** — signale quand les cotes de deux bookmakers permettent un gain sans risque.
- **Détection d'arbitrage sportif** — identifie les opportunités d'arbitrage ; rares mais précieuses.
- **Meilleur bookmaker par marché** — indique où obtenir la meilleure cote pour chaque type de pari.
- **Calcul de la marge du bookmaker** *(proche de #476)* — montre le coût caché de chaque marché ; utile pour comparer.
- **Alerte value bet par seuil** — prévient quand une cote dépasse un seuil de valeur fixé.
- **Journal des value bets** — garde la trace des paris à valeur, pour mesurer leur efficacité réelle.
- **Historique des variations de cotes** *(proche de #478)* — montre l'évolution des cotes ; indicateur de l'opinion du marché.
- **Convertisseur de cotes** — passe entre cotes décimales, fractionnaires et américaines ; utile aux débutants.
- **Calculateur de probabilité implicite** — transforme une cote en probabilité ; base de toute analyse.
- **Calculateur de cotes implicites** — aide à comprendre ce que la cote dit de la probabilité.
- **Calculateur de gain potentiel** — affiche le gain et la perte possibles avant de parier.
- **Meilleur moment pour parier** — analyse les moments où les cotes sont les plus avantageuses.
- **Comparateur de cotes entre bookmakers** *(proche de #14)* — compare les cotes pour trouver la meilleure.
- **Choix du format de cote** — permet à l'utilisateur de voir les cotes dans le format qu'il connaît.
- **Formatage de devises locales** — affiche les montants dans la devise de l'utilisateur ; plus clair.

### Joueurs Et Équipes (17)
- **Fiche joueur avec statistiques saison** — résume les performances d'un joueur ; référence de base.
- **Comparateur de joueurs** — met deux joueurs côte à côte pour choisir ou comprendre une différence.
- **Joueurs en forme cette semaine** — met en avant les joueurs en progression récente.
- **Alerte joueur en feu** — signale un joueur qui enchaîne les performances ; signal de forme.
- **Stats de jeunes talents à suivre** — repère les jeunes joueurs prometteurs ; contenu original.
- **Liste de joueurs à surveiller** — permet à l'utilisateur de suivre ses joueurs favoris.
- **Journal des transferts** — recense les mouvements de joueurs ; contexte important pour les équipes.
- **Alerte rumeur de transfert vérifiée** — signale les transferts confirmés par des sources fiables, pas les rumeurs.
- **Valeur d'achat d'un joueur** — compare le prix d'un joueur à ses performances ; utile pour les fans de fantasy.
- **Estimation de la valeur des joueurs** — estime la valeur marchande ; complément de l'analyse d'effectif.
- **Historique des confrontations directes** — résume les matchs passés entre deux équipes ; contexte classique.
- **Favoris et outsiders** — analyse les équipes favorites et les outsiders ; utile pour les paris.
- **Taux de nuls par championnat** — mesure la fréquence des nuls ; marché souvent sous-estimé.
- **Analyse des matchs nuls** — étudie les conditions qui mènent aux nuls, pour mieux anticiper.
- **Statistiques de penalties par équipe** — mesure la fréquence et la réussite des penalties ; facteur décisif.
- **Taux de réussite des penalties par tireur** — identifie les tireurs fiables ; utile pour les paris buteur.
- **Striking distance des buteurs** — mesure la régularité des buteurs à partir de leurs tirs.

### Explications Et Apprentissage (11)
- **Explication de la prédiction en langage simple** — traduit les calculs du modèle en mots compréhensibles.
- **Analyse post-match automatique** — résume ce qui a fonctionné ou non après chaque match.
- **Erreur de prono expliquée après match** — détaille pourquoi une prédiction s'est trompée, pour apprendre.
- **Résumé automatique d'après-match** — envoie un résumé court du match ; utile sans regarder la rencontre.
- **Tutoriel interactif au premier démarrage** — guide le nouvel utilisateur étape par étape ; réduit l'abandon.
- **Glossaire des termes de paris** *(proche de #672)* — explique le vocabulaire ; indispensable pour les débutants.
- **Mini-leçons de bankroll** — courts modules sur la gestion d'argent ; éducatif et protecteur.
- **Quiz sur les probabilités** — teste la compréhension des probabilités ; outil pédagogique.
- **Parcours d'apprentissage des paris** — propose un chemin progressif, du débutant à l'avancé.
- **Questions fréquentes intégrées** — répond aux questions courantes sans quitter le bot.
- **Notification de fin de tutoriel** — félicite l'utilisateur et propose la suite ; fluidifie l'onboarding.

### Expérience Utilisateur Et Interface (29)
- **Mode sombre pour l'interface Web** — améliore le confort de lecture ; demande très courante.
- **Thème personnalisable du tableau de bord** — permet d'adapter les couleurs et la présentation.
- **Application web progressive installable** — permet d'installer le service comme une application, sans store.
- **Notifications push navigateur** *(proche de #267)* — envoie des alertes même hors du bot ; meilleure réactivité.
- **Mode nuit et heures de silence** — évite les notifications à certaines heures ; respect du quotidien.
- **Digest quotidien unique** — regroupe les infos du jour en un message ; moins de bruit.
- **Digest hebdomadaire avec bilan** — résume la semaine ; rappel utile pour suivre sa progression.
- **Bilan mensuel automatique** — envoie un récapitulatif mensuel ; fidélise l'utilisateur.
- **Rapport de performance personnel** *(proche de #491)* — affiche les résultats individuels ; base de la transparence.
- **Tableau de bord personnel en image** — produit une image récapitulative, facile à partager.
- **Export CSV de l'historique des paris** — permet d'analyser ses données dans un tableur.
- **Export PDF du bilan mensuel** — fournit un document propre à archiver ou imprimer.
- **Export ICS des matchs favoris** — ajoute les matchs à un agenda ; pratique.
- **Synchronisation avec Google Calendar** — place automatiquement les matchs dans l'agenda de l'utilisateur.
- **Rappel avant coup d'envoi** — prévient avant le début des matchs suivis.
- **Météo du stade avant le match** — affiche la météo sur place ; facteur utile pour l'analyse.
- **Itinéraire vers le stade** — aide à se rendre au match ; service pratique pour les supporters.
- **Résumé audio des prédictions du jour** — permet d'écouter les prédictions ; utile en déplacement.
- **Message vocal de prédiction quotidienne** — envoie les prédictions en audio ; accessibilité renforcée.
- **Lecture à voix haute des stats** — lit les statistiques à voix haute ; utile pour les malvoyants.
- **Feedback 👍 👎 sur chaque prono** — recueille l'avis des utilisateurs ; aide à améliorer le service.
- **Sondage de satisfaction mensuel** — mesure la satisfaction globale ; indicateur de qualité.
- **Suggestion de nouvelle fonctionnalité** — permet aux utilisateurs de proposer des idées.
- **Vote sur les prochaines fonctionnalités** — fait participer la communauté aux choix de développement.
- **Changelog intégré dans le bot** — affiche les nouveautés ; informe sans effort.
- **Notes de version envoyées automatiquement** — prévient les utilisateurs des changements importants.
- **Support de l'arabe** — élargit l'audience, selon le public visé.
- **Support de l'anglais complet** — rend le service accessible à un public international.
- **Traduction des pronostics** — traduit les analyses à la volée ; pour un public multilingue.

### Communauté Et Partage (29)
- **Ligue privée entre amis** *(proche de #68)* — permet de jouer entre proches ; forte source d'engagement.
- **Défi hebdomadaire avec classement** — crée une compétition régulière ; motivante.
- **Badges de réussite** — récompense les étapes atteintes ; renforce la progression.
- **Niveaux d'expérience du parieur** — classe les utilisateurs selon leur expérience ; valorise l'apprentissage.
- **Programme d'ambassadeurs** — récompense les utilisateurs qui recommandent le service.
- **Pronostics collectifs de groupe** — permet des analyses partagées ; idée sociale.
- **Sondage de consensus du groupe** — montre l'avis majoritaire du groupe sur un match.
- **Chat de discussion par match** — crée un espace d'échange autour de chaque rencontre.
- **Fil de commentaires par match** — permet de commenter les matchs ; engagement communautaire.
- **Carte de partage de pronostic** — génère une image prête à partager ; visibilité naturelle.
- **Image de résultat à partager** — partage les résultats en image ; format attractif.
- **Lien de partage de bilan** — permet de montrer ses performances ; à utiliser avec transparence.
- **Code QR vers le bot** — facilite l'accès au bot depuis des supports imprimés.
- **Bot de canal Telegram automatique** — publie les prédictions dans un canal ; diffusion large.
- **Publication automatique dans un canal** — envoie les contenus au bon moment sans intervention.
- **Historique public des performances** *(proche de #7)* — rend les résultats visibles ; base de la confiance.
- **Badge de transparence des résultats** — affiche la preuve de fiabilité ; argument commercial fort.
- **Vérification indépendante des pronostics** — permet à un tiers de contrôler les résultats publiés.
- **Horodatage des prédictions avant match** — prouve que la prédiction a été faite avant le coup d'envoi.
- **Preuve cryptographique des pronostics** — garantit qu'un prono n'a pas été modifié après coup.
- **Export des preuves de prédiction** — fournit les preuves à l'utilisateur pour vérification.
- **Fil d'actualité des résultats** — affiche les derniers résultats ; contenu régulier.
- **Hall of fame des meilleurs parieurs** — valorise les meilleurs utilisateurs ; motivation communautaire.
- **Trophées de fin de saison** — récompense les performances annuelles ; moment fort de l'engagement.
- **Quête hebdomadaire** — propose un objectif hebdomadaire ; incite à revenir.
- **Mission quotidienne** — donne une tâche simple chaque jour ; habitude d'usage.
- **Intégration Discord** — étend le service à une communauté Discord, selon la demande.
- **Intégration WhatsApp** — étend le service à WhatsApp ; à vérifier selon les conditions de la plateforme.
- **Invitation par lien d'un groupe Telegram** — facilite l'arrivée de nouveaux membres.

### Administration Et Fiabilité (25)
- **Page de statut public** — informe les utilisateurs de l'état du service ; gage de confiance.
- **Statut des services en direct** — montre en temps réel l'état des composants.
- **Historique des incidents** — garde la trace des pannes, pour analyser et progresser.
- **Alerte panne API fournisseur** — prévient quand une source de données tombe ; réaction rapide.
- **Mode maintenance avec message** *(proche de #123)* — affiche un message clair pendant les interventions.
- **Journal des erreurs fournisseur** *(proche de #666)* — suit les erreurs des sources externes ; aide au diagnostic.
- **Sauvegarde automatique quotidienne** — protège les données ; indispensable en production.
- **Restauration en un clic** — permet de revenir rapidement à une sauvegarde saine.
- **Journal d'audit des actions admin** *(proche de #216)* — trace qui fait quoi ; sécurité et responsabilité.
- **Gestion des rôles admin** *(proche de #115)* — limite les droits selon la fonction de chacun.
- **Authentification à deux facteurs** — sécurise l'accès administrateur ; mesure de base.
- **Connexion par lien magique** — permet une connexion sans mot de passe ; plus simple.
- **Sessions multi-appareils** — affiche les appareils connectés ; gestion de sécurité.
- **Révocation de session** — déconnecte un appareil à distance ; utile en cas de perte.
- **Détection de connexion suspecte** — alerte sur les accès inhabituels ; protection des comptes.
- **Export RGPD des données utilisateur** *(proche de #688)* — fournit les données personnelles sur demande ; obligation légale dans de nombreux pays.
- **Suppression de compte en un clic** — respecte le droit à l'effacement ; attendu par les utilisateurs.
- **Politique de confidentialité intégrée** — rend la politique accessible depuis le bot ; transparence.
- **Consentement cookies et messages** — recueille l'accord de l'utilisateur ; exigence légale.
- **Vérification de l'âge des utilisateurs** — limite l'accès aux adultes ; obligatoire selon les pays.
- **Limites par pays selon la législation** — adapte les services à la réglementation locale.
- **Blocage de pays à risque** — restreint l'accès là où le service n'est pas autorisé.
- **Conformité aux règles locales** — vérifie les obligations légales de chaque marché.
- **Gestion des litiges de paiement** — traite les réclamations ; important pour la confiance.
- **Remboursement automatique** — rembourse selon des règles claires ; réduit les litiges.

### Abonnements Et Paiements (24)
- **Plans d'abonnement comparés** — présente clairement les offres ; aide au choix.
- **Essai gratuit de 7 jours** — permet de tester avant de payer ; levier de conversion classique.
- **Réduction pour paiement annuel** — encourage l'engagement long terme ; meilleure rétention.
- **Offre de fidélité** — récompense les abonnés anciens ; réduit le départ.
- **Facture mensuelle automatique** — envoie les factures sans effort ; utile pour la comptabilité.
- **Facture PDF par paiement** — fournit un justificatif à chaque achat.
- **Relance de paiement échoué** *(proche de #182)* — relance l'utilisateur pour éviter la perte d'abonnés.
- **Renouvellement automatique** — évite les interruptions de service, avec information claire.
- **Notification avant fin d'abonnement** — prévient à temps ; réduit les départs involontaires.
- **Email de rappel d'expiration** — rappelle l'échéance par email ; complément utile.
- **Pause d'abonnement** — permet de suspendre sans résilier ; option appréciée.
- **Passage de plan à la volée** — permet de changer d'offre immédiatement ; plus de souplesse.
- **Tarif étudiant** — rend le service accessible aux étudiants ; élargit l'audience.
- **Tarif groupe** — propose une offre pour plusieurs personnes ; idée de vente collective.
- **Offre famille** — partage un abonnement dans le cercle familial ; option de fidélisation.
- **Pass journée** — offre un accès court ; idée d'entrée à faible coût.
- **Pass championnat complet** — donne accès à une compétition entière ; offre ciblée.
- **Accès anticipé aux bêtas** — donne un avantage aux premiers abonnés ; valorise la fidélité.
- **Programme beta testeurs** — recrute des testeurs pour améliorer le produit.
- **Retour des bêta testeurs** — collecte les retours structurés ; utile pour la qualité.
- **Campagne de réengagement** — relance les utilisateurs qui ont cessé d'utiliser le service.
- **Relance des utilisateurs inactifs** — rappelle le service aux inactifs ; réduit le churn.
- **Email de bienvenue** — accueille les nouveaux utilisateurs ; première impression importante.
- **Offre de bienvenue personnalisée** *(proche de #315)* — propose une offre adaptée au profil ; meilleure conversion.
