# Callzo Software Engineer Assessment — Monorepo

> **Production-Grade Implementation for the Callzo Software Engineer Hiring Assessment**  
> Complete implementation of **Task 1 (Backend Usage Metering Service)** and **Task 2 (Usage Admin Console)**.

---

## 1. Project Overview & Objectives

This repository contains the end-to-end technical solution for the Callzo Software Engineer Assessment:
- **Task 1 — Backend Usage Metering Service**: High-throughput, idempotent FastAPI service handling telephony webhook events (`call.started`, `call.ended`, `call.failed`), HMAC-SHA256 signature verification over raw bytes, database-enforced idempotency, out-of-order event resolution, historical month accounting for late events, transactional usage cap enforcement, background retry workers, and automated reconciliation.
- **Task 2 — Usage Admin Console**: Enterprise SaaS administration console built with React, TypeScript, Tailwind CSS, Vite, and Recharts (strictly zero third-party component libraries or state packages). Features real-time KPI overview, resilient analytics charts absorbing deliberate 20% HTTP 500 error rates with bounded backoff, server-side paginated/filtered accounts directory with stable row selection across pages and silent 30s background refreshes, and a four-step account configuration wizard with debounced autosave and recovery from deliberate Step 4 -> Step 2 validation behaviors.

---

## 2. Key Features

### Task 1: Backend Usage Metering Service
- **HMAC-SHA256 Webhook Verification**: Cryptographic validation over unparsed raw request body bytes with constant-time equality check (`hmac.compare_digest`).
- **Database-Enforced Idempotency**: Unique constraint on `raw_webhook_events(event_id)` ensures duplicate deliveries safely return HTTP 200 without double-metering.
- **Out-of-Order Call Resolution**: Handles scenarios where `call.ended` arrives before `call.started` without data corruption or duplicate counting.
- **Late-Arriving Historical Accounting**: Events arriving ~35 days in the past target the exact historical `YYYY-MM` usage record; current month aggregates remain unaffected.
- **Accurate Financial Calculations**: Rate calculations and usage aggregations are strictly computed using integer cents (avoiding floating-point drift).
- **Transactional Usage Caps**: Atomic limit enforcement using database row-level locking (`SELECT ... FOR UPDATE`), setting soft warnings or hard blocks.
- **Self-Healing Reconciliation**: Recomputes aggregate totals from immutable event records and repairs any discovered drift.
- **Resilient Background Retries**: Persistent retry queue with bounded exponential backoff.

### Task 2: Usage Admin Console
- **Zero Component Libraries**: 100% custom UI built with pure Tailwind CSS and native React hooks per strict assessment constraints.
- **Live KPI Overview**: Real-time summary cards displaying active, trial, and suspended tenant counts, billed minutes, SMS volume, and billed costs.
- **Interactive Analytics Charts**: Recharts Area and Bar visualizations with high-contrast dark/light tooltips, toggleable across Minutes, SMS, Costs, and Signups.
- **Timezone-Safe Date Filters**: UTC-pinned date range filtering (`T00:00:00Z` to `T23:59:59Z`) preventing multi-day offsets across local timezones.
- **Advanced Accounts Directory**: Server-side pagination, multi-attribute filtering (Status, Plan, Country), and live text search across ID, company, name, and email.
- **Stable Multi-Page Row Selection & CSV Export**: Selection state keyed by account ID (`Set<string>`) retains selections across pagination, sorting, and refreshes, exporting all selected rows to CSV.
- **Account Detail Slide-Over Drawer**: Responsive drawer providing deep tenant usage breakdown and quick navigation to settings.
- **Four-Step Tenant Configuration Wizard**: Step 1 (Personal), Step 2 (Subscription & Country), Step 3 (Usage Limits), Step 4 (Webhook URL) with keyboard trap, debounced autosave (800ms), and recovery from deliberate Section 4.8 `billing_country is required` validation failure.
- **Resilient 20% 500 Handling**: 3-attempt exponential backoff with jitter on API calls, with graceful inline retry fallback ensuring the accounts directory stays operational.
- **Theme & Mobile Responsive**: Full dark/light mode toggle with `localStorage` persistence and responsive layouts verified down to 375px mobile screens.

