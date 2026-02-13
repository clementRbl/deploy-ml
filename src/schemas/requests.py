from pydantic import BaseModel, ConfigDict, Field


class BuildingInput(BaseModel):
    """Données d'entrée pour prédire la consommation énergétique et les émissions CO2."""

    # Features numériques
    NumberofBuildings: int = Field(..., ge=1, description="Nombre de bâtiments sur le site")
    NumberofFloors: float | None = Field(None, ge=0, description="Nombre d'étages")
    PropertyGFATotal: float = Field(..., gt=0, description="Surface totale en pieds carrés")
    PropertyGFAParking: float = Field(0, ge=0, description="Surface de parking en pieds carrés")
    PropertyGFABuilding: float = Field(
        ..., alias="PropertyGFABuilding(s)", gt=0, description="Surface du/des bâtiment(s)"
    )
    LargestPropertyUseTypeGFA: float = Field(..., gt=0, description="Surface de l'usage principal")
    SecondLargestPropertyUseTypeGFA: float = Field(
        0, ge=0, description="Surface de l'usage secondaire"
    )
    ThirdLargestPropertyUseTypeGFA: float = Field(0, ge=0, description="Surface du 3ème usage")

    # Features dérivées (calculées automatiquement si non fournies)
    BuildingAge: int | None = Field(None, ge=0, description="Âge du bâtiment en années")
    HasMultipleBuildings: int | None = Field(
        None, ge=0, le=1, description="1 si plusieurs bâtiments, 0 sinon"
    )
    FloorsPerBuilding: float | None = Field(None, ge=0, description="Ratio étages/bâtiments")
    HasSecondaryUse: int | None = Field(
        None, ge=0, le=1, description="1 si usage secondaire, 0 sinon"
    )
    DistanceToCenter: float | None = Field(
        None, ge=0, description="Distance au centre de Seattle (km)"
    )
    HasElectricity: int = Field(1, ge=0, le=1, description="1 si électricité, 0 sinon")
    HasNaturalGas: int = Field(1, ge=0, le=1, description="1 si gaz naturel, 0 sinon")
    HasSteam: int = Field(0, ge=0, le=1, description="1 si vapeur, 0 sinon")
    SurfaceGasInteraction: float | None = Field(None, ge=0, description="Interaction Surface × Gaz")

    # Features catégorielles
    BuildingType: str = Field("NonResidential", description="Type de bâtiment")
    PrimaryPropertyType: str = Field(
        ..., description="Type de propriété principal (Office, Hotel, etc.)"
    )
    LargestPropertyUseType: str = Field(..., description="Type d'usage principal")
    SecondLargestPropertyUseType: str = Field("None", description="Type d'usage secondaire")
    ThirdLargestPropertyUseType: str = Field("None", description="Type du 3ème usage")

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "NumberofBuildings": 1,
                "NumberofFloors": 5,
                "PropertyGFATotal": 50000,
                "PropertyGFAParking": 5000,
                "PropertyGFABuilding(s)": 45000,
                "LargestPropertyUseTypeGFA": 45000,
                "SecondLargestPropertyUseTypeGFA": 0,
                "ThirdLargestPropertyUseTypeGFA": 0,
                "BuildingAge": 20,
                "HasMultipleBuildings": 0,
                "FloorsPerBuilding": 5.0,
                "HasSecondaryUse": 0,
                "DistanceToCenter": 3.5,
                "HasElectricity": 1,
                "HasNaturalGas": 1,
                "HasSteam": 0,
                "SurfaceGasInteraction": 50000,
                "BuildingType": "NonResidential",
                "PrimaryPropertyType": "Office",
                "LargestPropertyUseType": "Office",
                "SecondLargestPropertyUseType": "None",
                "ThirdLargestPropertyUseType": "None",
            }
        },
    )
