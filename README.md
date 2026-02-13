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

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

API de Machine Learning pour prédire la **consommation énergétique** et les **émissions de CO2** des bâtiments non-résidentiels de Seattle.

## 📋 Table des matières

- [Description](#-description)
- [Architecture](#-architecture)
- [Installation](#-installation)
- [Utilisation](#-utilisation)
- [API Endpoints](#-api-endpoints)
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
- ✅ **Tests** : couverture Pytest + tests de structure
- ✅ **CI/CD** : GitHub Actions + déploiement Hugging Face Spaces
- ✅ **Clean Architecture** : séparation api/core/services/schemas

### 📦 Gestion des modèles ML

Les modèles ML (fichiers `.joblib`) ne sont **pas versionnés dans Git** (`.gitignore`).
- **Localement** : les fichiers sont présents dans `src/models/` pour le développement
- **En production** : téléchargés automatiquement depuis HuggingFace lors du build Docker via `hf_hub_download`
- **Taille totale** : ~3.7 MB (energy_model.joblib + co2_model.joblib)

## 🏗️ Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Client    │────▶│  FastAPI    │────▶│   Models    │
└─────────────┘     └─────────────┘     └─────────────┘
```

## 🚀 Installation

### Prérequis

- Python 3.12+
- Git

### Démarrage rapide

```bash
# 1. Cloner le repository
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

> **Note** : Les modèles `.joblib` doivent être présents dans `src/models/` pour que l'API fonctionne localement.

### Variables d'environnement (optionnel)

Le fichier `.env` n'est **pas nécessaire** pour tester l'API localement. Les valeurs par défaut fonctionnent directement.

```bash
# Copier l'exemple (optionnel)
cp .env.example .env
```

## 💡 Utilisation

### Exemple de requête

```python
import requests

response = requests.post(
    "http://localhost:7860/api/v1/predict",
    json={
        "Hauteur_m": 10,
        "Surface_Plancher_m2": 500,
        "Annee_Construction": 2015,
        "Type_Energie": "Gaz",
        "Type_Ventilation": "Simple flux",
        "Materiaux_Murs": "Béton",
        "Type_Vitrage": "Double"
    }
)
print(response.json())
```

### 🧪 Tester manuellement l'API

#### 1. Health check

```bash
curl http://localhost:7860/api/v1/health

# Réponse attendue :
# {"status": "healthy", "version": "0.3.0", "models_loaded": true}
```

#### 2. Prédiction

```bash
curl -X POST http://localhost:7860/api/v1/predict \
  -H "Content-Type: application/json" \
  -d '{"Hauteur_m": 10, "Surface_Plancher_m2": 500, "Annee_Construction": 2015, "Type_Energie": "Gaz", "Type_Ventilation": "Simple flux", "Materiaux_Murs": "Béton", "Type_Vitrage": "Double"}'
```

#### 3. Infos des modèles

```bash
curl http://localhost:7860/api/v1/models/info
```

Documentation interactive : [http://localhost:7860/docs](http://localhost:7860/docs)

## 🧪 Tests

```bash
# Lancer tous les tests
pytest -v

# Avec couverture de code
pytest --cov=src --cov-report=html

# Ouvrir le rapport
xdg-open htmlcov/index.html  # Linux
```

### Architecture Best Practices 2026

- ✅ **API versionnée** (`/api/v1/`) pour évolutions futures
- ✅ **Dependency Injection** avec FastAPI `Depends()`
- ✅ **Configuration centralisée** avec `pydantic-settings`
- ✅ **Logging structuré** avec niveaux et couleurs
- ✅ **Exceptions typées** pour gestion d'erreurs propre
- ✅ **Séparation des responsabilités** (api/core/services/schemas)

## 🔄 CI/CD

Le pipeline GitHub Actions (`.github/workflows/ci-cd.yml`) exécute :

1. **Tests** : `pytest` avec couverture
2. **Lint** : Vérification du code avec `ruff`
3. **Validation** : Vérification des métadonnées des modèles
4. **Deploy** : Upload vers Hugging Face Spaces (branche `main` uniquement)

## 🌐 Déploiement

### Workflow : Local → GitHub → Production

#### 1️⃣ Développement local

```bash
# Python (recommandé pour le dev)
uvicorn src.api.main:app --host 0.0.0.0 --port 7860 --reload

# Docker (pour tester la prod)
docker build -t energy-api .
docker run -p 7860:7860 energy-api
```

#### 2️⃣ Push sur GitHub

```bash
git add .
git commit -m "feat: nouvelle fonctionnalité"
git push origin main
```

#### 3️⃣ Déploiement automatique

```
GitHub push → GitHub Actions (tests + lint + validation)
           → upload_folder vers HuggingFace Spaces
           → HF construit l'image Docker
           → HF lance le container
           → API publique en ligne !
```

**Résultat** : API accessible sur `https://clementrbl-deploy-ml.hf.space`

### 🔑 Résumé

| Environnement | Méthode | Commande manuelle ? | Rechargement auto ? |
|---------------|---------|---------------------|---------------------|
| **Local Dev** | Python | `uvicorn ... --reload` | ✅ Oui |
| **Local Test** | Docker | `docker run` | ❌ Non (rebuild) |
| **Production** | HF Spaces | ❌ Aucune (automatique) | ✅ Oui (à chaque push) |

## 📁 Structure du projet

```
deploy-ml/
├── .github/workflows/     # CI/CD GitHub Actions
├── data/                  # Dataset Seattle
├── docs/                  # Documentation (secrets)
├── scripts/               # Notebook d'entraînement
├── src/
│   ├── api/               # FastAPI (main, routes, endpoints)
│   │   └── v1/endpoints/  # Endpoints versionnés
│   ├── core/              # Config, logging, exceptions
│   ├── models/            # Modèles ML (.joblib, métadonnées)
│   ├── schemas/           # Pydantic (requests, responses)
│   └── services/          # Logique métier (predictor)
├── tests/                 # Tests pytest
├── Dockerfile             # Image Docker production
├── requirements.txt       # Dépendances Python
└── README.md
```

## 👤 Auteur

Projet réalisé dans le cadre de la formation Data Scientist - OpenClassrooms.
