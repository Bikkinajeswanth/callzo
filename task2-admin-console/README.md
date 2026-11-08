# Task 2: Usage Admin Console

Modern, accessible, resilient SaaS administration console for Callzo telephony metering and multi-tenant management.

## 1. Technical Stack
- **Framework**: React 18, TypeScript 5
- **Styling**: Tailwind CSS 3.4
- **Build Tool**: Vite 5
- **Visualizations**: Recharts 2.12
- **State Management**: Built-in React Hooks (`useState`, `useEffect`, `useCallback`, `useMemo`, `useRef`) and native browser APIs.
- **Strict Compliance**: Zero external UI component libraries, zero heavy state packages (no Redux, no React Query, no Zustand, no Axios), per assessment constraints.

---

## 2. Architecture & Design Decisions

### 2.1 Component & Directory Structure
```
task2-admin-console/
├── src/
│   ├── components/
│   │   ├── Header.tsx                 # Top navigation, theme toggle, live refresh pulse
│   │   ├── MetricCard.tsx             # Stat cards (tenants, minutes, SMS, costs)
│   │   ├── AnalyticsCharts.tsx        # Recharts time-series & breakdown with retry
│   │   ├── AccountFilterBar.tsx       # Search, status, country, plan, date range picker
│   │   ├── AccountTable.tsx           # Paginated table with stable selection & CSV export
│   │   ├── AccountDetailDrawer.tsx    # Slide-over tenant detail & usage KPI drawer
│   │   ├── ErrorBoundary.tsx          # Top-level crash prevention with graceful reload UI
│   │   ├── SettingsWizardModal.tsx    # 4-step configuration dialog with keyboard trap
│   │   ├── FormStep1Personal.tsx      # Name & email step with validation
│   │   ├── FormStep2Subscription.tsx  # Plan & billing country (handles Section 4.8)
│   │   ├── FormStep3Limits.tsx        # Optional minutes & SMS caps
│   │   └── FormStep4Webhook.tsx       # Real-time webhook endpoint configuration
│   ├── hooks/
│   │   ├── useAccounts.ts             # Server-side pagination, search, sort, filter, stable selection
│   │   ├── useSummary.ts              # KPI metrics with bounded exponential backoff
│   │   ├── useSettingsDraft.ts        # 4-step wizard draft autosave, debouncing, recovery
│   │   └── useDebounce.ts             # Native timer debouncing
│   ├── services/
│   │   └── api.ts                     # Centralized, typed API layer with error mapping
│   ├── types/
│   │   └── index.ts                   # Strict TypeScript domain models & interfaces
│   ├── utils/
│   │   ├── formatters.ts              # Integer cents to currency, number commas, relative dates
│   │   └── retry.ts                   # Bounded exponential backoff with jitter
│   ├── pages/
│   │   └── DashboardPage.tsx          # Composed dashboard layout
│   ├── App.tsx                        # Root layout & dark mode state
│   └── main.tsx                       # React DOM entry point
├── mock-api/                          # Standalone Python mock API server & Dockerfile
├── nginx.conf                         # Production SPA router & reverse proxy
├── Dockerfile                         # Optimized multi-stage build (Node -> Nginx)
└── docker-compose.yml                 # Standalone Task 2 orchestration
```

### 2.2 State Management: Server, Client, and URL State
- **Server Cache & Synchronization**: Handled cleanly via custom hooks (`useAccounts`, `useSummary`). Avoids stale closures by comparing unique monotonically increasing request IDs (`activeRequestId.current`).
- **Stable Row Selection**: Selected rows are tracked using a `Set<string>` containing immutable `account.id` values. Unlike array index tracking, selecting a tenant on Page 1 is retained when navigating to Page 2, filtering, or when background 30-second polling refreshes the list.
- **Autosave Draft State**: Managed inside `useSettingsDraft`. Keystrokes instantly update local state (zero input lag) while debouncing network PUT requests by 800ms.

### 2.3 Resilient Handling of Random Summary API Failures (~20% Deliberate 500)
- The mock API deliberately returns HTTP 500 approximately 20% of the time.
- **Bounded Exponential Backoff**: The `useSummary` hook wraps requests in `fetchWithRetry` (3 attempts, initial 600ms delay, 1.8x factor + random jitter).
- **Graceful Degradation**: If all 3 retries fail, an isolated inline error card appears with a manual "Retry Analytics" button. The customer accounts directory, search, filters, and wizard remain **100% operational**. The dashboard never crashes.

### 2.4 Deliberate Section 4.8 Validation Behavior
- **The Behavior**: When step 4 has an active draft, the server deliberately rejects step 2 with `billing_country is required`, even if valid.
- **The Solution**: Rather than mutating the mock API, the frontend handles this via clean UX:
  1. All entered data across steps 1, 3, and 4 is strictly preserved.
  2. The wizard displays an informative warning banner explaining the requirement on Step 2.
  3. A one-click "Re-verify Country" action re-validates the field (`_revalidated: true`) and clears the error cleanly.

### 2.5 Periodic Silent Data Refresh
- Every 30 seconds, `useAccounts` executes a silent background fetch (`isBackgroundRefresh: true`).
- Does **not** unmount or flicker the table.
- Preserves pagination, active filters, and selected row IDs.
- Will not overwrite in-progress form edits.

### 2.6 Accessibility & Responsive Design
- Full keyboard operability (Tab navigation, Escape key closes modal, visible focus rings).
- Proper ARIA landmarks (`role="dialog"`, `aria-modal="true"`, `aria-labelledby`, `aria-label`).
- Responsive layout fully verified down to **375px mobile viewport** (stacked stat cards, responsive horizontal scroll table, touch-friendly touch targets).
- Dark and light theme toggle with system preference detection and localStorage persistence.

### 2.7 What Was Cut and Why
- **Heavy UI Component Libraries (e.g. Radix, MUI, AntD)**: Cut to strictly adhere to the assessment's mandate: *"The assessment restricts Task 2 to React, Tailwind and a chart library. Do not add component libraries"*.
- **External State Stores (Redux, Zustand, React Query)**: Cut to demonstrate mastery of native React hooks (`useCallback`, `useRef`, `useReducer`/`useState`), minimizing bundle weight to < 180kB gzip.

---

## 3. Docker & Deployment Instructions

### 3.1 Local Development
```bash
# Terminal 1: Start Mock API
cd mock-api
python server.py

# Terminal 2: Start Vite Dev Server
npm run dev
# App available at http://localhost:3000 (proxies /api -> http://localhost:8001)
```

### 3.2 Running with Docker Compose
```bash
docker compose up --build
```
- Frontend runs at `http://localhost:3000`
- Mock API runs at `http://localhost:8001`
- Frontend nginx container proxies `/api/` directly to `http://mock-api:8001/` internally.

### 3.3 Publishing Pre-Built Image to Docker Hub
Per Section 6:
```bash
# 1. Set your Docker Hub username
export DOCKER_HUB_USERNAME="yourusername"

# 2. Build production image
docker build -t $DOCKER_HUB_USERNAME/usage-admin-console:latest .

# 3. Log in to Docker Hub
docker login

# 4. Push image
docker push $DOCKER_HUB_USERNAME/usage-admin-console:latest
```
Evaluators can then run `docker compose up` directly using the published image.
