# Technical Interview Walkthrough & Defense Guide

Comprehensive, technically precise talking points and defense answers for the Callzo Engineering Assessment.

---

## 1. Task 1: Backend Usage Metering Service

### Q1: Why did you choose this particular database schema?
> **Answer**:  
> We separated the system into distinct operational concerns:
> 1. `raw_webhook_events`: An immutable ledger of carrier transmissions. It ensures an incontrovertible audit trail, stores raw payloads for replay/retries, and provides the foundation for idempotency.
> 2. `calls`: Represents the mutable entity state of a phone session, tracking start/end timestamps, duration, cost, and destination country.
> 3. `monthly_usage`: Pre-aggregated rollups keyed by `(account_id, year_month)`. In a carrier system processing millions of events, calculating invoices via `SELECT SUM()` across raw calls on every read is unscalable ($O(N)$ full-table scans). Storing aggregated metrics turns usage queries into $O(1)$ lookups.
> 4. `usage_caps` & `event_retry_records`: Dedicated tables for limits and backoff scheduling, preventing lock contention on core transaction tables.

### Q2: How does HMAC verification work and why MUST you verify raw request bytes instead of re-serializing JSON?
> **Answer**:  
> HMAC-SHA256 generates a cryptographic hash of the message using a shared secret. When a client signs a payload, the signature is computed over the exact sequence of bytes sent across the wire.  
> If an API framework parses the JSON into a dictionary/object and re-serializes it back to a string (`json.dumps()`), the re-serialized output will almost certainly diverge in key order, whitespace, float representations, or Unicode escapes. Even a single differing whitespace character produces an entirely different SHA256 digest, causing legitimate signatures to fail.  
> Therefore, we read `await request.body()` directly as unparsed bytes, calculate `hmac.new(secret, raw_bytes, sha256).hexdigest()`, and compare using `hmac.compare_digest` to prevent timing attacks.

### Q3: How is idempotency enforced, and how do you handle duplicate events that arrive simultaneously?
> **Answer**:  
> Idempotency is enforced at the database level with a unique constraint on `raw_webhook_events.event_id`.  
> For normal sequential duplicates, the service checks the table; if found, it immediately responds with HTTP 200 and `{"status": "duplicate"}` without modifying any call state or usage counters.  
> If two identical events arrive concurrently in parallel threads, both may pass an in-memory or read check. However, when both attempt to `INSERT` into `raw_webhook_events`, PostgreSQL's unique constraint triggers an `IntegrityError` on the second transaction. We catch this exception, rollback the transaction, and return `{"status": "duplicate"}`. No double-counting can ever occur.

### Q4: How are out-of-order events resolved (e.g., `call.ended` arriving before `call.started`)?
> **Answer**:  
> We treat `Call` as a state machine where `ended` is a terminal state.  
> If `call.ended` arrives first: We insert a new `Call` row with `status = "ended"`, recording the reported duration and cost. We increment `monthly_usage` with the duration, cost, and call count.  
> When `call.started` arrives later: We find the existing call already marked as `ended`. We populate `call.started_at`, but we **do not** revert the status to `started`, and we **do not** increment calls or usage again. The final call state remains complete and accurate.

### Q5: How are late events (~35 days in past) accounted for?
> **Answer**:  
> Late events are attributed strictly to their historical month using the event's original timestamp: `year_month = event.timestamp.strftime("%Y-%m")`.  
> The service updates the `(account_id, "2026-10")` record rather than the current month. This policy prevents late-arriving carrier records from distorting current month invoices or triggering false usage cap breaches.

### Q6: How is the monthly cap enforced?
> **Answer**:  
> Within the database transaction, we acquire a row lock on the tenant's `monthly_usage` row using `with_for_update()`. This serializes concurrent event processing for that specific tenant and prevents race conditions.  
> If the new total exceeds `monthly_minutes_cap` or `monthly_cost_cents_cap`:  
> For soft caps, the event is processed and tagged with `soft_limit_exceeded`.  
> For hard caps, in VoIP telephony, an ongoing call that finished must still be recorded for financial accuracy, but the response returns `hard_limit_exceeded`, signaling downstream telephony systems to reject subsequent call initiation attempts.

### Q7: How does reconciliation work?
> **Answer**:  
> `ReconciliationService.reconcile_monthly_usage` executes a `SUM()` query directly against all individual `Call` records for a specified tenant and month. It compares the raw sum against the pre-aggregated `monthly_usage` record.  
> If any discrepancy is found, it logs the drift details and synchronizes `monthly_usage` to match the raw records. It is safe and idempotent to run on demand or as a scheduled cron job.

### Q8: What happens if the database is temporarily unavailable?
> **Answer**:  
> Inbound events that encounter database connection errors are routed to the retry worker queue. The background worker uses exponential backoff (`delay = base * 2^(attempts-1)`) bounded to 5 attempts before marking status as `exhausted`. The `/health` endpoint checks database connectivity via `SELECT 1` and returns HTTP 503 if unreachable, allowing container orchestrators to route traffic or restart the pod.

---

## 2. Task 2: Usage Admin Console

### Q9: Why this frontend architecture and state management strategy?
> **Answer**:  
> The assessment explicitly forbade external UI frameworks, component libraries, or state-management packages (no Redux, no React Query, no Axios).  
> We built a clean, modular architecture using native React hooks:
> - Custom hooks encapsulate domain logic (`useAccounts`, `useSummary`, `useSettingsDraft`).
> - Request cancellation and race condition guards use `activeRequestId.current`.
> - Debouncing uses native JavaScript `setTimeout` wrapped in `useDebounce`.
> This resulted in a lean bundle (<180kB gzipped) with zero external dependency bloat.

### Q10: How does stable row selection work across pages and refreshes?
> **Answer**:  
> Naive implementations store row indexes (`[0, 1]`), which break when paginating or sorting. We store selected accounts in a `Set<string>` containing immutable `account.id` values. When users navigate between pages or when the 30-second background poll refreshes data, the selection state remains intact.

### Q11: How does the chart handle the deliberate 20% HTTP 500 error rate from the summary API?
> **Answer**:  
> We wrapped the summary fetch in a bounded exponential backoff helper (`fetchWithRetry`). When a 500 occurs, it automatically retries up to 3 times with exponential delay and jitter.  
> If all 3 attempts fail, an isolated inline error card is shown with a manual "Retry Analytics" button. Crucially, the account directory table and wizard are completely decoupled and remain **100% interactive**. The application never crashes.

### Q12: How did you handle the deliberate Step 4 -> Step 2 validation behavior?
> **Answer**:  
> Per Section 4.8, after step 4 has a draft, step 2 may reject `billing_country` with `"billing_country is required"`.  
> Rather than modifying the API or writing a hack that violates assessment rules, we implemented a UX recovery pattern:
> 1. All form values in steps 1, 3, and 4 are strictly preserved.
> 2. Step 2 displays a highlighted warning banner explaining the server condition.
> 3. A "Re-verify Country" button allows the user to re-validate and confirm the selection (`_revalidated: true`), seamlessly clearing the error and enabling submission.

### Q13: How is keyboard accessibility and 375px mobile responsiveness implemented?
> **Answer**:  
> - **Accessibility**: Full keyboard navigation across all buttons, inputs, and selects. The 4-step wizard modal includes `role="dialog"`, `aria-modal="true"`, focus management, visible focus rings, and an Escape key listener that closes the dialog.
> - **Responsiveness**: Grid layouts collapse to single-column cards on viewports down to 375px, tables feature smooth horizontal scroll containers, and tap targets meet WCAG standards (minimum 44x44px).
