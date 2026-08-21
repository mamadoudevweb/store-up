"""Unit tests for core services."""
from __future__ import annotations

import pytest

from src.core.services.base_service import BaseService, SupportsPermissionCheck
from src.core.services.errors import PermissionDeniedError
from src.core.services.result import ServiceResult


class MockActor(SupportsPermissionCheck):
    def __init__(self, allowed_permissions: set[str] | None = None):
        self.allowed_permissions = allowed_permissions or set()

    def has_permission(self, domain: str, entity: str, action: str) -> bool:
        perm = f"{domain}:{entity}:{action}"
        return perm in self.allowed_permissions


class DummyService(BaseService):
    def test_authorize(self, actor: SupportsPermissionCheck, domain: str, entity: str, action: str):
        self._authorize(actor, domain, entity, action)


def test_service_result():
    res = ServiceResult(data="test", meta={"count": 1})
    assert res.data == "test"
    assert res.meta == {"count": 1}
    assert res.success is True  # Assuming success property exists or just checking properties


def test_base_service_authorize_success():
    # Setup UoW factory is None because we don't use it in this unit test
    service = DummyService(lambda: None)  # type: ignore
    
    actor = MockActor(allowed_permissions={"catalog:product:create"})
    
    # Should not raise
    service.test_authorize(actor, "catalog", "product", "create")


def test_base_service_authorize_denied():
    service = DummyService(lambda: None)  # type: ignore
    
    actor = MockActor(allowed_permissions={"catalog:product:read"})
    
    # Should raise PermissionDeniedError
    with pytest.raises(PermissionDeniedError) as exc_info:
        service.test_authorize(actor, "catalog", "product", "create")
        
    assert exc_info.value.details["domain"] == "catalog"
    assert exc_info.value.details["entity"] == "product"
    assert exc_info.value.details["action"] == "create"
