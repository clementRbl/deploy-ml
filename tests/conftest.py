"""Configuration des fixtures de test.

Fournit une session SQLite en memoire pour les tests DB
et un client FastAPI avec les dependances mockees.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.db.database import get_db
from src.db.models import Base
from src.services.predictor import get_predictor


@pytest.fixture
def db_session():
    """Cree une session SQLite en memoire pour les tests."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    test_session_factory = sessionmaker(bind=engine)
    session = test_session_factory()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture
def client():
    """Client de test FastAPI avec DB SQLite en memoire."""
    from src.api.main import app

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    test_session_factory = sessionmaker(bind=engine)

    def override_get_db():
        session = test_session_factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as c:
        c._test_session_factory = test_session_factory
        yield c

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture
def predictor():
    """Instance reelle du predictor (modeles charges).

    Skip automatiquement si les modeles ne sont pas disponibles.
    """
    p = get_predictor()
    if not p.is_loaded():
        pytest.skip("ML models (.joblib) not available (CI environment)")
    return p


@pytest.fixture
def valid_building_input():
    """Payload valide pour une prediction (avec alias pour l'API)."""
    return {
        "NumberofBuildings": 1,
        "NumberofFloors": 5,
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


@pytest.fixture
def minimal_building_input():
    """Payload minimal (seuls les champs requis)."""
    return {
        "NumberofBuildings": 1,
        "PropertyGFATotal": 30000,
        "PropertyGFABuilding(s)": 28000,
        "LargestPropertyUseTypeGFA": 28000,
        "PrimaryPropertyType": "Office",
        "LargestPropertyUseType": "Office",
    }
