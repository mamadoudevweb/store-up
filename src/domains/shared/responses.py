"""Shared response envelope helper."""
from __future__ import annotations

from typing import Any

from flask import jsonify
from werkzeug.wrappers import Response

from src.domains.shared.pagination import Paginated


def success(data: Any, status: int = 200, meta: dict | None = None) -> tuple[Response, int]:
    return jsonify({
        "status": "success",
        "data": data,
        "error": None,
        "meta": meta,
    }), status


def paginated(result: Paginated, serializer: Any) -> tuple[Response, int]:
    return jsonify({
        "status": "success",
        "data": [serializer(item) for item in result.items],
        "error": None,
        "meta": result.meta.to_dict(),
    }), 200
