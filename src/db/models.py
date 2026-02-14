"""Modèles SQLAlchemy pour la base de données.

Tables :
- buildings : données du dataset Seattle Energy Benchmarking
- predictions : historique des prédictions (inputs + outputs)
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    """Classe de base pour tous les modèles SQLAlchemy."""


class Building(Base):
    """Table des bâtiments du dataset Seattle 2016.

    Stocke les données brutes du fichier CSV pour traçabilité
    et requêtes analytiques.
    """

    __tablename__ = "buildings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ose_building_id = Column(Integer, unique=True, nullable=False, index=True)
    data_year = Column(Integer, nullable=False)

    # Identification
    building_type = Column(String(100), nullable=False)
    primary_property_type = Column(String(200), nullable=False)
    property_name = Column(String(500))
    address = Column(String(500))
    city = Column(String(100))
    state = Column(String(10))
    zip_code = Column(String(10))
    neighborhood = Column(String(200))

    # Géolocalisation
    latitude = Column(Float)
    longitude = Column(Float)

    # Caractéristiques physiques
    year_built = Column(Integer)
    number_of_buildings = Column(Float)
    number_of_floors = Column(Integer)
    property_gfa_total = Column(Integer)
    property_gfa_parking = Column(Integer)
    property_gfa_building = Column(Integer)

    # Usages
    list_of_all_property_use_types = Column(Text)
    largest_property_use_type = Column(String(200))
    largest_property_use_type_gfa = Column(Float)
    second_largest_property_use_type = Column(String(200))
    second_largest_property_use_type_gfa = Column(Float)
    third_largest_property_use_type = Column(String(200))
    third_largest_property_use_type_gfa = Column(Float)

    # Performance énergétique
    energy_star_score = Column(Float)
    site_eui = Column(Float)
    site_eui_wn = Column(Float)
    source_eui = Column(Float)
    source_eui_wn = Column(Float)
    site_energy_use = Column(Float)
    site_energy_use_wn = Column(Float)

    # Consommation par type
    steam_use = Column(Float)
    electricity_kwh = Column(Float)
    electricity_kbtu = Column(Float)
    natural_gas_therms = Column(Float)
    natural_gas_kbtu = Column(Float)

    # Émissions
    total_ghg_emissions = Column(Float)
    ghg_emissions_intensity = Column(Float)

    # Métadonnées
    default_data = Column(Boolean)
    compliance_status = Column(String(100))
    outlier = Column(String(200))

    # Relation avec les prédictions
    predictions = relationship("Prediction", back_populates="building")

    def __repr__(self) -> str:  # noqa: D105
        return f"<Building(id={self.ose_building_id}, name='{self.property_name}')>"


class Prediction(Base):
    """Table des prédictions ML.

    Enregistre chaque appel à l'API de prédiction :
    - Inputs envoyés au modèle
    - Outputs générés (énergie + CO2)
    - Métadonnées (timestamp, durée, source)

    Assure la traçabilité complète des interactions avec le modèle.
    """

    __tablename__ = "predictions"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Lien optionnel vers un bâtiment existant
    building_id = Column(Integer, ForeignKey("buildings.id"), nullable=True)

    # --- Inputs du modèle ---
    # Features numériques
    number_of_buildings = Column(Integer, nullable=False)
    number_of_floors = Column(Float)
    property_gfa_total = Column(Float, nullable=False)
    property_gfa_parking = Column(Float)
    property_gfa_building = Column(Float, nullable=False)
    largest_property_use_type_gfa = Column(Float, nullable=False)
    second_largest_property_use_type_gfa = Column(Float)
    third_largest_property_use_type_gfa = Column(Float)

    # Features dérivées
    building_age = Column(Integer)
    has_multiple_buildings = Column(Integer)
    floors_per_building = Column(Float)
    has_secondary_use = Column(Integer)
    distance_to_center = Column(Float)
    has_electricity = Column(Integer)
    has_natural_gas = Column(Integer)
    has_steam = Column(Integer)
    surface_gas_interaction = Column(Float)

    # Features catégorielles
    building_type = Column(String(100))
    primary_property_type = Column(String(200))
    largest_property_use_type = Column(String(200))
    second_largest_property_use_type = Column(String(200))
    third_largest_property_use_type = Column(String(200))

    # --- Outputs du modèle ---
    energy_prediction_kbtu = Column(Float, nullable=False)
    co2_prediction_tons = Column(Float, nullable=False)

    # --- Métadonnées ---
    prediction_duration_ms = Column(Float)
    source = Column(String(50), default="api")

    # Relation
    building = relationship("Building", back_populates="predictions")

    def __repr__(self) -> str:  # noqa: D105
        return (
            f"<Prediction(id={self.id}, "
            f"energy={self.energy_prediction_kbtu:.0f} kBtu, "
            f"co2={self.co2_prediction_tons:.2f} t)>"
        )
