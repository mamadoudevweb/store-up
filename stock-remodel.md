# Stock Domain — Remodel (renamed from Inventory)

Renames `Inventory` → `Stock` (every event already said `Stock*` — `StockAdjusted`, `StockReserved`, `StockShipped` — this resolves that mismatch rather than introducing new naming), and re-keys everything from `product_id` to `variant_id` now that `ProductVariant` is the sellable unit (see `catalog-remodel.md`).

---

## 1. Why

- Every event in this domain already said "Stock," not "Inventory" — the entity/domain name was the odd one out.
- `Product` no longer carries price/SKU — `ProductVariant` does. Stock has to be tracked per-variant (Red/M and Blue/L have independent stock), so everything keying off `product_id` moves to `variant_id`.
- "Inventory" reads as a bigger concept (warehouses, locations, lot/batch tracking, valuation) than what this domain actually does today (on-hand/reserved quantity + a movement ledger, per variant). "Stock" doesn't overpromise. If multi-warehouse tracking gets added later, that's the point where the bigger name would actually be earned.

---

## 2. Entities

### StockItem (renamed from InventoryItem)

| Field | Type | Notes |
|---|---|---|
| `id` | UUID | |
| `variant_id` | UUID | renamed from `product_id`; FK → ProductVariant, unique — one `StockItem` per variant |
| `quantity_on_hand` | int | |
| `quantity_reserved` | int | |
| `low_stock_threshold` | int | |
| `available_quantity` | — | computed property (`on_hand - reserved`), not a stored column — unchanged |

Kept 1:1 with `ProductVariant` for now, deliberately — if per-warehouse stock gets added later, `StockItem` is where that granularity changes (e.g. keyed by `(variant_id, warehouse_id)` instead of `variant_id` alone), not something bolted onto `StockMovement`.

### StockMovement

References `StockItem`, not `ProductVariant` directly — so it automatically inherits whatever granularity `StockItem` has (including a future per-warehouse split) without its own schema change.

| Field | Type | Notes |
|---|---|---|
| `id` | UUID | |
| `stock_item_id` | UUID | renamed from `product_id`; FK → StockItem (not ProductVariant) |
| `quantity_change` | int | |
| `reason` | enum | `StockMovementReason` — see below |
| `reference_type` | enum | `ReferenceType` — see below |
| `reference_id` | str \| None | unchanged — still no FK, since the referenced row may live in another domain (or not exist yet) |
| `created_at` | datetime | |

### Reason / reference enums

Python enum + DB `CHECK` constraint, not lookup tables — the distinguishing factor from `Attribute`/`AttributeValue` (which *are* lookup tables) is that catalog managers add new attribute values through the app at runtime, while a stock movement reason is only ever set by a specific line of service code (`ship_stock` always writes `order_shipped`). A closed set that only changes when new code ships is a code concept, not a database catalog.

```
StockMovementReason:
  restock
  order_shipped
  manual_adjustment
  return
  damage

ReferenceType:
  sale
  purchase_order
  manual_adjustment
  return
```

If ops/support ever need to add a new reason without a deploy, that's the signal to revisit this as a lookup table instead — not expected to be true here.

---

## 3. Events

Every event carries **both** `stock_item_id` (the raising entity's own ID — standard across every domain's events) **and** `variant_id` (the field other domains actually recognize; nothing outside Stock knows what a `StockItem` is).

| Event | Fields |
|---|---|
| `StockItemCreated` **(new — `create()` registered none before)** | `stock_item_id`, `variant_id` |
| `StockAdjusted` | `stock_item_id`, `variant_id`, `quantity_change`, `new_quantity_on_hand` |
| `StockReserved` | `stock_item_id`, `variant_id`, `quantity`, `reference_type`, `reference_id` |
| `StockReleased` | `stock_item_id`, `variant_id`, `quantity`, `reference_type`, `reference_id` |
| `StockShipped` | `stock_item_id`, `variant_id`, `quantity`, `reference_type`, `reference_id` |
| `LowStockAlert` | `stock_item_id`, `variant_id`, `available_quantity`, `threshold` |
| `OutOfStock` | `stock_item_id`, `variant_id` |

`reserve_stock`/`release_stock`/`ship_stock` on the entity change signature accordingly — `reference_id: str | None` becomes `reference_type: ReferenceType, reference_id: str | None`, which ripples through the service layer, not just the two tables.

---

## 4. Event handler change

`event_handlers.py` currently subscribes `on_product_created` to Catalog's `ProductCreated`, auto-provisioning a zero-stock item. This becomes `on_variant_created`, subscribing to Catalog's `VariantCreated` instead — one `StockItem` per variant, not per product (a product with 3 variants needs 3 `StockItem` rows, not 1).

While rewriting this handler: drop the explicit `uow.commit()` inside its own `with` block — same redundant-commit pattern already removed from RBAC; the `with` block commits on clean exit on its own.

---

## 5. Relationships (text ERD)

```
ProductVariant 1───1 StockItem
StockItem 1───* StockMovement
```

---

## 6. Migration note

- Depends on the Catalog remodel shipping first — `StockItem.variant_id` has no valid target until `ProductVariant` rows exist. Sequence: migrate Catalog (Product → Product + ProductVariant) before migrating Stock.
- `inventory_items` → `stock_items`, `product_id` → `variant_id`: each existing `InventoryItem.product_id` maps to that product's (post-Catalog-migration) default variant — same one-variant-per-legacy-product mapping described in the Catalog migration note.
- `stock_movements.product_id` → `stock_item_id`: once `stock_items` exists with the mapping above, `stock_movements.product_id` resolves to the `StockItem` for that variant.
- Existing free-text `reason` values need a one-time mapping pass onto `StockMovementReason` — anything that doesn't cleanly match one of the five values needs a manual decision, same caution as the Catalog `status` migration (no blanket formula).
- Existing `reference_id` values with no `reference_type` — likely all inferable as `"sale"` if that's the only source that existed before this remodel, but worth confirming against actual data rather than assuming.
