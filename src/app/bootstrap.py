from typing import TYPE_CHECKING
from src.core.services.errors import AppError
from src.domains.accounts.exceptions import UsernameConflict, EmailConflict

if TYPE_CHECKING:
    from src.app.domain_service import DomainService

class SuperuserConfigError(AppError):
    code, status_code, message = "SUPERUSER_CONFIG_MISSING", 500, "Required SUPERUSER_* settings are missing"

SUPERUSER_ROLE = "superuser"

from typing import TYPE_CHECKING, Any

def ensure_superuser(domain_service: "DomainService", settings: Any) -> None:
    missing: list[str] = [
        f for f in ("SUPERUSER_USERNAME", "SUPERUSER_EMAIL", "SUPERUSER_PASSWORD") if not getattr(settings, f, None)
    ]
    if missing:
        raise SuperuserConfigError(missing=missing)

    username = settings.SUPERUSER_USERNAME
    email = settings.SUPERUSER_EMAIL
    password = settings.SUPERUSER_PASSWORD

    try:
        acc_res = domain_service.accounts.account.create_account(first_name="Super", last_name="User")
        account = acc_res.data
        assert account.id is not None
        domain_service.accounts.credential.set_credentials(
            account_id=account.id,
            username=username,
            email=email,
            password=password,
        )
    except (UsernameConflict, EmailConflict):
        pass # Already exists
