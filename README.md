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
- **Tests** : couverture Pytest (15 tests, ORM + structure)
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

### Tests disponibles (15)

| Categorie | Tests | Description |
|-----------|-------|-------------|
| Structure | 4 | Projet, modeles, metadata, requirements |
| Building ORM | 4 | CRUD, unicite, repr, bulk insert |
| Prediction ORM | 4 | CRUD, relation building, sans building, multiples |
| Schema DB | 3 | Tables creees, colonnes buildings, colonnes predictions |

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

## Structure du projet

```
deploy-ml/
+-- .github/workflows/     # CI/CD GitHub Actions
+-- data/                  # Dataset Seattle
+-- docs/                  # Documentation (secrets, UML)
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
