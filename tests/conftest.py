"""Global test fixtures."""
from __future__ import annotations

import pytest
from flask import Flask
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.app import create_app
from src.app.extensions import db
from src.app.uow import REPOSITORY_CLASSES
from src.core.events.dispatcher import EventDispatcher
from src.core.repositories.sql.sql_uow import SqlUnitOfWork
from src.core.services.base_service import SupportsPermissionCheck


@pytest.fixture(scope="session")
def engine():
    # Use an in-memory SQLite database for tests
    from src.config.testing import TestingConfig
    engine = create_engine(TestingConfig().DATABASE_URL)
    # Import ALL domain ORM models to ensure they are registered with metadata
    import src.domains.accounts.repositories.sql.orms  # noqa: F401
    import src.domains.rbac.repositories.sql.orms  # noqa: F401
    import src.domains.catalog.repositories.sql.orms  # noqa: F401
    import src.domains.stock.repositories.sql.orms  # noqa: F401
    import src.domains.sale.repositories.sql.orms  # noqa: F401

    db.Model.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def uow_factory(engine):
    # A session factory bound to the test engine
    session_factory = sessionmaker(bind=engine)
    dispatcher = EventDispatcher()
    
    def factory():
        return SqlUnitOfWork(session_factory, dispatcher, REPOSITORY_CLASSES)
        
    return factory


@pytest.fixture
def app(engine, monkeypatch):
    from src.config.testing import TestingConfig
    import redis
    test_redis = redis.from_url(TestingConfig().REDIS_URL, decode_responses=True)
    test_redis.flushdb()
    # Create the Flask app in testing mode
    app = create_app("testing")
    
    # Override the database session for tests
    session_factory = sessionmaker(bind=engine)
    dispatcher = EventDispatcher()
    
    def test_uow_factory():
        return SqlUnitOfWork(session_factory, dispatcher, REPOSITORY_CLASSES)
        
    from src.app.domain_service_builder import build_domain_service
    test_domain_service = build_domain_service(test_uow_factory, test_redis, dispatcher)
    app.extensions["domain_service"] = test_domain_service
    
    from src.app import register_domain_event_handlers
    register_domain_event_handlers(dispatcher, test_domain_service)
    
    yield app


@pytest.fixture
def client(app: Flask):
    return app.test_client()


class MockActor(SupportsPermissionCheck):
    def __init__(self, allowed_permissions: set[str] | None = None):
        self.allowed_permissions = allowed_permissions or set()

    def has_permission(self, domain: str, entity: str, action: str) -> bool:
        if "*" in self.allowed_permissions:
            return True
        perm = f"{domain}:{entity}:{action}"
        return perm in self.allowed_permissions


@pytest.fixture
def mock_actor():
    # Returns an actor with all permissions by default
    return MockActor(allowed_permissions={"*"})