---

## 3. Technology Stack

### Task 1 (Backend Service)
- **Runtime**: Python 3.12+
- **API Framework**: FastAPI 0.110+
- **Database**: PostgreSQL 16 & SQLite (In-Memory for Unit Tests)
- **ORM & Migrations**: SQLAlchemy 2.0 & Alembic 1.13
- **Validation**: Pydantic v2
- **Testing**: Pytest 8.2 & HTTPX TestClient
- **Containerization**: Docker multi-stage build & Docker Compose

### Task 2 (Frontend Admin Console)
- **UI Library**: React 18.3
- **Language**: TypeScript 5.4
- **Styling**: Tailwind CSS 3.4
- **Build Tool**: Vite 5.2
- **Charts**: Recharts 2.12
- **Web Server**: Nginx (Alpine) with SPA routing & reverse proxy

---

## 4. System Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                          CALLZO ARCHITECTURE                           │
└────────────────────────────────────────────────────────────────────────┘

  [ Telephony Simulator ]               [ Web Browser Client ]
             │                                     │
   POST /webhooks/calls (HMAC-SHA256)     HTTP /api (REST)
             ▼                                     ▼
┌─────────────────────────┐               ┌─────────────────────────┐
│   Task 1: Metering API  │               │    Task 2: Admin Console │
│        (FastAPI)        │               │   (React + Nginx/Vite)  │
│                         │               │                         │
│ • Raw Byte HMAC Check   │               │ • Dashboard KPIs        │
│ • Idempotency Filter    │               │ • Analytics Charts      │
│ • Out-of-Order Engine   │               │ • Paginated Directory   │
│ • Usage Cap Enforcer    │               │ • 4-Step Settings Wizard│
│ • Retry & Reconciliation│               │ • 20% Error Resilience  │
└────────────┬────────────┘               └────────────┬────────────┘
             │                                         │
             ▼                                         ▼
