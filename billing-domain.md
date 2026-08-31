# Billing Domain — Design

Greenfield, `0%` implemented. Core idea: `Payment` and `RefundSettlement` are the same shape — both append-only attempts ledgers, never a single mutable row. That one pattern, applied twice, is what makes "retryable" and "simple" compatible instead of a tradeoff.

---

## 1. Entities

### PaymentMethod

Small, fixed, pre-registered lookup — not a per-customer wallet (no customer accounts in this system).

| Field | Type | Notes |
|---|---|---|
| `id` | UUID | |
| `name` | str | `"Cash"`, `"Card"`, `"Mobile"` |
| `processor_key` | str | the pluggability hook — e.g. `"cash_manual"` today |
| `is_active` | bool | Card/Mobile can exist as rows now, `is_active = False`, until their processors are real |

### PaymentProcessor (pluggable interface, code not schema)

```python
class ProcessorResult:
    status: Literal["captured", "failed", "pending"]
    processor_reference: str | None
    failure_reason: str | None

class PaymentProcessor(ABC):
    key: ClassVar[str]

    @abstractmethod
    def capture(self, *, amount: int, payment_id: UUID) -> ProcessorResult: ...

    @abstractmethod
    def refund(self, *, amount: int, original_reference: str | None, refund_id: UUID) -> ProcessorResult: ...

PROCESSOR_REGISTRY: dict[str, type[PaymentProcessor]] = {
    "cash_manual": CashProcessor,
    # "card_gateway_x": CardGatewayProcessor,  — added later, zero changes to Payment/Billing service code
}
```

`CashProcessor` is the only implementation today — `capture()` returns `captured` immediately, no external call, `processor_reference = None` (nothing to reference).

### Payment — attempts ledger, 1:N with Sale

| Field | Type | Notes |
|---|---|---|
| `id` | UUID | |
| `sale_id` | UUID | |
| `attempt_number` | int | 1, 2, 3... |
| `payment_method_id` | UUID | **can differ per attempt** — card declined, retry with cash is attempt 2 with a different method |
| `processor_key` | str | snapshotted per attempt |
| `amount` | int | |
| `status` | enum | `pending \| captured \| failed` |
| `processor_reference` | str \| None | |
| `idempotency_key` | str | per attempt — guards a client resubmitting the *same* attempt (timeout/dropped connection) from double-capturing |
| `failure_reason` | str \| None | |
| `created_at` | datetime | |

Consequence: **`Sale.payment_method_id` is removed.** It can't mean one thing once payment method varies per attempt — "how was this actually paid" is answered by querying the successful `Payment` row, not stored redundantly on `Sale`.

### RefundSettlement — attempts ledger, same shape, 1:N with Refund

| Field | Type | Notes |
|---|---|---|
| `id` | UUID | |
| `refund_id` | UUID | Sale's `Refund` id, copied via event — not a live cross-domain FK |
| `payment_id` | UUID | FK → the `Payment` attempt that actually captured — resolves which `processor_key` to reverse through; **you can't refund a cash sale through a card processor** |
| `attempt_number` | int | |
| `amount` | int | |
| `processor_key` | str | copied from the resolved `Payment` |
| `status` | enum | `pending \| processed \| failed` |
| `processor_reference` | str \| None | |
| `failure_reason` | str \| None | |
| `created_at` | datetime | |

---

## 2. Actions

- **`capture(sale_id, payment_method_id, amount)`** — creates `Payment` attempt 1, calls the resolved processor.
- **`retry_payment(sale_id, payment_method_id?)`** — explicit, never automatic. Before creating attempt N+1, checks whether the *current* attempt already resolved to `captured` (guards the idempotent-retry case — a client resubmitting because of a timeout, not a real decline — from creating a phantom second charge). If genuinely `failed`, creates the next attempt, optionally against a different `payment_method_id`.
- **`settle_refund(refund_id, payment_id, amount)`** — creates `RefundSettlement` attempt 1 against the `Payment` that originally captured, calls that same processor's `.refund()`.
- **Retry on refund settlement is manual only** — same ledger shape, no automatic retry logic in Billing itself; an operator re-triggers `settle_refund` for a `failed` settlement.

---

## 3. Events

| Event | Fields | Fires |
|---|---|---|
| `PaymentCaptured` | `sale_id`, `payment_id`, `attempt_number` | on successful capture — **any** attempt, not just the first |
| `PaymentFailed` | `sale_id`, `payment_id`, `attempt_number`, `reason` | on a declined/errored attempt — does **not** fail the `Sale` by itself, see §4 |
| `RefundProcessed` | `refund_id`, `settlement_id` | on successful settlement — Sale reacts by restocking and flipping `Refund`/`Sale` status together, see §5 |
| `RefundFailed` | `refund_id`, `settlement_id`, `reason` | on a failed settlement attempt |

---

## 4. How this changes Sale's status model

This is the one place Billing's design reaches back and changes something already written into `sale-domain.md` — flagged explicitly rather than left as an implicit side effect. **A payment decline no longer auto-fails the `Sale`.** `pending` now persists across multiple attempts. Only two paths out of `pending → failed`, both distinguished by a new `Sale.failure_reason`:

- **Automatic:** Stock reservation fails → `failed`, `reason = stock_unavailable`. Not retryable — availability isn't something a client action fixes.
- **Manual:** cashier/client gives up after ≥1 declined attempts → explicit `abandon_sale(sale_id)` → `failed`, `reason = abandoned`.

`Sale` needs a new action (`abandon_sale`) it didn't have before, and its event-reaction to Billing changes from "react to `PaymentFailed` by failing" to "react to `PaymentFailed` by doing nothing — stay `pending`, the client decides what happens next."

---

## 5. Sequencing with Stock (already decided, restated here for completeness)

Billing does **not** react to `SaleCreated` directly.

```
SaleCreated
  → Stock attempts atomic reservation
      success → StockReserved(sale_id)              → Billing attempts capture
      failure → StockReservationFailed(sale_id, ...) → Sale: mark_failed(reason=stock_unavailable)
                                                          — Billing never invoked at all, not invoked-then-reversed
```

Chosen specifically so a stock failure never requires reversing an already-captured payment — avoiding compensating-transaction/saga complexity entirely by making the failure path never reach Billing in the first place.

---

## 6. Refunds: restock and status move together, at settlement completion

Both `Sale`/`Refund` status flip and the actual stock increase happen atomically, triggered by `RefundProcessed` — never split across two moments (resolves the inconsistency risk of restocking and status-flipping at different times).

**Accepted gap, on purpose:** between a physical return and `RefundProcessed` firing — and indefinitely, if settlement fails and isn't manually retried — the system shows the item as sold while it's physically back on the shelf. Acceptable for a single-shop setting where a cashier can just look at the shelf, and where Cash (the only real processor today) never fails. Revisit once Card/Mobile ship and refund declines become a real, recurring case rather than a theoretical one.

---

## 7. Reconciliation (updated for two-stage sequencing)

A stuck `pending` `Sale` can now be stuck at either stage — the reconciliation job needs to check which:

1. No `Payment` row exists at all for this `sale_id` → still waiting on Stock; something's wrong *upstream* of Billing entirely, this isn't Billing's problem to resolve.
2. A `Payment` row exists but is stale (`pending` past a threshold, or the processor never called back) → the original Billing-side reconciliation applies: query Billing's own record, replay the matching event through the same idempotent handler.
