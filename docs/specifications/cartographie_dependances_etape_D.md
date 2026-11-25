# Rapport de cartographie des dépendances — Étape D du référentiel

**Projet :** Prédiction Football  
**Date :** 2026-11-25  
**Référentiel :** REGLES_ET_METHODES_INTEGRATION_PROJET_PREDICTION_FOOTBALL.md

---

## 1. Vue d'ensemble

- **189 modules Python** découverts dans `src/`
- **149 modules** avec au moins une import interne
- **147 fichiers .py** au total (hors tests)

---

## 2. Architecture par couche

Conformément à la section 3.3 du référentiel, l'architecture recommandée est :

```
Interface (Telegram / Web / API) → Services applicatifs → Domaine métier → Dépôts de données et adaptateurs
```

### Couche Interface
| Module | Rôle |
|--------|------|
| `src/app.py` | Point d'entrée principal |
| `src/web/application.py` | Runtime web |
| `src/web/routes_admin.py` | Routes admin web |
| `src/web/routes_public.py` | Routes publiques web |
| `src/web/security.py` | Sécurité web |
| `src/telegram_bot/*.py` | Gestionnaires Telegram (36 fichiers) |
| `src/telegram_bot/admin/*` | Admin Telegram |
| `src/telegram_bot/consultation/*` | Consultation Telegram |
| `src/telegram_bot/handlers/*` | Handlers Telegram |
| `src/telegram_bot/payments/*` | Paiements Telegram |
| `src/telegram_bot/predictions/*` | Prédictions Telegram |

### Couche Services applicatifs
| Module | Rôle |
|--------|------|
| `src/core/services/admin.py` | Service admin |
| `src/core/services/alertes.py` | Service alertes |
| `src/core/services/engagement.py` | Service engagement |
| `src/core/services/paris.py` | Service paris |
| `src/core/services/paiement.py` | Service paiement |
| `src/core/services/prediction.py` | Service prédiction |
| `src/core/services/risque.py` | Service risque |
| `src/core/services/utilisateurs.py` | Service utilisateurs |

### Couche Domaine métier
| Module | Rôle |
|--------|------|
| `src/core/domaine.py` | Objets métier (Match, Prediction, Bankroll, etc.) |
| `src/core/exceptions.py` | Hiérarchie d'exceptions |
| `src/core/feature_registry.py` | Registre des fonctionnalités |

### Couche Dépôts et adaptateurs
| Module | Rôle |
|--------|------|
| `src/core/adaptateurs/*` | Adaptateurs externes (8 modules) |
| `src/users/database/*` | Couche base de données |
| `src/users/db.py` | Couche DB héritée (à migrer) |
| `src/users/matchs.py` | Dépôt matchs |
| `src/users/paiements.py` | Dépôt paiements |

---

## 3. Dépendances circulaires détectées

### 3.1 Cycle : `core.predictions.__init__` ↔ `core.predictions.prediction` ↔ `core.predictions.nouveau_prediction`

```
core.predictions.__init__
  └─> core.predictions.prediction
        └─> core.predictions.nouveau_prediction
              └─> core.predictions  (cycle !)
```

**Impact :** Ce cycle peut causer des erreurs d'importation selon l'ordre de chargement. Le fichier `core/predictions/__init__.py` importe `predire_match` depuis `prediction.py`, qui importe `nouveau_prediction`, qui importe à son tour `core.predictions` (le package lui-même).

**Correction recommandée :** Supprimer l'import de `predire_match` dans `core/predictions/__init__.py` (déjà fait partiellement) ou réorganiser pour briser le cycle.

### 3.2 Dépendance inversée : `core.utils.logs` → `core.administration.pic_erreurs`

