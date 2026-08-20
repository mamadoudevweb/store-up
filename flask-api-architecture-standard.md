# Flask API Architecture Standard

A reusable architecture for any domain-driven Flask API — not specific to any one project. **Catalog / Product** is used throughout as the single worked example so the code is concrete; every other bounded context in a real project (Billing, Orders, Users, whatever they are) follows the exact same shape. Swap the example, keep the pattern.

---

## 1. Layering rules (non-negotiable)

- **Entities** have zero imports from repositories, services, routes, Flask, or the ORM. Plain Python (dataclasses).
- **Repositories** talk only in Entities. ORM models never leave the repository package — a **mapper** converts both ways.
- **Repositories never own a session.** They receive one from the Unit of Work, which services obtain from a `uow_factory`.
- **`core/` never imports from `domains/`.** The kernel (base classes, UoW, envelope, error base) is generic infrastructure; it has no idea Catalog or Product exist. Only the app's composition root (`app/`) wires concrete domains into the generic machinery.
- **Services** never receive raw JSON. Routes parse into a Pydantic schema first, then pass typed values/DTOs into services.
- **Services** always return `ServiceResult` on success and always **raise** a registered `AppError` subclass on failure — never return an error object.
- **Routes** do request parsing (Pydantic), call a service, serialize the result — nothing else. No business logic, no inline API documentation.
- **Cross-domain communication happens only through events** emitted by entities and dispatched by the Unit of Work on commit — domains never import each other's services directly.
- **Everything is typed.** Every function/method signature has full parameter and return annotations (PEP 604 unions, `Generic`/`TypeVar` where behavior is generic, `Protocol` where only a shape is required). CI runs `mypy` (or `pyright`) in strict mode; an untyped `def` is a review blocker, not a style nit.

---

## 2. Project layout

```
src/
  config/
    __init__.py            # get_settings(env)
    base.py                # BaseAppSettings (pydantic-settings)
    development.py
    testing.py
    production.py          # values sourced from env vars
  app/                       # composition root — the only place that knows every concrete domain
    __init__.py              # create_app() factory
    extensions.py            # Limiter, CORS instances
    middlewares.py           # domain restriction, content-type enforcement
    error_handlers.py        # AppError / 404 / 429 / 500 -> envelope
    uow.py                   # REPOSITORY_CLASSES map + build_uow_factory()
    domain_service.py        # DomainService facade + build_domain_service()
    routes.py                # imports & registers every blueprint
    docs.py                  # imports & registers every openapi/*.py, serves docs
  core/                       # shared kernel — generic, no knowledge of any domain
    entities/
      base_entity.py
      events.py
      pagination.py
    events/
      dispatcher.py
    repositories/
      base_repository.py
      base_uow.py
      utils.py                # Mapper protocol
      sql/
        base_sql_repository.py
        sql_uow.py             # domain-agnostic — repository set is injected
    services/
      base_service.py
      result.py                # ServiceResult
      errors.py                 # AppError base, self-registering
    routes/
      envelope.py               # ok()/fail() response envelope
    docs/
      openapi_registry.py       # shared APISpec instance
      docs_blueprint.py         # serves /openapi.json and Swagger UI
  domains/
    catalog/                    # ── worked example — one bounded context ──
      entities/
        product.py
        events.py
        filters.py               # ProductFilter(EntityFilter)
      exceptions.py              # domain-specific AppError subclasses
      repositories/
        sql/
          mappers.py
          sql_product_repository.py
      services/
        product_service.py
        catalog_domain_service.py   # aggregates every entity service in this domain
      routes/
        v1/
          schemas/
            product_schema.py
          openapi/
            product_openapi.py
          product_routes.py
    # ... every other bounded context in the project, same shape:
    # billing/, orders/, users/, whatever your domains are
tests/
```

Every domain package mirrors the same layout: `entities/`, `exceptions.py`, `repositories/sql/`, `services/`, `routes/v1/{schemas,openapi}/`. Inside `routes/v1/`, **one file per entity**, not one per domain — `product_routes.py` deals only with products. A domain with several entities (Catalog: Product, Brand, Category, ProductImage) gets one service file per entity plus one `<domain>_domain_service.py` that aggregates them.

---

## 3. Core kernel (domain-agnostic)

### Entity base + events

```python
# core/entities/events.py
from dataclasses import dataclass, field
from datetime import datetime, timezone

@dataclass(frozen=True, kw_only=True)
class DomainEvent:
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
```

```python
# core/entities/base_entity.py
from dataclasses import dataclass, field
from core.entities.events import DomainEvent

@dataclass(kw_only=True)
class Entity:
    """Zero dependencies on any other layer — no ORM, no Flask, no pydantic."""
    id: int | None = None
    _events: list[DomainEvent] = field(default_factory=list, repr=False, compare=False)

    def register_event(self, event: DomainEvent) -> None:
        self._events.append(event)

    def pull_events(self) -> list[DomainEvent]:
        events, self._events = self._events, []
        return events
```

Entities emit events from their own methods, e.g. `Product.create()` registers `ProductCreated`; whatever entity your domain has does the analogous thing (`Order.place()` → `OrderPlaced`, `Invoice.pay()` → `InvoicePaid`).

### Pagination & filters

```python
# core/entities/pagination.py
from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")

@dataclass(kw_only=True)
class Pagination(Generic[T]):
    items: list[T]
    page: int
    limit: int
    total: int

    @property
    def total_pages(self) -> int:
        return max(1, -(-self.total // self.limit))

@dataclass(kw_only=True)
class EntityFilter:
    page: int = 1
    limit: int = 20
    sort_by: str | None = None
    sort_desc: bool = False
```

