from collections import defaultdict
from typing import Any, Callable, TypeVar
from src.core.entities.events import DomainEvent

T = TypeVar("T", bound=DomainEvent)

class EventDispatcher:
    def __init__(self) -> None:
        self._handlers: dict[type[DomainEvent], list[Callable[[Any], None]]] = defaultdict(list)

    def subscribe(self, event_type: type[T], handler: Callable[[T], None]) -> None:
        self._handlers[event_type].append(handler)

    def dispatch(self, event: DomainEvent) -> None:
        for handler in self._handlers[type(event)]:
            handler(event)
