from src.domains.accounts.routes.v1.openapi.account_openapi import register_account_docs
from src.domains.accounts.routes.v1.openapi.credential_openapi import register_credential_docs
from src.domains.accounts.routes.v1.openapi.account_role_openapi import register_account_role_docs

def register() -> None:
    register_account_docs()
    register_credential_docs()
    register_account_role_docs()
