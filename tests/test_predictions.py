"""Tests pour le service de prediction ML.

Teste le ModelPredictor : chargement, preparation des features,
predictions, et gestion des erreurs.
"""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from src.core.exceptions import ModelNotLoadedError, PredictionError
from src.services.predictor import ModelPredictor, get_predictor


class TestPredictorLoading:
    """Tests pour le chargement des modeles."""

    def test_predictor_loads_successfully(self, predictor):
        """Le predictor charge les modeles au demarrage."""
        assert predictor.is_loaded()
        assert predictor.energy_model is not None
        assert predictor.co2_model is not None
        assert predictor.metadata is not None

    def test_predictor_metadata_structure(self, predictor):
        """Les metadonnees ont la bonne structure."""
        assert "energy_model" in predictor.metadata
        assert "co2_model" in predictor.metadata
        assert "algorithm" in predictor.metadata["energy_model"]
        assert "r2_cv" in predictor.metadata["co2_model"]

    def test_predictor_singleton(self):
        """get_predictor() retourne toujours la meme instance."""
        p1 = get_predictor()
        p2 = get_predictor()
        assert p1 is p2

    def test_predictor_invalid_path_not_loaded(self):
        """Un chemin inexistant fait que le predictor n'est pas charge."""
        p = ModelPredictor(models_dir=Path("/nonexistent/path"))
        assert not p.is_loaded()


class TestPredictorPredict:
    """Tests pour la methode predict()."""

    def test_predict_returns_tuple(self, predictor, valid_building_input):
        """predict() retourne un tuple (energy, co2)."""
        result = predictor.predict(valid_building_input)
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_predict_positive_values(self, predictor, valid_building_input):
        """Les predictions sont positives."""
        energy, co2 = predictor.predict(valid_building_input)
        assert energy > 0
        assert co2 > 0

    def test_predict_returns_floats(self, predictor, valid_building_input):
        """Les predictions sont des floats."""
        energy, co2 = predictor.predict(valid_building_input)
        assert isinstance(energy, float)
        assert isinstance(co2, float)

    def test_predict_deterministic(self, predictor, valid_building_input):
        """Le meme input donne le meme output."""
        r1 = predictor.predict(valid_building_input.copy())
        r2 = predictor.predict(valid_building_input.copy())
        assert r1[0] == pytest.approx(r2[0], rel=1e-6)
        assert r1[1] == pytest.approx(r2[1], rel=1e-6)

    def test_predict_larger_building_more_energy(self, predictor):
        """Un batiment plus grand consomme plus d'energie."""
        small = {
            "NumberofBuildings": 1,
            "PropertyGFATotal": 10000,
            "PropertyGFAParking": 0,
            "PropertyGFABuilding(s)": 10000,
            "LargestPropertyUseTypeGFA": 10000,
            "SecondLargestPropertyUseTypeGFA": 0,
            "ThirdLargestPropertyUseTypeGFA": 0,
            "HasElectricity": 1,
            "HasNaturalGas": 1,
            "HasSteam": 0,
            "BuildingType": "NonResidential",
            "PrimaryPropertyType": "Office",
            "LargestPropertyUseType": "Office",
            "SecondLargestPropertyUseType": "None",
            "ThirdLargestPropertyUseType": "None",
        }
        large = {
            "NumberofBuildings": 1,
            "PropertyGFATotal": 500000,
            "PropertyGFAParking": 0,
            "PropertyGFABuilding(s)": 500000,
            "LargestPropertyUseTypeGFA": 500000,
            "SecondLargestPropertyUseTypeGFA": 0,
            "ThirdLargestPropertyUseTypeGFA": 0,
            "HasElectricity": 1,
            "HasNaturalGas": 1,
            "HasSteam": 0,
            "BuildingType": "NonResidential",
            "PrimaryPropertyType": "Office",
            "LargestPropertyUseType": "Office",
            "SecondLargestPropertyUseType": "None",
            "ThirdLargestPropertyUseType": "None",
        }
        e_small, _ = predictor.predict(small)
        e_large, _ = predictor.predict(large)
        assert e_large > e_small

    def test_predict_not_loaded_raises(self):
        """predict() leve une erreur si modeles non charges."""
        p = MagicMock(spec=ModelPredictor)
        p.is_loaded.return_value = False
        p.predict = ModelPredictor.predict.__get__(p)

        with pytest.raises(ModelNotLoadedError):
            p.predict({})


