---
title: Deploy ML - Energy & CO2 Prediction
emoji: 🏢
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
pinned: false
---

# 🏢 Deploy ML - Prédiction Énergétique et CO2 des Bâtiments

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

API de Machine Learning pour prédire la **consommation énergétique** et les **émissions de CO2** des bâtiments non-résidentiels de Seattle.

## 📋 Table des matières

- [Description](#-description)
- [Architecture](#-architecture)
- [Installation](#-installation)
- [Utilisation](#-utilisation)
- [API Endpoints](#-api-endpoints)
- [Base de données](#-base-de-données)
- [Tests](#-tests)
- [CI/CD](#-cicd)
- [Déploiement](#-déploiement)
- [Structure du projet](#-structure-du-projet)

## 📖 Description

Ce projet déploie deux modèles de Machine Learning entraînés sur le dataset [Seattle Building Energy Benchmarking](https://data.seattle.gov/dataset/2016-Building-Energy-Benchmarking/2bpz-gwpy) :

| Modèle | Target | Algorithme | R² CV |
|--------|--------|------------|-------|
| **Énergie** | `SiteEnergyUse(kBtu)` | RandomForest | 0.73 |
| **CO2** | `TotalGHGEmissions` | LightGBM | 0.92 |

### Fonctionnalités

- ✅ **API REST** avec FastAPI et documentation Swagger
- ✅ **Multi-output** : prédiction simultanée énergie + CO2
- ✅ **Traçabilité** : tous les inputs/outputs stockés en PostgreSQL
- ✅ **Tests** : couverture Pytest + tests fonctionnels
- ✅ **CI/CD** : GitHub Actions + déploiement Hugging Face Spaces

### 📦 Gestion des modèles ML

Les modèles ML (fichiers `.joblib`) sont gérés avec **Git LFS** (Large File Storage) :
- **Taille totale** : ~3.7 MB (energy_model.joblib + co2_model.joblib)
- **Avantage** : Clone rapide du repository (téléchargement optimisé des fichiers binaires)
- **Requis** : Git LFS doit être installé sur votre machine (voir [Installation](#-installation))

## 🏗️ Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Client    │────▶│  FastAPI    │────▶│   Models    │
└─────────────┘     └──────┬──────┘     └─────────────┘
                          │
                          ▼
                   ┌─────────────┐
                   │ PostgreSQL  │
                   └─────────────┘
```

## 🚀 Installation

### Prérequis

- Python 3.12+
- Git
- Git LFS (pour les modèles ML)

### Démarrage rapide (pour quelqu'un qui clone le projet)

```bash
# 0. Installer Git LFS (une seule fois sur votre machine)
# Linux:
sudo apt install git-lfs
# Mac:
brew install git-lfs
# Windows: https://git-lfs.github.com

git lfs install

# 1. Cloner le repository (Git LFS téléchargera automatiquement les modèles)
git clone https://github.com/clementRbl/deploy-ml.git
cd deploy-ml

# 2. Créer et activer l'environnement virtuel
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# ou: .venv\Scripts\activate  # Windows

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Lancer le serveur API
uvicorn src.api.main:app --host 0.0.0.0 --port 7860

# ✅ API accessible sur http://localhost:7860
# 📚 Documentation Swagger : http://localhost:7860/docs
```

### Variables d'environnement (optionnel)

Le fichier `.env` n'est **pas nécessaire** pour tester l'API localement. Les valeurs par défaut fonctionnent directement.

Si vous voulez personnaliser la configuration :

```bash
# Copier l'exemple (optionnel)
cp .env.example .env

# Éditer .env avec vos valeurs
nano .env
```

## 💡 Utilisation

### Exemple de requête

```python
import requests
🚀 Lancer le serveur

```bash
# Activer l'environnement virtuel (si pas déjà fait)
source .venv/bin/activate

# Lancer le serveur de développement
uvicorn src.api.main:app --host 0.0.0.0 --port 7860 --reload

# Serveur prêt !
# 🌐 API : http://localhost:7860
# 📚 Swagger : http://localhost:7860/docs
```

### 🧪 Tester manuellement l'API (sans tests automatiques)

#### 1. Health check

```bash
# Vérifier que l'API fonctionne
curl http://localhost:7860/api/v1/health

# Réponse attendue :
# {
#   "status": "healthy",
#   "version": "0.3.0",
#   "models_loaded": true
# }
```

Documentation interactive complète : **http://localhost:7860/docs**


#### 3. Obtenir les infos des modèles

```bash
curl http://localhost:7860/api/v1/models/info

# Réponse : métadonnées des modèles (algorithmes, R², features...)
```
Documentation interactive : [http://localhost:8000/docs](http://localhost:8000/docs)

## 🗄️ Base de données

### Schéma

```sql
-- Table des prédictions
CREATE TABLE predictions (
    id UUID PRIMARY KEY,
    created_at TIMESTAMP DEFAULT NOW(),
    input_data JSONB NOT NULL,
    energy_prediction FLOAT,
    co2_prediction FLOAT
);
```

### Lancer TOUS les tests

```bash
# Activer l'environnement virtuel
source .venv/bin/activate

# Lancer tous les tests
pytest

# Avec détails verbeux
pytest -v

# Avec couverture de code
pytest --cov=src --cov-report=html

# Ouvrir le rapport de couverture
open htmlcov/index.html  # Mac
# ou: xdg-open htmlcov/index.html  # Linux
```

### Tests disponibles

```bash
# Tests de structure uniquement
pytest tests/test_structure.py -v

# Tests d'un fichier spécifique
pytest tests/test_api.py -v  # (à venir)

# Tests avec sortie complète
pytest -vv --tb=short
```

### Architecture Best Practices 2026

- ✅ **API versionnée** (`/api/v1/`) pour évolutions futures
- ✅ **Dependency Injection** avec FastAPI `Depends()`
- ✅ **Configuration centralisée** avec `pydantic-settings`
- ✅ **Logging structuré** avec niveaux et couleurs
- ✅ **Exceptions typées** pour gestion d'erreurs propre
- ✅ **Séparation des responsabilités** (api/core/services/schemas)**Lint** : Vérifie le code avec ruff
3. **Deploy** : Déploie sur Hugging Face Spaces (branche main)

## 🌐 Déploiement

### 🔄 Workflow complet : Local → GitHub → Production

#### 1️⃣ Développement LOCAL (votre machine)

Quand quelqu'un clone le projet, il peut travailler **localement** de deux façons :

##### Option A : Python directement (recommandé pour le dev)

```bash
# Installation
git clone https://github.com/clementRbl/deploy-ml.git
cd deploy-ml
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Lancement
uvicorn src.api.main:app --host 0.0.0.0 --port 7860 --reload
# ✅ API sur http://localhost:7860
```

**Avantages** : Rechargement automatique (`--reload`), debugging facile, modifications visibles instantanément.

##### Option B : Docker localement (optionnel, pour tester la prod)

```bash
# Build de l'image
docker build -t energy-api .

# Lancement du container
docker run -p 7860:7860 energy-api
# ✅ API sur http://localhost:7860
```

**Avantages** : Environnement identique à la production, isolation complète.

#### 2️⃣ Push sur GITHUB

```bash
git add .
git commit -m "feat: nouvelle fonctionnalité"
git push origin main
```

Dès le push, **GitHub Actions** se déclenche automatiquement (voir `.github/workflows/ci.yml`) :
- ✅ Vérifie le code (linting)
- ✅ Lance les tests (`pytest`)
- ✅ Si tests OK → Continue vers le déploiement

#### 3️⃣ Déploiement PRODUCTION automatique (HuggingFace Spaces)

**C'est là que la "magie" opère** ! Aucune action manuelle nécessaire.

**Configuration initiale (déjà faite)** :
1. HuggingFace Spaces lié au repo GitHub
2. Secrets configurés : `HF_TOKEN`, `HF_USERNAME`, `HF_SPACE_NAME`

**Workflow automatique** :
```
GitHub push → HF détecte le changement
            → HF lit le Dockerfile
            → HF construit l'image Docker
            → HF lance le container
            → API publique en ligne !
```

**Résultat** : API accessible publiquement sur `https://clementrbl-deploy-ml.hf.space`

### 📦 Détails du Dockerfile

Le `Dockerfile` contient les instructions pour construire l'image :

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 7860
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "7860"]
```

**En local** : Vous exécutez `docker build` et `docker run` vous-même.
**En production (HF)** : HuggingFace exécute ces commandes automatiquement à chaque push.

### 🔑 Pour résumer

| Environnement | Méthode | Commande manuelle ? | Rechargement auto ? |
|---------------|---------|---------------------|---------------------|
| **Local Dev** | Python | `uvicorn ... --reload` | ✅ Oui |
| **Local Test** | Docker | `docker run` | ❌ Non (rebuild) |
| **Production** | HF Spaces | ❌ Aucune (automatique) | ✅ Oui (à chaque push) |


## 👤 Auteur

Projet réalisé dans le cadre de la formation Data Scientist - OpenClassrooms.

---
