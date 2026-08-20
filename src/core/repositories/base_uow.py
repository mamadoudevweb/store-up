from abc import ABC, abstractmethod
from types import TracebackType

class BaseUnitOfWork(ABC):
    """Owns the transaction boundary and aggregates every repository.
    Services obtain a UoW from a factory; repositories never open sessions."""

    def __enter__(self) -> "BaseUnitOfWork":
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        if exc_type is not None:
            self.rollback()
        else:
            self.commit()

    @abstractmethod
    def commit(self) -> None: ...

    @abstractmethod
    def rollback(self) -> None: ...
