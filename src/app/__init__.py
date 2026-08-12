"""
Flask application factory — the composition root.

This is the ONLY place in the codebase that imports from both app/ and domains/.
All wiring, DI, and registration happens here.
"""
from __future__ import annotations

import os

import redis as redis_lib
from flask import Flask

from src.config import get_config

from .extensions import cors, db, jwt, limiter, migrate
from .middleware import register_middleware


def create_app(env: str | None = None) -> Flask:
    """Create and configure the Flask application."""
    env = env or os.getenv("FLASK_ENV", "development")
    config = get_config(env)

    app = Flask(__name__, static_folder=None)
    app.config.from_mapping(config.to_flask_config())

    # ── Initialise extensions ──────────────────────────────────────────────
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    limiter.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": config.ALLOWED_ORIGINS}})

    # ── Redis client (injected into services that need it) ─────────────────
    redis_client = redis_lib.from_url(config.REDIS_URL, decode_responses=True)
    app.extensions["redis"] = redis_client

    # ── Store config on app for CLI commands ──────────────────────────────
    app.extensions["config"] = config

    # ── Wire domain services (DI — domains never import from app/) ─────────
    _wire_services(app, redis_client)

    # ── Register middleware ────────────────────────────────────────────────
    register_middleware(app)

    # ── Register error handlers ────────────────────────────────────────────
    _register_error_handlers(app)

    # ── Register JWT callbacks ─────────────────────────────────────────────
    _register_jwt_callbacks(app, redis_client)

    # ── Import and register ORM models (for Alembic awareness) ────────────
    with app.app_context():
        _import_models()

    # ── Register blueprints (all domain routes) ────────────────────────────
    _register_blueprints(app)

    # ── Register CLI commands ──────────────────────────────────────────────
    _register_cli(app)

    # ── Static file route for uploads ─────────────────────────────────────
    _register_static_files(app, config.UPLOAD_FOLDER)

    return app


# ── Private helpers ────────────────────────────────────────────────────────────

def _import_models() -> None:
    """Import all ORM models so SQLAlchemy / Alembic can discover them."""
    # Models are imported here (side-effect import) so that Alembic sees all
    # tables. Each domain's sql/orms/__init__.py is imported below as domains are built.
    # noqa: F401
    try:
        import src.domains.accounts.repositories.sql.orms  # noqa: F401
    except ImportError:
        pass
    try:
        import src.domains.auth.repositories.sql.models  # noqa: F401
    except ImportError:
        pass
    try:
        import src.domains.rbac.repositories.sql.models  # noqa: F401
    except ImportError:
        pass
    try:
        import src.domains.products.repositories.sql.models  # noqa: F401
    except ImportError:
        pass
    try:
        import src.domains.inventory.repositories.sql.models  # noqa: F401
    except ImportError:
        pass
    try:
        import src.domains.sales.repositories.sql.models  # noqa: F401
    except ImportError:
        pass
    try:
        import src.domains.notifications.repositories.sql.models  # noqa: F401
    except ImportError:
        pass


def _register_blueprints(app: Flask) -> None:
    """Register all domain route blueprints."""
    try:
        from src.domains.accounts.routes.v1 import router as accounts_v1
        from src.domains.auth.routes.v1 import router as auth_v1

        # Mount v1 domain routers
        app.register_blueprint(accounts_v1, url_prefix="/api/v1")
        app.register_blueprint(auth_v1, url_prefix="/api/v1")
    except ImportError:
        pass
    try:
        from src.domains.rbac.routes.v1 import router as rbac_router
        app.register_blueprint(rbac_router, url_prefix="/api/v1")
    except ImportError:
        pass
    try:
        from src.domains.products.routes.v1 import router as products_router
        app.register_blueprint(products_router, url_prefix="/api/v1")
    except ImportError:
        pass
    try:
        from src.domains.inventory.routes.v1 import router as inventory_router
        app.register_blueprint(inventory_router, url_prefix="/api/v1")
    except ImportError:
        pass
    try:
        from src.domains.sales.routes.v1 import router as sales_router
        app.register_blueprint(sales_router, url_prefix="/api/v1")
    except ImportError:
        pass
    try:
        from src.domains.reports.routes.v1 import router as reports_router
        app.register_blueprint(reports_router, url_prefix="/api/v1")
    except ImportError:
        pass
    try:
        from src.domains.notifications.routes.v1 import router as notifications_router
        app.register_blueprint(notifications_router, url_prefix="/api/v1")
    except ImportError:
        pass


