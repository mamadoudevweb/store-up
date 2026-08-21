from flask import Flask, request, abort, current_app
from werkzeug.exceptions import UnsupportedMediaType
from src.app.extensions import jwt

def enforce_allowed_domain(app: Flask) -> None:
    @app.before_request
    def _check_origin() -> None:
        allowed: list[str] = app.config.get("ALLOWED_DOMAINS", [])
        origin = request.headers.get("Origin") or request.headers.get("Referer", "")
        if allowed and origin and not any(d in origin for d in allowed):
            abort(403, description="Origin not allowed")

def enforce_json_content_type(app: Flask) -> None:
    @app.before_request
    def _check_content_type() -> None:
        if request.method in ("POST", "PUT", "PATCH") and request.content_length:
            ct = request.content_type or ""
            if "application/json" not in ct and "multipart/form-data" not in ct:
                raise UnsupportedMediaType("Unsupported Content-Type")

def setup_jwt_blocklist(app: Flask) -> None:
    @jwt.token_in_blocklist_loader
    def check_if_token_is_revoked(jwt_header, jwt_payload: dict) -> bool:
        jti = jwt_payload["jti"]
        domain_service = current_app.extensions.get("domain_service")
        if domain_service:
            return domain_service.auth.is_token_revoked(jti)
        return False
