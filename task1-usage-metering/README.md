# Task 1: Backend Usage Metering Service

Production-grade, idempotent call usage metering backend designed for high-concurrency telephony event ingestion.

## 1. Technical Stack
- **Framework**: Python 3.12+, FastAPI
- **Database**: PostgreSQL 16, SQLAlchemy 2.0 (ORM & Core)
- **Migrations**: Alembic
- **Validation**: Pydantic v2
- **Testing**: Pytest, TestClient, In-Memory SQLite & PostgreSQL
- **Containerization**: Docker multi-stage build, Docker Compose

---

## 2. Architecture & Design Decisions

### 2.1 Database Architecture
Normalized PostgreSQL schema featuring:
- `accounts`: Core tenant entity tracking status (`active`, `trial`, `suspended`), subscription plan (`basic`, `pro`, `enterprise`), and contact details.
- `raw_webhook_events`: Immutable audit ledger storing raw bytes, headers, and payload of every received webhook. Serves as the source of truth for idempotency, replayability, and reconciliation.
- `calls`: State machine entity tracking telephone calls (`call_id`, `status`, `started_at`, `ended_at`, `duration_seconds`, `cost_cents`, `destination_country`).
- `monthly_usage`: Pre-aggregated rollups keyed on `(account_id, year_month)`. Enforces instant query performance for monthly usage without costly full-table scans.
- `usage_caps`: Configurable monthly limits (`monthly_minutes_cap`, `monthly_cost_cents_cap`, `is_hard_cap`).
- `event_retry_records`: Persistent queue for failed event processing with exponential backoff scheduling.

### 2.2 Webhook Signature Verification (HMAC-SHA256)
- **Raw Bytes Verification**: Signatures are evaluated against raw incoming bytes from `await request.body()`. JSON re-serialization is strictly avoided because key ordering and whitespace divergence invalidate HMAC hashes.
- **Constant-Time Comparison**: `hmac.compare_digest` is used to prevent timing attacks.
- **Fail-Closed**: Payloads with missing or invalid `X-Signature` headers are immediately rejected with HTTP 401 without processing.

### 2.3 Database-Enforced Idempotency
- A unique index on `raw_webhook_events.event_id` guarantees that no event can be committed twice.
- If an existing event is received, the service returns HTTP 200 with `status: "duplicate"` and does not alter usage metrics or call states.
- Concurrent identical requests hitting the API simultaneously are safely caught via database transaction rollback (`IntegrityError`), preventing double-metering under high load.

### 2.4 Out-of-Order Event Handling
- Real-world networks can deliver `call.ended` before `call.started`.
- **When `call.ended` arrives first**: A call record is created with `status = "ended"`, storing the reported duration, cost, and end time. The monthly usage aggregate is incremented.
- **When `call.started` arrives later**: The service detects that the call record already exists with status `ended`. It populates `started_at`, but retains the ended status and does **not** double-count calls, minutes, or cost.

### 2.5 Late Events Policy (~35 Days in the Past)
- Telephony networks occasionally deliver delayed CDR (Call Detail Record) webhooks.
- **Policy**: Late events are assigned to their historical usage month based on the event's original `timestamp` (`year_month = event.timestamp.strftime("%Y-%m")`).
- This prevents historical call data from artificially inflating current month invoices or triggering false usage cap breaches.

### 2.6 Monthly Usage Cap Policy
- Accounts can configure monthly minute and cost caps.
- Caps support both soft warnings (`soft_limit_exceeded`) and hard limits (`hard_limit_exceeded`).
- Row-level locking (`with_for_update()`) during aggregation guarantees atomic evaluation under concurrency.
- In telephony billing, an in-progress call that completes is legally incurred and must be recorded for accurate billing, while the response flags `hard_limit_exceeded` to inform downstream telephony gateways to block subsequent outbound call initiations.

### 2.7 Reconciliation & Self-Healing
- The reconciliation endpoint (`POST /api/v1/reconciliation/{account_id}/{year_month}`) queries the individual call records, calculates the true sum, and compares it against `monthly_usage`.
- If drift or discrepancy is detected, it auto-repairs the aggregate to ensure 100% financial accuracy.
- Safe and idempotent to execute repeatedly.

### 2.8 Background Retries with Exponential Backoff
- Transient runtime errors trigger automatic insertion into `event_retry_records`.
- Exponential backoff schedule: $\text{delay} = \text{base} \times 2^{(\text{attempts}-1)}$.
- Bounded to a maximum of 5 attempts before marking status as `exhausted`.

---

## 3. API Endpoints

| Method | Endpoint | Auth | Purpose |
| :--- | :--- | :--- | :--- |
| `POST` | `/webhooks/calls` | `X-Signature` | Ingests telephony events from simulator |
| `GET` | `/health` | None | Service readiness & DB connectivity check |
| `GET` | `/api/v1/accounts/{id}/usage/overview` | `X-API-Key` | Current month + lifetime usage summary |
| `GET` | `/api/v1/accounts/{id}/usage/monthly` | `X-API-Key` | Monthly breakdown by `year_month` |
| `GET` | `/api/v1/accounts/{id}/calls` | `X-API-Key` | Paginated call history with filters |
| `GET` | `/api/v1/accounts/{id}/cap` | `X-API-Key` | Cap limits & current utilization |
| `PUT` | `/api/v1/accounts/{id}/cap` | `X-API-Key` | Configure monthly usage cap limits |
| `POST` | `/api/v1/reconciliation/{id}/{month}` | `X-API-Key` | Recompute and repair monthly aggregates |
| `POST` | `/api/v1/reconciliation/retries/process` | `X-API-Key` | Trigger retry worker cycle |

---

## 4. How to Run Locally

### 4.1 Running with Docker Compose (Full Stack)
```bash
docker compose up --build
```
This automatically:
1. Provisions PostgreSQL 16 with persistent volume `pgdata`.
2. Waits for PostgreSQL readiness.
3. Applies Alembic migrations (`alembic upgrade head`).
4. Starts FastAPI on port `8000`.
5. Starts the Telephony Simulator container which fires all scenarios against the API.

### 4.2 Running Simulator Scenarios Individually
```bash
# Run all scenarios
python simulator/runner.py

# Run specific scenario
python simulator/runner.py 1   # Normal lifecycle
python simulator/runner.py 2   # Duplicate events (Idempotency)
python simulator/runner.py 3   # Out-of-order delivery
python simulator/runner.py 4   # Late events
python simulator/runner.py 5   # Monthly cap breach
python simulator/runner.py 6   # Security & HMAC verification
python simulator/runner.py 7   # Malformed payloads
```

### 4.3 Running Pytest Suite
```bash
pytest -v
```
