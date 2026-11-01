
# QualiCampus

### Plateforme web de gestion du Système de Management de la Qualité (SMQ)

QualiCampus est une application web développée avec **Django**, dédiée à la digitalisation et à la gestion du Système de Management de la Qualité au sein d'un établissement universitaire.

Elle permet de centraliser les activités qualité, d'améliorer la traçabilité des opérations et de faciliter la collaboration entre les différents acteurs.

## Objectifs du projet

- Centraliser les informations du système qualité.
- Simplifier la gestion des processus universitaires.
- Améliorer la gestion documentaire et le suivi des versions.
- Faciliter la planification et le suivi des audits.
- Assurer le traitement des non-conformités.
- Suivre les actions correctives et leur efficacité.
- Renforcer la traçabilité et l'amélioration continue.

## Fonctionnalités principales

### 1. Authentification et gestion des utilisateurs

- Connexion sécurisée.
- Création et gestion des comptes utilisateurs.
- Attribution des rôles.
- Gestion des droits d'accès.

### 2. Gestion des unités organisationnelles

- Création et modification des unités.
- Organisation hiérarchique des structures.
- Visualisation de l'organigramme.
- Recherche et filtrage.

### 3. Gestion des processus

- Création et modification des processus.
- Affectation des pilotes.
- Suivi des processus.
- Recherche et filtrage par statut et unité.

### 4. Gestion documentaire

- Création des documents qualité.
- Gestion des versions.
- Soumission à validation.
- Validation et publication.
- Archivage des anciennes versions.

### 5. Gestion des audits

- Planification des audits.
- Affectation des auditeurs.
- Suivi de l'avancement.
- Gestion des différents statuts.

### 6. Gestion des non-conformités

- Déclaration des non-conformités.
- Classification par gravité.
- Prise en charge.
- Résolution et clôture.

### 7. Gestion des actions correctives

- Création et attribution des actions.
- Suivi de leur réalisation.
- Vérification de leur efficacité.
- Création de nouvelles actions si nécessaire.

### 8. Tableau de bord

- Indicateurs des activités qualité.
- Statistiques des documents.
- Suivi des audits.
- Suivi des non-conformités.
- Visualisation des actions correctives.

### 9. Notifications et recherche

- Notifications adaptées aux utilisateurs.
- Suivi des activités en attente.
- Recherche globale.
- Filtrage selon les autorisations.

### 10. Historique et paramètres

- Traçabilité des opérations.
- Consultation de l'historique.
- Informations du compte utilisateur.
- Modification du mot de passe.

## Rôles utilisateurs

La plateforme repose sur six rôles :

| Rôle | Responsabilités |
|------|-----------------|
| Administrateur | Gestion des utilisateurs, des unités et de l'historique |
| Responsable qualité | Supervision des activités qualité et gestion des modules du SMQ |
| Responsable de direction | Consultation des indicateurs et des informations autorisées |
| Pilote de processus | Suivi des processus et réalisation des actions attribuées |
| Auditeur | Réalisation des audits et déclaration des non-conformités |
| Contributeur | Création et soumission des documents qualité |

Les droits d'accès sont adaptés aux responsabilités de chaque utilisateur.

## Technologies utilisées

| Composant | Technologie |
|-----------|-------------|
| Back-end | Python, Django |
| Front-end | HTML, CSS, JavaScript |
| Base de données | PostgreSQL |
| Accès aux données | Django ORM |
| Architecture | MVT (Model-View-Template) |

## Architecture du projet

QualiCampus utilise l'architecture **MVT de Django**.

- **Model** : gestion et organisation des données.
- **View** : traitement des requêtes et logique métier.
- **Template** : affichage des interfaces HTML.

Cette architecture permet de séparer les responsabilités et de faciliter la maintenance de l'application.

## Installation locale

### 1. Cloner le projet

```bash
git clone https://github.com/Nourbenmiled/QualiCampus.git
cd QualiCampus
```

### 2. Créer un environnement virtuel

```bash
python -m venv venv
```

### 3. Activer l'environnement virtuel

Sur Windows :

```powershell
.\venv\Scripts\Activate.ps1
```

### 4. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 5. Configurer PostgreSQL

Créer une base de données PostgreSQL et configurer les paramètres de connexion utilisés par Django.

Ne pas publier les mots de passe ni les clés secrètes.

### 6. Appliquer les migrations

```bash
python manage.py migrate
```

### 7. Créer un superutilisateur

```bash
python manage.py createsuperuser
```

### 8. Démarrer le serveur

```bash
python manage.py runserver
```


## Sécurité

QualiCampus intègre une gestion des autorisations basée sur les rôles.

Les fichiers sensibles, les environnements virtuels et les bases de données locales ne doivent pas être publiés dans le dépôt GitHub.

## Perspectives d'amélioration

- Développement de tableaux de bord analytiques avancés.
- Automatisation des notifications et des rappels.
- Intégration de fonctionnalités d'intelligence artificielle.
- Amélioration continue de l'ergonomie et des performances.

## Auteur

**Nour Ben Miled**


