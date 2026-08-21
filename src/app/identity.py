"""Identity context."""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import TYPE_CHECKING

from flask import current_app
from flask_jwt_extended import get_jwt_identity

if TYPE_CHECKING:
    from src.app.domain_service import DomainService


@dataclass
class IdentityContext:
    """Implements SupportsPermissionCheck for use in core BaseService."""
    account_id: uuid.UUID
    domain_service: DomainService

    def has_permission(self, domain: str, entity: str, action: str) -> bool:
        """Fetch the account's roles and check if they have the given permission."""
        # 1. Fetch roles for the account
        roles_result = self.domain_service.accounts.account_role.list_for_account(self.account_id)
        role_ids = [str(r.role_id) for r in roles_result.data]

        if not role_ids:
            return False

        # 2. Check permissions via RBAC domain
        check_result = self.domain_service.rbac.permission.check_roles_have_permission(
            role_ids=role_ids,
            resource=f"{domain}:{entity}",
            action=action
        )
        return check_result.data


def get_current_actor() -> IdentityContext:
    """Helper to fetch the current actor from the request context."""
    identity = get_jwt_identity()
    if not identity:
        raise ValueError("No JWT identity found in request context.")

    domain_svc: DomainService = current_app.extensions["domain_service"]
    return IdentityContext(
        account_id=uuid.UUID(identity),
        domain_service=domain_svc
    )
