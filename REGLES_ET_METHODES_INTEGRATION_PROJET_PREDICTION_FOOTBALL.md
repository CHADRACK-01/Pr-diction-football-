# RÈGLES ET MÉTHODES D'INTÉGRATION ET DE FIABILISATION

## Projet Prédiction Football

**Version :** 1.0\
**Nature du document :** Référentiel technique obligatoire pour le
développement, la correction, l'intégration et l'évolution du projet.\
**Périmètre :** fonctionnalités existantes, partiellement développées, à
développer et futures fonctionnalités.

------------------------------------------------------------------------

# 1. Objectif et principe directeur

Ce document définit les règles que toute intervention sur le projet doit
respecter afin que les fonctionnalités ne soient pas seulement
développées séparément, mais fonctionnent correctement ensemble.

Le but final est d'obtenir un système cohérent dans lequel :

-   chaque fonctionnalité a un rôle précis ;
-   les modules communiquent par des interfaces clairement définies ;
-   les données restent cohérentes entre les modules ;
-   une modification ne casse pas une fonctionnalité déjà opérationnelle
    ;
-   les erreurs sont détectées avant la mise en production ;
-   les traitements automatiques ne s'exécutent pas plusieurs fois par
    erreur ;
-   les fonctionnalités futures peuvent être ajoutées sans devoir
    reconstruire tout le projet.

**Règle fondamentale : une fonctionnalité n'est jamais considérée comme
terminée parce que son fichier existe ou parce que son écran apparaît.
Elle est terminée uniquement lorsque son comportement, ses données, ses
dépendances, ses interactions avec les autres modules et ses tests sont
validés.**

Ce référentiel doit être appliqué à toutes les fonctionnalités, sans
exception, y compris celles qui semblent petites.

# 2. État officiel des fonctionnalités

Chaque fonctionnalité doit posséder un identifiant stable et un état
unique dans le catalogue officiel.

États autorisés :

  ------------------------------------------------------------------------
  État                     Signification           Condition
  ------------------------ ----------------------- -----------------------
  `EXISTANTE_VALIDEE`      Fonctionnalité déjà     Tests et critères
                           opérationnelle          d'acceptation réussis

  `EXISTANTE_A_VERIFIER`   Fonctionnalité          Audit et tests
                           présente, mais pas      nécessaires
                           suffisamment validée    

  `PARTIELLE`              Une partie du           Les éléments manquants
                           comportement est        sont identifiés
                           développée              

  `A_DEVELOPPER`           Fonctionnalité prévue,  Spécification
                           non développée          disponible ou à rédiger

  `BLOQUEE`                Développement           Blocage documenté
                           impossible tant qu'une  
                           dépendance n'est pas    
                           résolue                 

  `A_REFAIRE`              Implémentation          Plan de remplacement
                           existante jugée         approuvé
                           inadaptée               

  `ABANDONNEE`             Fonctionnalité retirée  Décision et motif
                           du périmètre            conservés
  ------------------------------------------------------------------------

Ne pas utiliser « terminé », « presque terminé » ou « fonctionnel » sans
critères vérifiables.

Pour chaque fonctionnalité, conserver au minimum :

-   identifiant et nom ;
-   description et résultat attendu ;
-   état ;
-   responsable ou module propriétaire ;
-   fichiers et composants concernés ;
-   dépendances entrantes et sortantes ;
-   données lues et écrites ;
-   événements émis et consommés ;
-   permissions requises ;
-   cas normaux, limites et erreurs ;
-   tests associés ;
-   date de dernière vérification ;
-   version dans laquelle elle a été validée.

Le catalogue des 700 fonctionnalités reste la référence fonctionnelle.
Les documents texte, le fichier JSON, le fichier Markdown et le code
doivent être synchronisés. Aucun document ne doit être considéré comme
plus exact que le code sans vérification.

# 3. Règles d'architecture obligatoires

## 3.1 Une responsabilité claire par module

Chaque module doit avoir une responsabilité principale identifiable.

Exemples de domaines à préserver dans ce projet :

-   collecte et normalisation des données sportives ;
-   équipes, compétitions, matchs et résultats ;
-   statistiques et préparation des données ;
-   modèles et calculs de prédiction ;
-   validation, calibration et backtesting ;
-   gestion des utilisateurs et de leurs préférences ;
-   interface et interactions Telegram ;
-   abonnements, crédits et paiements ;
-   administration et contrôle ;
-   notifications et planification ;
-   API et interfaces web, si elles sont utilisées.