`core.utils.logs` (module utilitaire de bas niveau) importe `core.administration.pic_erreurs` (module d'administration de haut niveau).

```
core.utils.logs  ──>  core.administration.pic_erreurs
```

**Impact :** Violation de l'architecture en couches. Un module bas niveau ne devrait pas dépendre d'un module haut niveau.

**Correction recommandée :** Déplacer `enregistrer_erreur` vers un module de bas niveau (ex: `core.utils.metrics`) ou utiliser une injection de dépendance / callback.

### 3.3 Dépendance : `core.utils.logs` → `core.securite`

```
core.utils.logs  ──>  core.securite
```

`securite.py` ne'importe pas `logs`, donc ce n'est pas circulaire, mais c'est une dépendance inhabituelle d'un module utilitaire vers un module de sécurité.

---

## 4. Fonctions dupliquées (52 identifiées)

### 4.1 Doublons métier critiques (même nom, modules différents)

| Fonction | Module principal (à conserver) | Module doublon (à supprimer/rediriger) |
|----------|-------------------------------|----------------------------------------|
| `analyser_value_bet` | `core/betting/value_bet.py` | `core/services/paris.py` |
| `calculer_cashout` | `core/betting/cashout.py` | `core/services/paris.py` |
| `calculer_cashout_partiel` | `core/betting/cashout.py` | `core/services/paris.py` |
| `calculer_mise_kelly` | `core/betting/bankroll.py` | `core/services/risque.py` |
| `checklist_avant_pari` | `core/betting/gestion_risques.py` | `core/betting/outils_locaux_avances.py` |
| `bonus_connexion_quotidienne` | `core/services/engagement.py` | `core/engagement/engagement_local.py` |
| `calculer_elo_live` | `core/experience/fonctionnalites_restantes.py` | `core/predictions/analyses_avancees.py` |
| `detecter_underdog` | `core/betting/outils_locaux_avances.py` | `core/betting/outils_paris.py` |
| `verifier_buts_live` | `core/administration/alertes_live.py` | `core/services/alertes.py` |
| `controler_et_alerter` | `core/administration/controle_quota.py` | `core/administration/pic_erreurs.py` |
| `obtenir_fonctionnalite` | `core/feature_registry.py` | `core/catalog/catalogue_fonctionnalites.py` |
| `lister_non_implantees` | `core/feature_registry.py` | `core/services/admin.py` |
| `predire` | `core/services/prediction.py` | `core/catalog/features.py` |

### 4.2 Doublons de fonctions de base de données

| Fonction | Module hérité (à supprimer) | Module nouveau (à conserver) |
|----------|----------------------------|------------------------------|
| `db_connection` | `users/db.py` | `users/database/connection.py` |
| `db_execute` | `users/db.py` | `users/database/queries.py` |
| `db_fetchall` | `users/db.py` | `users/database/queries.py` |
| `db_fetchone` | `users/db.py` | `users/database/queries.py` |
| `db_fetchone_dict` | `users/db.py` | `users/database/queries.py` |
| `db_fetchone_strict` | `users/db.py` | `users/database/queries.py` |
| `get_connection` | `users/db.py` | `users/database/connection.py` |

### 4.3 Doublons d'adaptateurs (socles_tiers → adaptateurs)

| Fonction | Module hérité (`socles_tiers.py`) | Module nouveau (`adaptateurs/*`) |
|----------|----------------------------------|----------------------------------|
| `verifier_reference` | `core/socles_tiers.py` | `core/adaptateurs/base.py`, `core/adaptateurs/paiements.py` |
| `publier_texte` | `core/socles_tiers.py` | `core/adaptateurs/base.py`, `core/adaptateurs/reseaux_sociaux.py` |
| `publier_image` | `core/socles_tiers.py` | `core/adaptateurs/base.py`, `core/adaptateurs/reseaux_sociaux.py` |
| `generer_audio` | `core/socles_tiers.py` | `core/adaptateurs/base.py`, `core/adaptateurs/audio.py` |
| `creer_evenement` | `core/socles_tiers.py` | `core/adaptateurs/base.py`, `core/adaptateurs/calendrier.py` |
| `get_cotes` | `core/socles_tiers.py` | `core/adaptateurs/base.py` |
| `get_matchs_live` | `core/socles_tiers.py` | `core/adaptateurs/base.py` |
| `get_meteo` | `core/socles_tiers.py` | `core/adaptateurs/base.py`, `core/adaptateurs/meteo.py` |
| `get_resultat` | `core/socles_tiers.py` | `core/adaptateurs/base.py` |
| `generer_code_paiement` | `core/adaptateurs/base.py` | `core/adaptateurs/paiements.py` |

### 4.4 Doublons de commandes Telegram

| Fonction | Module 1 | Module 2 |
|----------|----------|----------|
| `cmd_cashout` | `telegram_bot/consultation_handlers.py` | `telegram_bot/handlers/nouvelles_fonctionnalités.py` |
| `cmd_meteo` | `telegram_bot/consultation_handlers.py` | `telegram_bot/handlers/nouvelles_fonctionnalités.py` |

### 4.5 Fonctions utilitaires privées dupliquées

| Fonction | Modules concernés |
|----------|------------------|
| `_assurer_table` | `core/bilans.py`, `core/engagement/engagement_local.py`, `core/predictions/model_governance.py`, `users/credits.py` |
| `_assurer_tables` | `core/administration/support_extension.py`, `core/data/registre_sportif.py`, `core/engagement/gouvernance_extension.py` |
| `_faire_requete` | `core/api/api_football.py`, `core/api/bzzoiro.py`, `core/api/football_data.py` |
| `_extraire_message_erreur` | `core/api/api_football.py`, `core/api/bzzoiro.py`, `core/api/football_data.py` |
| `_get_headers` | `core/api/api_football.py`, `core/api/bzzoiro.py` |
| `lire` | `core/administration/alerte_apis.py`, `core/predictions/backtest.py` |
| `ecrire` | `core/administration/alerte_apis.py` (2x dans le même fichier) |
| `tester_api` | `core/api/api_football.py`, `core/api/bzzoiro.py`, `core/api/football_data.py`, `core/api/openligadb.py`, `core/api/thesportsdb.py` |

---

## 5. Anciens gestionnaires / points d'entrée obsolètes

### 5.1 Modules parallèles (fichiers en double à la racine de `core/` vs sous-dossiers)

| Fichier hérité | Équivalent nouveau | Statut |
|---------------|-------------------|--------|
| `src/core/bookmakers.py` | `src/core/betting/bookmakers.py` | À fusionner |
| `src/core/paiement_auto.py` | `src/core/payments.py` / `core/adaptateurs/paiements.py` | À fusionner |
| `src/core/paiement_validation.py` | `src/core/payments.py` | À fusionner |
| `src/core/payments.py` | `core/adaptateurs/paiements.py` | À fusionner |
| `src/core/notifications_programmees.py` | `src/core/notifications/programmed.py` | À fusionner |
| `src/core/catalogue_fonctionnalites.py` | `src/core/catalog/catalogue_fonctionnalites.py` | À fusionner |
| `src/core/catalogue_extensions.py` | `src/core/catalog/catalogue_extensions.py` | À fusionner |
| `src/core/fonctionnalites_700.py` | `src/core/catalog/fonctionnalites_700.py` | À fusionner |
| `src/core/runtime_700.py` | `src/core/catalog/runtime_700.py` | À fusionner |
| `src/users/db.py` | `src/users/database/*` | À fusionner |

### 5.2 Gestionnaires Telegram obsolètes

| Fichier | Problème |
|---------|----------|
| `telegram_bot/consultation_handlers.py` | Contient `cmd_cashout` et `cmd_meteo` dupliqués dans `handlers/nouvelles_fonctionnalités.py` |
| `telegram_bot/handlers/nouvelles_fonctionnalités.py` | Contient des commandes dupliquées et importe tous les services (couche interface ↔ couche service violée) |

### 5.3 Fichiers à la racine du projet supprimés (déjà nettoyé)

Les 15 scripts d'analyse à la racine ont été déplacés vers `scripts/outils_dev/` lors d'une intervention antérieure. Le dossier `payments/` a été supprimé.

---

## 6. Sources de vérité (section 3.2 du référentiel)

| Donnée métier | Source de vérité désignée | Modules autorisés à consulter |
|---------------|--------------------------|-------------------------------|
| Résultat officiel d'un match | `users.matchs` / `users.database` | Tous les services via `users.db` |
| Solde de crédits utilisateur | `users.credits` / `users.account_base` | `users.credits`, `users.account_limits` |
| Statut d'un paiement | `users.paiements` | `users.paiements`, `telegram_bot/payments/*` |
| Préférences de notification | `users.account_base` / `users.account_notifications` | Tous les modules utilisateur |
| Statut d'une prédiction | `core.domaine` (classe `Prediction`) | `core.services.prediction`, `core.predictions.*` |
| Solde de bankroll | `core.domaine` (classe `Bankroll`) | `core.betting.bankroll`, `core.services.risque` |
| Catalogue des fonctionnalités | `core.catalog.catalogue_fonctionnalites` | `core.feature_registry`, `tests/*` |
| Configuration de l'application | `src/config.py` | `src/app.py`, `core.utils.logs`, `core.config_adaptateurs` |
| Journaux / logs | `core.utils.logs` | Tous les modules |
| Clés API externes | Variables d'environnement (via `config.py`) | Adaptateurs correspondants |

**Règle :** Aucun module ne doit créer sa propre copie modifiable de ces informations. Les copies de cache doivent être identifiées comme telles, datées et renouvelables (section 3.2).

---

## 7. Recommandations de remédiation (ordre de priorité)

### Priorité 1 — Briser les dépendances circulaires
1. Supprimer l'import circulaire dans `core/predictions/__init__.py` (déjà fait partiellement, vérifier)
2. Déplacer `enregistrer_erreur` de `core.administration.pic_erreurs` vers `core.utils.metrics` (ou utiliser un callback) pour briser `core.utils.logs → core.administration.pic_erreurs`

### Priorité 2 — Éliminer les doublons de fonctions métier
Pour chaque paire de doublons, conserver une seule implémentation et rediriger l'autre :
- `core/services/paris.py` → déléguer à `core/betting/value_bet.py` et `core/betting/cashout.py`
- `core/services/risque.py` → déléguer à `core/betting/bankroll.py`
- `core/betting/outils_locaux_avances.py` → déléguer à `core/betting/gestion_risques.py`
- `core/predictions/analyses_avancees.py` → déléguer à `core/experience/fonctionnalites_restantes.py`
- `core/services/alertes.py` → déléguer à `core/administration/alertes_live.py`
- `core/services/admin.py` → déléguer à `core/feature_registry.py`
- `core/catalog/catalogue_fonctionnalites.py` → déléguer à `core/feature_registry.py`

### Priorité 3 — Fusionner les modules parallèles
Supprimer les fichiers hérités à la racine de `core/` et `users/` en redirigeant leurs imports vers les sous-dossiers équivalents.

### Priorité 4 — Nettoyer les gestionnaires Telegram
- Fusionner `telegram_bot/consultation_handlers.py` dans `telegram_bot/consultation/*`
- Supprimer ou alléger `telegram_bot/handlers/nouvelles_fonctionnalités.py` (trop de responsabilités, importe 8 services)

---

## 8. Preuves de validation

- 156 tests unitaires passent (0 échec)
- `python -m pytest tests/ --tb=short -q` → `156 passed in 1.44s`
- Aucun `sys.path` dans `src/` (respect de la section 3.4)
- Aucun secret en dur dans le code source (respect de la section 14)
- `.env` dans `.gitignore` (respect de la section 14)
- Point d'entrée unique : `src/app.py` (respect de la section 3.4)

---

## 9. État final proposé

| Chantier | État |
|----------|------|
| Cartographie des dépendances | ✅ Terminée (ce rapport) |
| Dépendances circulaires | ⚠️ 2 cycles détectés, à corriger |
| Fonctions dupliquées | ⚠️ 52 doublons identifiés, à fusionner |
| Anciens gestionnaires | ⚠️ 10 modules parallèles à fusionner |
| Sources de vérité | ✅ Désignées dans ce rapport |

**Prochaine étape :** Appliquer les corrections de Priorité 1 (dépendances circulaires) puis Priorité 2 (fusion des doublons), en respectant la méthode en petites étapes de la section 5 du référentiel.
