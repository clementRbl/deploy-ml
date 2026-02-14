from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PredictionOutput(BaseModel):
    """Résultat de la prédiction (énergie + CO2)."""

    energy_prediction_kbtu: float = Field(
        ..., description="Consommation énergétique prédite en kBtu"
    )
    co2_prediction_tons: float = Field(..., description="Émissions de CO2 prédites en tonnes")
    prediction_id: str = Field(..., description="ID unique de la prédiction")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "energy_prediction_kbtu": 2947914.5,
                "co2_prediction_tons": 51.6,
                "prediction_id": "abc123-def456",
            }
        }
    )


class PredictionRecord(BaseModel):
    """Enregistrement complet d'une prédiction (pour l'historique)."""

    id: str
    created_at: datetime
    primary_property_type: str | None
    building_type: str | None
    property_gfa_total: float | None
    energy_prediction_kbtu: float
    co2_prediction_tons: float
    prediction_duration_ms: float | None
    source: str | None

    model_config = ConfigDict(from_attributes=True)


class PredictionHistoryResponse(BaseModel):
    """Réponse paginée de l'historique des prédictions."""

    total: int = Field(..., description="Nombre total de prédictions")
    predictions: list[PredictionRecord] = Field(..., description="Liste des prédictions")


class BuildingRecord(BaseModel):
    """Résumé d'un bâtiment en base."""

    id: int
    ose_building_id: int
    building_type: str
    primary_property_type: str
    property_name: str | None
    neighborhood: str | None
    year_built: int | None
    property_gfa_total: int | None
    site_energy_use: float | None
    total_ghg_emissions: float | None

    model_config = ConfigDict(from_attributes=True)


class BuildingsListResponse(BaseModel):
    """Réponse paginée de la liste des bâtiments."""

    total: int
    buildings: list[BuildingRecord]


class HealthCheckResponse(BaseModel):
    """Réponse du health check."""

    status: str = Field(..., description="Statut de l'API")
    version: str = Field(..., description="Version de l'API")
    models_loaded: bool = Field(..., description="True si les modèles sont chargés")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "healthy",
                "version": "0.4.0",
                "models_loaded": True,
            }
        }
    )


class ModelInfoResponse(BaseModel):
    """Informations détaillées sur les modèles."""

    energy_model: dict = Field(..., description="Métadonnées du modèle d'énergie")
    co2_model: dict = Field(..., description="Métadonnées du modèle de CO2")
