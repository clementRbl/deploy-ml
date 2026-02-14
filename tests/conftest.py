"""Configuration des fixtures de test.

Fournit une session SQLite en mémoire pour les tests DB
et un client FastAPI avec les dépendances mockées.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.db.models import Base


@pytest.fixture
def db_session():
    """Crée une session SQLite en mémoire pour les tests."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    test_session_factory = sessionmaker(bind=engine)
    session = test_session_factory()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
