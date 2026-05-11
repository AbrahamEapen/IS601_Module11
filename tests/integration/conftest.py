# tests/integration/conftest.py
"""
Fixtures for DB-backed integration tests.
Uses a transaction-per-test approach: every test runs inside a transaction
that is rolled back after the test, keeping the DB clean without needing
teardown logic in individual tests.
"""

import os
import uuid
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import User  # noqa: F401 – ensures User table is registered

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://user:password@localhost:5432/myappdb"
)


@pytest.fixture(scope="session")
def db_engine():
    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture
def db_session(db_engine):
    """Provides a transactional session that rolls back after each test."""
    connection = db_engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection)
    session = Session()
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def test_user(db_session):
    """Creates a User row inside the current test transaction."""
    user = User(
        username=f"user_{uuid.uuid4().hex[:8]}",
        email=f"test_{uuid.uuid4().hex[:8]}@example.com",
    )
    db_session.add(user)
    db_session.flush()  # assign id without committing
    return user
