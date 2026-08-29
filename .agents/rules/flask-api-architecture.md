---
trigger: always_on
---

# Flask API Architecture Rules

These rules govern every code contribution to this project.  
They are distilled from `flask-api-architecture-standard.md` — the canonical reference for full examples and rationale.

---

## Layering (non-negotiable)

- **Entities** (`domains/<x>/entities/`) — pure Python dataclasses only. Zero imports from repositories, services, routes, Flask, or SQLAlchemy. Business logic lives here.
- **Repositories** — speak only in entities. ORM models never leave the `repositories/sql/` package. A **mapper** converts entity ↔ ORM model both ways.
- **Repositories never own a session.** Sessions are injected by the Unit of Work; services obtain a UoW from a `uow_factory`.
- **`core/` never imports from `domains/`.** Core is generic infrastructure with no knowledge of any domain. Only `app/` (the composition root) wires concrete domains into core machinery.
- **Services never receive raw JSON.** Routes parse request data into a Pydantic schema first, then pass typed values into services.
- **Services** always return `ServiceResult` on success and always **raise** an `AppError` subclass on failure — never return an error object.
- **Routes** do: request parsing (Pydantic), one service call, envelope serialization. Nothing else — no business logic, no inline OpenAPI docs.
- **Cross-domain communication through events only.** Domains never import each other's services directly. One domain reacts to another by subscribing to its domain events in `<domain>/event_handlers.py`.
- **Everything is typed.** Every `def` has full parameter and return annotations. An untyped `def` is a review blocker.

---

## Project Layout

Every new bounded context follows this exact structure — no exceptions:

```
domains/<name>/
  entities/
    <entity>.py          # plain dataclass entity
    events.py            # domain events (frozen dataclasses)
    enums.py             # domain enums (if any)
  exceptions.py          # domain AppError subclasses (code prefix: <DOMAIN>_)
  repositories/
    filters.py           # <Entity>Filter(EntityFilter) dataclasses
    sql/
      orms/            # SQLAlchemy ORM models
      mappers.py         # entity ↔ ORM model conversion
      <entity>_repository.py  # subclass BaseSqlRepository
  services/
    <entity>_service.py        # one service per entity, subclasses BaseService
    <name>_domain_service.py   # aggregates entity services for this domain
  routes/
    v1/
      schemas/
        <entity>_schema.py     # Pydantic in/out schemas
      openapi/
        <entity>_openapi.py    # APISpec paths — separate from route code
      <entity>_routes.py       # one Blueprint per entity
  event_handlers.py      # optional — only if domain reacts to external events
```

The `app/` composition root is the **only** place that wires domains together:
- `app/uow.py` — `REPOSITORY_CLASSES` dict, one entry per SQL repository
- `app/domain_service_builder.py` — instantiates every domain service
- `app/routes.py` — registers every domain blueprint (no `try/except ImportError: pass`)
- `app/docs.py` — registers every OpenAPI module

---

## Entities

- Use `@dataclass(kw_only=True)` and subclass `BaseEntity[ID]`.
- Domain events are emitted **from inside entity methods** (e.g. `StockItem.create()` calls `self.register_event(StockItemCreated(...))`).
- Events are dispatched by the UoW **after a successful commit** via `uow.track(entity)`.
- `id` is never `None` after creation — validate it immediately in `cls.create()`.

---

## Exceptions

- Each domain owns `exceptions.py` at its root.
- All exceptions subclass a core generic (`NotFoundError`, `ConflictError`, `ValidationError`, `PermissionDeniedError`).
- Error codes use a domain-prefix: `STOCK_ITEM_NOT_FOUND`, `CATALOG_DUPLICATE_SKU`, `SALE_ALREADY_COMPLETED`, etc.
- `AppError.__init_subclass__` auto-registers every subclass — no manual registry.

---

## Services