Un module ne doit pas devenir un endroit où l'on ajoute n'importe quelle
fonction simplement parce qu'il est déjà importé.

## 3.2 Une seule source de vérité

Pour chaque donnée métier, définir un propriétaire officiel.

Exemples :

-   le résultat officiel d'un match doit avoir une source de vérité ;
-   le solde de crédits doit être calculé ou enregistré selon une règle
    unique ;
-   le statut d'un paiement doit être géré par le domaine des paiements
    ;
-   les préférences de notification doivent être gérées par le domaine
    utilisateur ;
-   le statut d'une prédiction doit être défini par le domaine des
    prédictions.

Les autres modules consultent cette source au moyen d'une interface
documentée. Ils ne créent pas leur propre copie modifiable de la même
information.

Les copies destinées au cache ou à l'analyse doivent être identifiées
comme telles, datées et renouvelables.

## 3.3 Interdire les dépendances circulaires

Un module A ne doit pas dépendre de B si B dépend déjà de A.

Les règles métier ne doivent pas dépendre directement des gestionnaires
Telegram, des pages web ou des détails d'un fournisseur externe.

Architecture recommandée :

**Interface (Telegram / Web / API) → Services applicatifs → Domaine
métier → Dépôts de données et adaptateurs**

Les adaptateurs communiquent avec les services externes et traduisent
leurs réponses vers les formats internes du projet.

## 3.4 Imports et points d'entrée

-   Définir un seul point d'entrée officiel pour le démarrage de
    l'application.
-   Définir une seule configuration officielle.
-   Utiliser des imports cohérents depuis le package racine.
-   Ne pas mélanger les imports relatifs et absolus sans convention
    documentée.
-   Ne pas contourner les packages en modifiant le `sys.path` dans
    plusieurs fichiers.
-   Toute migration de fichier doit entraîner la mise à jour de tous ses
    imports, tests, commandes et documents.
-   Les anciens points d'entrée doivent être supprimés ou maintenus
    comme passerelles temporaires clairement signalées.

Pour ce projet, les coexistences de fichiers à la racine et dans `src/`,
ainsi que les anciens et nouveaux gestionnaires, doivent être traitées
comme des zones à auditer avant toute nouvelle extension.

# 4. Contrat obligatoire avant de développer une fonctionnalité

Aucun développement ne commence directement par l'écriture du code.

Chaque fonctionnalité doit d'abord posséder une fiche de conception
contenant :

1.  **Identité :** identifiant du catalogue et nom.
2.  **Problème :** besoin concret auquel elle répond.
3.  **Résultat attendu :** comportement observable par l'utilisateur ou
    un autre module.
4.  **Déclencheur :** commande, action, événement, horaire ou appel API.
5.  **Entrées :** données nécessaires, formats et validations.
6.  **Sorties :** réponse, données enregistrées ou événement produit.
7.  **Propriétaire :** module responsable de la règle métier.
8.  **Dépendances :** modules, services, API et données nécessaires.
9.  **Permissions :** rôles autorisés et contrôles requis.
10. **Règles métier :** calculs, limites, conditions et exceptions.
11. **États :** cycle de vie de l'opération.
12. **Erreurs :** erreurs possibles et comportement attendu.
13. **Sécurité :** secrets, données personnelles, abus et risques.
14. **Observabilité :** journaux, métriques et alertes utiles.
15. **Tests :** scénarios unitaires, intégration et bout en bout.
16. **Compatibilité :** effets sur les fonctionnalités existantes.
17. **Critères d'acceptation :** conditions mesurables de validation.

Si une information manque, la fonctionnalité reste en conception ou est
marquée `BLOQUEE`. Le développeur ne doit pas inventer silencieusement
une règle métier.

# 5. Méthode de développement en petites étapes

Pour chaque fonctionnalité, appliquer l'ordre suivant :

