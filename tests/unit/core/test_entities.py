"""Unit tests for core entities."""
from __future__ import annotations

from dataclasses import dataclass

from src.core.entities.base_entity import Entity
from src.core.entities.events import DomainEvent
from src.core.entities.pagination import Pagination, EntityFilter


@dataclass(kw_only=True, frozen=True)
class DummyEvent(DomainEvent):
    payload: str


@dataclass(kw_only=True)
class DummyEntity(Entity):
    name: str


def test_entity_event_registration():
    entity = DummyEntity(name="test")
    event1 = DummyEvent(payload="1")
    event2 = DummyEvent(payload="2")

    entity.register_event(event1)
    entity.register_event(event2)

    # Internal state is populated
    assert len(entity._events) == 2

    # Pulling events clears them
    pulled = entity.pull_events()
    assert len(pulled) == 2
    assert pulled[0] == event1
    assert pulled[1] == event2
    assert len(entity._events) == 0


def test_pagination_arithmetic():
    # 5 items total, 2 per page -> 3 pages
    pag = Pagination(items=[1, 2], page=1, limit=2, total=5)
    assert pag.total_pages == 3

    # 4 items total, 2 per page -> 2 pages
    pag = Pagination(items=[1, 2], page=1, limit=2, total=4)
    assert pag.total_pages == 2

    # 0 items total, 2 per page -> 1 page (minimum 1 page)
    pag = Pagination(items=[], page=1, limit=2, total=0)
    assert pag.total_pages == 1
