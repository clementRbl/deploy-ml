"""Tests pour valider la structure du projet.
Ces tests seront enrichis dans la branche feature/5-tests.
"""  # noqa: D205

import json
from pathlib import Path

import pytest


def test_project_structure():
    """Vérifie que la structure de base du projet existe."""
    project_root = Path(__file__).parent.parent

    # Dossiers requis
    assert (project_root / "src").is_dir()
    assert (project_root / "src" / "api").is_dir()
    assert (project_root / "src" / "models").is_dir()
    assert (project_root / "src" / "db").is_dir()
    assert (project_root / "tests").is_dir()
    assert (project_root / "data").is_dir()


def test_models_exist():
    """Vérifie que les modèles ML sont présents.

    Note: Les fichiers .joblib ne sont plus versionnés dans Git.
    Ils sont uniquement inclus dans l'image Docker via COPY.
    Ce test skip en CI/CD mais valide la présence locale.
    """
    models_dir = Path(__file__).parent.parent / "src" / "models"

    # Skip si les modèles ne sont pas présents (environnement CI/CD)
    if not (models_dir / "energy_model.joblib").exists():
        pytest.skip("Models not in Git (included in Docker image only)")

    assert (models_dir / "energy_model.joblib").exists()
    assert (models_dir / "co2_model.joblib").exists()
    assert (models_dir / "model_metadata.json").exists()


def test_model_metadata_valid():
    """Vérifie que les métadonnées des modèles sont valides."""
    metadata_path = Path(__file__).parent.parent / "src" / "models" / "model_metadata.json"

    with open(metadata_path) as f:
        metadata = json.load(f)

    # Vérifier la structure
    assert "energy_model" in metadata
    assert "co2_model" in metadata

    # Vérifier les champs requis
    for model_key in ["energy_model", "co2_model"]:
        model_info = metadata[model_key]
        assert "file" in model_info
        assert "target" in model_info
        assert "algorithm" in model_info
        assert "r2_cv" in model_info
        assert "numeric_features" in model_info
        assert "categorical_features" in model_info


def test_requirements_file():
    """Vérifie que requirements.txt existe et contient les dépendances clés."""
    requirements_path = Path(__file__).parent.parent / "requirements.txt"

    assert requirements_path.exists()

    content = requirements_path.read_text()

    # Vérifier les dépendances critiques
    assert "fastapi" in content.lower()
    assert "scikit-learn" in content.lower()
    assert "pandas" in content.lower()
    assert "pytest" in content.lower()