1.  Lire la fiche fonctionnelle et le code existant.
2.  Rechercher les fonctions similaires pour éviter les doublons.
3.  Identifier le module propriétaire et les dépendances.
4.  Vérifier les données et les contrats déjà disponibles.
5.  Définir les scénarios normaux et les scénarios d'échec.
6.  Écrire ou mettre à jour les tests avant ou pendant l'implémentation.
7.  Développer la logique métier indépendamment de l'interface.
8.  Ajouter les dépôts, adaptateurs ou migrations nécessaires.
9.  Relier la fonctionnalité à Telegram, au Web ou à l'API via les
    services applicatifs.
10. Tester les échanges avec les modules dépendants.
11. Exécuter toute la suite de tests concernée, puis la suite complète.
12. Mettre à jour le catalogue, l'architecture et la documentation.
13. Effectuer une revue de code.
14. Déployer progressivement et surveiller le comportement.
15. Passer à `EXISTANTE_VALIDEE` uniquement lorsque les critères sont
    satisfaits.

Chaque modification doit rester aussi petite et réversible que possible.
Éviter les réécritures massives qui mélangent plusieurs fonctionnalités.

# 6. Contrats de communication entre modules

Tout échange entre deux modules doit être explicite et documenté.

Pour chaque interface, préciser :

-   le nom de l'opération ;
-   le module qui la fournit ;
-   les modules autorisés à l'appeler ;
-   les paramètres obligatoires et facultatifs ;
-   les types et formats ;
-   la valeur de retour ;
-   les erreurs possibles ;
-   les effets de bord ;
-   les règles de transaction ;
-   la version du contrat.

Ne pas faire dépendre un module des variables internes ou des fonctions
privées d'un autre module.

Éviter les appels directs à la base de données depuis les gestionnaires
Telegram. Les gestionnaires doivent déléguer aux services applicatifs.

Les réponses des API externes doivent être converties vers des objets
internes stables. Le reste du projet ne doit pas dépendre du format brut
d'un fournisseur.

# 7. Gestion des données et de la base de données

## 7.1 Intégrité

-   Définir des clés primaires et étrangères.
-   Ajouter les contraintes `NOT NULL`, `UNIQUE` et `CHECK` pertinentes.
-   Définir les règles de suppression et de mise à jour des relations.
-   Utiliser des transactions pour les opérations composées.
-   Stocker les dates et heures de manière cohérente, avec un traitement
    explicite des fuseaux horaires.
-   Définir clairement les unités : devise, montant, pourcentage, cote,
    probabilité, nombre de buts, etc.
-   Éviter les valeurs ambiguës et les colonnes dont le sens n'est pas
    documenté.

## 7.2 Migrations

Toute modification de schéma doit être livrée avec une migration
versionnée.

Une migration doit être :

-   relue ;
-   testée sur une base vierge ;
-   testée sur une copie représentative des données existantes ;
-   accompagnée d'une stratégie de sauvegarde et de retour arrière ;
-   compatible avec la version de l'application prévue pour le
    déploiement.

Ne jamais modifier manuellement la base de production sans procédure
enregistrée.

## 7.3 Historique et traçabilité

Les changements importants doivent conserver leur historique lorsque
cela est nécessaire : paiement, abonnement, crédit, prédiction publiée,
résultat de match, correction de données et action administrative.

Ne pas écraser une information historique si cela empêche de comprendre
ce qui s'est passé.

## 7.4 Concurrence et opérations répétées

Les opérations sensibles doivent être protégées contre les exécutions
simultanées et les répétitions.

Utiliser, selon le besoin :

-   contraintes d'unicité ;
-   transactions ;
-   verrouillage adapté ;
-   clés d'idempotence ;
-   contrôle de version ;
-   file de tâches avec identifiant unique.

Un double clic, un délai réseau ou une relance automatique ne doit pas
provoquer deux paiements, deux crédits ou deux notifications facturées.

# 8. Règles particulières aux données footballistiques et aux prédictions

## 8.1 Données sportives

Chaque donnée provenant d'un fournisseur doit conserver, lorsque
possible :

-   le fournisseur ;
-   son identifiant externe ;
-   la date de récupération ;
-   la date de dernière mise à jour ;
-   le statut de validation ;
-   la saison et la compétition concernées.

Normaliser les noms des équipes, compétitions, saisons et statuts de
match. Ne pas supposer que deux noms identiques représentent toujours la
même entité.

Prévoir les cas suivants :

-   match reporté ou annulé ;
-   match interrompu ;
-   changement d'horaire ;
-   résultat corrigé ;
-   données manquantes ;
-   API indisponible ;
-   doublon de match ;
-   compétition ou équipe inconnue.