Each entity subclasses `EntityFilter` (e.g. `ProductFilter(search, category_id, brand_id)`).

### Repository contract

```python
# core/repositories/base_repository.py
from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar
from core.entities.base_entity import Entity
from core.entities.pagination import Pagination, EntityFilter

E = TypeVar("E", bound=Entity)
F = TypeVar("F", bound=EntityFilter)
EntityId = int

class BaseRepository(ABC, Generic[E, F]):
    """Repositories never own a session — it's injected by the UoW.
    No business logic here: execute and query only."""

    @abstractmethod
    def add(self, entity: E) -> E: ...

    @abstractmethod
    def get(self, criteria: EntityId | F) -> E | None:
        """Fetch a single entity — either by primary key (EntityId) or by
        an EntityFilter when the lookup is by some other criteria (e.g. a
        unique sku, an email). If a filter matches more than one row, the
        first by the query's natural order is returned; use list() when
        you actually want every match."""
        ...

    @abstractmethod
    def list(self, entity_filter: F) -> Pagination[E]: ...

    @abstractmethod
    def update(self, entity: E) -> E: ...

    @abstractmethod
    def delete(self, entity: E) -> None: ...

    @abstractmethod
    def _apply_filter(self, query: Any, entity_filter: F) -> Any:
        """Translate an EntityFilter into ORM query clauses only."""
        ...
```

### Unit of Work contract

```python
# core/repositories/base_uow.py
from abc import ABC, abstractmethod
from types import TracebackType

class BaseUnitOfWork(ABC):
    """Owns the transaction boundary and aggregates every repository.
    Services obtain a UoW from a factory; repositories never open sessions."""

    def __enter__(self) -> "BaseUnitOfWork":
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        if exc_type is not None:
            self.rollback()
        else:
            self.commit()

    @abstractmethod
    def commit(self) -> None: ...

    @abstractmethod
    def rollback(self) -> None: ...
```

### Mapper (entity ⟷ ORM model)

```python
# core/repositories/utils.py
from typing import Protocol, TypeVar
from core.entities.base_entity import Entity

E = TypeVar("E", bound=Entity)
M = TypeVar("M")

class Mapper(Protocol[E, M]):
    def to_entity(self, model: M) -> E: ...
    def to_model(self, entity: E, model: M | None = None) -> M: ...
```

Each domain provides one mapper per aggregate, e.g. `domains/catalog/repositories/sql/mappers.py: ProductMapper`.

### Generic SQL repository

```python
# core/repositories/sql/base_sql_repository.py
from typing import Any
from sqlalchemy import select, func
from sqlalchemy.sql import Select
from sqlalchemy.orm import Session
from core.repositories.base_repository import BaseRepository, EntityId, E, F
from core.repositories.utils import Mapper
from core.entities.pagination import Pagination

class BaseSqlRepository(BaseRepository[E, F]):
    model: type[Any]           # ORM model class — set by subclass
    mapper: Mapper[E, Any]      # Mapper instance — set by subclass
    filter_cls: type[F]         # the EntityFilter subclass this repo accepts — set by subclass

    def __init__(self, session: Session) -> None:
        self._session: Session = session   # injected, never owned

    def add(self, entity: E) -> E:
        model = self.mapper.to_model(entity)
        self._session.add(model)
        self._session.flush()
        return self.mapper.to_entity(model)

    def get(self, criteria: EntityId | F) -> E | None:
        if isinstance(criteria, self.filter_cls):
            query = self._apply_filter(select(self.model), criteria)
            model = self._session.scalars(query.limit(1)).first()
        else:
            model = self._session.get(self.model, criteria)   # criteria is an EntityId
        return self.mapper.to_entity(model) if model else None

    def list(self, entity_filter: F) -> Pagination[E]:
        query = self._apply_filter(select(self.model), entity_filter)
        total: int = self._session.scalar(select(func.count()).select_from(query.subquery())) or 0
        query = query.limit(entity_filter.limit).offset((entity_filter.page - 1) * entity_filter.limit)
        models = self._session.scalars(query).all()
        return Pagination(
            items=[self.mapper.to_entity(m) for m in models],
            page=entity_filter.page, limit=entity_filter.limit, total=total,
        )

    def update(self, entity: E) -> E:
        model = self._session.get(self.model, entity.id)
        model = self.mapper.to_model(entity, model)
        self._session.flush()
        return self.mapper.to_entity(model)

    def delete(self, entity: E) -> None:
        model = self._session.get(self.model, entity.id)
        if model:
            self._session.delete(model)
            self._session.flush()

    def _apply_filter(self, query: Select[Any], entity_filter: F) -> Select[Any]:
        raise NotImplementedError
```

Worked example:

```python
# domains/catalog/repositories/sql/sql_product_repository.py
from typing import Any
from sqlalchemy.sql import Select
from core.repositories.sql.base_sql_repository import BaseSqlRepository
from domains.catalog.entities.product import Product
from domains.catalog.entities.filters import ProductFilter
from domains.catalog.repositories.sql.mappers import ProductMapper
from domains.catalog.repositories.sql.models import ProductModel

class SqlProductRepository(BaseSqlRepository[Product, ProductFilter]):
    model = ProductModel
    mapper = ProductMapper()
    filter_cls = ProductFilter

    def _apply_filter(self, query: Select[Any], f: ProductFilter) -> Select[Any]:
        if f.search:
            query = query.where(ProductModel.name.ilike(f"%{f.search}%"))
        if f.category_id:
            query = query.where(ProductModel.category_id == f.category_id)
        if getattr(f, "sku", None):
            query = query.where(ProductModel.sku == f.sku)
        if f.sort_by:
            col = getattr(ProductModel, f.sort_by)
            query = query.order_by(col.desc() if f.sort_desc else col.asc())
        return query
```

```python
uow.products.get(42)                            # by primary key
uow.products.get(ProductFilter(sku="ABC-123"))    # by unique criteria
```

### The Unit of Work — domain-agnostic, repository set injected

`core/` must not import a concrete domain, so `SqlUnitOfWork` receives the set of repositories to expose as a plain `{attribute_name: repository_class}` mapping, built by the composition root — not hardcoded here.

```python
# core/repositories/sql/sql_uow.py
from types import TracebackType
from typing import Any, Callable
from sqlalchemy.orm import Session
from core.repositories.base_uow import BaseUnitOfWork
from core.events.dispatcher import EventDispatcher
from core.entities.base_entity import Entity

class SqlUnitOfWork(BaseUnitOfWork):
    """Knows nothing about which repositories exist — the concrete set is
    injected. Adding a new domain never means editing this file."""

    def __init__(
        self,
        session_factory: Callable[[], Session],
        dispatcher: EventDispatcher,
        repository_classes: dict[str, type[Any]],
    ) -> None:
        self._session_factory = session_factory
        self._dispatcher = dispatcher
        self._repository_classes = repository_classes
        self._session: Session | None = None
        self._tracked: list[Entity] = []

    def __enter__(self) -> "SqlUnitOfWork":
        self._session = self._session_factory()
        for attr_name, repo_cls in self._repository_classes.items():
            setattr(self, attr_name, repo_cls(self._session))
        return self

    def track(self, entity: Entity) -> None:
        """Services register entities that have pending domain events so
        they get dispatched only after a successful commit."""
        self._tracked.append(entity)

    def commit(self) -> None:
        assert self._session is not None
        self._session.commit()
        for entity in self._tracked:
            for event in entity.pull_events():
                self._dispatcher.dispatch(event)
        self._tracked.clear()

    def rollback(self) -> None:
        assert self._session is not None
        self._session.rollback()
        self._tracked.clear()

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        try:
            super().__exit__(exc_type, exc, tb)
        finally:
            assert self._session is not None
            self._session.close()
```

The composition root supplies the map:

```python
# app/uow.py
from typing import Any, Callable
from sqlalchemy.orm import Session
from core.events.dispatcher import EventDispatcher
from core.repositories.sql.sql_uow import SqlUnitOfWork
from domains.catalog.repositories.sql.sql_product_repository import SqlProductRepository
# ... one import per repository, across every domain in the project

REPOSITORY_CLASSES: dict[str, type[Any]] = {
    "products": SqlProductRepository,
    # "brands": SqlBrandRepository, "orders": SqlOrderRepository, ... — one entry per repository
}

def build_uow_factory(session_factory: Callable[[], Session], dispatcher: EventDispatcher) -> Callable[[], SqlUnitOfWork]:
    return lambda: SqlUnitOfWork(session_factory, dispatcher, REPOSITORY_CLASSES)
```

Adding a domain never touches `core/` — only `REPOSITORY_CLASSES` in `app/uow.py` grows by one line per new repository.

---

## 4. Domain events (cross-domain communication)

```python
# core/events/dispatcher.py
from collections import defaultdict
from typing import Callable
from core.entities.events import DomainEvent

class EventDispatcher:
    def __init__(self) -> None:
        self._handlers: dict[type[DomainEvent], list[Callable[[DomainEvent], None]]] = defaultdict(list)

    def subscribe(self, event_type: type[DomainEvent], handler: Callable[[DomainEvent], None]) -> None:
        self._handlers[event_type].append(handler)

    def dispatch(self, event: DomainEvent) -> None:
        for handler in self._handlers[type(event)]:
            handler(event)
```

Domains subscribe to each other's events at startup — never by importing each other's services directly:

```python
# domains/<some_domain>/event_handlers.py
from typing import Any
from core.events.dispatcher import EventDispatcher
from domains.catalog.entities.events import ProductCreated

def register(dispatcher: EventDispatcher, some_domain_service: Any) -> None:
    # `Any` here stands in for that domain's own DomainService type —
    # replace with the real class, e.g. BillingDomainService.
    dispatcher.subscribe(ProductCreated, lambda e: some_domain_service.react_to_new_product(e.product_id))
```

Each domain's `event_handlers.py` (if it has one) gets called once at startup from the app factory, alongside every other domain's. This is how one domain reacts to another (e.g. "low stock" reacting to "sale recorded") without either importing the other's service.

---

## 5. Services

### ServiceResult & self-registering errors

```python
# core/services/result.py
from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")

@dataclass(frozen=True, kw_only=True)
class ServiceResult(Generic[T]):
    data: T
    meta: dict | None = None
```

