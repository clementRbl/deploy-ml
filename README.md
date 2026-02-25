---
title: Deploy ML - Energy & CO2 Prediction
emoji: "🏢"
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
pinned: false
---

# Deploy ML - Prediction Energetique et CO2 des Batiments

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

API de Machine Learning pour predire la **consommation energetique** et les **emissions de CO2** des batiments non-residentiels de Seattle.

## Table des matieres

- [Description](#description)
- [Architecture](#architecture)
- [Installation](#installation)
- [Base de donnees](#base-de-donnees)
- [Utilisation](#utilisation)
- [API Endpoints](#api-endpoints)
- [Tests](#tests)
- [CI/CD](#cicd)
- [Deploiement](#deploiement)
- [Authentification](#authentification)
- [Sécurisation](#sécurisation)
- [Documentation technique](#documentation-technique)
- [Structure du projet](#structure-du-projet)

## Description

Ce projet deploie deux modeles de Machine Learning entraines sur le dataset [Seattle Building Energy Benchmarking](https://data.seattle.gov/dataset/2016-Building-Energy-Benchmarking/2bpz-gwpy) :

| Modele | Target | Algorithme | R2 CV |
|--------|--------|------------|-------|
| **Energie** | `SiteEnergyUse(kBtu)` | RandomForest | 0.73 |
| **CO2** | `TotalGHGEmissions` | LightGBM | 0.92 |

### Fonctionnalites

- **API REST** avec FastAPI et documentation Swagger
- **Multi-output** : prediction simultanee energie + CO2
- **Base de donnees PostgreSQL** : dataset + tracabilite des predictions
- **Tests** : couverture Pytest (69 tests, API + service + ORM + structure)
- **CI/CD** : GitHub Actions + deploiement Hugging Face Spaces
- **Clean Architecture** : separation api/core/services/schemas/db

### Gestion des modeles ML

Les modeles ML (fichiers `.joblib`) ne sont **pas versionnes dans Git** (`.gitignore`).
- **Localement** : les fichiers sont presents dans `src/models/` pour le developpement
- **En production** : telecharges automatiquement depuis HuggingFace lors du build Docker via `hf_hub_download`
- **Taille totale** : ~3.7 MB (energy_model.joblib + co2_model.joblib)

## Architecture

```
                                    +------------------+
                                    |   PostgreSQL     |
                                    |   (buildings,    |
                                    |    predictions)  |
                                    +--------+---------+
                                             |
+-------------+     +--------------+     +---+--------+
|   Client    +---->|   FastAPI    +---->|  Services  |
+-------------+     +--------------+     +---+--------+
                                             |
                                    +--------+---------+
                                    |   Models ML      |
                                    |   (.joblib)      |
                                    +------------------+
```

## Installation

### Prerequis

- Python 3.12+
- Docker (pour PostgreSQL)
- Git

### Demarrage rapide

```bash
# 1. Cloner le repository
git clone https://github.com/clementRbl/deploy-ml.git
cd deploy-ml

# 2. Creer et activer l'environnement virtuel
python -m venv .venv
source .venv/bin/activate  # Linux/Mac

# 3. Installer les dependances
pip install -r requirements.txt

# 4. Lancer PostgreSQL
docker compose up -d

# 5. Creer les tables et inserer le dataset
python scripts/create_db.py --reset --seed

# 6. Lancer le serveur API
uvicorn src.api.main:app --host 0.0.0.0 --port 7860

# API accessible sur http://localhost:7860
# Documentation Swagger : http://localhost:7860/docs
```

> **Note** : Les modeles `.joblib` doivent etre presents dans `src/models/` pour que l'API fonctionne localement.

### Variables d'environnement (optionnel)

Le fichier `.env` n'est **pas necessaire** pour tester l'API localement. Les valeurs par defaut fonctionnent directement.

```bash
cp .env.example .env
```

## Base de donnees

### PostgreSQL local

La base PostgreSQL est geree via Docker Compose :

```bash
# Demarrer PostgreSQL
docker compose up -d

# Creer les tables et inserer le dataset (3376 batiments)
python scripts/create_db.py --reset --seed

# Verifier les donnees
python scripts/create_db.py --verify
```

### Schema

Deux tables principales (voir [docs/database_uml.md](docs/database_uml.md) pour le schema UML complet) :

| Table | Description | Lignes |
|-------|-------------|--------|
| `buildings` | Dataset Seattle 2016 Energy Benchmarking | 3 376 |
| `predictions` | Historique des predictions ML (inputs + outputs) | variable |

### Scripts de requetes

```bash
# Statistiques globales
python scripts/query_db.py --stats

# Lister les batiments
python scripts/query_db.py --buildings --limit 10

# Top 10 batiments les plus energivores
python scripts/query_db.py --top-energy 10

# Prediction depuis un batiment en base (input -> modele -> output -> DB)
python scripts/query_db.py --predict --building-id 1

# Historique des predictions
python scripts/query_db.py --predictions
```

### Tracabilite

Chaque appel a `/api/v1/predict` enregistre automatiquement en base :
- Les inputs envoyes au modele
- Les outputs generes (energie + CO2)
- La duree de prediction
- Le timestamp

## Utilisation

### Exemple rapide

```bash
curl -X POST http://localhost:7860/api/v1/predict \
  -H "Content-Type: application/json" \
  -d '{
    "NumberofBuildings": 1,
    "PropertyGFATotal": 50000,
    "PropertyGFABuilding(s)": 45000,
    "LargestPropertyUseTypeGFA": 45000,
    "PrimaryPropertyType": "Office",
    "LargestPropertyUseType": "Office"
  }'
# {"energy_prediction_kbtu": 2947914.5, "co2_prediction_tons": 51.6, "prediction_id": "abc123"}
```

### Documentation interactive (Swagger)

Tous les endpoints, schemas et exemples sont disponibles dans la documentation auto-generee :

**http://localhost:7860/docs**

## Tests

```bash
# Lancer tous les tests
pytest -v

# Avec couverture de code
pytest --cov=src --cov-report=html

# Ouvrir le rapport
xdg-open htmlcov/index.html  # Linux
```

### Tests disponibles (69)

| Categorie | Nombre | Description |
|-----------|--------|-------------|
| Structure | 4 | Projet, modeles, metadata, requirements |
| API Endpoints | 29 | Health, predict (valide/erreurs), models/info, db/buildings, db/predictions, 404 |
| Predictions (service) | 25 | Chargement predictor, predict, feature engineering, schemas, exceptions |
| Building ORM | 4 | CRUD, unicite, repr, bulk insert |
| Prediction ORM | 4 | CRUD, relation building, sans building, multiples |
| Schema DB | 3 | Tables creees, colonnes buildings, colonnes predictions |

Pour lister tous les tests : `pytest --collect-only -q`.

### Best Practices

- **API versionnee** (`/api/v1/`) pour evolutions futures
- **Dependency Injection** avec FastAPI `Depends()`
- **Configuration centralisee** avec `pydantic-settings`
- **Logging structure** avec niveaux et couleurs
- **Exceptions typees** pour gestion d'erreurs propre
- **Separation des responsabilites** (api/core/services/schemas/db)

## CI/CD

Le pipeline GitHub Actions (`.github/workflows/ci-cd.yml`) execute :

1. **Tests** : `pytest` avec couverture
2. **Lint** : Verification du code avec `ruff`
3. **Validation** : Verification des metadonnees des modeles
4. **Deploy** : Upload vers Hugging Face Spaces (branche `main` uniquement)

### Déclenchement du pipeline

- **Push sur `main`** : lance les tests puis le déploiement Hugging Face.
- **Pull request vers `main`** : lance les tests uniquement. Les tests doivent passer avant de merger (configurer la protection de branche : *Settings → Branches → Add rule* sur `main` → cocher *Require status checks to pass before merging* et sélectionner le job *Tests & Lint*).
- **Push sur une branche `feature/*`** : ne déclenche pas la CI (évite les runs inutiles).

### Environnements (dev / test / prod)

- **Dev** : developpement local (ou branches `feature/*`) — `ENVIRONMENT=development`, base PostgreSQL locale.
- **Test** : pipeline CI sur PR vers `main` — job avec `ENVIRONMENT: test`, pas de deploiement.
- **Prod** : deploiement automatique sur Hugging Face Spaces après push sur `main` — utilise les secrets GitHub (`HF_TOKEN`, etc.). Voir [docs/secrets.md](docs/secrets.md) pour le detail.

## Deploiement

### Workflow : Local -> GitHub -> Production

#### 1. Developpement local

```bash
# Python (recommande pour le dev)
uvicorn src.api.main:app --host 0.0.0.0 --port 7860 --reload

# Docker (pour tester la prod)
docker build -t energy-api .
docker run -p 7860:7860 energy-api
```

#### 2. Push sur GitHub

```bash
git add .
git commit -m "feat: nouvelle fonctionnalite"
git push origin main
```

#### 3. Deploiement automatique

```
GitHub push -> GitHub Actions (tests + lint + validation)
           -> upload_folder vers HuggingFace Spaces
           -> HF construit l'image Docker
           -> HF lance le container
           -> API publique en ligne
```

**Resultat** : API accessible sur `https://clementrbl-deploy-ml.hf.space`

### Resume

| Environnement | Methode | Commande manuelle ? | Rechargement auto ? |
|---------------|---------|---------------------|---------------------|
| **Local Dev** | Python | `uvicorn ... --reload` | Oui |
| **Local Test** | Docker | `docker run` | Non (rebuild) |
| **Production** | HF Spaces | Aucune (automatique) | Oui (a chaque push) |

## Authentification

Cette API est livrée en **Proof of Concept (POC)** : elle ne met pas en œuvre d’authentification par défaut. Tous les endpoints sont accessibles sans token ni identifiant.

- **En local / démo** : aucun paramètre d’auth n’est requis.
- **En production** : pour sécuriser l’accès, vous pouvez ajouter par exemple :
  - une **API key** dans un header (ex. `X-API-Key`) vérifiée par un middleware ou une dépendance FastAPI ;
  - ou une authentification **JWT** (OAuth2) avec les dépendances déjà présentes dans `requirements.txt` (`python-jose`, `passlib`).

## Sécurisation

### Gestion des secrets

- **En local** : ne jamais commiter le fichier `.env`. Utiliser `.env.example` comme modèle et copier vers `.env` pour y renseigner les valeurs réelles. Le fichier `.env` est listé dans `.gitignore`.
- **En CI/CD** : les secrets (token Hugging Face, identifiants du Space) sont injectés via les **GitHub Secrets** (`HF_TOKEN`, `HF_USERNAME`, `HF_SPACE_NAME`). Ils ne figurent pas dans le code ni dans le workflow en clair.
- **Base de données** : l’URL de connexion PostgreSQL (`DATABASE_URL`) doit rester dans `.env` en local ; en production HF, la base n’est pas exposée (API seule).

Pour le détail des variables et bonnes pratiques, voir [docs/secrets.md](docs/secrets.md).

### Bonnes pratiques

- Ne pas exposer de clés, tokens ou mots de passe dans le dépôt.
- Utiliser des variables d’environnement pour toute configuration sensible.
- En production, restreindre CORS et limiter les origines autorisées si besoin (voir `src/core/config.py`).

## Documentation technique

- **Performances du modèle et maintenance** : métriques (R²), périmètre des données, limites connues, mise à jour des modèles (.joblib), compatibilité des features et versioning — voir [docs/model_performance.md](docs/model_performance.md).
- **Schéma de la base de données** : [docs/database_uml.md](docs/database_uml.md).
- **Architecture de l’API** : [ARCHITECTURE_GUIDE.md](ARCHITECTURE_GUIDE.md).

## Structure du projet

```
deploy-ml/
+-- .github/workflows/     # CI/CD GitHub Actions
+-- data/                  # Dataset Seattle
+-- docs/                  # Documentation (UML, secrets, performances/modèle)
+-- scripts/               # Scripts DB + notebook
+-- sql/                   # Schema SQL
+-- src/
|   +-- api/               # FastAPI (main, routes, endpoints)
|   |   +-- v1/endpoints/  # health, predictions, models, database
|   +-- core/              # Config, logging, exceptions
|   +-- db/                # SQLAlchemy (models, database, session)
|   +-- models/            # Modeles ML (.joblib, metadonnees)
|   +-- schemas/           # Pydantic (requests, responses)
|   +-- services/          # Logique metier (predictor)
+-- tests/                 # Tests pytest
+-- docker-compose.yml     # PostgreSQL local
+-- Dockerfile             # Image Docker production
+-- requirements.txt       # Dependances Python
+-- README.md
```

## Auteur

Projet realise dans le cadre de la formation Data Scientist - OpenClassrooms.
