import time
import uuid

from fastapi import APIRouter, HTTPException

from src.api.dependencies import DbDep, PredictorDep
from src.core.exceptions import InvalidInputError, ModelNotLoadedError, PredictionError
from src.core.logging import logger
from src.db.models import Prediction
from src.schemas.requests import BuildingInput
from src.schemas.responses import PredictionOutput

router = APIRouter(tags=["Predictions"])


@router.post("/predict", response_model=PredictionOutput, status_code=200)
async def predict_building(
    building: BuildingInput,
    predictor: PredictorDep,
    db: DbDep,
) -> PredictionOutput:
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

        # Faire la prédiction (mesurer le temps)
        start_time = time.perf_counter()
        energy_kbtu, co2_tons = predictor.predict(building_dict)
        duration_ms = (time.perf_counter() - start_time) * 1000

        logger.info(
            f"Prédiction {prediction_id} - Résultats: "
            f"{energy_kbtu:.2f} kBtu, {co2_tons:.2f} tons CO2 ({duration_ms:.1f}ms)"
        )

        # Enregistrer la prédiction en base de données
        try:
            db_prediction = Prediction(
                # Inputs numériques
                number_of_buildings=building.NumberofBuildings,
                number_of_floors=building.NumberofFloors,
                property_gfa_total=building.PropertyGFATotal,
                property_gfa_parking=building.PropertyGFAParking,
                property_gfa_building=building.PropertyGFABuilding,
                largest_property_use_type_gfa=building.LargestPropertyUseTypeGFA,
                second_largest_property_use_type_gfa=building.SecondLargestPropertyUseTypeGFA,
                third_largest_property_use_type_gfa=building.ThirdLargestPropertyUseTypeGFA,
                # Inputs dérivés
                building_age=building.BuildingAge,
                has_multiple_buildings=building.HasMultipleBuildings,
                floors_per_building=building.FloorsPerBuilding,
                has_secondary_use=building.HasSecondaryUse,
                distance_to_center=building.DistanceToCenter,
                has_electricity=building.HasElectricity,
                has_natural_gas=building.HasNaturalGas,
                has_steam=building.HasSteam,
                surface_gas_interaction=building.SurfaceGasInteraction,
                # Inputs catégoriels
                building_type=building.BuildingType,
                primary_property_type=building.PrimaryPropertyType,
                largest_property_use_type=building.LargestPropertyUseType,
                second_largest_property_use_type=building.SecondLargestPropertyUseType,
                third_largest_property_use_type=building.ThirdLargestPropertyUseType,
                # Outputs
                energy_prediction_kbtu=energy_kbtu,
                co2_prediction_tons=co2_tons,
                # Métadonnées
                prediction_duration_ms=duration_ms,
                source="api",
            )
            db.add(db_prediction)
            db.commit()
            prediction_id = str(db_prediction.id)[:8]
            logger.info(f"Prédiction {prediction_id} enregistrée en base")
        except Exception as db_err:
            # Log l'erreur DB mais ne pas bloquer la réponse
            db.rollback()
            logger.warning(f"Échec enregistrement DB (non bloquant): {db_err}")

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
