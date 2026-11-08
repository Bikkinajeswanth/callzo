# Callzo Software Engineer Assessment — Monorepo

> **Production-Grade Implementation for the Callzo Software Engineer Hiring Assessment**  
> Complete implementation of **Task 1 (Backend Usage Metering Service)** and **Task 2 (Usage Admin Console)**.

---

## 1. Project Overview & Objectives
This repository contains the end-to-end technical solution for the Callzo Software Engineer Assessment:
- **Task 1 — Backend Usage Metering Service**: High-throughput, idempotent FastAPI service handling telephony webhook events (`call.started`, `call.ended`, `call.failed`), HMAC-SHA256 signature verification over raw bytes, database-enforced idempotency, out-of-order event resolution, historical month accounting for late events, transactional usage cap enforcement, background retry workers, and reconciliation.
- **Task 2 — Usage Admin Console**: Enterprise SaaS administration console built with React, TypeScript, Tailwind CSS, Vite, and Recharts (strictly zero third-party component libraries or state packages). Features real-time KPI overview, resilient analytics charts absorbing deliberate 20% HTTP 500 error rates with bounded backoff, server-side paginated/filtered accounts directory with stable row selection across pages and silent 30s background refreshes, and a four-step account configuration wizard with debounced autosave and recovery from deliberate Step 4 -> Step 2 validation behaviors.

---

## 2. Technologies Used

### Task 1 (Backend Service)
- **Runtime**: Python 3.12+
- **API Framework**: FastAPI 0.110+
- **Database**: PostgreSQL 16 & SQLite (Testing)
- **ORM & Migrations**: SQLAlchemy 2.0 & Alembic 1.13
- **Validation**: Pydantic v2
- **Testing**: Pytest 8.2 & TestClient
- **Containerization**: Docker multi-stage build & Docker Compose

### Task 2 (Frontend Admin Console)
- **Library**: React 18
- **Language**: TypeScript 5
- **Styling**: Tailwind CSS 3.4
- **Build Tool**: Vite 5
- **Charts**: Recharts 2.12
- **Web Server**: Nginx (Alpine) with SPA routing & reverse proxy

---

## 3. Repository Structure

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
│   │   ├── components/      # Header, MetricCard, AnalyticsCharts, AccountTable, Wizard
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

## 4. Prerequisites
- **Docker & Docker Compose** (Docker Desktop on Windows/Mac, or Docker Engine on Linux)
- **Python 3.11+** (for local backend development/tests)
- **Node.js 20+ & npm** (for local frontend development)

---

## 5. Quick Start (Running with Docker Compose)

### 5.1 Run Entire Monorepo (Task 1 + Task 2)
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

### 5.2 Access Applications
- **Admin Console Dashboard**: [http://localhost:3000](http://localhost:3000)
- **Metering API Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Metering API Health Endpoint**: [http://localhost:8000/health](http://localhost:8000/health)
- **Mock Admin API**: [http://localhost:8001/accounts](http://localhost:8001/accounts)

---

## 6. How to Run Tasks Individually

### 6.1 Task 1: Backend Service Alone
```bash
cd task1-usage-metering

# Using Docker Compose
docker compose up --build

# Or running locally:
python -m venv venv
source venv/bin/activate  # Or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### Running Simulator Scenarios Individually
```bash
python simulator/runner.py 1   # Normal lifecycle
python simulator/runner.py 2   # Duplicate events (Idempotency)
python simulator/runner.py 3   # Out-of-order delivery
python simulator/runner.py 4   # Late events (~35 days in past)
python simulator/runner.py 5   # Monthly cap breach
python simulator/runner.py 6   # HMAC security verification
python simulator/runner.py 7   # Malformed payloads
python simulator/runner.py     # All scenarios
```

#### Running Backend Tests
```bash
python -m pytest task1-usage-metering/tests -v
```
**Results**: 24 tests passed in ~1.15s.

---

### 6.2 Task 2: Admin Console Alone
```bash
cd task2-admin-console

# Using Docker Compose
docker compose up --build

# Or running locally:
# Terminal 1: Start mock API
cd mock-api && python server.py

# Terminal 2: Start frontend Vite server
npm install
npm run dev
# Open http://localhost:3000
```

#### Publishing Pre-Built Image to Docker Hub (Section 6 Requirement)
```bash
export DOCKER_HUB_USERNAME="your_username"
cd task2-admin-console
docker build -t $DOCKER_HUB_USERNAME/usage-admin-console:latest .
docker push $DOCKER_HUB_USERNAME/usage-admin-console:latest
```

---

## 7. Submission Checklist & Verification Status

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
