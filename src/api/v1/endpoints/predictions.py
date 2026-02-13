import uuid

from fastapi import APIRouter, HTTPException

from src.api.dependencies import PredictorDep
from src.core.exceptions import InvalidInputError, ModelNotLoadedError, PredictionError
from src.core.logging import logger
from src.schemas.requests import BuildingInput
from src.schemas.responses import PredictionOutput

router = APIRouter(tags=["Predictions"])


@router.post("/predict", response_model=PredictionOutput, status_code=200)
async def predict_building(building: BuildingInput, predictor: PredictorDep) -> PredictionOutput:
    """Prédit la consommation énergétique et les émissions de CO2 d'un bâtiment.

    ## Données requises

    - **Informations structurelles** : nombre de bâtiments, étages, surfaces
    - **Type d'usage** : PrimaryPropertyType (Office, Hotel, Retail, etc.)
    - **Sources d'énergie** : électricité, gaz naturel, vapeur

    ## Retour

    - **energy_prediction_kbtu** : Consommation énergétique en kBtu
    - **co2_prediction_tons** : Émissions de CO2 en tonnes métriques
    - **prediction_id** : Identifiant unique de la prédiction

    ## Exemple de requête

    ```json
    {
        "NumberofBuildings": 1,
        "NumberofFloors": 5,
        "PropertyGFATotal": 50000,
        "PropertyGFABuilding(s)": 45000,
        "PrimaryPropertyType": "Office",
        "LargestPropertyUseType": "Office"
    }
    ```

    ## Notes

    - Les features dérivées (HasMultipleBuildings, FloorsPerBuilding, etc.) sont calculées automatiquement
    - L'énergie prédite est utilisée en entrée pour la prédiction CO2
    - Les modèles utilisent une transformation log1p inversée avec expm1
    """
    try:
        # Convertir en dict pour le prédicteur (avec alias)
        building_dict = building.model_dump(by_alias=True)

        # Générer un ID unique avant la prédiction
        prediction_id = str(uuid.uuid4())[:8]

        logger.info(f"Prédiction {prediction_id} - Début pour {building.PrimaryPropertyType}")

        # Faire la prédiction
        energy_kbtu, co2_tons = predictor.predict(building_dict)

        logger.info(
            f"Prédiction {prediction_id} - Résultats: "
            f"{energy_kbtu:.2f} kBtu, {co2_tons:.2f} tons CO2"
        )

        return PredictionOutput(
            energy_prediction_kbtu=energy_kbtu,
            co2_prediction_tons=co2_tons,
            prediction_id=prediction_id,
        )

    except ModelNotLoadedError as e:
        logger.error(f"Modèles non chargés: {e}")
        raise HTTPException(status_code=503, detail=str(e.message))

    except (ValueError, InvalidInputError) as e:
        logger.warning(f"Données invalides: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid input data: {str(e)}")

    except PredictionError as e:
        logger.error(f"Erreur de prédiction: {e}")
        raise HTTPException(status_code=500, detail=str(e.message))

    except Exception as e:
        logger.error(f"Erreur inattendue: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
