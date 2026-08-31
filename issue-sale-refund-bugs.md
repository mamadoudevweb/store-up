# [Sale] Refund flow corrupts status, never restocks, and crosses Stock's repository boundary

**Type:** Bug
**Domain:** Sale (+ Stock coupling)
**Severity:** High — data integrity (sale status) and inventory accuracy (stock never restocked)

## Context

Found during code review of the Sale domain implementation against the design doc (`sale-domain.md`, `sale-billing-flow.mermaid`). Three separate problems in the refund path, all in `RefundService` / `SaleService` / `Sale.process_refund()`.

---

## 1. `Sale.process_refund()` flips `status` to `RETURNED` unconditionally

**Location:** `src/domains/sale/entities/sale.py`, `Sale.process_refund()`

```python
def process_refund(self, refund_id: uuid.UUID, amount: int) -> None:
    if self.status not in (SaleStatus.COMPLETED, SaleStatus.RETURNED):
        raise InvalidSaleStateError("Sale must be completed to process a refund")
    self.status = SaleStatus.RETURNED
    self.returned_at = datetime.now(timezone.utc)
    self.register_event(SaleReturned(refund_id=refund_id, sale_id=self.id, amount=amount))
```

**Problem:** No check that every `SaleLine.refunded_quantity` equals its `quantity` before flipping `status`. Called from `SaleService.process_refund()` every time a `RefundRequested` event is handled — including a partial refund of 1 unit out of a 10-unit sale.

**Impact:** Any partial refund marks the entire `Sale` as fully `RETURNED`. Once that happens, `Sale.status` can never distinguish "fully returned" from "one item came back" again — the information is destroyed at write time, not just displayed wrong.

**Fix:** Guard the transition — `process_refund()` (or the caller, `SaleService.process_refund()`, which already has the updated `refunded_quantity` values in hand) must check `all(line.refunded_quantity == line.quantity for line in sale.lines)` before flipping `status`/`returned_at`/emitting `SaleReturned`. If not all lines are fully refunded, `status` stays `COMPLETED` — nothing else changes.

---

## 2. Refunds never restock — no call to Stock anywhere in the refund path

**Location:** `RefundService.request_refund()`, `SaleService.process_refund()`, `Refund.mark_processed()` / `mark_failed()`

**Problem:** None of the refund-path methods call `atomic_release`, `adjust_stock`, or any other Stock method. `SaleLine.refunded_quantity` and `Refund`/`RefundLine` rows get created and updated correctly — the ledger is right — but the physical stock consequence never happens.

**Impact:** A refunded/returned item is never added back to `StockItem.quantity_on_hand`. Every return silently understocks the shop's real inventory relative to what the system shows as available.

**Fix:** Restocking is settlement-gated and event-based. After Billing settles the refund, Sale handles `RefundProcessed` and emits `RefundCompleted` with each returned variant and quantity. Stock consumes `RefundCompleted` and records the corresponding `reason=return` increase. Sale never calls `StockService` or `uow.stock_items` directly for this flow.

---

## 3. Sale reaches directly into Stock's repository

**Location:** `SaleService.checkout()` and `SaleService.fail_sale()`

```python
success = getattr(uow, "stock_items").atomic_reserve(variant_id, qty)
...
getattr(uow, "stock_items").atomic_release(line.variant_id, line.quantity)
```

**Problem:** `SaleService` calls the shared UoW's `stock_items` repository directly, making Sale perform Stock-owned reservation and release work inside Sale's synchronous flow instead of handing that work to Stock through domain events.

**Impact:** Sale's behavior is coupled to Stock's schema and transaction boundary rather than Stock's event contract. Internal changes to how Stock stores or validates reservations can silently break Sale and prevent independent retries.

**Fix:** Remove both synchronous cross-domain calls. Sale emits `SaleCreated` for Stock to reserve inventory and `SaleFailed` for Stock to release any reservation. Stock owns those event handlers and invokes its own service/repository locally; Sale must not call `StockService` directly.

---

## Acceptance criteria

- A partial refund (not all lines fully refunded) leaves `Sale.status == COMPLETED`.
- A refund that brings every line to `refunded_quantity == quantity` sets `Sale.status = RETURNED` exactly once.
- Every processed refund results in a corresponding stock increase on the affected `StockItem`(s) — verified via `StockMovement` records, not just `quantity_on_hand`.
- `SaleService` contains no direct reference to `uow.stock_items` (or any other cross-domain repository) and makes no synchronous Stock service calls; coordination occurs through domain events.
- Test coverage: a partial-refund test asserting `status` stays `COMPLETED`; a full-refund test asserting `status` becomes `RETURNED` and a `StockMovement` exists; existing `test_sale_services.py`/`test_refund.py` updated to cover the corrected behavior, not just the current (buggy) one.

## Out of scope

- Payment-processor-specific settlement and reconciliation behavior beyond the `RefundProcessed` success gate.
- `SaleFailed` having no subscribers — not broken, just currently unused; worth confirming intent separately, not blocking this ticket.
