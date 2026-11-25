# Architecture du projet

## Responsabilités

- `app.py` : démarrage, webhook Telegram, routes HTTP et orchestration du scheduler.
- `config.py` : configuration centrale et validation du démarrage.
- `core/` : règles métier, prédiction, risque, API externes, logs et administration.
- `users/` : persistance et opérations utilisateur/paiement.
- `telegram_bot/` : traduction des commandes Telegram vers les services métier.
- `telegram_bot/admin/` : interface d'administration découpée par menus, actions et sélections.
- `scripts/` : automatisations exécutables hors boucle Telegram.
- `entrainement/` : entraînement et sérialisation des modèles.
- `tests/` : tests unitaires, intégration locale et contrats catalogue.
- `docs/` : documentation fonctionnelle et technique.

## Règles de dépendances

1. Les handlers Telegram ne contiennent pas de SQL métier. Ils appellent `core/` ou `users/`.
2. `core/` ne connaît pas les détails du bot Telegram autant que possible.
3. `users/` ne décide pas des règles Premium. Le service métier utilise `users/` comme persistance.
4. Toute dépendance externe passe par un adaptateur injecté ou configurable.
5. Une dépendance absente retourne un état `en_attente_configuration`, jamais une réussite simulée.
6. Les erreurs réseau, SQL et Telegram sont capturées explicitement et loggées.
7. Aucun secret n'est stocké dans le dépôt ou envoyé dans les logs.

## Ajout d'une fonctionnalité

1. Ajouter son identifiant dans `core/catalogue_fonctionnalites.py` ou le parseur d'extensions.
2. Créer un service dans `core/` avec des entrées validées.
3. Ajouter une couche Telegram limitée au formatage et aux callbacks.
4. Ajouter une persistance dans `users/` ou une table dédiée si nécessaire.
5. Ajouter des tests unitaires et un test d'intégration du handler critique.
6. Passer le catalogue de `a_implanter` à `partielle`, puis `complete` uniquement après validation.

## Statuts du catalogue

- `complete` : contrat implémenté, testé et relié à une entrée utilisateur.
- `partielle` : implémentation locale disponible mais fournisseur, flux ou interface incomplet.
- `a_implanter` : contrat absent ou réservé dans le runtime.

## Backend

Les modules utilisent Turso/libSQL via `users/db.py`. Toute requête doit utiliser des paramètres `?`, jamais une interpolation SQL directe.

## Couche base de données

- `users/database/connection.py` : création et fermeture centralisée des connexions.
- `users/database/queries.py` : helpers SQL standardisés et erreurs strictes.
- `users/database/maintenance.py` : taille, inventaire des tables et nettoyages planifiés.
- `users/database/exceptions.py` : exceptions remontées explicitement.
- `users/db.py` : schéma, migrations et adaptateur historique temporaire.

Les nouveaux usages doivent importer les fonctions depuis `users.database`. Les anciennes importations depuis `users.db` restent disponibles pendant la migration.

## Qualité

- Ruff pour le lint.
- pytest pour les tests.
- pytest-cov pour la couverture.
- CI Python pour compiler, lintér et tester chaque push.

## Nouveaux Modules

- `core/scheduling/` : boucle planifiée et tâches périodiques.
- `core/notifications/` : préparation et envoi des notifications.
- `core/payments/` : fournisseurs externes et règles de paiement.
- `telegram_bot/payments/` : validation et handlers Telegram de paiement.

Les anciens noms en racine sont conservés temporairement comme adaptateurs de compatibilité. Tout nouveau code doit importer directement les nouveaux sous-dossiers.

## Nouvelle organisation du dossier core

- `core/predictions/` : modèle, Poisson, Monte Carlo, validation et gouvernance.
- `core/data/` : matchs, résultats, équipes, météo et statistiques sportives.
- `core/betting/` : cotes, bookmakers, value bet, bankroll, cash-out et risques.
- `core/engagement/` : XP, favoris, codes, concours et jeu responsable.
- `core/administration/` : alertes, quotas, broadcast, sauvegarde, support et audit.
- `core/catalog/` : fonctionnalités 1 à 700 et moteurs associés.
- `core/scheduling/` : boucle planifiée et tâches périodiques.

## Découpage Telegram des consultations

Les fonctionnalités Telegram sont progressivement déplacées hors des gros modules historiques.

- `telegram_bot/consultation/` : handlers Telegram séparés par domaine.
- `telegram_bot/consultation/devises.py` : gestion de la devise utilisateur et de ses callbacks.
- `telegram_bot/consultation/codes_promo.py` : création et utilisation des codes promotionnels.
- `telegram_bot/consultation/preuves.py` : historique vérifiable des résultats.
- `telegram_bot/consultation_handlers.py` : adaptateur historique temporaire pour préserver les anciens imports.

Les nouveaux imports doivent cibler directement `telegram_bot/consultation/<domaine>.py`. Le fichier historique ne doit recevoir aucune nouvelle implémentation métier.

## Couche HTTP

- `web/routes_public.py` : webhook Telegram, accueil et santé de la base.
- `web/routes_admin.py` : diagnostics, maintenance et actions administratives protégées.
- `web/security.py` : validation du secret et décorateur administrateur.
- `app.py` : bootstrap applicatif, bot Telegram, middleware, notifications et démarrage du scheduler.

Les nouvelles routes doivent être enregistrées dans un module `web/routes_*.py`, puis raccordées depuis `app.py`.
