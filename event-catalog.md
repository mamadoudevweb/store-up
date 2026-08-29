# Event Catalog — Consumers & Reactions

Every event in the system, who owns it, who consumes it, and what the consumer does. This is the single place all four domains' event contracts have to agree with each other — individual domain docs each got this partly right in isolation; three things below only became visible once put side by side (flagged inline).

---

## 1. Catalog → Stock

| Event | Owner | Payload | Consumer | Reaction |
|---|---|---|---|---|
| `VariantCreated` | Catalog | `variant_id`, `product_id` | Stock | Creates a `StockItem` for the variant, `quantity_on_hand = 0`. Emits `StockItemCreated`. |
| `ProductStatusChanged` / `VariantStatusChanged` | Catalog | `product_id`/`variant_id`, `status` | *(none committed yet)* | Candidate: Notification, if "this went archived" is worth surfacing. Not required for MVP — noted, not designed further here. |

Everything else Catalog-owned (`ProductUpdated`, `ProductImage*`, `Attribute*`, etc.) has no consumers today — internal to Catalog, listed in `catalog-remodel.md` §5 for completeness, not repeated here.

---

## 2. Sale ↔ Stock ↔ Billing — the real coordination

This is where the three domains' independently-designed pieces have to interlock exactly right. Full sequence:

### 2.1 Checkout

| Event | Owner | Payload | Consumer | Reaction |
|---|---|---|---|---|
| `SaleCreated` | Sale | `sale_id`, `lines: [{variant_id, quantity}]`, `amount`, `payment_method_id` | Stock | Attempts the atomic conditional reservation (§8 of `sale-domain.md`) for every line, in one local transaction. |

**`payment_method_id` on this event is the requested method for the *first* payment attempt — it is not stored anywhere on `Sale` itself** (removed per `billing-domain.md` §1, since method now varies per `Payment` attempt). It exists only as a value passed through this one event to seed `capture()`'s first attempt. Worth stating explicitly since it's easy to assume a field on an event implies a column somewhere, and here it doesn't.

### 2.2 Reservation outcome — gates whether Billing is ever invoked

