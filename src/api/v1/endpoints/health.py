from fastapi import APIRouter

from src.api.dependencies import PredictorDep, SettingsDep
from src.schemas.responses import HealthCheckResponse

router = APIRouter(tags=["Health"])


@router.get("/", response_model=HealthCheckResponse)
async def root(settings: SettingsDep, predictor: PredictorDep) -> HealthCheckResponse:
    """Health check de base.

    Vérifie que l'API est ok et que les modèles sont chargés.
    """
    return HealthCheckResponse(
        status="ok",
        version=settings.app_version,
        models_loaded=predictor.is_loaded(),
    )


@router.get("/health", response_model=HealthCheckResponse)
async def health_check(settings: SettingsDep, predictor: PredictorDep) -> HealthCheckResponse:
    """Health check détaillé.

    Vérifie en profondeur que l'API est prête à recevoir des prédictions.
    """
    return HealthCheckResponse(
        status="healthy" if predictor.is_loaded() else "unhealthy",
        version=settings.app_version,
        models_loaded=predictor.is_loaded(),
    )
