"""Tests pour la couche base de données.

Valide les modèles ORM, l'insertion du dataset,
et l'enregistrement des prédictions.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.db.models import Base, Building, Prediction


def _create_session():
    """Helper : crée une session SQLite en mémoire."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine)
    return session_factory(), engine


class TestBuildingModel:
    """Tests pour le modèle Building."""

    def test_create_building(self, db_session):
        """Test l'insertion d'un bâtiment."""
        building = Building(
            ose_building_id=1,
            data_year=2016,
            building_type="NonResidential",
            primary_property_type="Office",
            property_name="Test Building",
            property_gfa_total=50000,
            site_energy_use=2500000.0,
            total_ghg_emissions=120.5,
        )
        db_session.add(building)
        db_session.commit()

        result = db_session.query(Building).first()
        assert result is not None
        assert result.ose_building_id == 1
        assert result.primary_property_type == "Office"
        assert result.property_gfa_total == 50000
        assert result.site_energy_use == 2500000.0

    def test_building_unique_ose_id(self, db_session):
        """Test la contrainte d'unicité OSEBuildingID."""
        b1 = Building(
            ose_building_id=42,
            data_year=2016,
            building_type="NonResidential",
            primary_property_type="Office",
        )
        b2 = Building(
            ose_building_id=42,
            data_year=2016,
            building_type="NonResidential",
            primary_property_type="Hotel/Motel",
        )
        db_session.add(b1)
        db_session.commit()
        db_session.add(b2)

        import pytest
        from sqlalchemy.exc import IntegrityError

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_building_repr(self, db_session):
        """Test la représentation string du modèle."""
        building = Building(
            ose_building_id=99,
            data_year=2016,
            building_type="NonResidential",
            primary_property_type="Office",
            property_name="My Building",
        )
        assert "99" in repr(building)
        assert "My Building" in repr(building)

    def test_bulk_insert_buildings(self, db_session):
        """Test l'insertion en masse de bâtiments."""
        buildings = [
            Building(
                ose_building_id=i,
                data_year=2016,
                building_type="NonResidential",
                primary_property_type="Office",
                property_name=f"Building {i}",
            )
            for i in range(1, 51)
        ]
        db_session.add_all(buildings)
        db_session.commit()

        count = db_session.query(Building).count()
        assert count == 50


class TestPredictionModel:
    """Tests pour le modèle Prediction."""

    def test_create_prediction(self, db_session):
        """Test l'insertion d'une prédiction."""
        prediction = Prediction(
            number_of_buildings=1,
            property_gfa_total=50000.0,
            property_gfa_building=45000.0,
            largest_property_use_type_gfa=45000.0,
            primary_property_type="Office",
            building_type="NonResidential",
            energy_prediction_kbtu=2500000.0,
            co2_prediction_tons=120.5,
            prediction_duration_ms=15.3,
            source="test",
        )
        db_session.add(prediction)
        db_session.commit()

        result = db_session.query(Prediction).first()
        assert result is not None
        assert result.energy_prediction_kbtu == 2500000.0
        assert result.co2_prediction_tons == 120.5
        assert result.prediction_duration_ms == 15.3
        assert result.source == "test"
        assert result.id is not None
        assert result.created_at is not None

    def test_prediction_with_building_relation(self, db_session):
        """Test la relation prédiction → bâtiment."""
        building = Building(
            ose_building_id=1,
            data_year=2016,
            building_type="NonResidential",
            primary_property_type="Office",
        )
        db_session.add(building)
        db_session.commit()

        prediction = Prediction(
            building_id=building.id,
            number_of_buildings=1,
            property_gfa_total=50000.0,
            property_gfa_building=45000.0,
            largest_property_use_type_gfa=45000.0,
            energy_prediction_kbtu=2500000.0,
            co2_prediction_tons=120.5,
        )
        db_session.add(prediction)
        db_session.commit()

        # Vérifier la relation
        result = db_session.query(Prediction).first()
        assert result.building_id == building.id

        # Vérifier la relation inverse
        db_session.refresh(building)
        assert len(building.predictions) == 1
        assert building.predictions[0].energy_prediction_kbtu == 2500000.0

    def test_prediction_without_building(self, db_session):
        """Test qu'une prédiction peut exister sans bâtiment lié."""
        prediction = Prediction(
            number_of_buildings=1,
            property_gfa_total=50000.0,
            property_gfa_building=45000.0,
            largest_property_use_type_gfa=45000.0,
            energy_prediction_kbtu=2500000.0,
            co2_prediction_tons=120.5,
        )
        db_session.add(prediction)
        db_session.commit()

        result = db_session.query(Prediction).first()
        assert result.building_id is None

    def test_multiple_predictions(self, db_session):
        """Test l'insertion de plusieurs prédictions."""
        for i in range(5):
            pred = Prediction(
                number_of_buildings=1,
                property_gfa_total=50000.0 + i * 10000,
                property_gfa_building=45000.0,
                largest_property_use_type_gfa=45000.0,
                energy_prediction_kbtu=2500000.0 + i * 100000,
                co2_prediction_tons=120.5 + i * 10,
                source="test",
            )
            db_session.add(pred)

        db_session.commit()
        count = db_session.query(Prediction).count()
        assert count == 5


class TestSchemaCreation:
    """Tests pour la création du schéma."""

    def test_tables_created(self):
        """Vérifie que les tables sont créées correctement."""
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=engine)

        from sqlalchemy import inspect

        inspector = inspect(engine)
        tables = inspector.get_table_names()

        assert "buildings" in tables
        assert "predictions" in tables

    def test_buildings_columns(self):
        """Vérifie les colonnes de la table buildings."""
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=engine)

        from sqlalchemy import inspect

        inspector = inspect(engine)
        columns = {c["name"] for c in inspector.get_columns("buildings")}

        expected = {
            "id",
            "ose_building_id",
            "data_year",
            "building_type",
            "primary_property_type",
            "property_name",
            "site_energy_use",
            "total_ghg_emissions",
            "property_gfa_total",
            "latitude",
            "longitude",
        }
        assert expected.issubset(columns)

    def test_predictions_columns(self):
        """Vérifie les colonnes de la table predictions."""
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=engine)

        from sqlalchemy import inspect

        inspector = inspect(engine)
        columns = {c["name"] for c in inspector.get_columns("predictions")}

        expected = {
            "id",
            "created_at",
            "building_id",
            "number_of_buildings",
            "property_gfa_total",
            "energy_prediction_kbtu",
            "co2_prediction_tons",
            "prediction_duration_ms",
            "source",
        }
        assert expected.issubset(columns)