| Event | Owner | Payload | Consumer | Reaction |
|---|---|---|---|---|
| `StockReserved` | Stock | `stock_item_id`, `variant_id`, `sale_id` (as `reference_id`, `reference_type="sale"`) | Billing | Calls `capture(sale_id, payment_method_id, amount)` — attempt 1. |
| **`StockReservationFailed`** *(new — didn't exist before this catalog, only success was named)* | Stock | `sale_id`, `variant_id`, `reason` | Sale | `mark_failed(reason=stock_unavailable)`. **Billing is never invoked at all** — not invoked-then-reversed, genuinely skipped, which is the entire point of the sequencing decision (avoids ever needing to reverse a captured payment). |

### 2.3 Payment outcome

| Event | Owner | Payload | Consumer | Reaction |
|---|---|---|---|---|
| `PaymentCaptured` | Billing | `sale_id`, `payment_id`, `attempt_number` | Sale | `mark_completed()` — `status → completed`, emits `SaleCompleted` (below). |
| `PaymentCaptured` | Billing | (same) | Stock | See §2.4 below. |
| **`SaleCompleted`** *(exists in code — `src/domains/sale/entities/sale.py`, zero consumers wired anywhere; missing from the original version of this catalog entirely)* | Sale | `sale_id` | Reporting rollups, Notification | **This, not `PaymentCaptured`, is the correct consumption point** for anything outside Sale/Billing that cares "a sale happened" — a revenue rollup or a receipt notification shouldn't need to know Billing's event names to react to a completed sale. Revenue-per-product/seller rollups (§5 of `sale-domain.md`'s scalability section) should react to `SaleCompleted`/`RefundProcessed`, not `SaleCreated` — a `pending` or `failed` sale was never real revenue. |
| `PaymentFailed` | Billing | `sale_id`, `payment_id`, `attempt_number`, `reason` | Sale | **Nothing.** `status` stays `pending`. Per `billing-domain.md` §4, a decline no longer auto-fails the sale — the client decides whether to `retry_payment` or `abandon_sale`. |

### 2.4 The gap this catalog surfaces: nothing ever converts a reservation into an actual stock decrement

Every domain doc assumed *something* eventually calls Stock's `ship_stock` (the action that actually decrements `quantity_on_hand`, not just `quantity_reserved`) — but tracing every event end to end, nothing ever triggers it. `StockReserved` only reserves. Once sequencing split "reserve" (before payment) from "the sale is actually done" (after payment), **shipping needs its own trigger**, and `PaymentCaptured` is it:

| Event | Owner | Payload | Consumer | Reaction |
|---|---|---|---|---|
| `PaymentCaptured` | Billing | `sale_id`, ... | Stock | Converts the existing reservation into an actual decrement (`ship_stock` per line) — `quantity_on_hand -= qty`, `quantity_reserved -= qty`. Emits `StockShipped`. |

### 2.5 Abandonment — releasing a reservation that was never converted

| Event | Owner | Payload | Consumer | Reaction |
|---|---|---|---|---|
| `SaleFailed` | Sale | `sale_id`, `reason` (`stock_unavailable \| abandoned`) | Stock | Releases any reservation for `sale_id`, idempotently — a no-op if `reason = stock_unavailable` (nothing was ever reserved for a sale that failed reservation itself), a real release if `reason = abandoned` (reservation existed, payment never captured). **One handler, no branching on `reason` needed** — release-if-exists covers both cases correctly without the handler needing to know why it failed. |

This also resolves something now stale: the bug ticket's proposed fix for issue #3 ("replace the direct `uow.stock_items` call with a call to `StockService`") assumed `SaleService.checkout()`/`fail_sale()` should still call Stock *synchronously*, just through the right layer. **That's superseded** — per the sequencing decision, `checkout()` shouldn't call Stock at all anymore, synchronously or otherwise; it creates `Sale` in `pending` and emits `SaleCreated`, full stop. Same for `fail_sale()` — it no longer calls `atomic_release` itself; that's now Stock's own reaction to consuming `SaleFailed`. The fix for issue #3 is "delete the direct calls entirely," not "redirect them through a service."

---

## 3. Refunds — Sale ↔ Billing ↔ Stock

| Event | Owner | Payload | Consumer | Reaction |
|---|---|---|---|---|
| `RefundRequested` | Sale | `refund_id`, `sale_id`, `lines: [{sale_line_id, quantity}]`, `amount` | Billing | Resolves the original `Payment` for `sale_id` → its `processor_key`. Calls `settle_refund`. |
| `RefundProcessed` | Billing | `refund_id`, `settlement_id` | Sale | Bumps `refunded_quantity` per line, `Refund.status = processed`. **Emits `RefundCompleted`** (below) always, and **`SaleReturned`** only if every line is now fully refunded. |
| `RefundFailed` | Billing | `refund_id`, `settlement_id`, `reason` | Sale | `Refund.status = failed`. Nothing else changes — no restock, no status flip. Manual retry only (`settle_refund` re-triggered by an operator), per `billing-domain.md` §2. |

### 3.1 The second gap this catalog surfaces: restocking needs its own event, distinct from `SaleReturned`

`SaleReturned` was always defined as firing only when *every* line is fully refunded (the whole-sale status transition). But restocking has to happen on **every** processed refund — partial or full, not just the one that happens to complete the sale. Reusing `SaleReturned` for both would mean a partial refund never restocks at all (exactly bug #2 from `issue-sale-refund-bugs.md`, reintroduced through the event design instead of a missing method call). These need to be two separate events:

| Event | Owner | Payload | Consumer | Reaction |
|---|---|---|---|---|
| **`RefundCompleted`** *(new)* | Sale | `refund_id`, `sale_id`, `lines: [{variant_id, quantity}]` | Stock | `adjust_stock(+quantity, reason=return)` per line. Fires on **every** processed refund. |
| `SaleReturned` | Sale | `sale_id` | *(reporting/Notification, not required for correctness)* | Purely the whole-sale-status signal — same reasoning as keeping `ProductStatusChanged` separate from `ProductUpdated`. Fires only when refunded_quantity reaches quantity on every line. |

Both are emitted by `Sale` in reaction to `RefundProcessed`, in the same handler — `RefundCompleted` unconditionally, `SaleReturned` conditionally.

---

## 4. Everything else (unchanged from each domain's own doc)

| Event | Owner | Consumer | Reaction |
|---|---|---|---|
| `StockAdjusted`, `LowStockAlert`, `OutOfStock` | Stock | Notification | Surfaces an alert/warning to shop staff. No state change elsewhere. |
| `PaymentFailed`, `RefundFailed` | Billing | *(candidate: Notification)* | Operational visibility only — not required for correctness, worth adding once Notification exists, so staff see repeated declines/failed settlements without querying the DB directly. |

---

## 5. Summary — four things this catalog changed or added, none of which existed cleanly before

1. **`StockReservationFailed`** — named and formalized; previously only the success path (`StockReserved`) had a clear event.
2. **`PaymentCaptured` triggers `ship_stock` on Stock** — a real gap. Nothing in any prior doc ever converted a reservation into an actual on-hand decrement once reserve and ship were split by the sequencing decision.
3. **`RefundCompleted`, separate from `SaleReturned`** — without this split, restocking silently only happens on the refund that completes a sale, reproducing bug #2 through the event design rather than through a missing method call.
4. **`SaleCompleted` exists in the code (`Sale.mark_completed()` already registers it) but was missing from this catalog entirely, and has zero consumers wired anywhere.** Reporting rollups and Notification should consume this — a Sale-domain-owned signal — rather than `PaymentCaptured`, a Billing-domain concept that nothing outside Sale/Billing should need to know about.

And one fix superseded: issue #3's proposed remedy (call `StockService` instead of the repository) is replaced by removing the synchronous Stock calls from `SaleService` entirely, now that reservation is Stock's own reaction to `SaleCreated`.

**Same shape of gap, different domain, not designed here:** `AccountSuspended` (`accounts/entities/account.py`) and `RoleRevoked` (`accounts/services/account_role.py`) both exist in code with zero consumers — same pattern as `SaleCompleted` before this update. Whether Sale should care about a seller's account being suspended or a role being revoked mid-shift is the open question from the previous message that wasn't answered yet, not something resolved by this pass.
