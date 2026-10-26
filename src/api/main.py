from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from src.api.v1.router import api_router
from src.core.config import get_settings
from src.core.exceptions import DeployMLError
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


# --- En-têtes de sécurité + masquage de la bannière serveur ---
@app.middleware("http")
async def security_headers(request: Request, call_next):
    """Ajoute les en-têtes de sécurité et retire la bannière serveur."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    if "server" in response.headers:
        del response.headers["server"]  # ne pas exposer "uvicorn"
    return response


# --- Handlers d'erreur: aucune stacktrace ne fuit, codes HTTP cohérents ---
@app.exception_handler(DeployMLError)
async def deploy_ml_error_handler(request: Request, exc: DeployMLError):
    """Renvoie l'erreur métier avec son code HTTP, sans trace."""
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


@app.exception_handler(SQLAlchemyError)
async def database_error_handler(request: Request, exc: SQLAlchemyError):
    """Répond 503 quand la base est indisponible."""
    # DB injoignable (ex. non provisionnée en prod) => 503 propre au lieu d'un 500 brut
    logger.error(f"Erreur base de données sur {request.url.path}: {type(exc).__name__}")
    return JSONResponse(
        status_code=503,
        content={"detail": "Base de données indisponible"},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """Répond 500 sans exposer le détail de l'erreur."""
    logger.error(f"Erreur non gérée sur {request.url.path}: {type(exc).__name__}")
    return JSONResponse(status_code=500, content={"detail": "Erreur interne"})
