"""Auth domain routes."""
from __future__ import annotations

from flask import Blueprint, current_app, request
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required

from src.domains.auth.routes.v1.schemas.auth_schemas import LoginRequest, TokenResponse
from src.core.routes.envelope import ok

bp = Blueprint("auth", __name__)


def get_domain_service():
    return current_app.extensions["domain_service"]


@bp.post("/login")
def login():
    body = LoginRequest.model_validate(request.get_json(force=True))
    result = get_domain_service().auth.login(body.username, body.password, request.remote_addr)
    return ok(TokenResponse.model_validate(result.data).model_dump(mode="json"))


@bp.post("/logout")
@jwt_required()
def logout():
    jwt_data = get_jwt()
    get_domain_service().auth.logout(jwt_data["jti"], jwt_data["exp"])
    return ok(None)


@bp.post("/refresh")
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity()
    result = get_domain_service().auth.refresh(identity)
    data = TokenResponse(access_token=result.data).model_dump(mode="json")
    return ok(data)
