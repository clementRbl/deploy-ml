"""Dépendances FastAPI pour injection."""

from typing import Annotated

from fastapi import Depends

from src.core.config import Settings, get_settings
from src.services.predictor import ModelPredictor, get_predictor

# Type  pour les dépendances
SettingsDep = Annotated[Settings, Depends(get_settings)]
PredictorDep = Annotated[ModelPredictor, Depends(get_predictor)]