Une donnée manquante ne doit jamais être transformée silencieusement en
zéro.

## 8.2 Prédictions

Toute prédiction doit pouvoir être retracée.

Conserver au minimum, selon le modèle :

-   le match concerné ;
-   l'horodatage de génération ;
-   la version du modèle ;
-   les données utilisées ou leur référence ;
-   les probabilités calculées ;
-   les marchés concernés ;
-   les paramètres importants ;
-   le statut de validation ;
-   le résultat réel après le match ;
-   la méthode d'évaluation.

Les probabilités doivent être cohérentes et leur somme doit respecter
les règles du marché considéré. Les valeurs impossibles, NaN, infinies
ou hors intervalle doivent être rejetées.

Ne jamais entraîner ou évaluer un modèle avec des informations qui
n'étaient pas disponibles au moment historique de la prédiction.
Prévenir les fuites de données (*data leakage*).

Les performances doivent être évaluées sur des périodes séparées et
représentatives, avec comparaison à des références simples. Mesurer
notamment la calibration, le score de Brier, la log-loss et les
performances par compétition et par marché lorsque les données le
permettent.

Un modèle plus complexe n'est pas automatiquement meilleur. Toute mise à
jour du modèle doit être comparée à la version précédente avant
activation.

## 8.3 Publication

Une prédiction ne doit être présentée comme disponible que si ses
données et son état de validation satisfont les règles définies.

Afficher clairement les limites, l'incertitude et la date de génération.
Ne jamais présenter une probabilité comme une garantie de résultat.

# 9. Paiements, crédits et abonnements

Les paiements constituent un domaine critique.

-   Ne jamais considérer un paiement comme réussi sur la seule base d'un
    retour visuel de l'interface.
-   Vérifier la confirmation côté serveur auprès du fournisseur.
-   Vérifier les signatures des notifications de paiement lorsque le
    fournisseur en propose.
-   Utiliser une référence de transaction unique.
-   Rendre les traitements de confirmation idempotents.
-   Séparer les états `EN_ATTENTE`, `CONFIRME`, `REFUSE`, `EXPIRE`,
    `REMBOURSE` et les autres états nécessaires.
-   Enregistrer les événements et changements d'état.
-   Ne jamais stocker les données complètes de carte bancaire.
-   Ne jamais inscrire de secret ou de jeton dans les journaux.
-   Réconcilier régulièrement les paiements locaux avec les transactions
    du fournisseur.

Les crédits doivent être gérés par un journal d'opérations traçable.
Éviter de modifier un solde sans enregistrer la raison et l'opération
correspondante.

Les changements d'abonnement doivent être cohérents avec les droits
réellement accordés à l'utilisateur.

# 10. Telegram, interface Web et expérience utilisateur

L'interface ne doit pas contenir les règles métier principales.

Un gestionnaire Telegram doit :

1.  recevoir l'action ;
2.  vérifier le contexte et l'identité ;
3.  contrôler les permissions ;
4.  valider les paramètres de base ;
5.  appeler un service applicatif ;
6.  présenter le résultat.

Les mêmes règles métier doivent pouvoir être réutilisées depuis une
autre interface sans les recopier.

Prévoir :

-   les erreurs compréhensibles pour l'utilisateur ;
-   les délais de réponse ;
-   les commandes inconnues ;
-   les messages trop longs ;
-   les clics répétés ;
-   les conversations interrompues ;
-   les utilisateurs non autorisés ;
-   les limitations de fréquence ;
-   la reprise d'un parcours interrompu.

Les boutons et menus ne doivent pas donner accès à une action simplement
parce qu'ils sont visibles. Les permissions doivent être revérifiées
côté serveur à chaque opération sensible.

# 11. Planification, tâches automatiques et notifications

Toute tâche programmée doit préciser :

-   son identifiant ;
-   son objectif ;
-   sa fréquence ;
-   son fuseau horaire ;
-   ses conditions d'exécution ;
-   sa durée maximale ;
-   sa politique de nouvelle tentative ;
-   son comportement en cas d'échec ;
-   sa règle d'unicité ;
-   son journal d'exécution.

Les tâches doivent être idempotentes autant que possible. Une tâche
relancée après une panne ne doit pas répéter les effets déjà appliqués.