def _register_error_handlers(app: Flask) -> None:
    """Centralised error handler — converts AppError and HTTP errors to envelope."""
    from flask import jsonify
    from werkzeug.exceptions import HTTPException

    from src.domains.shared.exceptions import AppError

    @app.errorhandler(AppError)
    def handle_app_error(exc: AppError):  # type: ignore[no-untyped-def]
        return jsonify({
            "status": "error",
            "data": None,
            "error": {"code": exc.code, "message": exc.message},
            "meta": None,
        }), exc.http_status

    @app.errorhandler(HTTPException)
    def handle_http_error(exc: HTTPException):  # type: ignore[no-untyped-def]
        return jsonify({
            "status": "error",
            "data": None,
            "error": {"code": exc.name.upper().replace(" ", "_"), "message": exc.description},
            "meta": None,
        }), exc.code

    @app.errorhandler(Exception)
    def handle_unexpected_error(exc: Exception):  # type: ignore[no-untyped-def]
        app.logger.exception("Unhandled exception: %s", exc)
        return jsonify({
            "status": "error",
            "data": None,
            "error": {"code": "INTERNAL_SERVER_ERROR", "message": "An unexpected error occurred"},
            "meta": None,
        }), 500


def _register_jwt_callbacks(app: Flask, redis_client: redis_lib.Redis) -> None:  # type: ignore[type-arg]
    """Register JWT callbacks: token identity loader + blocklist check."""
    from flask_jwt_extended import decode_token

    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header: dict, jwt_payload: dict) -> bool:  # type: ignore[type-arg]
        jti = jwt_payload["jti"]
        # Delegate to whichever denylist implementation was wired (Redis or InMemory)
        denylist = app.extensions.get("token_denylist")
        if denylist is None:
            return False
        return denylist.is_revoked(jti)

    @jwt.revoked_token_loader
    def revoked_token_response(jwt_header: dict, jwt_payload: dict):  # type: ignore[type-arg]
        from flask import jsonify
        return jsonify({
            "status": "error",
            "data": None,
            "error": {"code": "TOKEN_REVOKED", "message": "Token has been revoked"},
            "meta": None,
        }), 401

    @jwt.expired_token_loader
    def expired_token_response(jwt_header: dict, jwt_payload: dict):  # type: ignore[type-arg]
        from flask import jsonify
        return jsonify({
            "status": "error",
            "data": None,
            "error": {"code": "TOKEN_EXPIRED", "message": "Token has expired"},
            "meta": None,
        }), 401

    @jwt.invalid_token_loader
    def invalid_token_response(error: str):  # type: ignore[no-untyped-def]
        from flask import jsonify
        return jsonify({
            "status": "error",
            "data": None,
            "error": {"code": "TOKEN_INVALID", "message": "Token is invalid"},
            "meta": None,
        }), 422

    @jwt.unauthorized_loader
    def missing_token_response(error: str):  # type: ignore[no-untyped-def]
        from flask import jsonify
        return jsonify({
            "status": "error",
            "data": None,
            "error": {"code": "TOKEN_MISSING", "message": "Authorization token is required"},
            "meta": None,
        }), 401


def _register_cli(app: Flask) -> None:
    """Register custom Flask CLI commands."""
    try:
        from src.domains.auth.cli import bootstrap_superuser
        app.cli.add_command(bootstrap_superuser)
    except ImportError:
        pass


def _register_static_files(app: Flask, upload_folder: str) -> None:
    """Serve uploaded files via /files/<path:filename>."""
    import os
    from flask import send_from_directory

    os.makedirs(upload_folder, exist_ok=True)

    @app.route("/files/<path:filename>")
    def serve_upload(filename: str):  # type: ignore[no-untyped-def]
        return send_from_directory(os.path.abspath(upload_folder), filename)


