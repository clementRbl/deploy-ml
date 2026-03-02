# Documentation technique : performances et maintenance du modèle

Ce document décrit les **performances** des modèles ML déployés et les **procédures de maintenance** (mise à jour des modèles, compatibilité, versioning).

---

## Performances du modèle

### Métriques

Les deux modèles ont été entraînés sur le dataset Seattle Building Energy Benchmarking 2016, avec une validation par **cross-validation** (R² rapporté).


| Modèle      | Cible                 | Algorithme               | R² (CV)  | Unité      |
| ----------- | --------------------- | ------------------------ | -------- | ---------- |
| **Énergie** | `SiteEnergyUse(kBtu)` | Random Forest (optimisé) | **0,73** | kBtu       |
| **CO2**     | `TotalGHGEmissions`   | LightGBM (optimisé)      | **0,92** | tonnes CO2 |


- **Modèle énergie** : prédit la consommation énergétique totale du bâtiment. R² ≈ 0,73 indique une bonne capacité explicative avec une marge d’erreur acceptable pour un usage POC / aide à la décision.
- **Modèle CO2** : prédit les émissions de GES (tonnes CO2). R² ≈ 0,92 indique une très bonne précision ; le modèle utilise en entrée la consommation énergétique (réelle ou prédite) ainsi que les caractéristiques du bâtiment.

Les prédictions sont obtenues après transformation **log1p** à l’entraînement et **expm1** à l’inférence (réduction de l’impact des valeurs extrêmes).

### Périmètre et limites

- **Données** : bâtiments **non résidentiels** de Seattle, année 2016. Environ 1 649 échantillons utilisés pour l’entraînement (après nettoyage).
- **Limites connues** :
  - Les modèles ne sont pas calibrés pour d’autres villes ou années sans ré-entraînement.
  - Les types de bâtiments et usages doivent rester cohérents avec les catégories du jeu d’entraînement (Office, Hotel, Retail, etc.).
  - Les valeurs extrêmes (surfaces ou consommations très élevées) peuvent être moins bien prédites.
- **Usage recommandé** : estimation et comparaison de bâtiments dans un contexte proche de Seattle 2016 ; pas de remplacement d’un audit énergétique officiel.

---

## Maintenance

### Mise à jour des modèles (.joblib)

1. **Ré-entraînement** (notebook ou script) : produire de nouveaux fichiers `energy_model.joblib` et `co2_model.joblib` en conservant les **mêmes noms de features** que dans `src/models/model_metadata.json` (voir ci-dessous).
2. **Métadonnées** : mettre à jour `src/models/model_metadata.json` si les features, l’algorithme ou le R² ont changé (les tests CI vérifient la structure de ce fichier).
3. **Tests** : lancer `pytest tests/ -v` et vérifier que les prédictions restent cohérentes (éventuellement ajuster les tests de régression si les métriques cibles ont changé).
4. **Déploiement** : en local, remplacer les fichiers dans `src/models/` ; pour Hugging Face Spaces, pousser les changements sur `main` (le workflow CI/CD gère l’upload). Si les modèles sont hébergés ailleurs (ex. HF Hub), adapter le `Dockerfile` ou le code de chargement dans `src/services/predictor.py`.

### Compatibilité des features

- Les **entrées API** sont définies par le schéma Pydantic `BuildingInput` (`src/schemas/requests.py`). Toute modification des features attendues par les modèles doit être reflétée dans ce schéma et dans le feature engineering dans `src/services/predictor.py`.
- Le fichier **model_metadata.json** liste les `numeric_features` et `categorical_features` attendues. Il est utilisé pour la documentation et la validation ; le prédicteur s’appuie sur le dictionnaire renvoyé par `BuildingInput.model_dump(by_alias=True)` et sur le calcul des features dérivées (HasMultipleBuildings, FloorsPerBuilding, etc.). En cas de nouvel entraînement avec d’autres variables, mettre à jour à la fois les modèles, `model_metadata.json`, `BuildingInput` et `predictor.py`.

### Versioning

- Les **tags Git** (ex. `v0.1.0`, `v0.2.0`) permettent de repérer une version livrée. Il est recommandé de créer un tag après chaque mise à jour majeure des modèles ou de l’API.
- La **version de l’API** est définie dans `src/core/config.py` (`app_version`) et affichée dans `/api/v1/` et `/api/v1/health`.

---

## Protocole de mise à jour régulière

- **Modèles ML** : ré-évaluer au moins une fois par an (nouveaux données Seattle ou évolution du périmètre). Ré-entraîner, mettre à jour `model_metadata.json` et les fichiers `.joblib`, lancer les tests, puis déployer (push sur `main` pour HF Spaces).
- **Dépendances Python** : trimestriellement, mettre à jour `requirements.txt` (ex. `pip list --outdated`), lancer les tests et le lint, corriger les éventuelles régressions, puis créer un tag (ex. `v0.3.0`).
- **Sécurité** : surveiller les alertes GitHub (Dependabot) et les CVE sur les paquets utilisés ; appliquer les correctifs et relancer le pipeline CI/CD.
- **Déploiement** : chaque push sur `main` déclenche le pipeline (tests + déploiement HF). Pour une mise à jour planifiée, merger une branche dédiée (ex. `release/2025-Q1`) dans `main` après revue.

---

## Références

- Schéma des entrées : `src/schemas/requests.py`
- Service de prédiction : `src/services/predictor.py`
- Métadonnées des modèles : `src/models/model_metadata.json`
- Guide d’architecture : [ARCHITECTURE_GUIDE.md](../ARCHITECTURE_GUIDE.md)
