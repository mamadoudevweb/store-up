"""Auth v1 routes."""
from __future__ import annotations

from flask import Blueprint

from src.domains.auth.routes.v1.auth_routes import bp as auth_bp

router = Blueprint("auth_v1", __name__)

router.register_blueprint(auth_bp, url_prefix="/auth")