def _wire_services(app: Flask, redis_client: object) -> None:
    """
    Instantiate all domain UoWs and services, register them in app.extensions.
    """
    from sqlalchemy.orm import sessionmaker

    from src.app.extensions import db
    from src.domains.shared.events import event_bus

    # SQLAlchemy session factory
    session_factory = sessionmaker(bind=db.engine)

    # ── Accounts ──────────────────────────────────────────────────────────
    try:
        from src.domains.accounts.repositories.sql.sql_uow import SqlAccountUnitOfWork
        from src.domains.accounts.services import AccountService
        account_uow = SqlAccountUnitOfWork(session_factory)
        app.extensions["account_service"] = AccountService(account_uow, event_bus)
    except ImportError:
        pass

    # ── Auth ──────────────────────────────────────────────────────────────
    try:
        from src.domains.auth.services import AuthService
        
        # Choose denylist implementation based on environment:
        # - production → Redis (persistent, shared across processes)
        # - development / testing → InMemory (no external dependency)
        env = app.config.get("FLASK_ENV", "development")
        if env == "production":
            from src.domains.auth.repositories.redis_denylist import RedisTokenDenylist
            denylist = RedisTokenDenylist(redis_client)  # type: ignore[arg-type]
        else:
            from src.domains.auth.repositories.memory_denylist import InMemoryTokenDenylist
            denylist = InMemoryTokenDenylist()
        
        app.extensions["auth_service"] = AuthService(account_uow, denylist, event_bus)
        app.extensions["token_denylist"] = denylist
    except ImportError:
        pass

    # ── RBAC ──────────────────────────────────────────────────────────────
    try:
        from src.domains.rbac.repositories.sql.sql_uow import SqlRbacUnitOfWork
        from src.domains.rbac.services.rbac_service import RbacService
        rbac_uow = SqlRbacUnitOfWork(session_factory)
        app.extensions["rbac_service"] = RbacService(rbac_uow, event_bus)
    except ImportError:
        pass

    # ── Products ──────────────────────────────────────────────────────────
    try:
        from src.domains.products.repositories.sql.sql_uow import SqlProductUnitOfWork
        from src.domains.products.services.product_service import ProductService
        product_uow = SqlProductUnitOfWork(session_factory)
        app.extensions["product_service"] = ProductService(product_uow, event_bus)
    except ImportError:
        pass

    # ── Inventory ─────────────────────────────────────────────────────────
    try:
        from src.domains.inventory.repositories.sql.sql_uow import SqlInventoryUnitOfWork
        from src.domains.inventory.services.inventory_service import InventoryService
        inventory_uow = SqlInventoryUnitOfWork(session_factory)
        app.extensions["inventory_service"] = InventoryService(inventory_uow, event_bus)
    except ImportError:
        pass

    # ── Sales ─────────────────────────────────────────────────────────────
    try:
        from src.domains.sales.repositories.sql.sql_uow import SqlSalesUnitOfWork
        from src.domains.sales.services.sale_service import SaleService
        sales_uow = SqlSalesUnitOfWork(session_factory)
        app.extensions["sale_service"] = SaleService(sales_uow, event_bus)
    except ImportError:
        pass

    # ── Reports ───────────────────────────────────────────────────────────
    try:
        from src.domains.reports.repositories.sql.sql_uow import SqlReportUnitOfWork
        from src.domains.reports.services.report_service import ReportService
        report_uow = SqlReportUnitOfWork(session_factory)
        app.extensions["report_service"] = ReportService(report_uow)
    except ImportError:
        pass

    # ── Notifications ─────────────────────────────────────────────────────
    try:
        from src.domains.notifications.repositories.sql.sql_uow import SqlNotificationUnitOfWork
        from src.domains.notifications.services.notification_service import NotificationService
        notification_uow = SqlNotificationUnitOfWork(session_factory)
        notification_service = NotificationService(notification_uow, event_bus)
        app.extensions["notification_service"] = notification_service
        # Register event subscribers
        notification_service.register_subscribers()
    except ImportError:
        pass
