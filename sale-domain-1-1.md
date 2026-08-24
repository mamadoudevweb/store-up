# Sale Domain — Design

POS-style transaction. Stock is reserved synchronously at checkout; payment is authorized asynchronously by Billing, which owns the only real risk of failure after the fact.

---

## 1. Lifecycle

```
pending ──▶ completed ──▶ returned
   └──────▶ failed
```

- **`pending`** — checkout succeeded, stock reserved, payment not yet authorized.
- **`completed`** — Billing authorized the payment. The only state a return can be requested against.
- **`failed`** — Billing declined/errored on authorization. Terminal; stock released.
- **`returned`** — every line fully refunded. Terminal.

One-way, two branch points, no other transition. Every write that moves `status` guards on the expected current value (compare-and-swap), since duplicate or out-of-order event delivery is routine, not exceptional (§4).

"Partially returned" is never a status — it's `any(SaleLine.refunded_quantity > 0)`, computed on demand. It doesn't gate anything, nothing reacts to it, and it can recur (more partial refunds against the same `completed` sale) — none of which fit a lifecycle state. `returned` itself fires only once every line is fully refunded.

---

## 2. Data model

**Sale** — `id`, `number` (str | None, deferred, see §5), `customer_name` (str | None — walk-in, no buyer account), `seller_account_id` (FK Account), `status`, `payment_method_id` (FK Billing.PaymentMethod, immutable once set), `discount`, `subtotal` (Σ line subtotals), `total` (subtotal − discount), `created_at`, `returned_at`, `failed_at`.

`payment_method_id` references a `PaymentMethod` owned and pre-registered by Billing — not created as part of checkout. With no customer accounts in scope, Billing only needs generic, non-customer-tied records (`cash`, `card`, `mobile`) — effectively a small fixed lookup table rather than a per-customer wallet. Every sale, walk-in or not, resolves to one of these. The cashier/UI selects from Billing's existing list at checkout; Sale never writes to Billing's table, it only stores the id.

