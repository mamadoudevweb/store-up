"""RBAC repository utilities and mappers."""
from __future__ import annotations

from src.domains.rbac.entities import Permission, Role
from src.domains.rbac.repositories.sql.orms import PermissionModel, RoleModel


def map_role_to_entity(model: RoleModel) -> Role:
    return Role(
        id=model.id,
        name=model.name,
        description=model.description,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def map_role_to_model(entity: Role) -> RoleModel:
    return RoleModel(
        id=entity.id,
        name=entity.name,
        description=entity.description,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
    )


def map_permission_to_entity(model: PermissionModel) -> Permission:
    return Permission(
        id=model.id,
        resource=model.resource,
        action=model.action,
        description=model.description,
        created_at=model.created_at,
    )


def map_permission_to_model(entity: Permission) -> PermissionModel:
    return PermissionModel(
        id=entity.id,
        resource=entity.resource,
        action=entity.action,
        description=entity.description,
        created_at=entity.created_at,
    )
