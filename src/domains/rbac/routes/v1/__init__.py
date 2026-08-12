"""RBAC v1 routes — /api/v1/roles and /api/v1/permissions"""
from __future__ import annotations

from flask import Blueprint

from .permission_routes import bp as permission_bp
from .role_permission_routes import bp as role_permission_bp
from .role_routes import bp as role_bp

router = Blueprint("rbac", __name__)

router.register_blueprint(role_bp, url_prefix="/roles")
router.register_blueprint(permission_bp, url_prefix="/permissions")
router.register_blueprint(role_permission_bp, url_prefix="/roles")
