"""Auth domain routes."""
from __future__ import annotations

from flask import Blueprint, current_app, request
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required

from src.domains.auth.routes.v1.schemas.auth_schemas import LoginRequest, TokenResponse
from src.domains.shared.responses import success

bp = Blueprint("auth", __name__)


def get_auth_service():  # type: ignore[no-untyped-def]
    return current_app.extensions["auth_service"]


@bp.post("/login")
def login():  # type: ignore[no-untyped-def]
    body = LoginRequest.model_validate(request.get_json(force=True))
    result = get_auth_service().login(body.username, body.password, request.remote_addr)
    return success(TokenResponse.model_validate(result.data).model_dump(mode="json"))


@bp.post("/logout")
@jwt_required()
def logout():  # type: ignore[no-untyped-def]
    jwt_data = get_jwt()
    get_auth_service().logout(jwt_data["jti"], jwt_data["exp"])
    return success(None)


@bp.post("/refresh")
@jwt_required(refresh=True)
def refresh():  # type: ignore[no-untyped-def]
    identity = get_jwt_identity()
    result = get_auth_service().refresh(identity)
    data = TokenResponse(access_token=result.data).model_dump(mode="json")
    return success(data)
