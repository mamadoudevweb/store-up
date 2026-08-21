from dataclasses import dataclass, field
from src.core.entities.events import DomainEvent

@dataclass(kw_only=True)
class Entity:
    """Zero dependencies on any other layer — no ORM, no Flask, no pydantic."""
    id: int | None = None
    _events: list[DomainEvent] = field(default_factory=list, repr=False, compare=False)

    def register_event(self, event: DomainEvent) -> None:
        self._events.append(event)

    def pull_events(self) -> list[DomainEvent]:
        events, self._events = self._events, []
        return events

# Backward-compat alias used by catalog entities
BaseEntity = Entity
