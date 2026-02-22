"""Marqueurs pytest partages (ex. skip si modeles ML absents)."""

from pathlib import Path

import pytest

_models_dir = Path(__file__).parent.parent / "src" / "models"
MODELS_AVAILABLE = (_models_dir / "energy_model.joblib").exists()

requires_models = pytest.mark.skipif(
    not MODELS_AVAILABLE,
    reason="ML models (.joblib) not available (CI environment)",
)
