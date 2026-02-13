import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from src.core.exceptions import ModelNotLoadedError, PredictionError
from src.core.logging import logger


class ModelPredictor:
    """Gère le chargement et l'utilisation des modèles ML."""

    def __init__(self, models_dir: Path = None):
        """Initialise le prédicteur et charge les modèles."""
        if models_dir is None:
            models_dir = Path(__file__).parent.parent / "models"

        self.models_dir = models_dir
        self.energy_model = None
        self.co2_model = None
        self.metadata = None
        self._load_models()

    def _load_models(self) -> None:
        """Charge les modèles et métadonnées depuis les fichiers."""
        try:
            # Charger les modèles
            self.energy_model = joblib.load(self.models_dir / "energy_model.joblib")
            self.co2_model = joblib.load(self.models_dir / "co2_model.joblib")

            # Charger les métadonnées
            with open(self.models_dir / "model_metadata.json") as f:
                self.metadata = json.load(f)

            logger.info("Modèles chargés avec succès")
            logger.info(f"   - Energy: {self.metadata['energy_model']['algorithm']}")
            logger.info(f"   - CO2: {self.metadata['co2_model']['algorithm']}")

        except Exception as e:
            logger.error(f"Erreur lors du chargement des modèles: {e}")
            raise ModelNotLoadedError(f"Failed to load models: {e}")

    def _prepare_features(self, data: dict) -> pd.DataFrame:
        """Prépare les features pour la prédiction."""
        # Calculer les features dérivées si non fournies
        if data.get("HasMultipleBuildings") is None:
            data["HasMultipleBuildings"] = 1 if data["NumberofBuildings"] > 1 else 0

        if data.get("FloorsPerBuilding") is None:
            n_floors = data.get("NumberofFloors", 5.0)
            n_buildings = data["NumberofBuildings"]
            data["FloorsPerBuilding"] = (
                n_floors / n_buildings if n_buildings > 0 and n_floors else 0
            )

        if data.get("HasSecondaryUse") is None:
            data["HasSecondaryUse"] = 0 if data["SecondLargestPropertyUseType"] == "None" else 1

        if data.get("SurfaceGasInteraction") is None:
            data["SurfaceGasInteraction"] = data["PropertyGFATotal"] * data.get("HasNaturalGas", 1)

        if data.get("DistanceToCenter") is None:
            # Valeur par défaut si non fournie (centre de Seattle)
            data["DistanceToCenter"] = 3.5

        if data.get("BuildingAge") is None:
            # Valeur par défaut si non fournie
            data["BuildingAge"] = 20

        # Gérer l'alias PropertyGFABuilding -> PropertyGFABuilding(s)
        if "PropertyGFABuilding" in data and "PropertyGFABuilding(s)" not in data:
            data["PropertyGFABuilding(s)"] = data.pop("PropertyGFABuilding")

        # Assurer que NumberofFloors a une valeur par défaut
        if data.get("NumberofFloors") is None:
            data["NumberofFloors"] = 5.0  # Moyenne observée dans le dataset

        return pd.DataFrame([data])

    def predict(self, building_data: dict) -> tuple[float, float]:
        """Prédit la consommation énergétique et les émissions CO2.

        Args:
            building_data: Dictionnaire contenant les features du bâtiment

        Returns:
            Tuple (energy_kbtu, co2_tons)

        Raises:
            ModelNotLoadedError: Si les modèles ne sont pas chargés
            PredictionError: Si une erreur survient lors de la prédiction
        """
        if not self.is_loaded():
            raise ModelNotLoadedError()

        try:
            # Préparer les données pour le modèle énergie
            features_energy = self._prepare_features(building_data.copy())

            # Prédiction énergie (modèle prédit en log, on inverse)
            energy_log = self.energy_model.predict(features_energy)[0]
            energy_kbtu = np.expm1(energy_log)

            # Préparer les données pour le modèle CO2 (ajouter l'énergie prédite)
            features_co2 = features_energy.copy()
            features_co2["SiteEnergyUse(kBtu)"] = energy_kbtu
            features_co2["EnergyPerSurface"] = energy_kbtu / building_data["PropertyGFATotal"]

            # Prédiction CO2 (modèle prédit en log, on inverse)
            co2_log = self.co2_model.predict(features_co2)[0]
            co2_tons = np.expm1(co2_log)

            logger.debug(f"Prédiction réussie: {energy_kbtu:.2f} kBtu, {co2_tons:.2f} tons CO2")
            return float(energy_kbtu), float(co2_tons)

        except Exception as e:
            logger.error(f"Erreur lors de la prédiction: {e}")
            raise PredictionError(str(e))

    def is_loaded(self) -> bool:
        """Vérifie si les modèles sont chargés."""
        return self.energy_model is not None and self.co2_model is not None


# Instance globale du prédicteur (chargée au démarrage de l'app)
_predictor_instance = None


def get_predictor() -> ModelPredictor:
    """Retourne l'instance du prédicteur (singleton pattern)."""
    global _predictor_instance
    if _predictor_instance is None:
        _predictor_instance = ModelPredictor()
    return _predictor_instance
