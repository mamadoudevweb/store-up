"""Unit tests for sale-domain wiring in the application composition root."""
from __future__ import annotations

from unittest.mock import MagicMock

from flask import Flask

from src.app import register_domain_event_handlers
from src.app.docs import register_openapi
from src.app.domain_service import DomainService
from src.app.domain_service_builder import build_domain_service
from src.app.routes import register_routes
from src.app.uow import REPOSITORY_CLASSES
from src.core.events.dispatcher import EventDispatcher
from src.domains.sale.events import RefundRequested, SaleReturned
from src.domains.sale.repositories.sql.refund_repository import SqlRefundRepository
from src.domains.sale.repositories.sql.sale_repository import SqlSaleRepository
from src.domains.sale.services import RefundService, SaleDomainService, SaleService


def test_repository_classes_include_sale_domain():
    assert REPOSITORY_CLASSES["sales"] is SqlSaleRepository
    assert REPOSITORY_CLASSES["refunds"] is SqlRefundRepository


def test_build_domain_service_wires_sale_domain_service():
    uow_factory = lambda: None  # noqa: E731
    redis_client = MagicMock()
    dispatcher = EventDispatcher()

    domain_service = build_domain_service(uow_factory, redis_client, dispatcher)

    assert isinstance(domain_service, DomainService)
    assert isinstance(domain_service.sale, SaleDomainService)
    assert isinstance(domain_service.sale.sale, SaleService)
    assert isinstance(domain_service.sale.refund, RefundService)
    # The sale services share the same uow_factory that was passed in.
    assert domain_service.sale.sale._uow_factory is uow_factory
    assert domain_service.sale.refund._uow_factory is uow_factory


def test_register_routes_registers_sale_and_refund_blueprints():
    app = Flask(__name__)
    register_routes(app)

    assert "sales" in app.blueprints
    assert "refunds" in app.blueprints

    rules = {rule.rule for rule in app.url_map.iter_rules()}
    assert "/api/v1/sales/checkout" in rules
    assert "/api/v1/sales/<uuid:sale_id>/complete" in rules
    assert "/api/v1/sales/<uuid:sale_id>/fail" in rules
    assert "/api/v1/refunds" in rules


def test_register_openapi_registers_sale_paths():
    app = Flask(__name__)
    register_openapi(app)

    from src.core.docs.openapi_registry import spec

    paths = spec.to_dict()["paths"]
    assert "/api/v1/sales/checkout" in paths
    assert "post" in paths["/api/v1/sales/checkout"]
    assert "/api/v1/refunds" in paths
    assert "post" in paths["/api/v1/refunds"]
    assert "docs" in app.blueprints


def test_register_domain_event_handlers_subscribes_sale_events():
    dispatcher = EventDispatcher()
    domain_service_mock = MagicMock()

    register_domain_event_handlers(dispatcher, domain_service_mock)

    assert len(dispatcher._handlers) > 0