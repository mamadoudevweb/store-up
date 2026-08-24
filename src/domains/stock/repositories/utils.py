"""Stock mappers."""
from __future__ import annotations

from src.core.repositories.utils import Mapper
from src.domains.stock.entities import StockItem, StockMovement
from src.domains.stock.repositories.sql.orms import StockItemModel, StockMovementModel


class StockItemMapper(Mapper[StockItem, StockItemModel]):
    def to_entity(self, model: StockItemModel) -> StockItem:
        return StockItem(
            id=model.id,
            variant_id=model.variant_id,
            quantity_on_hand=model.quantity_on_hand,
            quantity_reserved=model.quantity_reserved,
            low_stock_threshold=model.low_stock_threshold,
        )

    def to_model(self, entity: StockItem, model: StockItemModel | None = None) -> StockItemModel:
        m = model or StockItemModel()
        m.id = entity.id
        m.variant_id = entity.variant_id
        m.quantity_on_hand = entity.quantity_on_hand
        m.quantity_reserved = entity.quantity_reserved
        m.low_stock_threshold = entity.low_stock_threshold
        return m


class StockMovementMapper(Mapper[StockMovement, StockMovementModel]):
    def to_entity(self, model: StockMovementModel) -> StockMovement:
        from src.domains.stock.entities.enums import StockMovementReason, ReferenceType
        return StockMovement(
            id=model.id,
            stock_item_id=model.stock_item_id,
            quantity_change=model.quantity_change,
            reason=StockMovementReason(model.reason),
            reference_type=ReferenceType(model.reference_type),
            reference_id=model.reference_id,
            created_at=model.created_at,
        )

    def to_model(self, entity: StockMovement, model: StockMovementModel | None = None) -> StockMovementModel:
        m = model or StockMovementModel()
        m.id = entity.id
        m.stock_item_id = entity.stock_item_id
        m.quantity_change = entity.quantity_change
        m.reason = entity.reason.value
        m.reference_type = entity.reference_type.value
        m.reference_id = entity.reference_id
        m.created_at = entity.created_at
        return m