Les notifications doivent respecter les préférences de l'utilisateur,
les limites de fréquence et les règles de désabonnement.

Éviter qu'un même événement soit envoyé plusieurs fois par des systèmes
de notification différents. Définir un propriétaire et un mécanisme de
déduplication.

# 12. Stratégie de tests obligatoire

Aucune fonctionnalité ne peut être validée uniquement par un test
manuel.

## 12.1 Tests unitaires

Tester séparément les règles métier et les calculs :

-   entrées normales ;
-   valeurs limites ;
-   données invalides ;
-   données absentes ;
-   erreurs attendues ;
-   cas particuliers.

Les tests unitaires doivent être rapides et indépendants des API
réelles.

## 12.2 Tests d'intégration

Vérifier les interactions réelles entre composants :

-   service et base de données ;
-   service et adaptateur API ;
-   paiement et journal des crédits ;
-   prédiction et données du match ;
-   notification et préférences utilisateur ;
-   gestionnaire Telegram et service métier.

Utiliser des bases et fournisseurs de test, ou des réponses simulées
contrôlées lorsque nécessaire.

## 12.3 Tests de bout en bout

Tester des parcours complets représentatifs, par exemple :

-   utilisateur → consultation d'un match → génération ou affichage
    d'une prédiction ;
-   récupération des matchs → normalisation → stockage → statistiques →
    prédiction ;
-   demande de paiement → confirmation fournisseur → activation des
    droits ;
-   résultat final → mise à jour du match → évaluation de la prédiction
    ;
-   tâche planifiée → détection d'un événement → notification unique.

## 12.4 Tests de non-régression

Après chaque modification, relancer les tests des fonctionnalités
dépendantes et les tests globaux.

Un test qui échouait avant la modification doit être identifié comme
tel. Il ne faut jamais masquer un échec en supprimant le test ou en
réduisant ses assertions sans justification.

## 12.5 Tests de charge et de résilience

Pour les fonctions critiques, vérifier :

-   plusieurs utilisateurs simultanés ;
-   plusieurs tâches simultanées ;
-   ralentissement ou indisponibilité d'une API ;
-   coupure de base de données ;
-   relance après interruption ;
-   volume important de matchs et de notifications.

# 13. Contrôles automatiques avant chaque fusion de code

Mettre en place une chaîne de vérification automatique (*CI*).

Ordre recommandé :

1.  vérification de la syntaxe ;
2.  contrôle du formatage ;
3.  analyse statique et détection des erreurs ;
4.  vérification des imports ;
5.  tests unitaires ;
6.  tests d'intégration ;
7.  tests de non-régression ;
8.  contrôle des migrations ;
9.  vérification des dépendances et vulnérabilités ;
10. contrôle des secrets ;
11. génération ou validation de la documentation.

Une modification ne doit pas être fusionnée si un contrôle obligatoire
échoue, sauf dérogation documentée, approuvée et limitée.

Pour le projet actuel, la première étape est de rendre l'environnement
de test reproductible et de corriger les erreurs de collecte des tests
avant d'ajouter de nouvelles fonctionnalités.

# 14. Sécurité obligatoire

-   Les secrets restent dans l'environnement ou un gestionnaire de
    secrets, jamais dans le code.
-   Le fichier `.env` ne doit pas être distribué ni versionné.
-   Le fichier `.env.example` ne contient que des valeurs fictives.
-   Vérifier les permissions côté serveur.
-   Valider et normaliser les entrées utilisateur.
-   Utiliser des requêtes SQL paramétrées.
-   Limiter les tentatives et les appels abusifs.
-   Protéger les webhooks et callbacks.
-   Ne pas exposer les erreurs internes à l'utilisateur.
-   Masquer les données sensibles dans les journaux.
-   Mettre à jour les dépendances et surveiller les vulnérabilités.
-   Prévoir sauvegardes, restauration et contrôle d'accès aux
    sauvegardes.

Toute faille critique doit bloquer la mise en production jusqu'à
correction ou acceptation formelle du risque.

# 15. Gestion des erreurs et observabilité

Une erreur ne doit pas être simplement ignorée.

Chaque erreur importante doit produire :

-   un message de journal structuré ;
-   un niveau de gravité ;
-   un identifiant de corrélation lorsque plusieurs modules
    interviennent ;