```python
# core/services/errors.py
from typing import Any

class AppError(Exception):
    """Base of every error in the system. Subclassing (anywhere, including
    inside a domain package) auto-registers the error by its `code` — no
    manual registry to maintain."""
    code: str = "APP_ERROR"
    status_code: int = 400
    message: str = "An error occurred"

    _registry: dict[str, type["AppError"]] = {}

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        AppError._registry[cls.code] = cls

    def __init__(self, message: str | None = None, **details: Any) -> None:
        self.message: str = message or self.message
        self.details: dict[str, Any] = details
        super().__init__(self.message)

# Generic, cross-domain errors. Domains raise these directly when nothing
# more specific applies, or subclass them for a business-specific case.
class NotFoundError(AppError):
    code, status_code, message = "NOT_FOUND", 404, "Resource not found"

class ValidationError(AppError):
    code, status_code, message = "VALIDATION_ERROR", 422, "Invalid data"

class PermissionDeniedError(AppError):
    code, status_code, message = "PERMISSION_DENIED", 403, "Permission denied"

class ConflictError(AppError):
    code, status_code, message = "CONFLICT", 409, "Conflicting state"

ERROR_REGISTRY: dict[str, type[AppError]] = AppError._registry   # populated as domain exception modules are imported
```

### Domain-specific exceptions

Each domain owns an `exceptions.py` at its root with errors that name its actual business rules, subclassing whichever generic error fits the HTTP semantics:

```python
# domains/catalog/exceptions.py
from core.services.errors import ConflictError

class DuplicateSkuError(ConflictError):
    code, message = "CATALOG_DUPLICATE_SKU", "A product with this SKU already exists"
```

A `<DOMAIN>_` code prefix keeps codes unique across domains without any coordination — a Billing domain's `DuplicateInvoiceNumberError` would use `BILLING_DUPLICATE_INVOICE_NUMBER`, an Orders domain's `OrderAlreadyShippedError` would use `ORDERS_ALREADY_SHIPPED`, and so on.

`app/error_handlers.py`'s single `@app.errorhandler(AppError)` still catches every one of them, generic or domain-specific, because Flask dispatches error handlers by class hierarchy, and `err.code`/`err.status_code` already carry everything the envelope needs.

### Base service contract

```python
# core/services/base_service.py
from abc import ABC
from typing import Callable, Protocol
from core.services.errors import PermissionDeniedError
from core.repositories.base_uow import BaseUnitOfWork

class SupportsPermissionCheck(Protocol):
    """The only thing a service needs from whatever 'account' object the
    route passes in. Defined here, in core, as a Protocol rather than a
    concrete Account import — core still doesn't depend on the Account
    domain, it only requires this one method to exist."""
    def has_permission(self, domain: str, entity: str, action: str) -> bool: ...

class BaseService(ABC):
    def __init__(self, uow_factory: Callable[[], BaseUnitOfWork]) -> None:
        self._uow_factory = uow_factory

    def _authorize(self, account: SupportsPermissionCheck, domain: str, entity: str, action: str) -> None:
        if not account.has_permission(domain, entity, action):
            raise PermissionDeniedError(domain=domain, entity=entity, action=action)
```

### Worked example: entity-level service

```python
# domains/catalog/services/product_service.py
from core.services.base_service import BaseService, SupportsPermissionCheck
from core.services.result import ServiceResult
from core.services.errors import NotFoundError
from core.repositories.base_repository import EntityId
from core.entities.pagination import Pagination
from domains.catalog.exceptions import DuplicateSkuError
from domains.catalog.entities.product import Product
from domains.catalog.entities.filters import ProductFilter

class ProductService(BaseService):
    """Scoped to exactly one entity, so method names don't need to repeat
    'product' — the class already says that."""

    def create(
        self,
        account: SupportsPermissionCheck,
        *,
        sku: str,
        name: str,
        description: str | None,
        category_id: int,
        cost_price: int,
        sell_price: int,
    ) -> ServiceResult[Product]:
        self._authorize(account, "catalog", "product", "create")
        with self._uow_factory() as uow:
            if uow.products.get(ProductFilter(sku=sku)) is not None:
                raise DuplicateSkuError(sku=sku)
            product = Product.create(
                sku=sku, name=name, description=description,
                category_id=category_id, cost_price=cost_price, sell_price=sell_price,
            )
            product = uow.products.add(product)
            uow.track(product)
        return ServiceResult(data=product)

    def get(self, account: SupportsPermissionCheck, criteria: EntityId | ProductFilter) -> ServiceResult[Product]:
        self._authorize(account, "catalog", "product", "read")
        with self._uow_factory() as uow:
            product = uow.products.get(criteria)
        if product is None:
            raise NotFoundError(entity="Product", criteria=criteria)
        return ServiceResult(data=product)

    def list(self, account: SupportsPermissionCheck, product_filter: ProductFilter) -> ServiceResult[Pagination[Product]]:
        self._authorize(account, "catalog", "product", "read")
        with self._uow_factory() as uow:
            page = uow.products.list(product_filter)
        return ServiceResult(data=page)
```

Every other entity's service (in Catalog or any other domain) has the same shape: `create`, `get`, `list`, plus whatever verbs its business rules actually need (`change_price`, `void`, `assign_role` — short, meaningful, never `update_x_where_y`).

### Domain-level aggregator

```python
# domains/catalog/services/catalog_domain_service.py
from typing import Any

class CatalogDomainService:
    """Aggregates every entity service in this domain. Routes reach them
    through this object, e.g. domain_service().catalog.products.create(...)."""

    def __init__(self, **entity_services: Any) -> None:
        self.__dict__.update(entity_services)
```

