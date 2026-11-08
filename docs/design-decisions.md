# Engineering Design Decisions & Trade-Offs

## 1. Task 1: Backend Usage Metering Decisions

### 1.1 Why raw bytes for HMAC verification instead of re-serializing JSON?
* **Problem**: In HTTP APIs, JSON serialization is non-deterministic regarding key order, whitespace, and Unicode escaping. If the backend parses the JSON and then re-serializes it with `json.dumps()` to compute the HMAC, any slight variation in key order or indentation produces a different hash, causing legitimate signatures to fail.
* **Decision**: Extract `await request.body()` directly as unparsed bytes and feed them immediately to `hmac.new(..., payload_bytes, hashlib.sha256)`.
* **Trade-off**: Requires reading the raw request stream before FastAPI's automatic Pydantic dependency parsing, which is handled cleanly via a FastAPI dependency.

### 1.2 Why store raw webhook events immutably?
* **Problem**: Billing disputes and audit requirements require an incontrovertible ledger of exactly what the telephony carrier sent.
* **Decision**: Every webhook is saved to `raw_webhook_events` with its raw payload, headers, signature, and timestamp.
* **Trade-off**: Increases disk storage over time. In high-volume production, a table partitioning strategy (e.g., partitioning `raw_webhook_events` by month) and archival to cold object storage (S3/GCS) after 90 days would be used.

### 1.3 Why pre-aggregate monthly usage rather than dynamic `SUM()` queries?
* **Problem**: Running `SELECT SUM(duration_seconds), SUM(cost_cents) FROM calls WHERE account_id = ? AND started_at BETWEEN ? AND ?` on every usage query requires scanning millions of rows in a production telephony system.
* **Decision**: Maintain a `monthly_usage` table keyed by `(account_id, year_month)`. Each incoming call event increments the counter in $O(1)$ time.
* **Trade-off**: Pre-aggregation risks drift if bugs or untracked writes occur. We solve this by providing the `ReconciliationService`, which periodically recalculates totals from raw calls and auto-heals any discrepancies.

### 1.4 How are late events handled?
* **Problem**: A call finished 35 days ago might be received today due to carrier delays or offline retries.
* **Decision**: The event is attributed to the month of the event's original `timestamp` (`YYYY-MM`), updating that historical month's row in `monthly_usage`.
* **Trade-off**: Invoices for past closed billing periods might need adjustment or delta billing. However, this is far better than distorting the current month's usage, which could trigger false cap breaches or confuse real-time customer dashboards.

---

## 2. Task 2: Admin Console Decisions

### 2.1 Why native React state instead of Redux or React Query?
* **Problem**: The assessment guidelines strictly state: *"The assessment restricts Task 2 to React, Tailwind and a chart library. Do not add component libraries, UI frameworks, state-management packages, React Query or unnecessary dependencies."*
* **Decision**: Rely entirely on native React hooks (`useState`, `useEffect`, `useCallback`, `useMemo`, `useRef`).
* **Implementation Details**:
  - `activeRequestId.current` guards against race conditions from out-of-order fetch responses.
  - Custom `useDebounce` hook provides smooth 800ms autosave buffering without external lodash libraries.
  - Native browser timers (`setInterval` / `clearInterval`) power silent 30-second background refreshes.

### 2.2 How is stable row selection achieved across pages and refreshes?
* **Problem**: Typical naive implementations store selected row indexes (e.g. `[0, 2]`), which break when the page changes or when sorting/filtering alters row order.
* **Decision**: Track selection in a `Set<string>` containing immutable `account.id` strings.
* **Benefits**:
  - Survives pagination (selecting items on page 1 remains preserved when viewing page 2).
  - Survives sorting and filtering.
  - Survives 30-second background polling refreshes.

### 2.3 UX Strategy for Deliberate Step 4 -> Step 2 Server Rejection
* **Problem**: Section 4.8 specifies that after step 4 has an active draft, the server may reject step 2 with `billing_country is required`, even if valid.
* **Decision**:
  - Never modify the mock API to make the test pass (violates assessment rules).
  - Instead, the frontend catches this condition gracefully, highlights Step 2 with an informative alert banner, preserves all other data in steps 1, 3, and 4, and gives the user a single-click "Re-verify Country" action to confirm and proceed.
