"""Integration test fixtures."""
from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.app.extensions import db


@pytest.fixture(scope="session")
def engine():
    # Use an in-memory SQLite database for tests
    engine = create_engine("sqlite:///:memory:")
    # Create all tables (requires models to be imported)
    from src.domains.accounts.repositories.sql.orms import account_model, account_role_model, credential_model
    db.Model.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def uow_factory(engine):
    # A session factory bound to the test engine
    return sessionmaker(bind=engine)
