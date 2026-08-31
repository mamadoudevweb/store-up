"""RBAC repository utilities and mappers."""
from __future__ import annotations
from typing import Any

from src.core.repositories.utils import Mapper
from src.domains.rbac.entities import Permission, Role, RolePermission
from src.domains.rbac.repositories.sql.orms import PermissionModel, RoleModel, RolePermissionModel


class RoleMapper(Mapper[Role, RoleModel]):
    def to_entity(self, model: RoleModel) -> Role:
        return Role(
            id=model.id,
            name=model.name,
            description=model.description,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def to_model(self, entity: Role, existing: RoleModel | None = None) -> RoleModel:
        model = existing or RoleModel()
        if entity.id is not None:
            model.id = entity.id
        model.name = entity.name
        model.description = entity.description
        model.created_at = entity.created_at
        model.updated_at = entity.updated_at
        return model


class PermissionMapper(Mapper[Permission, PermissionModel]):
    def to_entity(self, model: PermissionModel) -> Permission:
        return Permission(
            id=model.id,
            resource=model.resource,
            action=model.action,
            description=model.description,
            created_at=model.created_at,
        )

    def to_model(self, entity: Permission, existing: PermissionModel | None = None) -> PermissionModel:
        model = existing or PermissionModel()
        if entity.id is not None:
            model.id = entity.id
        model.resource = entity.resource
        model.action = entity.action
        model.description = entity.description
        model.created_at = entity.created_at
        return model


class RolePermissionMapper(Mapper[RolePermission, RolePermissionModel]):
    def to_entity(self, model: RolePermissionModel) -> RolePermission:
        return RolePermission(
            id=model.role_id, # Use role_id as placeholder for Entity's ID since there is no ID
            role_id=model.role_id,
            permission_id=model.permission_id,
            assigned_at=model.assigned_at,
            revoked_at=model.revoked_at,
        )

    def to_model(self, entity: RolePermission, existing: RolePermissionModel | None = None) -> RolePermissionModel:
        model = existing or RolePermissionModel()
        model.role_id = entity.role_id
        model.permission_id = entity.permission_id
        model.assigned_at = entity.assigned_at
        model.revoked_at = entity.revoked_at
        return model