```python
catalog = CatalogDomainService(products=ProductService(uow_factory))
# a domain with more entities just passes more kwargs:
# billing = BillingDomainService(invoices=InvoiceService(uow_factory), payments=PaymentService(uow_factory))
```

### Top-level DomainService — dynamic, no hardcoded domain list

```python
# app/domain_service.py
from typing import Any
from flask import Flask

class DomainService:
    """Aggregates every domain's DomainService. core/ and this class don't
    know the domain names in advance — the composition root supplies them."""

    def __init__(self, **domains: Any) -> None:
        self.__dict__.update(domains)

    def init_app(self, app: Flask) -> None:
        app.extensions["domain_service"] = self
```

```python
# app/domain_service_builder.py — the only place that lists every domain
from typing import Callable
from core.repositories.base_uow import BaseUnitOfWork
from app.domain_service import DomainService
from domains.catalog.services.product_service import ProductService
from domains.catalog.services.catalog_domain_service import CatalogDomainService
# ... import every other domain's entity services + its DomainService

def build_domain_service(uow_factory: Callable[[], BaseUnitOfWork]) -> DomainService:
    catalog = CatalogDomainService(products=ProductService(uow_factory))
    # billing = BillingDomainService(...), orders = OrdersDomainService(...), ...
    return DomainService(catalog=catalog)   # + billing=billing, orders=orders, ...
```

Routes reach a specific entity's methods with `domain_service().catalog.products.create(...)`, `domain_service().billing.invoices.issue(...)`, etc. — same call shape regardless of which domain.

---

## 6. Routes

### Response envelope (identical across every domain)

```python
# core/routes/envelope.py
from typing import Any
from pydantic import BaseModel

class Envelope(BaseModel):
    success: bool
    data: Any | None = None
    error: dict[str, Any] | None = None
    meta: dict[str, Any] | None = None

EnvelopeResponse = tuple[dict[str, Any], int]   # what every route/handler returns

def ok(data: Any = None, meta: dict[str, Any] | None = None, status: int = 200) -> EnvelopeResponse:
    return Envelope(success=True, data=data, meta=meta).model_dump(mode="json"), status

def fail(code: str, message: str, status: int, details: dict[str, Any] | None = None) -> EnvelopeResponse:
    return Envelope(success=False, error={"code": code, "message": message, "details": details}).model_dump(mode="json"), status
```

### Pydantic schemas (validate in, serialize out)

```python
# domains/catalog/routes/v1/schemas/product_schema.py
from pydantic import BaseModel, Field, ConfigDict

class ProductCreateSchema(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    sku: str
    name: str
    description: str | None = None
    category_id: int
    cost_price: int = Field(ge=0)
    sell_price: int = Field(ge=0)

class ProductOutSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    sku: str
    name: str
    description: str | None
    category_id: int
    cost_price: int
    sell_price: int
```

### Versioned, per-entity blueprint

```python
# domains/catalog/routes/v1/product_routes.py
from typing import TYPE_CHECKING
from flask import Blueprint, request, current_app
from core.routes.envelope import ok, EnvelopeResponse
from domains.catalog.routes.v1.schemas.product_schema import ProductCreateSchema, ProductOutSchema
from domains.catalog.entities.filters import ProductFilter

if TYPE_CHECKING:
    from app.domain_service import DomainService

bp = Blueprint("products_v1", __name__, url_prefix="/api/v1/products")

def domain_service() -> "DomainService":
    return current_app.extensions["domain_service"]

@bp.post("")
def create_product() -> EnvelopeResponse:
    payload = ProductCreateSchema.model_validate(request.get_json())
    result = domain_service().catalog.products.create(account=request.account, **payload.model_dump())
    return ok(ProductOutSchema.model_validate(result.data).model_dump(), status=201)

@bp.get("/<int:product_id>")
def get_product(product_id: int) -> EnvelopeResponse:
    result = domain_service().catalog.products.get(account=request.account, criteria=product_id)
    return ok(ProductOutSchema.model_validate(result.data).model_dump())

@bp.get("")
def list_products() -> EnvelopeResponse:
    args = request.args
    product_filter = ProductFilter(
        page=args.get("page", 1, type=int), limit=args.get("limit", 20, type=int),
        search=args.get("search"), category_id=args.get("category_id", type=int),
    )
    result = domain_service().catalog.products.list(account=request.account, product_filter=product_filter)
    page = result.data
    items = [ProductOutSchema.model_validate(p).model_dump() for p in page.items]
    return ok(items, meta={"page": page.page, "limit": page.limit, "total": page.total, "total_pages": page.total_pages})
```

Every other entity gets its own file the same shape — its own blueprint, its own prefix, scoped to exactly one entity. Routes never touch a UoW or a repository directly — only `domain_service()`.

---

## 7. API documentation (OpenAPI) — kept out of route code entirely

Route functions carry **no** doc decorators and **no** docstrings used for docs. Documentation lives in its own `openapi/` package per domain, built with `apispec` from the same Pydantic schemas the routes already validate against.

```python
# core/docs/openapi_registry.py
from apispec import APISpec

spec = APISpec(title="API", version="1.0.0", openapi_version="3.0.3", info={"description": "..."})
```

