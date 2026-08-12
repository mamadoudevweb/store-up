"""
Extension instances — bare, uninitialised.

These are instantiated here so any part of the app layer can import them,
but they are ONLY initialised (via .init_app()) inside create_app().

Domain layers NEVER import from this module.
"""
from __future__ import annotations

from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
cors = CORS()
limiter = Limiter(key_func=get_remote_address)
