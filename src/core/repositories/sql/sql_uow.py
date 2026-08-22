from types import TracebackType
from typing import Any, Callable
from sqlalchemy.orm import Session
from src.core.repositories.base_uow import BaseUnitOfWork
from src.core.events.dispatcher import EventDispatcher
from src.core.entities.base_entity import Entity

class SqlUnitOfWork(BaseUnitOfWork):
    """Knows nothing about which repositories exist — the concrete set is
    injected. Adding a new domain never means editing this file."""

    def __init__(
        self,
        session_factory: Callable[[], Session],
        dispatcher: EventDispatcher,
        repository_classes: dict[str, type[Any]],
    ) -> None:
        self._session_factory = session_factory
        self._dispatcher = dispatcher
        self._repository_classes = repository_classes
        self._session: Session | None = None
        self._tracked: list[Entity[Any]] = []

    def __enter__(self) -> "SqlUnitOfWork":
        self._session = self._session_factory()
        for attr_name, repo_cls in self._repository_classes.items():
            setattr(self, attr_name, repo_cls(self._session))
        return self

    def track(self, entity: Entity[Any]) -> None:
        """Services register entities that have pending domain events so
        they get dispatched only after a successful commit."""
        self._tracked.append(entity)

    def commit(self) -> None:
        assert self._session is not None
        self._session.commit()
        for entity in self._tracked:
            for event in entity.pull_events():
                self._dispatcher.dispatch(event)
        self._tracked.clear()

    def rollback(self) -> None:
        if self._session is not None:
            self._session.rollback()
        self._tracked.clear()

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        try:
            super().__exit__(exc_type, exc, tb)
        finally:
            if self._session is not None:
                self._session.close()