**SaleLine** — `id`, `sale_id`, `variant_id`, `quantity` (original sold, never mutated), `unit_price` (snapshotted at sale time — a historical sale shows what was actually charged, not today's price), `discount`, `subtotal`, `refunded_quantity` (denormalized cache; source of truth is the ledger below). Net revenue at any point: `(quantity − refunded_quantity) × unit_price`.

**Refund / RefundLine** — a ledger, not a counter, same pattern as `StockItem`/`StockMovement`: two returns on different dates stay two distinct records. `Refund`: `id`, `sale_id`, `processed_by`, `reason` (free-form for now), `status` (pending | processed | failed — Billing's settlement, independent of `Sale.status`), `created_at`. `RefundLine`: `refund_id`, `sale_line_id`, `quantity`.

---

## 3. Checkout: reserving stock

Stock reservation is synchronous and in-transaction — the only cross-domain *check* that happens *before* a `Sale` exists. `payment_method_id` doesn't add a second one: it's selected from Billing's already-existing, pre-registered methods (§2), so checkout only needs the id the client supplies — no call to Billing to create or validate it before `Sale` is inserted. If the id turns out to be stale or invalid, that surfaces the same way any other authorization problem does: Billing declines and emits `PaymentFailed` (§4).

1. Within the transaction that will insert `Sale`, run the atomic conditional decrement per line (order lines consistently, e.g. by `variant_id`, to avoid cross-checkout deadlocks):
   ```sql
   UPDATE stock_items
   SET quantity_reserved = quantity_reserved + :qty
   WHERE id = :id AND quantity_on_hand - quantity_reserved >= :qty
   ```
2. Any line at 0 rows affected rolls back the whole transaction. **No `Sale` row is ever created** — checkout returns an out-of-stock error directly. Nothing to cancel, nothing to reconcile.
3. On full success: insert `Sale` + `SaleLine`s, `status = pending`, commit, emit `SaleCreated`.

---

## 4. Payment: Billing authorizes

`SaleCreated` → Billing attempts capture → one of:
- `PaymentCaptured(sale_id)` → Sale: `pending → completed`.
- `PaymentFailed(sale_id, reason)` → Sale: `pending → failed`, `failed_at` set, emits `SaleFailed` → Stock releases the reservation.

This is genuinely asynchronous because Billing's response *is* the authorization — it can fail after checkout has already committed, which is exactly why `Sale` can't be `completed` until it's heard from.

Every Sale-side handler reacting to a Billing event must dedupe by `sale_id` — at-least-once delivery plus reconciliation replays (§6) make duplicates a certainty.

---

## 5. Returns: refund a completed sale

Deliberately **not** symmetric with payment. By the time a return is requested, the item is already physically back — that's operationally final regardless of how the money settles.

1. Sale handles the return itself, synchronously, no dependency on Billing: create `Refund` (`status = pending`) + `RefundLine`(s), bump `refunded_quantity`, restock directly via `Stock.adjust_stock(+quantity, reason=return)`, and if every line is now fully refunded, `status: completed → returned`, `returned_at` set.
2. Sale emits `SaleReturned` — a money-only instruction to Billing, not a coordination signal.
3. Billing settles and emits `RefundProcessed(refund_id)` or `RefundFailed(refund_id, reason)`.
4. Sale updates **`Refund.status` only** — `Sale.status` and `refunded_quantity` don't move again. A failed settlement is a billing retry/reconciliation problem, not grounds to un-restock an item or reopen the sale.

---

## 6. Failure handling

**Stuck `pending` sales.** A lost `PaymentCaptured`/`PaymentFailed` event leaves a `Sale` in `pending` indefinitely. Don't resolve with a blind timeout-to-`failed` — that risks contradicting a payment that actually succeeded. Instead, a scheduled job:
1. Selects `pending` sales older than a threshold set from normal Billing latency (minutes, if capture is normally seconds).
2. Queries **Billing's own record** for that `sale_id` — the gateway's actual outcome, not "did an event arrive."
3. Replays the matching event through the same idempotent handlers as the live path.
4. No resolution yet → leave it, recheck next run. Past a much harder ceiling (15+ min) → alert an operator; that's an incident, not something to keep polling.

The checkout UI itself should hold for `completed`/`failed` rather than exposing `pending` as a customer-facing wait — the reconciliation job is a safety net for pipeline failures, not part of normal checkout timing.

---

## 7. Events reference

| Event | Emitted by | Fields | Fires |
|---|---|---|---|
| `SaleCreated` | Sale | `sale_id`, `seller_account_id`, `lines`, `total`, `payment_method_id` | checkout commit, stock reserved |
| `PaymentCaptured` | Billing | `sale_id` | authorization succeeds |
| `PaymentFailed` | Billing | `sale_id`, `reason` | authorization declined/errors |
| `SaleFailed` | Sale | `sale_id` | reacting to `PaymentFailed` |
| `SaleReturned` | Sale | `refund_id`, `sale_id`, `amount` | return fully processed on Sale's side |
| `RefundProcessed` | Billing | `refund_id` | refund settles |
| `RefundFailed` | Billing | `refund_id`, `reason` | refund settlement fails |

`Payment*`/`Refund*` events belong to Billing; `Sale*` events belong to Sale — keep that split explicit so it doesn't blur later.

---

## 8. Operational notes

**Stock decrement stays synchronous**, inside the checkout transaction — deliberately not offloaded to a background consumer. For single-shop scale the lock window is negligible, and it's what lets a stock failure prevent `Sale` from ever being created (§3.2).

**Revenue rollups** (`revenue_by_product_day`, `revenue_by_seller_day`) should be updated on `PaymentCaptured` and `SaleReturned`/`RefundProcessed` — not `SaleCreated`, since a sale still `pending` or later `failed` isn't real revenue. Pair with monthly partitioning on `SaleLine`/`RefundLine` for the rare raw-row query.

**Sale number generation** (deferred): a shared counter + row lock would serialize every sale system-wide. Prefer a date-bucketed Postgres sequence (`nextval()`, lock-free), or assign it asynchronously just after commit — viable only if nothing needs it synchronously in the checkout response (e.g. no instant printed receipt).
