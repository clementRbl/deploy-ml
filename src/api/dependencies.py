"""Dépendances FastAPI pour injection."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from src.core.config import Settings, get_settings
from src.db.database import get_db
from src.services.predictor import ModelPredictor, get_predictor

# Types annotés pour les dépendances
SettingsDep = Annotated[Settings, Depends(get_settings)]
PredictorDep = Annotated[ModelPredictor, Depends(get_predictor)]
DbDep = Annotated[Session, Depends(get_db)]
