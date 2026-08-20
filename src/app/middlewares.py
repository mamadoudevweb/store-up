from flask import Flask, request, abort
from werkzeug.exceptions import UnsupportedMediaType

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
