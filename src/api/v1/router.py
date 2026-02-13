from fastapi import APIRouter

from src.api.v1.endpoints import health, models, predictions

# Router principal V1
api_router = APIRouter()

# routers des endpoints
api_router.include_router(health.router)
api_router.include_router(predictions.router)
api_router.include_router(models.router)