-   le contexte technique utile, sans secret ;
-   une action de reprise ou une alerte si nécessaire.

Utiliser des niveaux cohérents : DEBUG, INFO, WARNING, ERROR et
CRITICAL.

Surveiller au minimum :

-   disponibilité des API ;
-   échecs de collecte ;
-   retard des tâches planifiées ;
-   erreurs de base de données ;
-   échecs de paiement ;
-   erreurs de prédiction ;
-   volume de notifications ;
-   taux d'échec des commandes ;
-   temps de réponse ;
-   erreurs non interceptées.

Les journaux ne remplacent pas les métriques et les alertes.

# 16. Compatibilité et évolution future

Toute nouvelle fonctionnalité doit respecter les contrats existants.

Avant de modifier un contrat utilisé par plusieurs modules :

1.  rechercher tous ses consommateurs ;
2.  mesurer l'impact ;
3.  définir une stratégie de transition ;
4.  maintenir temporairement la compatibilité si nécessaire ;
5.  migrer les consommateurs ;
6.  supprimer l'ancien contrat seulement après vérification.

Pour les changements importants, versionner les API, événements ou
structures de données.

Les extensions futures doivent utiliser les interfaces publiques
prévues. Elles ne doivent pas accéder directement aux variables internes
d'un autre module.

Préférer une architecture extensible, mais ne pas créer des couches
abstraites sans besoin concret. Toute abstraction doit résoudre un
problème réel et documenté.

# 17. Revue de code obligatoire

Chaque modification doit être relue par une autre personne ou, à défaut,
faire l'objet d'une revue structurée.

La revue vérifie :

-   respect de la responsabilité du module ;
-   absence de logique métier dupliquée ;
-   lisibilité et nommage ;
-   gestion des erreurs ;
-   sécurité ;
-   intégrité des données ;
-   concurrence et idempotence ;
-   tests suffisants ;
-   compatibilité avec l'existant ;
-   documentation actualisée ;
-   absence de secrets ou de fichiers temporaires.

Une modification importante ne doit pas être acceptée uniquement parce
qu'elle fonctionne sur l'ordinateur de son auteur.

# 18. Déploiement progressif et retour arrière

Le déploiement doit suivre une procédure répétable :

1.  sauvegarder les données ;
2.  vérifier la version et les dépendances ;
3.  appliquer les migrations compatibles ;
4.  déployer la nouvelle version ;
5.  vérifier les contrôles de santé ;
6.  exécuter les tests de fumée ;
7.  surveiller les erreurs et métriques ;
8.  confirmer la stabilité ;
9.  revenir à la version précédente si les seuils d'échec sont dépassés.

Lorsque possible, utiliser des fonctionnalités activables
progressivement (*feature flags*) pour tester une nouvelle fonction sur
un périmètre limité.

Une migration irréversible exige une procédure de restauration
documentée et testée.

# 19. Définition officielle de « fonctionnalité terminée »

Une fonctionnalité peut passer à `EXISTANTE_VALIDEE` uniquement si
toutes les conditions applicables sont satisfaites :

-   [ ] Besoin et comportement documentés.
-   [ ] Identifiant du catalogue conservé.
-   [ ] Module propriétaire identifié.
-   [ ] Dépendances identifiées.
-   [ ] Contrats d'entrée et de sortie documentés.
-   [ ] Règles métier implémentées.
-   [ ] Validations et permissions appliquées.
-   [ ] Gestion des erreurs prévue.
-   [ ] Données persistées de manière cohérente.
-   [ ] Migrations testées si nécessaire.
-   [ ] Tests unitaires réussis.
-   [ ] Tests d'intégration réussis.
-   [ ] Tests de non-régression réussis.
-   [ ] Parcours de bout en bout réussi si applicable.
-   [ ] Sécurité vérifiée.
-   [ ] Journaux et métriques utiles disponibles.
-   [ ] Documentation mise à jour.
-   [ ] Revue de code effectuée.
-   [ ] Déploiement vérifié ou procédure de déploiement validée.

Si une condition applicable manque, la fonctionnalité reste partielle, à
vérifier ou bloquée.

# 20. Ordre de stabilisation recommandé pour le projet actuel

Avant d'accélérer le développement du catalogue, traiter les fondations
dans cet ordre :