```python
# domains/catalog/routes/v1/openapi/product_openapi.py
from core.docs.openapi_registry import spec
from domains.catalog.routes.v1.schemas.product_schema import ProductCreateSchema, ProductOutSchema

def register() -> None:
    spec.path(
        path="/api/v1/products",
        operations={
            "post": {
                "tags": ["Catalog / Products"],
                "summary": "Create a product",
                "requestBody": {"content": {"application/json": {"schema": ProductCreateSchema.model_json_schema()}}},
                "responses": {
                    "201": {"content": {"application/json": {"schema": ProductOutSchema.model_json_schema()}}, "description": "Created"},
                    "422": {"description": "Validation error"},
                },
            },
            "get": {
                "tags": ["Catalog / Products"],
                "summary": "List products",
                "parameters": [
                    {"name": "search", "in": "query", "schema": {"type": "string"}},
                    {"name": "page", "in": "query", "schema": {"type": "integer", "default": 1}},
                    {"name": "limit", "in": "query", "schema": {"type": "integer", "default": 20}},
                ],
                "responses": {"200": {"description": "Paginated list of products"}},
            },
        },
    )
```

Every other entity gets its own `<entity>_openapi.py`, importing that entity's own schemas — one file, one entity's paths. Nothing here touches `product_routes.py`; they're only ever wired together by registration:

```python
# app/docs.py
from flask import Flask

def register_openapi(app: Flask) -> None:
    from domains.catalog.routes.v1.openapi import product_openapi
    # ... one import per entity across every domain

    for module in (product_openapi,):   # extend with every other entity's module
        module.register()

    from core.docs.docs_blueprint import bp as docs_bp
    app.register_blueprint(docs_bp)
```

```python
# core/docs/docs_blueprint.py
from flask import Blueprint, Response, jsonify, render_template_string
from core.docs.openapi_registry import spec

bp = Blueprint("docs", __name__, url_prefix="/api/v1")

@bp.get("/openapi.json")
def openapi_json() -> Response:
    return jsonify(spec.to_dict())

@bp.get("/docs")
def swagger_ui() -> str:
    return render_template_string(SWAGGER_UI_TEMPLATE, spec_url="/api/v1/openapi.json")
```

`register_openapi(app)` is called from `create_app()` alongside `register_routes(app)` — same registration pattern, entirely separate concern, so a route can change shape without the spec noticing (worth a lint/test that diffs the two once the project is large enough for that to matter).

---

## 8. App wiring

### Extensions

```python
# app/extensions.py
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS

limiter = Limiter(key_func=get_remote_address)
cors = CORS()
```

### Middlewares — domain restriction + content-type enforcement

```python
# app/middlewares.py
from flask import Flask, request, abort

def enforce_allowed_domain(app: Flask) -> None:
    @app.before_request
    def _check_origin() -> None:
        allowed: list[str] = app.config["ALLOWED_DOMAINS"]
        origin = request.headers.get("Origin") or request.headers.get("Referer", "")
        if allowed and not any(d in origin for d in allowed):
            abort(403, description="Origin not allowed")

def enforce_json_content_type(app: Flask) -> None:
    @app.before_request
    def _check_content_type() -> None:
        if request.method in ("POST", "PUT", "PATCH"):
            ct = request.content_type or ""
            if "application/json" not in ct and "multipart/form-data" not in ct:
                abort(415, description="Unsupported Content-Type")
```

### Centralized error handlers

```python
# app/error_handlers.py
from flask import Flask
from pydantic import ValidationError as PydanticValidationError
from core.services.errors import AppError
from core.routes.envelope import fail, EnvelopeResponse

def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(AppError)
    def handle_app_error(err: AppError) -> EnvelopeResponse:
        return fail(err.code, err.message, err.status_code, err.details)

    @app.errorhandler(PydanticValidationError)
    def handle_validation_error(err: PydanticValidationError) -> EnvelopeResponse:
        return fail("VALIDATION_ERROR", "Invalid request data", 422, {"errors": err.errors()})

    @app.errorhandler(404)
    def handle_404(err: Exception) -> EnvelopeResponse:
        return fail("NOT_FOUND", "Resource not found", 404)

    @app.errorhandler(429)
    def handle_rate_limited(err: Exception) -> EnvelopeResponse:
        return fail("RATE_LIMITED", "Too many requests", 429)

    @app.errorhandler(Exception)
    def handle_unexpected(err: Exception) -> EnvelopeResponse:
        app.logger.exception(err)
        return fail("INTERNAL_ERROR", "Something went wrong", 500)
```

### Route registration

```python
# app/routes.py
from flask import Flask

def register_routes(app: Flask) -> None:
    from domains.catalog.routes.v1.product_routes import bp as product_bp
    # ... one import per entity across every domain

    for bp in (product_bp,):   # extend with every other entity's blueprint
        app.register_blueprint(bp)
```

### App factory

