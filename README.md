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

- Python 3.10+
- PostgreSQL 14+ (pour la traçabilité)
- Git

### Installation locale

```bash
# Cloner le repository
git clone https://github.com/<username>/deploy_ml.git
cd deploy_ml

# Créer un environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou: venv\Scripts\activate  # Windows

# Installer les dépendances
pip install -r requirements.txt

# Entraîner les modèles (optionnel, modèles pré-entraînés inclus)
python scripts/train_model.py

# Lancer l'API
uvicorn src.api.main:app --reload
```

### Variables d'environnement

Créer un fichier `.env` à la racine :

```env
# API
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=true

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/deploy_ml

# Security
SECRET_KEY=your-secret-key-here
```

## 💡 Utilisation

### Exemple de requête

```python
import requests

# Données d'un bâtiment
building_data = {
    "PropertyGFATotal": 50000,
    "PropertyGFABuilding(s)": 50000,
    "NumberofBuildings": 1,
    "NumberofFloors": 5,
    "PrimaryPropertyType": "Office",
    "LargestPropertyUseType": "Office",
    "LargestPropertyUseTypeGFA": 50000,
    # ... autres features
}

# Appel API
response = requests.post(
    "http://localhost:8000/predict",
    json=building_data
)

# Résultat
print(response.json())
# {
#     "energy_prediction_kbtu": 2500000.0,
#     "co2_prediction_tons": 150.5,
#     "prediction_id": "uuid-xxxx"
# }
```

## 🔌 API Endpoints

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `GET` | `/` | Health check |
| `GET` | `/docs` | Documentation Swagger |
| `POST` | `/predict` | Prédiction énergie + CO2 |
| `GET` | `/predictions/{id}` | Récupérer une prédiction |
| `GET` | `/predictions` | Liste des prédictions |

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

### Initialisation

```bash
# Créer la base de données
python src/db/create_db.py
```

## 🧪 Tests

```bash
# Lancer tous les tests
pytest

# Avec couverture
pytest --cov=src --cov-report=html

# Tests spécifiques
pytest tests/test_api.py -v
```

## 🔄 CI/CD

Le pipeline GitHub Actions :

1. **Test** : Exécute pytest sur chaque push/PR
2. **Lint** : Vérifie le code avec ruff
3. **Deploy** : Déploie sur Hugging Face Spaces (branche main)

## 🌐 Déploiement

### Hugging Face Spaces

L'application est déployée automatiquement sur : `https://huggingface.co/spaces/<username>/deploy-ml`

### Docker (optionnel)

```bash
docker build -t deploy-ml .
docker run -p 8000:8000 deploy-ml
```

## 📁 Structure du projet

```
deploy_ml/
├── .github/
│   └── workflows/          # CI/CD GitHub Actions
├── data/
│   └── *.csv               # Dataset
├── docs/                   # Documentation
├── scripts/
│   ├── train_model.py      # Script d'entraînement
│   └── *.ipynb             # Notebooks d'exploration
├── src/
│   ├── api/                # FastAPI application
│   │   ├── main.py
│   │   ├── routes.py
│   │   └── schemas.py
│   ├── db/                 # Database scripts
│   │   ├── create_db.py
│   │   └── models.py
│   └── models/             # ML models (.joblib)
├── tests/                  # Tests Pytest
├── .env.example
├── .gitignore
├── README.md
└── requirements.txt
```

## 📄 License

MIT License - voir [LICENSE](LICENSE) pour plus de détails.

## 👤 Auteur

Projet réalisé dans le cadre de la formation Data Scientist - OpenClassrooms.

---

*Dernière mise à jour : Février 2026*