**Étape A --- Sécuriser le dépôt** - contrôler les secrets et les
fichiers `.env` ; - nettoyer les fichiers temporaires et compilés ; -
vérifier `.gitignore` ; - identifier les fichiers de configuration
officiels.

**Étape B --- Stabiliser le démarrage** - choisir un point d'entrée ; -
choisir une configuration ; - uniformiser les imports ; - vérifier
l'installation reproductible des dépendances.

**Étape C --- Rendre les tests exécutables** - installer les dépendances
de test ; - corriger les erreurs de collecte ; - séparer les tests
unitaires des tests nécessitant des services externes ; - obtenir un
rapport de référence.

**Étape D --- Cartographier les dépendances** - établir les dépendances
entre modules ; - repérer les fonctions dupliquées ; - repérer les
anciens gestionnaires ; - désigner les sources de vérité.

**Étape E --- Stabiliser les domaines critiques** - données
footballistiques ; - prédictions et évaluation ; - utilisateurs et
permissions ; - paiements et crédits ; - tâches planifiées et
notifications.

**Étape F --- Développer les fonctionnalités** - appliquer la fiche de
conception ; - développer par petits lots ; - tester les interactions
; - actualiser le catalogue.

**Étape G --- Préparer la production** - tests de charge et de
résilience ; - sauvegarde et restauration ; - sécurité ; - surveillance
; - déploiement progressif.

Cet ordre est une recommandation de méthode. Il ne signifie pas que
chaque module est déjà défectueux : chaque point doit être confirmé par
un audit et des tests.

# 21. Règles à donner à tout agent IA ou développeur

Toute personne ou agent IA intervenant sur le projet doit respecter les
instructions suivantes :

1.  Lire ce référentiel et la documentation pertinente avant de modifier
    le code.
2.  Lire la fiche de la fonctionnalité concernée dans le catalogue.
3.  Examiner les fichiers existants et rechercher les implémentations
    similaires.
4.  Ne pas créer une deuxième implémentation d'une fonction déjà
    disponible.
5.  Ne pas modifier ou supprimer une fonction publique sans analyser ses
    consommateurs.
6.  Ne pas remplacer une règle métier par une supposition.
7.  Ne pas modifier plusieurs domaines sans expliquer pourquoi.
8.  Ne pas supprimer un test pour faire passer la suite.
9.  Ajouter ou mettre à jour les tests avec chaque changement.
10. Vérifier les interactions avec les modules dépendants.
11. Mettre à jour la documentation et le catalogue.
12. Signaler explicitement les points non testés, les hypothèses et les
    limites.
13. Ne jamais déclarer une fonctionnalité terminée sans preuves de
    validation.
14. Fournir un compte rendu des fichiers modifiés, des tests exécutés et
    des résultats.
15. En cas de doute sur une règle métier ou un contrat, arrêter la
    modification concernée et demander une décision plutôt que
    d'inventer.

## Format obligatoire du compte rendu d'intervention

Pour chaque tâche, fournir :

-   **Fonctionnalité :** identifiant et nom.
-   **État avant intervention :** état du catalogue.
-   **Objectif :** résultat recherché.
-   **Fichiers consultés :** chemins exacts.
-   **Fichiers modifiés :** chemins exacts et raison.
-   **Dépendances examinées :** modules et contrats concernés.
-   **Tests ajoutés ou modifiés :** liste.
-   **Commandes de vérification :** commandes réellement exécutées.
-   **Résultats :** réussites et échecs exacts.
-   **Risques restants :** éléments non vérifiés.
-   **Documentation mise à jour :** références.
-   **État final proposé :** état justifié par les preuves.

# 22. Principe final de qualité

La qualité du projet ne se mesure pas au nombre de fichiers, au nombre
de lignes ou au nombre de fonctionnalités annoncées.

Elle se mesure à la capacité du système à :

-   produire le bon résultat ;
-   préserver l'intégrité des données ;
-   résister aux erreurs et aux interruptions ;
-   faire collaborer ses modules ;
-   évoluer sans casser l'existant ;
-   être testé, compris, maintenu et déployé de manière reproductible.

**Aucune fonctionnalité nouvelle ne doit affaiblir la fiabilité des
fonctionnalités déjà validées. Chaque évolution doit renforcer la
cohérence globale du projet.**
