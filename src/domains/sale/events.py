import uuid
import typing
from dataclasses import dataclass
from src.core.entities.events import DomainEvent


@dataclass(kw_only=True, frozen=True)
class SaleCreated(DomainEvent):
    """Emitted when a new sale is created (checkout committed, stock reserved)."""
    sale_id: uuid.UUID
    seller_account_id: uuid.UUID
    total: int
    payment_method_id: uuid.UUID
    event_name: str = "sale_created"


@dataclass(kw_only=True, frozen=True)
class SaleFailed(DomainEvent):
    """Emitted when a sale fails (authorization declined)."""
    sale_id: uuid.UUID
    event_name: str = "sale_failed"


@dataclass(kw_only=True, frozen=True)
class SaleCompleted(DomainEvent):
    """Emitted when a sale completes successfully."""
    sale_id: uuid.UUID
    event_name: str = "sale_completed"


@dataclass(kw_only=True, frozen=True)
class SaleReturned(DomainEvent):
    """Emitted when a return is fully processed on the Sale side."""
    refund_id: uuid.UUID
    sale_id: uuid.UUID
    amount: int
    event_name: str = "sale_returned"


@dataclass(kw_only=True, frozen=True)
class RefundRequested(DomainEvent):
    """Emitted when a refund is requested."""
    refund_id: uuid.UUID
    sale_id: uuid.UUID
    amount: int
    lines_data: list[dict[str, typing.Any]]
    event_name: str = "refund_requested"


@dataclass(kw_only=True, frozen=True)
class RefundCompleted(DomainEvent):
    """Emitted when a refund is processed (partial or full), so stock can restock items."""
    refund_id: uuid.UUID
    sale_id: uuid.UUID
    lines: list[dict[str, typing.Any]]
    event_name: str = "refund_completed"

