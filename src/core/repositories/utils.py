from typing import Any, Protocol, TypeVar
from src.core.entities.base_entity import Entity

E = TypeVar("E", bound=Entity[Any])
M = TypeVar("M")

class Mapper(Protocol[E, M]):
    def to_entity(self, model: M) -> E: ...
    def to_model(self, entity: E, model: M | None = None) -> M: ...
