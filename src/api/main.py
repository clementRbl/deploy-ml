from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.v1.router import api_router
from src.core.config import get_settings
from src.core.logging import logger
from src.services.predictor import get_predictor

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gère le cycle de vie de l'application."""
    logger.info(f"Démarrage de {settings.app_name} v{settings.app_version}")
    logger.info("Chargement des modèles ML...")

    # Charger les modèles au démarrage (singleton) pour éviter de les recharger à chaque requête
    predictor = get_predictor()

    if predictor.is_loaded():
        logger.info("API prête à recevoir des requêtes")
    else:
        logger.error("Erreur: modèles non chargés")

    yield

    logger.info("Arrêt de l'API")


# Configuration FastAPI
app = FastAPI(
    title=settings.app_name,
    description="""
    API REST pour prédire la consommation énergétique et les émissions de CO2
    des bâtiments non-résidentiels de Seattle.
    """,
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs" if settings.docs_enabled else None,
    redoc_url="/redoc" if settings.docs_enabled else None,
)

# Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclure le router API v1
app.include_router(api_router, prefix=settings.api_v1_prefix)