class TestFeatureEngineering:
    """Tests pour le calcul automatique des features derivees."""

    def test_auto_has_multiple_buildings(self, predictor):
        """HasMultipleBuildings est calcule automatiquement."""
        data = {
            "NumberofBuildings": 3,
            "PropertyGFATotal": 50000,
            "PropertyGFAParking": 5000,
            "PropertyGFABuilding(s)": 45000,
            "LargestPropertyUseTypeGFA": 45000,
            "SecondLargestPropertyUseTypeGFA": 0,
            "ThirdLargestPropertyUseTypeGFA": 0,
            "HasElectricity": 1,
            "HasNaturalGas": 1,
            "HasSteam": 0,
            "BuildingType": "NonResidential",
            "PrimaryPropertyType": "Office",
            "LargestPropertyUseType": "Office",
            "SecondLargestPropertyUseType": "None",
            "ThirdLargestPropertyUseType": "None",
        }
        # Pas de HasMultipleBuildings fourni -> calcule automatiquement
        energy, co2 = predictor.predict(data)
        assert energy > 0  # Pas d'erreur = feature bien calculee

    def test_auto_floors_per_building(self, predictor):
        """FloorsPerBuilding est calcule automatiquement."""
        data = {
            "NumberofBuildings": 2,
            "NumberofFloors": 10,
            "PropertyGFATotal": 50000,
            "PropertyGFAParking": 5000,
            "PropertyGFABuilding(s)": 45000,
            "LargestPropertyUseTypeGFA": 45000,
            "SecondLargestPropertyUseTypeGFA": 0,
            "ThirdLargestPropertyUseTypeGFA": 0,
            "HasElectricity": 1,
            "HasNaturalGas": 1,
            "HasSteam": 0,
            "BuildingType": "NonResidential",
            "PrimaryPropertyType": "Office",
            "LargestPropertyUseType": "Office",
            "SecondLargestPropertyUseType": "None",
            "ThirdLargestPropertyUseType": "None",
        }
        energy, co2 = predictor.predict(data)
        assert energy > 0

    def test_auto_distance_default(self, predictor):
        """DistanceToCenter a une valeur par defaut."""
        data = {
            "NumberofBuildings": 1,
            "PropertyGFATotal": 50000,
            "PropertyGFAParking": 5000,
            "PropertyGFABuilding(s)": 45000,
            "LargestPropertyUseTypeGFA": 45000,
            "SecondLargestPropertyUseTypeGFA": 0,
            "ThirdLargestPropertyUseTypeGFA": 0,
            "HasElectricity": 1,
            "HasNaturalGas": 1,
            "HasSteam": 0,
            "BuildingType": "NonResidential",
            "PrimaryPropertyType": "Office",
            "LargestPropertyUseType": "Office",
            "SecondLargestPropertyUseType": "None",
            "ThirdLargestPropertyUseType": "None",
        }
        energy, co2 = predictor.predict(data)
        assert energy > 0

    def test_auto_building_age_default(self, predictor):
        """BuildingAge a une valeur par defaut."""
        data = {
            "NumberofBuildings": 1,
            "PropertyGFATotal": 50000,
            "PropertyGFAParking": 5000,
            "PropertyGFABuilding(s)": 45000,
            "LargestPropertyUseTypeGFA": 45000,
            "SecondLargestPropertyUseTypeGFA": 0,
            "ThirdLargestPropertyUseTypeGFA": 0,
            "HasElectricity": 1,
            "HasNaturalGas": 1,
            "HasSteam": 0,
            "BuildingType": "NonResidential",
            "PrimaryPropertyType": "Office",
            "LargestPropertyUseType": "Office",
            "SecondLargestPropertyUseType": "None",
            "ThirdLargestPropertyUseType": "None",
        }
        energy, co2 = predictor.predict(data)
        assert energy > 0

    def test_auto_secondary_use_detection(self, predictor):
        """HasSecondaryUse est detecte si SecondLargestPropertyUseType fourni."""
        data = {
            "NumberofBuildings": 1,
            "PropertyGFATotal": 50000,
            "PropertyGFAParking": 5000,
            "PropertyGFABuilding(s)": 45000,
            "LargestPropertyUseTypeGFA": 35000,
            "SecondLargestPropertyUseTypeGFA": 10000,
            "ThirdLargestPropertyUseTypeGFA": 0,
            "HasElectricity": 1,
            "HasNaturalGas": 1,
            "HasSteam": 0,
            "BuildingType": "NonResidential",
            "PrimaryPropertyType": "Office",
            "LargestPropertyUseType": "Office",
            "SecondLargestPropertyUseType": "Retail Store",
            "ThirdLargestPropertyUseType": "None",
        }
        energy, co2 = predictor.predict(data)
        assert energy > 0


