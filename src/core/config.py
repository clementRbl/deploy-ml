from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration de l'app."""

    # Méta
    app_name: str = "Deploy ML API"
    app_version: str = "0.4.0"
    api_v1_prefix: str = "/api/v1"

    # Environment
    environment: str = "development"
    debug: bool = True

    # CORS
    cors_origins: list[str] = ["*"]

    # Paths
    models_dir: Path = Path(__file__).parent.parent / "models"

    # Database
    database_url: str = "postgresql://deploy_ml:deploy_ml@localhost:5432/deploy_ml"

    # Logging
    log_level: str = "INFO"
    log_format: str = "json"

    # API
    docs_enabled: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Ignore variables non déclarées pour éviter les erreurs
    )


@lru_cache
def get_settings() -> Settings:
    """Retourne les settings (cached)."""
    return Settings()
