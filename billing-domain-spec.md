# Billing Domain — Specification

**Status:** Draft, ready for implementation
**Supersedes:** `billing-domain.md` (informal design doc — decisions carried forward, formalized below)
**Related:** `sale-domain.md`, `event-catalog.md`, `stock-remodel.md`

---

## 1. Purpose & Scope

Billing owns payment authorization and refund settlement for Sale. It is the only domain permitted to hold or reference payment-processor state. This document is the authoritative contract for anyone implementing, consuming, or auditing this domain — it formalizes decisions made informally in `billing-domain.md` and adds what an informal design pass doesn't: concurrency guarantees, security/compliance boundaries, observability requirements, and a formal error taxonomy.

**In scope:** payment capture, payment retry, refund settlement, pluggable processor integration, reconciliation.
**Out of scope (explicitly):** stored/tokenized payment methods per customer (no customer accounts exist), subscriptions or recurring billing, multi-currency, tax calculation, dispute/chargeback handling. Any of these entering scope later requires a new spec revision, not an extension of this one.

---

## 2. Terminology

| Term | Definition |
|---|---|
| **Capture** | A single attempt to charge a `Sale` through a processor. |
| **Attempt** | One row in the `Payment` or `RefundSettlement` ledger — one try, successful or not. |
| **Processor** | A pluggable implementation of `PaymentProcessor` handling one payment method's actual authorization/settlement. |
| **Settlement** | An attempt to reverse a prior capture (a refund). |
| **Terminal state** | A `status` value an attempt row never transitions out of once reached (`captured`, `failed` for `Payment`; `processed`, `failed` for `RefundSettlement`). |

---

## 3. Design principles (carried forward, stated as constraints)

