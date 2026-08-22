import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Generic, TypeVar

from src.core.entities.events import DomainEvent

ID = TypeVar("ID")

def _now() -> datetime:
    return datetime.now(timezone.utc)

@dataclass(kw_only=True)
class Entity(Generic[ID]):
    """Zero dependencies on any other layer — no ORM, no Flask, no pydantic."""
    id: ID | None = None
    created_at: datetime = field(default_factory=_now)
    updated_at: datetime = field(default_factory=_now)
    _events: list[DomainEvent] = field(default_factory=list, repr=False, compare=False)

    def register_event(self, event: DomainEvent) -> None:
        self._events.append(event)

    def pull_events(self) -> list[DomainEvent]:
        events, self._events = self._events, []
        return events

# Backward-compat alias used by catalog entities
BaseEntity = Entity