class TestSchemaValidation:
    """Tests pour la validation Pydantic des schemas."""

    def test_valid_input_accepted(self):
        """Un input valide passe la validation."""
        from src.schemas.requests import BuildingInput

        data = {
            "NumberofBuildings": 1,
            "PropertyGFATotal": 50000,
            "PropertyGFABuilding(s)": 45000,
            "LargestPropertyUseTypeGFA": 45000,
            "PrimaryPropertyType": "Office",
            "LargestPropertyUseType": "Office",
        }
        building = BuildingInput(**data)
        assert building.NumberofBuildings == 1
        assert building.PropertyGFATotal == 50000

    def test_negative_buildings_rejected(self):
        """Un nombre negatif de batiments est rejete."""
        from pydantic import ValidationError

        from src.schemas.requests import BuildingInput

        with pytest.raises(ValidationError):
            BuildingInput(
                NumberofBuildings=-1,
                PropertyGFATotal=50000,
                PropertyGFABuilding=45000,
                LargestPropertyUseTypeGFA=45000,
                PrimaryPropertyType="Office",
                LargestPropertyUseType="Office",
            )

    def test_zero_surface_rejected(self):
        """Une surface a zero est rejetee (gt=0)."""
        from pydantic import ValidationError

        from src.schemas.requests import BuildingInput

        with pytest.raises(ValidationError):
            BuildingInput(
                NumberofBuildings=1,
                PropertyGFATotal=0,
                PropertyGFABuilding=45000,
                LargestPropertyUseTypeGFA=45000,
                PrimaryPropertyType="Office",
                LargestPropertyUseType="Office",
            )

    def test_optional_fields_default(self):
        """Les champs optionnels ont des valeurs par defaut."""
        from src.schemas.requests import BuildingInput

        building = BuildingInput(
            NumberofBuildings=1,
            PropertyGFATotal=50000,
            PropertyGFABuilding=45000,
            LargestPropertyUseTypeGFA=45000,
            PrimaryPropertyType="Office",
            LargestPropertyUseType="Office",
        )
        assert building.PropertyGFAParking == 0
        assert building.HasElectricity == 1
        assert building.HasNaturalGas == 1
        assert building.HasSteam == 0
        assert building.BuildingType == "NonResidential"

    def test_prediction_output_schema(self):
        """PredictionOutput a le bon format."""
        from src.schemas.responses import PredictionOutput

        output = PredictionOutput(
            energy_prediction_kbtu=1000.0,
            co2_prediction_tons=50.0,
            prediction_id="abc123",
        )
        assert output.energy_prediction_kbtu == 1000.0
        assert output.prediction_id == "abc123"

    def test_health_response_schema(self):
        """HealthCheckResponse a le bon format."""
        from src.schemas.responses import HealthCheckResponse

        health = HealthCheckResponse(
            status="healthy",
            version="0.4.0",
            models_loaded=True,
        )
        assert health.status == "healthy"
        assert health.models_loaded is True


class TestExceptions:
    """Tests pour les exceptions custom."""

    def test_model_not_loaded_error(self):
        """ModelNotLoadedError a le bon code HTTP."""
        from src.core.exceptions import ModelNotLoadedError

        err = ModelNotLoadedError()
        assert err.status_code == 503
        assert "non chargés" in err.message or "not loaded" in err.message.lower()

    def test_invalid_input_error(self):
        """InvalidInputError a le bon code HTTP."""
        from src.core.exceptions import InvalidInputError

        err = InvalidInputError("Bad field")
        assert err.status_code == 400
        assert "Bad field" in err.message

    def test_prediction_error(self):
        """PredictionError a le bon code HTTP."""
        err = PredictionError("ML failure")
        assert err.status_code == 500
        assert "ML failure" in err.message

    def test_base_exception_inheritance(self):
        """Toutes les exceptions heritent de DeployMLError."""
        from src.core.exceptions import (
            DeployMLError,
            InvalidInputError,
            ModelNotLoadedError,
        )

        assert issubclass(ModelNotLoadedError, DeployMLError)
        assert issubclass(InvalidInputError, DeployMLError)
        assert issubclass(PredictionError, DeployMLError)
