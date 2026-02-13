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


class HealthCheckResponse(BaseModel):
    """Réponse du health check."""

    status: str = Field(..., description="Statut de l'API")
    version: str = Field(..., description="Version de l'API")
    models_loaded: bool = Field(..., description="True si les modèles sont chargés")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "healthy",
                "version": "0.3.0",
                "models_loaded": True,
            }
        }
    )


class ModelInfoResponse(BaseModel):
    """Informations détaillées sur les modèles."""

    energy_model: dict = Field(..., description="Métadonnées du modèle d'énergie")
    co2_model: dict = Field(..., description="Métadonnées du modèle de CO2")
