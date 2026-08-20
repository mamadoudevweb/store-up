"""SQL implementation of Credential repository."""
from __future__ import annotations
from typing import Any

from sqlalchemy import or_

from src.core.repositories.sql.base_sql_repository import BaseSqlRepository
from src.domains.accounts.entities import Credential
from src.domains.accounts.repositories.filters import CredentialFilter
from src.domains.accounts.repositories.sql.orms import CredentialModel
from src.domains.accounts.repositories.utils import CredentialMapper

class SqlCredentialRepository(BaseSqlRepository[Credential, CredentialFilter]):
    model = CredentialModel
    mapper = CredentialMapper()
    filter_cls = CredentialFilter

    def _apply_filter(self, query: Any, entity_filter: CredentialFilter) -> Any:
        q = query
        if entity_filter.id:
            q = q.where(CredentialModel.id == entity_filter.id)
        if entity_filter.account_id:
            q = q.where(CredentialModel.account_id == entity_filter.account_id)
        if entity_filter.username:
            q = q.where(CredentialModel.username == entity_filter.username)
        if entity_filter.email:
            q = q.where(CredentialModel.email == entity_filter.email)
        if entity_filter.username_or_email:
            q = q.where(
                or_(
                    CredentialModel.username == entity_filter.username_or_email,
                    CredentialModel.email == entity_filter.username_or_email,
                )
            )
        return q
