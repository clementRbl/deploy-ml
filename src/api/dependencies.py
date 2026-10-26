"""Dépendances FastAPI pour injection."""

import secrets
from typing import Annotated

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session

from src.core.config import Settings, get_settings
from src.db.database import get_db
from src.services.predictor import ModelPredictor, get_predictor

# Types annotés pour les dépendances
SettingsDep = Annotated[Settings, Depends(get_settings)]
PredictorDep = Annotated[ModelPredictor, Depends(get_predictor)]
DbDep = Annotated[Session, Depends(get_db)]

# --- Sécurité: clé d'API pour les endpoints /db/* ---
_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def require_api_key(
    settings: SettingsDep,
    provided_key: Annotated[str | None, Security(_api_key_header)] = None,
) -> None:
    """Protège les endpoints exposant des données en base.

    - Si aucune clé n'est configurée (``API_KEY`` absent) => 503, feature désactivée.
    - Sinon, exige un en-tête ``X-API-Key`` correspondant (comparaison constante).
    """
    if not settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Endpoints base de données désactivés (aucune clé d'API configurée)",
        )
    if not provided_key or not secrets.compare_digest(provided_key, settings.api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Clé d'API invalide ou manquante (en-tête X-API-Key)",
        )