- One service class per entity (e.g. `StockItemService` not `StockService`).
- Every method signature: `(self, actor: SupportsPermissionCheck, ...) -> ServiceResult[T]`.
- Every method starts with `self._authorize(actor, domain, entity, action)`.
- Open the UoW with `with self._uow_factory() as uow:`, call `uow.track(entity)` for any entity with pending events. The UoW commits on clean exit, rolls back on exception.
- Never catch `ValueError` from entity methods — wrap them into the appropriate domain `AppError` subclass before re-raising.

---

## Routes

- One `Blueprint` per entity, one file per entity (`product_routes.py`, not `catalog_routes.py`).
- URL prefix: `/api/v1/<entity-name-plural>` (kebab-case, no trailing slash in prefix).
- Every route is decorated with `@jwt_required()`.
- Parse all request bodies with `Schema.model_validate(request.get_json(force=True))`.
- Parse all query parameters with `request.args.get("key", default, type=T)` or a dedicated Pydantic query schema — never with bare `int(request.args.get(...))`.
- Return `ok(data, meta=..., status=...)` or let the error handler handle exceptions.
- Import `domain_service` lazily via `current_app.extensions["domain_service"]` — never at module level.
- OpenAPI documentation lives in `openapi/<entity>_openapi.py` — **never** inside the route file.

---

## Response Envelope

All responses use the shared envelope:
```python
# Success
{"success": true, "data": {...}, "meta": {...}}

# Error
{"success": false, "error": {"code": "...", "message": "...", "details": {...}}}
```

Use `ok()` and `fail()` from `src/core/routes/envelope.py` exclusively. Never construct raw dicts.

---

## Unit of Work & Repositories

- `SqlUnitOfWork` is domain-agnostic. Adding a domain means adding to `REPOSITORY_CLASSES` in `app/uow.py` — never modifying `core/`.
- Repositories subclass `BaseSqlRepository[Entity, Filter]`, set `model`, `mapper`, `filter_cls`, and implement `_apply_filter()` only.
- `get(criteria: EntityId | Filter)` — by primary key or filter; `list(filter)` — paginated; `add`, `update`, `delete`.

---

## Configuration

- All config via `pydantic-settings` `BaseConfig` subclasses (`development`, `testing`, `production`).
- Production config has **no defaults** for sensitive fields (`SECRET_KEY`, `DATABASE_URL`, superuser credentials). Missing vars must fail at startup.
- `SECRET_KEY` and `JWT_SECRET_KEY` are **separate** fields — never the same value.
- The `to_flask_config()` method is the single source of truth for what lands in `app.config`.
- `RATELIMIT_DEFAULT` must be set in `to_flask_config()` **before** `limiter.init_app(app)` is called.

---

## Testing

- Integration tests use an in-memory SQLite engine with the real `SqlUnitOfWork` and `REPOSITORY_CLASSES`.
- Each test runs in a transaction that is rolled back after completion (no shared mutable state across tests).
- `MockActor` satisfies `SupportsPermissionCheck` by accepting an explicit permission set (`{"*"}` for admin).
- Tests must not assert `>= 1` on list results without controlling the exact inserted data — use specific counts or item identity.

---

## Checklist: Adding a New Domain

1. `domains/<name>/entities/<entity>.py` — pure dataclass
2. `domains/<name>/entities/events.py` + `enums.py`
3. `domains/<name>/exceptions.py` — code prefix `<NAME>_`
4. `domains/<name>/repositories/filters.py`
5. `domains/<name>/repositories/sql/orms/` + `mappers.py` + `<entity>_repository.py`
6. `domains/<name>/services/<entity>_service.py` + `<name>_domain_service.py`
7. `domains/<name>/routes/v1/schemas/<entity>_schema.py`
8. `domains/<name>/routes/v1/<entity>_routes.py`
9. `domains/<name>/routes/v1/openapi/<entity>_openapi.py`
10. (optional) `domains/<name>/event_handlers.py`
11. Wire: `app/uow.py` → `app/domain_service_builder.py` → `app/routes.py` → `app/docs.py`

**Nothing in `core/` changes when adding a domain.**
