"""Inventory mappers."""
from __future__ import annotations

from src.core.repositories.utils import Mapper
from src.domains.inventory.entities import InventoryItem, StockMovement
from src.domains.inventory.repositories.sql.orms import InventoryItemModel, StockMovementModel


class InventoryItemMapper(Mapper[InventoryItem, InventoryItemModel]):
    def to_entity(self, model: InventoryItemModel) -> InventoryItem:
        return InventoryItem(
            id=model.id,
            product_id=model.product_id,
            quantity_on_hand=model.quantity_on_hand,
            quantity_reserved=model.quantity_reserved,
            low_stock_threshold=model.low_stock_threshold,
        )

    def to_model(self, entity: InventoryItem, model: InventoryItemModel | None = None) -> InventoryItemModel:
        m = model or InventoryItemModel()
        m.id = entity.id
        m.product_id = entity.product_id
        m.quantity_on_hand = entity.quantity_on_hand
        m.quantity_reserved = entity.quantity_reserved
        m.low_stock_threshold = entity.low_stock_threshold
        return m


class StockMovementMapper(Mapper[StockMovement, StockMovementModel]):
    def to_entity(self, model: StockMovementModel) -> StockMovement:
        return StockMovement(
            id=model.id,
            product_id=model.product_id,
            quantity_change=model.quantity_change,
            reason=model.reason,
            reference_id=model.reference_id,
            created_at=model.created_at,
        )

    def to_model(self, entity: StockMovement, model: StockMovementModel | None = None) -> StockMovementModel:
        m = model or StockMovementModel()
        m.id = entity.id
        m.product_id = entity.product_id
        m.quantity_change = entity.quantity_change
        m.reason = entity.reason
        m.reference_id = entity.reference_id
        m.created_at = entity.created_at
        return m
