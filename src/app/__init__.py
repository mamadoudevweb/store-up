import os
from typing import Callable
from flask import Flask
from sqlalchemy.orm import Session, sessionmaker
import redis as redis_lib

from src.config import get_config
from src.app.extensions import db, migrate, jwt, limiter, cors
from src.app.middlewares import enforce_allowed_domain, enforce_json_content_type, setup_jwt_blocklist
from src.app.error_handlers import register_error_handlers
from src.app.uow import build_uow_factory
from src.app.domain_service_builder import build_domain_service
from src.app.domain_service import DomainService
from src.app.routes import register_routes
from src.app.docs import register_openapi
from src.app.cli import register_cli
from src.core.events.dispatcher import EventDispatcher
from src.core.repositories.sql.sql_uow import SqlUnitOfWork

def build_session_factory(db) -> Callable[[], Session]:
    return sessionmaker(bind=db.engine)

def register_domain_event_handlers(dispatcher: EventDispatcher, domain_service: DomainService) -> None:
    from src.domains.stock import event_handlers as stock_event_handlers
    stock_event_handlers.register(dispatcher, domain_service)

def create_app(env: str | None = None) -> Flask:
    env_name = env or os.getenv("FLASK_ENV", "development") or "development"
    config = get_config(env_name)

    app = Flask(__name__)
    app.config.from_mapping(config.to_flask_config())

    # Initialise extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    limiter.init_app(app)
    app.config["RATELIMIT_DEFAULT"] = config.RATE_LIMIT_DEFAULT if hasattr(config, 'RATE_LIMIT_DEFAULT') else "200 per hour"
    cors.init_app(app, resources={r"/api/*": {"origins": config.ALLOWED_ORIGINS}})

    # Redis client (injected into services that need it)
    redis_client = redis_lib.from_url(config.REDIS_URL, decode_responses=True)
    app.extensions["redis"] = redis_client
    app.extensions["config"] = config

    enforce_allowed_domain(app)
    enforce_json_content_type(app)
    setup_jwt_blocklist(app)
    register_error_handlers(app)

    dispatcher = EventDispatcher()
    
    with app.app_context():
        session_factory = build_session_factory(db)
        uow_factory: Callable[[], SqlUnitOfWork] = build_uow_factory(session_factory, dispatcher)
        domain_service = build_domain_service(uow_factory, redis_client, dispatcher, config.UPLOAD_FOLDER)
        domain_service.init_app(app)
        
        # Import models so Alembic can see them
        try:
            import src.domains.accounts.repositories.sql.orms
            import src.domains.auth.repositories.sql.models
            import src.domains.rbac.repositories.sql.orms
            import src.domains.catalog.repositories.sql.orms
            import src.domains.stock.repositories.sql.orms
        except ImportError:
            pass

    register_domain_event_handlers(dispatcher, domain_service)
    register_routes(app)
    register_openapi(app)
    register_cli(app)

    # Static file route for uploads
    _register_static_files(app, config.UPLOAD_FOLDER)

    return app

def _register_static_files(app: Flask, upload_folder: str) -> None:
    """Serve uploaded files via /files/<path:filename>."""
    from flask import send_from_directory
    os.makedirs(upload_folder, exist_ok=True)

    @app.route("/files/<path:filename>")
    def serve_upload(filename: str):
        return send_from_directory(os.path.abspath(upload_folder), filename)
