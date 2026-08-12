"""
Domain Event infrastructure.

Every operation emits at least one event. Subscribers register handlers
and only process the events they care about. The EventBus is synchronous
and in-process — swap the dispatch strategy to async/queue without
touching entity or subscriber code.
"""
from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable, ClassVar, Type
from uuid import UUID, uuid4

logger = logging.getLogger(__name__)


@dataclass
class DomainEvent:
    """Base class for all domain events.

    Each event carries a unique ID and UTC timestamp. Subclasses add
    domain-specific fields as dataclass fields.
    """

    event_id: UUID = field(default_factory=uuid4, init=False)
    occurred_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc), init=False
    )

    # Subclasses declare this to identify the event type for routing.
    event_type: ClassVar[str] = "domain.event"


class EventBus:
    """
    Simple synchronous in-process event bus.

    Usage:
        bus = EventBus()

        @bus.subscribe(ProductCreated)
        def on_product_created(event: ProductCreated) -> None:
            ...

        bus.publish(ProductCreated(product_id=...))
    """

    def __init__(self) -> None:
        self._handlers: dict[Type[DomainEvent], list[Callable[[DomainEvent], None]]] = (
            defaultdict(list)
        )

    def subscribe(
        self, event_type: Type[DomainEvent]
    ) -> Callable[[Callable[[DomainEvent], None]], Callable[[DomainEvent], None]]:
        """Decorator: register a handler for a specific event type."""
        def decorator(
            handler: Callable[[DomainEvent], None]
        ) -> Callable[[DomainEvent], None]:
            self._handlers[event_type].append(handler)
            return handler
        return decorator

    def register(
        self, event_type: Type[DomainEvent], handler: Callable[[DomainEvent], None]
    ) -> None:
        """Imperatively register a handler."""
        self._handlers[event_type].append(handler)

    def publish(self, event: DomainEvent) -> None:
        """Dispatch an event to all registered handlers synchronously."""
        handlers = self._handlers.get(type(event), [])
        if not handlers:
            logger.debug("No handlers registered for event %s", type(event).__name__)
            return
        for handler in handlers:
            try:
                handler(event)
            except Exception:
                logger.exception(
                    "Handler %s failed processing event %s",
                    handler.__name__,
                    type(event).__name__,
                )

    def publish_all(self, events: list[DomainEvent]) -> None:
        """Dispatch a list of events in order."""
        for event in events:
            self.publish(event)


# ── Singleton bus — injected into services by the app factory ──────────────────
event_bus = EventBus()