```python
# app/__init__.py
from typing import Callable
from flask import Flask
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import create_engine
from config import get_settings
from config.base import BaseAppSettings
from app.extensions import limiter, cors
from app.middlewares import enforce_allowed_domain, enforce_json_content_type
from app.error_handlers import register_error_handlers
from app.uow import build_uow_factory
from app.domain_service_builder import build_domain_service
from app.domain_service import DomainService
from app.routes import register_routes
from app.docs import register_openapi
from app.cli import register_cli
from core.events.dispatcher import EventDispatcher
from core.repositories.sql.sql_uow import SqlUnitOfWork

def build_session_factory(database_uri: str) -> Callable[[], Session]:
    engine = create_engine(database_uri)
    return sessionmaker(bind=engine)

def register_domain_event_handlers(dispatcher: EventDispatcher, domain_service: DomainService) -> None:
    from domains.catalog import event_handlers as catalog_event_handlers
    # ... one import per domain that has event_handlers.py

    catalog_event_handlers.register(dispatcher, domain_service.catalog)

def create_app(env: str | None = None) -> Flask:
    app = Flask(__name__)
    settings: BaseAppSettings = get_settings(env)
    app.config.from_object(settings)

    limiter.init_app(app)
    app.config["RATELIMIT_DEFAULT"] = settings.RATE_LIMIT_DEFAULT
    cors.init_app(app, origins=settings.ALLOWED_DOMAINS)

    enforce_allowed_domain(app)
    enforce_json_content_type(app)
    register_error_handlers(app)

    dispatcher = EventDispatcher()
    session_factory = build_session_factory(settings.SQLALCHEMY_DATABASE_URI)
    uow_factory: Callable[[], SqlUnitOfWork] = build_uow_factory(session_factory, dispatcher)

    domain_service = build_domain_service(uow_factory)
    domain_service.init_app(app)

    register_domain_event_handlers(dispatcher, domain_service)
    register_routes(app)
    register_openapi(app)
    register_cli(app)

    return app
```

`app/` is the only package that imports from more than one domain at a time — `core/` stays generic infrastructure, and each `domains/<x>/` package only ever imports its own entities/repositories/services plus events it explicitly subscribes to.

---

## 9. Configuration (pydantic-settings)

```python
# config/base.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class BaseAppSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    ENV: str = "development"
    DEBUG: bool = False
    TESTING: bool = False
    SECRET_KEY: str = "dev-secret"
    SQLALCHEMY_DATABASE_URI: str = "sqlite:///dev.db"
    ALLOWED_DOMAINS: list[str] = ["localhost"]
    RATE_LIMIT_DEFAULT: str = "200 per hour"

    # Only relevant if the project has Account + RBAC domains — see §12.
    SUPERUSER_USERNAME: str | None = None
    SUPERUSER_EMAIL: str | None = None
    SUPERUSER_PASSWORD: str | None = None
    SUPERUSER_FIRST_NAME: str = "Super"
    SUPERUSER_LAST_NAME: str = "Admin"
```

```python
# config/development.py
from config.base import BaseAppSettings

class DevelopmentSettings(BaseAppSettings):
    DEBUG: bool = True
    SUPERUSER_USERNAME: str = "admin"
    SUPERUSER_EMAIL: str = "admin@localhost"
    SUPERUSER_PASSWORD: str = "dev-only-password"   # never used in testing/production
```

```python
# config/testing.py
from config.base import BaseAppSettings

class TestingSettings(BaseAppSettings):
    TESTING: bool = True
    SQLALCHEMY_DATABASE_URI: str = "sqlite:///:memory:"
    RATE_LIMIT_DEFAULT: str = "10000 per hour"   # effectively unlimited in tests
    SUPERUSER_USERNAME: str = "test-admin"
    SUPERUSER_EMAIL: str = "test-admin@example.com"
    SUPERUSER_PASSWORD: str = "test-only-password"
```

```python
# config/production.py
from pydantic_settings import SettingsConfigDict
from config.base import BaseAppSettings

class ProductionSettings(BaseAppSettings):
    # every field below MUST come from the environment — no defaults in code
    model_config = SettingsConfigDict(env_prefix="APP_", extra="ignore")

    SECRET_KEY: str
    SQLALCHEMY_DATABASE_URI: str
    ALLOWED_DOMAINS: list[str]
```

```python
# config/__init__.py
import os
from config.base import BaseAppSettings
from config.development import DevelopmentSettings
from config.testing import TestingSettings
from config.production import ProductionSettings

_SETTINGS: dict[str, type[BaseAppSettings]] = {
    "development": DevelopmentSettings,
    "testing": TestingSettings,
    "production": ProductionSettings,
}

def get_settings(env: str | None = None) -> BaseAppSettings:
    env = env or os.getenv("FLASK_ENV", "development")
    return _SETTINGS[env]()
```

Production is instantiated purely from env vars; missing required vars fail fast at startup rather than silently falling back to a dev default. Superuser bootstrap is a separate, explicit CLI action (see §12) — nothing here auto-runs it.

---

## 10. Rate limiting & domain restriction

- **Rate limiting** — `Flask-Limiter`, keyed by remote address (or by `account.id` once authenticated, via a custom `key_func`). A global default (`RATE_LIMIT_DEFAULT`) applies everywhere; sensitive routes get a tighter `@limiter.limit(...)` override.
- **Domain restriction** — `Flask-CORS` restricts browser-side cross-origin calls to `ALLOWED_DOMAINS`; the `enforce_allowed_domain` before-request hook additionally rejects any request (not just CORS preflight) whose `Origin`/`Referer` doesn't match, covering non-browser clients too.

---

## 11. Adding a new domain — checklist

To add, e.g., a **Billing** domain with an **Invoice** entity:

