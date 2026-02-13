from fastapi import APIRouter, HTTPException

from src.api.dependencies import PredictorDep
from src.core.logging import logger
from src.schemas.responses import ModelInfoResponse

router = APIRouter(tags=["Models"])


@router.get("/models/info", response_model=ModelInfoResponse)
async def get_models_info(predictor: PredictorDep) -> ModelInfoResponse:
    """Retourne les informations détaillées sur les modèles ML chargés.

    ## Informations incluses

    - **Algorithme** : RandomForest / LightGBM
    - **Score R²** : Performance sur validation croisée
    - **Features numériques** : Liste des features continues
    - **Features catégorielles** : Liste des features catégoriques
    - **Target** : Variable cible prédite
    - **Transform** : Transformation appliquée (log1p)

    ## Utilité

    - Comprendre les features attendues par les modèles
    - Vérifier la performance des modèles en production
    - Documenter l'architecture ML pour les équipes data

    ## Note

    - Ces métadonnées sont chargées depuis `model_metadata.json`
    - Les modèles ont été entraînés sur le dataset Seattle Building Energy Benchmarking
    """
    if not predictor.is_loaded():
        logger.error("Tentative d'accès aux métadonnées avec modèles non chargés")
        raise HTTPException(status_code=503, detail="Models not loaded")

    logger.debug("Récupération des métadonnées des modèles")

    return ModelInfoResponse(
        energy_model=predictor.metadata["energy_model"],
        co2_model=predictor.metadata["co2_model"],
    )