┌─────────────────────────┐               ┌─────────────────────────┐
│   PostgreSQL Database   │               │   Mock Telephony API    │
│                         │               │        (FastAPI)        │
│ • raw_webhook_events    │               │                         │
│ • calls                 │               │ • GET /accounts/summary │
│ • monthly_usage         │               │ • GET /accounts         │
│ • usage_caps            │               │ • PUT /settings/step/*  │
│ • event_retry_records   │               │ • Deliberate 500 & 422  │
└─────────────────────────┘               └─────────────────────────┘
```

---

## 5. Repository Structure

```
callzo/
├── task1-usage-metering/
│   ├── app/
│   │   ├── api/             # Webhook, usage, caps, health, reconciliation routes
│   │   ├── core/            # Config, HMAC security, structured JSON logging
│   │   ├── database/        # Engine, session factory, declarative base
│   │   ├── models/          # Accounts, raw_webhook_events, calls, monthly_usage, caps, retries
│   │   ├── schemas/         # Pydantic request/response schemas
│   │   ├── services/        # Webhook processing, usage calculation, cap checks, reconciliation
│   │   ├── workers/         # Persistent retry worker with exponential backoff
│   │   └── main.py          # FastAPI application initialization & correlation middleware
│   ├── alembic/             # Database migration configurations & version scripts
│   ├── simulator/           # Telephony event simulator & scenario runner
│   ├── tests/               # Pytest suite (24 comprehensive tests)
│   ├── Dockerfile           # Optimized Python 3.12 container
│   ├── docker-compose.yml   # Standalone Task 1 container orchestration
│   ├── requirements.txt     # Backend dependencies
│   ├── .env.example         # Environment template
│   └── README.md            # In-depth Task 1 documentation
│
├── task2-admin-console/
│   ├── src/
│   │   ├── components/      # Header, MetricCard, AnalyticsCharts, AccountTable, Wizard, Drawer
│   │   ├── pages/           # DashboardPage
│   │   ├── hooks/           # useAccounts, useSummary, useSettingsDraft, useDebounce
│   │   ├── services/        # Centralized typed API service layer
│   │   ├── types/           # Domain TypeScript definitions
│   │   ├── utils/           # Formatters (cents, numbers, dates) and retry helpers
│   │   └── styles/          # Tailwind CSS styles
│   ├── mock-api/            # Standalone mock admin API (FastAPI) simulating 20% 500 error
│   ├── nginx.conf           # Production Nginx SPA configuration & API proxy
│   ├── Dockerfile           # Multi-stage production build (Node.js -> Nginx)
│   ├── docker-compose.yml   # Standalone Task 2 container orchestration
│   ├── package.json         # Frontend dependencies
│   ├── .env.example         # Frontend environment template
│   └── README.md            # In-depth Task 2 documentation
│
├── docs/
│   ├── architecture.md      # System architecture, data flow & mermaid diagrams
│   ├── design-decisions.md  # Engineering trade-offs and rationale
│   ├── testing-report.md    # Detailed test matrix and results
│   └── interview-preparation.md # Defense walkthrough questions and technical answers
│
├── docker-compose.yml       # Unified orchestration for entire platform
├── README.md                # Root project documentation
└── .gitignore               # Comprehensive Git ignore rules
```

---

## 6. Installation & Execution

### 6.1 Prerequisites
- **Docker & Docker Compose** (Docker Desktop on Windows/macOS, or Docker Engine on Linux)
- **Python 3.11+** (for local backend development/tests)
- **Node.js 20+ & npm** (for local frontend development)

---

### 6.2 Quick Start (Running via Docker Compose)

To build and start both the backend metering service and the frontend admin console with one command:
```bash
docker compose up --build
```

This automatically boots:
- `callzo-postgres`: PostgreSQL 16 on port `5432`
- `callzo-metering-api`: Usage Metering FastAPI on port `8000` (auto-runs migrations)
- `callzo-simulator`: Fires all 7 telephony test scenarios against the metering API
- `callzo-mock-api`: Mock Telephony Admin API on port `8001`
- `callzo-admin-console`: React Frontend Console on port `3000`

#### Access Application Endpoints:
- **Admin Console Dashboard**: [http://localhost:3000](http://localhost:3000)
- **Metering API Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Metering API Health Endpoint**: [http://localhost:8000/health](http://localhost:8000/health)
- **Mock Admin API**: [http://localhost:8001/accounts](http://localhost:8001/accounts)

---

### 6.3 Local Development (Without Docker)

#### Running Task 1: Backend Usage Metering
```bash
cd task1-usage-metering

# Set up virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start FastAPI server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### Running Task 2: Usage Admin Console
```bash
# Terminal 1: Start Mock Admin API
cd task2-admin-console/mock-api
pip install -r requirements.txt
python server.py
# Runs on http://0.0.0.0:8002

# Terminal 2: Start Vite Dev Server
cd task2-admin-console
npm install
npm run dev
# Open http://localhost:5173 (proxies /api to http://127.0.0.1:8002)
```

---

## 7. Testing Commands & Verification

### 7.1 Backend Unit & Integration Tests (Task 1)
```bash
python -m pytest task1-usage-metering/tests -v
```
**Results**: **24 passed** in 1.31s (signatures, idempotency, out-of-order, caps, retries, reconciliation, accounts CRUD).

### 7.2 Telephony Simulator Runner (Task 1)
```bash
# Run all 7 scenarios end-to-end:
python task1-usage-metering/tests/verify_simulator.py

# Or run individual simulator scenarios:
python task1-usage-metering/simulator/runner.py 1   # Normal lifecycle
python task1-usage-metering/simulator/runner.py 2   # Duplicate events (Idempotency)
python task1-usage-metering/simulator/runner.py 3   # Out-of-order delivery
python task1-usage-metering/simulator/runner.py 4   # Late events (~35 days in past)
python task1-usage-metering/simulator/runner.py 5   # Monthly cap breach
python task1-usage-metering/simulator/runner.py 6   # HMAC security verification
python task1-usage-metering/simulator/runner.py 7   # Malformed payloads
```
**Results**: **7/7 scenarios verified**.

### 7.3 Frontend Functional Verification Suite (Task 2)
```bash
node task2-admin-console/tests/functional_verification.js
```
**Results**: **51 passed, 0 failed** across all 16 Task 2 requirements.

### 7.4 TypeScript Compilation & Production Build (Task 2)
```bash
cd task2-admin-console

# Typecheck
npx tsc --noEmit

# Production Build
npm run build
```
**Results**: 0 TypeScript errors; bundle built in 10.8s (`dist/` generated with separate `recharts` and `react-vendor` chunks).

---

## 8. API Documentation

### Task 1: Metering API Endpoints (`http://localhost:8000`)
| Method | Path | Auth | Description |
| :--- | :--- | :---: | :--- |
| `POST` | `/webhooks/calls` | `X-Signature` | Ingests telephony events (`call.started`, `call.ended`, `call.failed`). |
| `GET` | `/health` | Public | System uptime, database connectivity, and health metrics. |
| `GET` | `/accounts` | `X-API-Key` | Lists all accounts with pagination and status/plan filters. |
| `POST` | `/accounts` | `X-API-Key` | Creates a new customer account with auto-provisioned caps. |
| `GET` | `/accounts/{id}` | `X-API-Key` | Retrieves single account metadata and usage. |
| `PATCH` | `/accounts/{id}` | `X-API-Key` | Updates account plan, country, name, or email. |
| `GET` | `/usage/{account_id}/current` | `X-API-Key` | Current month minutes, SMS count, and cost in integer cents. |
| `GET` | `/usage/{account_id}/history` | `X-API-Key` | Historical monthly usage breakdown. |
| `GET` | `/usage/{account_id}/calls` | `X-API-Key` | Paginated call detail records (CDR). |
| `POST` | `/caps/{account_id}` | `X-API-Key` | Configures soft and hard limits for an account. |
| `POST` | `/reconciliation/reconcile` | `X-API-Key` | Triggers self-healing audit reconciling aggregated usage. |

### Task 2: Mock Admin API Endpoints (`http://localhost:8001` or `8002`)
| Method | Path | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | Mock API health check. |
| `GET` | `/accounts` | Search, country/plan/status filter, sorting, and pagination. |
| `GET` | `/accounts/{id}` | Single account detail for slide-over drawer. |
| `GET` | `/accounts/summary` | Dashboard KPI overview and 6-month trends (deliberate ~20% HTTP 500). |
| `GET` | `/accounts/{id}/settings` | Retrieves autosaved tenant configuration draft. |
| `PUT` | `/accounts/{id}/settings/step/{n}` | Saves configuration step (simulates Section 4.8 Step 2 validation behavior). |
| `POST` | `/accounts/{id}/settings/submit` | Final wizard submission and tenant activation. |

---

## 9. UI Screenshots & Layout

### 9.1 Dashboard Overview (Dark Theme)
The admin console opens with high-level KPI cards and a 6-month analytics trend chart:
- **Top Bar**: Callzo branding, dark/light theme toggle, real-time background refresh indicator, and backend connection status pill.
- **KPI Grid**: Total Accounts (45), Active/Trial/Suspended breakdown, Billed Voice Minutes, SMS Volume, and Billed Costs ($20,930.55).
- **Analytics Visualization**: Recharts time-series with toggles for Billed Minutes, SMS Volume, Billed Cost, and Signups, featuring responsive tooltips and date-range filtering.

### 9.2 Accounts Directory & Multi-Page Selection
- **Filter Toolbar**: Search by tenant/email, filters for Status (Active, Trial, Suspended), Plan (Enterprise, Pro, Basic), Country (US, IN, GB, CA, AU), and UTC Date Range.
- **Data Table**: Server-side sorting, pagination (5 accounts per page), and stable multi-page checkbox selection.
- **Bulk Actions**: Multi-page selection counter pill, "Clear Selection", and CSV Export.

### 9.3 Slide-Over Account Drawer
- Clicking **"View"** on any account slides open a detailed profile drawer from the right, displaying live tenant details, monthly minutes, SMS volume, and billed costs, with an action button to launch the configuration wizard.

### 9.4 Four-Step Tenant Configuration Wizard
- **Step 1: Personal Details**: Name, administrative email, with immediate format validation.
- **Step 2: Subscription & Jurisdiction**: Plan selection and billing country. Handles the deliberate Section 4.8 validation with an inline re-verification action (`_revalidated: true`).
- **Step 3: Usage Limits**: Optional soft and hard caps for voice minutes and SMS.
- **Step 4: Webhook Configuration**: Real-time event delivery URL and secret token.
- **Draft Autosave**: Keystrokes automatically autosave via an 800ms debounce without user intervention.

---

## 10. Submission Checklist & Verification Status

| Requirement Item | Status | Verification Detail |
| :--- | :---: | :--- |
| **Task 1 Webhook Signature Verification** | ✅ Completed | HMAC-SHA256 verified over raw bytes; constant-time comparison; tested in `test_signatures.py`. |
| **Task 1 Idempotency** | ✅ Completed | Enforced via DB unique constraint; duplicate deliveries return HTTP 200 without double-metering. |
| **Task 1 Out-of-Order Handling** | ✅ Completed | `call.ended` arriving before `call.started` creates ended call; subsequent start event populates start time without double-counting. |
| **Task 1 Late Events** | ✅ Completed | Events with timestamps ~35 days in past attribute strictly to historical month; current month unaffected. |
| **Task 1 Monthly Usage Caps** | ✅ Completed | Atomic evaluation using row-level locking (`SELECT ... FOR UPDATE`); soft and hard limit flags. |
| **Task 1 Retries & Reconciliation** | ✅ Completed | Persistent backoff retry worker + reconciliation audit repair endpoint; tested in `test_reconciliation.py`. |
| **Task 1 Automated Tests** | ✅ Completed | 24/24 automated tests passing in Pytest (100% pass rate). |
| **Task 1 Docker Compose** | ✅ Completed | PostgreSQL readiness wait + auto-Alembic migration + healthy API + simulator runner. |
| **Task 2 Overview Dashboard** | ✅ Completed | KPI metric cards (tenants, minutes, SMS, costs) + Recharts time-series and breakdowns. |
| **Task 2 Resilient Error Handling** | ✅ Completed | Bounded retry on deliberate 20% 500 error; inline error with manual retry; table remains fully operational. |
| **Task 2 Account Directory** | ✅ Completed | Server-side pagination, search, sorting, status/plan/country filters, and date range picker. |
| **Task 2 Stable Row Selection** | ✅ Completed | Selection state keyed by account ID; preserved across pagination, sorting, and background refreshes. |
| **Task 2 Four-Step Wizard** | ✅ Completed | Personal details, subscription, caps, webhook; debounced autosave; preserves values across steps. |
| **Task 2 Special Validation Recovery** | ✅ Completed | Graceful UX handling of deliberate Step 4 -> Step 2 `billing_country is required` behavior. |
| **Task 2 Periodic Refresh** | ✅ Completed | Silent background fetch every 30s; no table jumps or loss of unsaved form drafts. |
| **Task 2 Accessibility & 375px Mobile** | ✅ Completed | Keyboard accessible; ARIA attributes; focus indicators; tested down to 375px mobile screen width. |
| **Task 2 Docker & Multi-stage Build** | ✅ Completed | Multi-stage Node.js build -> lightweight Nginx server with SPA routing and `/api` reverse proxy. |
| **Documentation & Defense Guide** | ✅ Completed | Root README, Task READMEs, Architecture, Design Decisions, Testing Report, Interview Preparation. |