- **P1 — Attempts are immutable once terminal.** No `Payment` or `RefundSettlement` row is ever updated after reaching a terminal `status`. A retry is a new row, never a mutation of an old one. This is what makes the audit trail trustworthy — see §9.
- **P2 — Retry is always explicit, never automatic.** No code path in this domain silently creates a new attempt. `retry_payment`/manual settlement retry are the only entry points, both operator/client-initiated.
- **P3 — Billing never gates on itself.** Whether Billing is invoked at all is decided upstream (Stock's reservation outcome, per `event-catalog.md` §2.2) — Billing has no opinion on stock, and no code path here should ever need to know about it.
- **P4 — One money-moving action per domain event.** Each of `SaleCreated`→capture and `RefundRequested`→settle is a single, complete unit of work — no partial-attempt state is ever visible outside a transaction boundary.

---

## 4. Domain model

### 4.1 PaymentMethod

| Field | Type | Constraints |
|---|---|---|
| `id` | UUID | PK |
| `name` | str | unique, not null |
| `processor_key` | str | not null, must exist in `PROCESSOR_REGISTRY` at startup validation (§6.4) |
| `is_active` | bool | default `false` |

### 4.2 Payment

| Field | Type | Constraints |
|---|---|---|
| `id` | UUID | PK |
| `sale_id` | UUID | not null, indexed |
| `attempt_number` | int | not null; unique together with `sale_id` |
| `payment_method_id` | UUID | FK → PaymentMethod, not null |
| `processor_key` | str | not null — snapshotted at attempt creation, never re-read from `PaymentMethod` after |
| `amount` | int | not null, `> 0` |
| `status` | enum | `pending \| captured \| failed` — see §5.1 for legal transitions |
| `processor_reference` | str \| null | populated only on `captured`; never contains cardholder data, see §9.1 |
| `idempotency_key` | str | not null, **unique** (§7.2) |
| `failure_reason` | str \| null | populated only on `failed` |
| `created_at` | datetime | not null |
| `resolved_at` | datetime \| null | set when `status` leaves `pending` |

**Invariant, enforced at the database, not just application logic:** at most one `Payment` row per `sale_id` may have `status = pending` at any time (partial unique index on `sale_id` where `status = 'pending'`). This is what prevents a race between two concurrent capture attempts for the same sale — see §7.1.

### 4.3 RefundSettlement

| Field | Type | Constraints |
|---|---|---|
| `id` | UUID | PK |
| `refund_id` | UUID | not null, indexed — Sale's `Refund.id`, copied via event, never a live FK across the domain boundary |
| `payment_id` | UUID | FK → Payment, not null — the attempt that originally captured; resolves which `processor_key` must be reversed through |
| `attempt_number` | int | not null; unique together with `refund_id` |
| `amount` | int | not null, `> 0` |
| `processor_key` | str | not null, copied from the resolved `Payment` |
| `status` | enum | `pending \| processed \| failed` |
| `processor_reference` | str \| null | |
| `failure_reason` | str \| null | |
| `created_at` | datetime | not null |
| `resolved_at` | datetime \| null | |

**Same invariant as §4.2, scoped to `refund_id`:** at most one `RefundSettlement` per `refund_id` may be `pending` at a time.

---

## 5. State machines

### 5.1 Payment (per row — the ledger, not the Sale, has the state machine)

```text
        capture() / retry_payment()
              │
              ▼
          [pending] ──── processor says captured ────▶ [captured]  (terminal)
              │
              └──────── processor says declined ──────▶ [failed]    (terminal)
```

No row ever moves `captured → *` or `failed → *`. "Retry" is `retry_payment` creating attempt N+1 as an entirely new `pending` row — a state machine transition on the *ledger*, not on any individual row.

**Undefined-outcome handling:** if a processor call times out or the outcome is genuinely unknown (network failure mid-call, no response), the row **stays `pending`** — it is not marked `failed` speculatively. §11.2 (reconciliation) is the only mechanism that resolves a stuck `pending` row, and it resolves it by *asking the processor*, never by assuming an outcome.

### 5.2 RefundSettlement

Identical shape to §5.1, substituting `processed` for `captured`. Same rule: an unresolved processor response leaves the row `pending`, resolved only by reconciliation or manual operator action — never assumed.

---

## 6. Service contracts

Each method's precondition is checked and enforced *before* any processor call — a precondition failure never results in a processor being invoked.

### 6.1 `capture(sale_id, payment_method_id, amount, idempotency_key) -> Payment`
- **Precondition:** no existing `Payment` row for `sale_id` (this is attempt 1 — if one exists, this call is invalid; use `retry_payment`).
- **Postcondition:** exactly one new `Payment` row, `attempt_number = 1`, in a terminal or `pending` state; if terminal, exactly one of `PaymentCaptured`/`PaymentFailed` emitted.

### 6.2 `retry_payment(sale_id, payment_method_id?) -> Payment`
- **Precondition:** the most recent `Payment` row for `sale_id` has `status = failed`. If the most recent row is `pending`, reject — do not create a new attempt over an unresolved one (this is the idempotent-retry guard from `billing-domain.md` §2, formalized: a client resubmitting because of its own timeout must not be able to create attempt N+1 while attempt N might still resolve to `captured`).
- **Postcondition:** one new `Payment` row, `attempt_number` = previous + 1, optionally a different `payment_method_id`.

### 6.3 `settle_refund(refund_id, payment_id, amount) -> RefundSettlement`
- **Precondition:** `amount > 0`. Zero and negative amounts are validation failures: no `RefundSettlement` row is created and the processor is not called.
- **Precondition:** `amount` does not exceed the remaining unsettled amount for `refund_id` (sum of prior `processed` settlements for this `refund_id` + this `amount` ≤ the `Refund`'s total, as reported in the triggering event's payload — Billing does not independently query Sale's tables to verify this, only trusts the event payload, per the domain-isolation rule).
- **Postcondition:** one new `RefundSettlement` row, reversed through `payment_id`'s `processor_key` — **never** a different processor than the one that captured the original payment (§4.3).

### 6.4 Processor registry validation
At application startup, every `PaymentMethod.processor_key` with `is_active = true` **must** resolve to a registered class in `PROCESSOR_REGISTRY`. Startup fails fast if not — an active payment method pointing at an unregistered processor is a deploy-blocking configuration error, not a runtime surprise discovered on the first sale.

---

## 7. Concurrency & idempotency guarantees

### 7.1 No double-capture under concurrent requests
Enforced by the partial unique index in §4.2 — a second concurrent `capture()`/`retry_payment()` call for the same `sale_id` while one is already `pending` fails at the database constraint level, not merely by an application-level check-then-act (which has a race window; the constraint does not).

### 7.2 No double-capture under duplicate delivery
`idempotency_key` is unique per `Payment` row. A retried/duplicated *event* delivery (per `event-catalog.md`'s note on the reconciliation job assuming duplicate delivery is routine) that would otherwise call `capture()` twice with the same key is rejected by the unique constraint on the second attempt — the caller should treat that rejection as "already handled," not as an error to surface.

### 7.3 Attempt numbering
`attempt_number` assignment must not use `MAX(attempt_number) + 1` read-then-write (the same race class flagged for Sale's number generation in `sale-domain.md`) — use a DB-level mechanism (sequence scoped to `sale_id`, or the insert itself computing `MAX+1` inside the same statement/transaction with appropriate locking) so two concurrent retries can never be assigned the same `attempt_number`.

---

## 8. Events

Full contracts already defined in `event-catalog.md` §2.3, §3 — restated here as the authoritative source for this domain's *outbound* contract:

| Event | Trigger |
|---|---|
| `PaymentCaptured` | `Payment.status → captured` |
| `PaymentFailed` | `Payment.status → failed` |
| `RefundProcessed` | `RefundSettlement.status → processed` |
| `RefundFailed` | `RefundSettlement.status → failed` |

**Versioning:** every event carries `event_version` per the architecture standard's envelope (`flask-api-architecture-standard.md` §5). A breaking change to any of these four payloads is a new version, never a mutation of the existing one. `PaymentCaptured` is consumed by both Sale and Stock; during a rollout, Sale must be able to run against either event version, and Stock's consumer must be upgraded compatibly.

---

## 9. Security & compliance

### 9.1 No cardholder data, ever
Billing's schema contains **no field capable of holding a primary account number, CVV, or any other PCI-scoped cardholder data** — `processor_reference` is an opaque token/transaction id issued *by* the processor, never raw card data. Any future `PaymentProcessor` implementation (Card, Mobile) **must** use the processor's own tokenization/hosted-fields flow — raw card data must never transit through this domain's code or database. This keeps Billing out of PCI DSS SAQ-D scope; violating it is not a bug, it's a compliance incident.

### 9.2 Secrets
Processor API credentials are configuration, sourced from the environment per the established `pydantic-settings` pattern (`flask-api-architecture-standard.md` §9) — never hardcoded, never logged, never stored in `Payment`/`RefundSettlement` rows.

### 9.3 PII minimization
Billing does not copy `customer_name` or any other directly identifying Sale field. However, `Payment.sale_id` can be joined to `Sale.customer_name`, so Billing has an indirect, pseudonymous PII footprint. Treat `sale_id` as personal data: expose it only to the Billing service and authorized finance/compliance operators, audit administrative access, and retain it only under §13.

---

## 10. Observability

### 10.1 Structured logging
Every `capture`, `retry_payment`, and `settle_refund` call logs with the `correlation_id` from the triggering event's envelope (per the microservices design doc's event envelope, §5) — a support engineer must be able to trace one sale's entire journey (Stock reservation → capture attempts → completion or refund) from one identifier, across domains.

### 10.2 Required metrics
- Capture success/failure rate, segmented by `processor_key` — a specific processor degrading should be visible immediately, not discovered from support tickets.
- Attempt count distribution per `sale_id` — an unusual spike in retries against one processor is an early signal of a card reader or gateway problem.
- `RefundSettlement` failure count awaiting manual retry — this is a real operational queue (per §11 of `billing-domain.md`, retry is manual-only) and needs to be a visible, alertable number, not something only discovered by querying the table.
- Reconciliation backlog size (count of `Payment` rows `pending` past the staleness threshold, §11.2) — an SLO-worthy metric on its own.

### 10.3 Alerting
Define an explicit threshold for "reconciliation backlog too large" that pages an operator rather than relying on someone noticing. No specific number is prescribed here — it's an operational decision — but the requirement that *a* threshold exists and is wired to alerting is not optional for a domain handling money.

---

## 11. Reliability

### 11.1 Processor call timeout
Every `PaymentProcessor.capture()`/`.refund()` call has a bounded timeout, configured per processor (a real gateway and `CashProcessor` do not need the same timeout characteristics). A timeout is treated as "unknown outcome," per §5.1 — the row stays `pending`, it is never marked `failed` on a timeout alone, since that risks a false decline for a payment the processor actually captured.

### 11.2 Reconciliation
Formalizing `billing-domain.md` §7: a scheduled job queries every `Payment`/`RefundSettlement` row `pending` past a configured staleness threshold, queries the processor's authoritative record for that attempt, and resolves the row accordingly (idempotent — safe to run repeatedly, safe to find nothing to do). Past a second, longer threshold with still no resolution, the job stops attempting automatic resolution and raises an alert (§10.3) — indefinite silent retrying of a genuinely stuck attempt is not acceptable for money movement.

---

## 12. Error taxonomy

Following the project-wide `AppError` pattern (self-registering by `code`, `<DOMAIN>_` prefix):

| Code | Meaning |
|---|---|
| `BILLING_DUPLICATE_ATTEMPT` | `capture()` called for a `sale_id` that already has a `Payment` row |
| `BILLING_RETRY_ON_UNRESOLVED_ATTEMPT` | `retry_payment()` called while the most recent attempt is still `pending` |
| `BILLING_UNSUPPORTED_PROCESSOR` | `processor_key` not found in `PROCESSOR_REGISTRY` |
| `BILLING_PROCESSOR_TIMEOUT` | a capture/refund call exceeded its configured timeout — surfaces as "unknown," not "failed" |
| `BILLING_OVER_REFUND` | `settle_refund` amount would exceed the remaining unsettled amount for a `refund_id` |
| `BILLING_SETTLEMENT_NOT_FOUND` | manual retry referencing a `RefundSettlement`/`refund_id` that doesn't exist |

---

## 13. Data retention & auditability

`Payment` and `RefundSettlement` rows follow a seven-year retention schedule measured from `resolved_at` (or from formal closure for an attempt that never resolves). Keep them in the operational database for two years, then move them to encrypted, access-logged archival storage for the remaining five years. At the end of seven years, erase the rows and associated links such as `sale_id`.

An applicable financial-record law, unresolved dispute, audit, or legal hold may require longer retention. Such records must be isolated in the restricted archive, accessible only to authorized finance/compliance operators, and erased when the documented obligation expires. Shorter erasure required by applicable privacy law takes precedence where no financial-record obligation applies.

**Privacy-owner confirmation:** Pending. Record the approver and approval date here before this draft advances to production implementation; jurisdiction-specific retention overrides must be recorded with that approval.

---

## 14. Testing requirements

- **Contract test suite for `PaymentProcessor`** — any new implementation (Card, Mobile, or a future replacement) must pass a shared conformance suite before being registered: `capture()` on success must return a non-null `processor_reference`; both methods must be safe to call with a timeout injected; `refund()` must be a no-op-safe when called with an amount of zero (defensive, not expected in practice).
- **Concurrency test for §7.1** — two simultaneous `capture()`/`retry_payment()` calls for the same `sale_id` must result in exactly one `pending`/terminal row, never two.
- **Idempotency test for §7.2** — a duplicated event delivery with the same `idempotency_key` must not create a second `Payment` row.
- **Timeout-path test for §11.1** — a simulated processor timeout must leave the row `pending`, never `failed`.

---

## 15. Open risks & assumptions

- **No real gateway exists yet.** Everything in §9.1/§11 is written to hold once Card/Mobile are real, but is currently unverified against an actual gateway's failure modes — revisit this spec once the first real `PaymentProcessor` beyond `CashProcessor` is built, since real gateways may violate assumptions made here (e.g., some gateways don't support a true "unknown" outcome and force a binary answer).
- **`AccountSuspended`/`RoleRevoked` are not addressed here** (per `event-catalog.md`'s closing note) — whether a suspended seller's in-flight `Payment` should be affected is unresolved and out of this spec's scope.
- **Multi-currency and tax are explicitly out of scope (§1)** — `amount` is assumed to be a single implicit currency throughout this document; introducing a second currency is a breaking change to every table here, not an additive one.
