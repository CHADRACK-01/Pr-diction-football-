# Base pour les fonctionnalités nécessitant une intervention humaine

Ce document indique les intégrations qui ne peuvent pas être finalisées sans comptes, secrets, contrats fournisseur ou configuration opérationnelle.

## Paiements Mobile Money

Fonctionnalités concernées : 31, 98.

Base disponible : `core/paiement_auto.py` et `core/socles_tiers.py`.

À fournir ensuite :

- Identifiants officiels Airtel Money, M-Pesa et Orange Money
- URLs et certificats des API
- Format des références de transaction
- Webhooks ou mécanisme de vérification
- Règles de rapprochement, remboursement et idempotence

## WhatsApp, Facebook, TikTok et Instagram

Fonctionnalités : 75, 76, 77, 78, 40.

Base disponible : `FournisseurContenu` dans `core/socles_tiers.py`.

À fournir ensuite :

- Jetons Meta, comptes professionnels et identifiants de pages
- Autorisations de publication
- Contrôle des versions API
- Génération locale des images et légendes

## Audio, voix et vocal

Fonctionnalités : 37, 51, 83.

Base disponible : `FournisseurAudio` dans `core/socles_tiers.py`.

À fournir ensuite :

- Fournisseur de synthèse vocale
- Langues Lingala, français et Swahili
- Limites de débit et coût par caractère
- Gestion des fichiers audio Telegram

## Calendrier Google

Fonctionnalité : 86.

Base disponible : `FournisseurCalendrier` dans `core/socles_tiers.py`.

À fournir ensuite :

- OAuth Google
- Identifiants de client et redirection autorisée
- Gestion du consentement utilisateur
- Fuseau `Africa/Kinshasa`

## Email

Fonctionnalités : 80.

À fournir ensuite :

- Fournisseur SMTP ou API transactionnelle
- Adresse expéditrice vérifiée
- Modèles HTML
- Désinscription et limites d'envoi

## PDF, rapport et ticket

Fonctionnalités : 11, 79.

À fournir ensuite :

- Bibliothèque de rendu choisie
- Logo officiel et charte graphique
- Sources des chiffres comptables
- Numérotation des rapports

## Sauvegarde et restauration

Fonctionnalités : 130, 131.

Base disponible : `core/sauvegarde_backup.py`.

À fournir ensuite :

- Destination chiffrée
- Gestion des clés de chiffrement
- Rotation des sauvegardes
- Test de restauration isolé
- Autorisation stricte de l'administrateur

## Règles métier restant à valider

- Quelles compos officielles doivent déclencher une alerte
- Source autorisée pour les blessés et arbitres
- Liste exacte des championnats africains
- Prix des produits XP
- Règles de Ligue privée entre amis
- Valeurs limites pour un match suspect
- Durées de mute, bannissement et expiration

## Ordre recommandé

1. Configurer les adaptateurs externes.
2. Ajouter les secrets uniquement dans l'environnement Render/VS Code.
3. Écrire les tests d'intégration sans appeler les services réels.
4. Activer progressivement les feature flags.
5. Surveiller quotas, erreurs et journaux admin.