1. `domains/billing/entities/invoice.py` — plain dataclass, `Invoice.issue()` etc. registering events.
2. `domains/billing/entities/events.py`, `filters.py` (`InvoiceFilter(EntityFilter)`).
3. `domains/billing/exceptions.py` — e.g. `InvoiceAlreadyPaidError(ConflictError)`.
4. `domains/billing/repositories/sql/mappers.py` + `sql_invoice_repository.py` — subclass `BaseSqlRepository`.
5. `domains/billing/services/invoice_service.py` — subclass `BaseService`; `domains/billing/services/billing_domain_service.py` aggregating it.
6. `domains/billing/routes/v1/schemas/invoice_schema.py`, `routes/v1/invoice_routes.py` — a `Blueprint`.
7. `domains/billing/routes/v1/openapi/invoice_openapi.py` — the OpenAPI paths, separate from the route file.
8. (optional) `domains/billing/event_handlers.py` if Billing reacts to another domain's events.
9. Wire it into the composition root: add `SqlInvoiceRepository` to `app/uow.py`'s `REPOSITORY_CLASSES`, add `BillingDomainService(...)` to `app/domain_service_builder.py`, add its blueprint to `app/routes.py`, its openapi module to `app/docs.py`, and its `event_handlers.register(...)` call if step 8 applies.

Nothing in `core/` changes. That's the point of the standard.

---

## 12. Bootstrapping a superuser (Account + RBAC)

Only relevant when the project actually has Account + RBAC domains (built the same way as Catalog, per §11). Without a bootstrap step the API is unusable on first deploy — nothing exists yet with permission to create the first account.

Bootstrap is a **CLI-only** action — an explicit, auditable command, never a side effect of starting the app. `ensure_superuser` is idempotent, so running it more than once (across dev, CI, or a redeploy) is always safe:

```python
# app/bootstrap.py
from typing import TYPE_CHECKING, Any
from core.services.errors import AppError
from domains.account.exceptions import DuplicateUsernameError

if TYPE_CHECKING:
    from app.domain_service import DomainService
    from config.base import BaseAppSettings

class SuperuserConfigError(AppError):
    code, status_code, message = "SUPERUSER_CONFIG_MISSING", 500, "Required SUPERUSER_* settings are missing"

SUPERUSER_ROLE = "superuser"

def ensure_superuser(domain_service: "DomainService", settings: "BaseAppSettings") -> None:
    missing: list[str] = [
        f for f in ("SUPERUSER_USERNAME", "SUPERUSER_EMAIL", "SUPERUSER_PASSWORD") if not getattr(settings, f)
    ]
    if missing:
        raise SuperuserConfigError(missing=missing)

    role = domain_service.rbac.roles.ensure_system_role(name=SUPERUSER_ROLE, grants_all=True)

    if domain_service.account.accounts.exists(role_id=role.id):
        return   # already bootstrapped — no-op on every subsequent run

    try:
        account = domain_service.account.accounts.create(
            first_name=settings.SUPERUSER_FIRST_NAME, last_name=settings.SUPERUSER_LAST_NAME,
        )
        domain_service.account.credentials.create(
            account_id=account.id, username=settings.SUPERUSER_USERNAME,
            email=settings.SUPERUSER_EMAIL, password=settings.SUPERUSER_PASSWORD,
        )
        domain_service.rbac.roles.assign(account_id=account.id, role_id=role.id)
    except DuplicateUsernameError:
        return   # a concurrent invocation beat us to it — fine, idempotent by design
```

```python
# app/cli.py
import click
from flask import Flask, current_app
from flask.cli import with_appcontext
from config import get_settings
from app.bootstrap import ensure_superuser
from app.domain_service import DomainService

@click.command("create-superuser")
@with_appcontext
def create_superuser_command() -> None:
    """Bootstrap the superuser account from SUPERUSER_* env vars."""
    settings = get_settings()
    domain_service: DomainService = current_app.extensions["domain_service"]
    ensure_superuser(domain_service, settings)
    click.echo("Superuser ensured.")

def register_cli(app: Flask) -> None:
    app.cli.add_command(create_superuser_command)
```

`register_cli(app)` is called from `create_app()` (see §8), same as `register_routes`/`register_openapi` — but `create_app()` itself never calls `ensure_superuser`. It only runs when someone explicitly runs:

```
flask create-superuser
```

- **Dev / testing** — `SUPERUSER_USERNAME/EMAIL/PASSWORD` default to fixed placeholder values in `DevelopmentSettings`/`TestingSettings` (§9), so running the command locally with no env vars set just works.
- **Production** — `APP_SUPERUSER_USERNAME` / `APP_SUPERUSER_EMAIL` / `APP_SUPERUSER_PASSWORD` are supplied through the deployment's secrets manager for that one command invocation (as part of the deploy step) — never committed to a repo or a `.env` file checked into version control. Because the command only runs when invoked, there's no risk of every worker/replica racing to bootstrap on process startup.

```
# .env (production secrets — not committed; only needed for the one `flask create-superuser` run)
APP_SECRET_KEY=...
APP_SQLALCHEMY_DATABASE_URI=...
APP_ALLOWED_DOMAINS=["https://app.example.com"]
APP_SUPERUSER_USERNAME=...
APP_SUPERUSER_EMAIL=...
APP_SUPERUSER_PASSWORD=...
```

---

## 13. Suggested dependencies

```
flask
flask-limiter
flask-cors
sqlalchemy
flask-migrate         # or plain alembic
pydantic
pydantic-settings
apispec                # OpenAPI spec assembly, kept out of route code
gunicorn               # production WSGI server
pytest / pytest-flask  # testing
```

---

## 14. Testing note

Because repositories never own a session and services depend only on a `uow_factory`, tests can inject a `SqlUnitOfWork` built on an in-memory SQLite session factory with a smaller `REPOSITORY_CLASSES` map (or a fake in-memory UoW implementing `BaseUnitOfWork` directly) — services and routes are tested without touching a real database, and without needing every domain wired up at once.
