"""Request/response middleware and hooks."""
from __future__ import annotations

from flask import Flask, Request, request
from werkzeug.exceptions import UnsupportedMediaType


def _require_json_content_type(req: Request) -> None:
    """Enforce application/json on mutating requests that carry a body."""
    if req.method in {"POST", "PUT", "PATCH"} and req.content_length:
        # Allow multipart for file upload endpoints
        ct = req.content_type or ""
        if not (ct.startswith("application/json") or ct.startswith("multipart/form-data")):
            raise UnsupportedMediaType(
                "Content-Type must be application/json or multipart/form-data"
            )


def register_middleware(app: Flask) -> None:
    """Attach all middleware hooks to the Flask app."""

    @app.before_request
    def enforce_content_type() -> None:
        _require_json_content_type(request)

    @app.after_request
    def set_security_headers(response):  # type: ignore[no-untyped-def]
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response
