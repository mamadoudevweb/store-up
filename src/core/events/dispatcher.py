from collections import defaultdict
from typing import Callable
from src.core.entities.events import DomainEvent

class EventDispatcher:
    def __init__(self) -> None:
        self._handlers: dict[type[DomainEvent], list[Callable[[DomainEvent], None]]] = defaultdict(list)

    def subscribe(self, event_type: type[DomainEvent], handler: Callable[[DomainEvent], None]) -> None:
        self._handlers[event_type].append(handler)

    def dispatch(self, event: DomainEvent) -> None:
        for handler in self._handlers[type(event)]:
            handler(event)
