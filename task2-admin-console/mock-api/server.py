"""
Callzo Mock Telephony Admin API Service
Simulates the backend services for the Usage Admin Console per Task 2 specifications:
- GET /health
- GET /accounts (search, filter, sort, pagination)
- GET /accounts/{id}
- GET /accounts/summary (deliberate ~20% HTTP 500 failure rate)
- GET /accounts/{id}/settings
- PUT /accounts/{id}/settings/step/{step} (deliberate step 4 -> step 2 validation behavior)
- POST /accounts/{id}/settings/submit
"""

import os
import random
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, Query, status, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field

app = FastAPI(title="Callzo Mock Admin API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Seed realistic customer accounts
COMPANIES = ["Acme Corp", "NovaTech", "Apex Logistics", "Starlight Media", "CloudFlow", "Vanguard AI", "Summit Health", "Pinnacle Capital", "Horizon Telecom", "Beacon Financial"]
COUNTRIES = ["US", "IN", "GB", "CA", "AU"]
PLANS = ["basic", "pro", "enterprise"]
STATUSES = ["active", "trial", "suspended"]

ACCOUNTS_DB: List[Dict[str, Any]] = []

def seed_accounts():
    random.seed(42)
    base_time = datetime(2026, 1, 15, tzinfo=timezone.utc)
    for i in range(1, 46):
        acc_id = f"acc_{i:03d}"
        company = COMPANIES[(i - 1) % len(COMPANIES)]
        name = f"Admin User {i}"
        country = COUNTRIES[(i - 1) % len(COUNTRIES)]
        plan = PLANS[(i - 1) % len(PLANS)]
        acc_status = "active" if i % 6 != 0 else ("trial" if i % 3 == 0 else "suspended")
        created_at = (base_time + timedelta(days=i * 6)).isoformat()
        last_active = (datetime.now(timezone.utc) - timedelta(minutes=random.randint(5, 14400))).isoformat()
        
        minutes = random.randint(120, 18500)
        sms = random.randint(50, 4200)
        cost_cents = int((minutes * 4.5) + (sms * 2.0))

        ACCOUNTS_DB.append({
            "id": acc_id,
            "name": name,
            "email": f"user{i}@{company.lower().replace(' ', '')}.com",
            "company": company,
            "country": country,
            "plan": plan,
            "status": acc_status,
            "monthly_minutes": minutes,
            "monthly_sms": sms,
            "cost_cents": cost_cents,
            "created_at": created_at,
            "last_active": last_active
        })

seed_accounts()

# In-memory storage for settings drafts per account
# schema: { account_id: { step1: {}, step2: {}, step3: {}, step4: {}, submitted: False } }
SETTINGS_DRAFTS: Dict[str, Dict[str, Any]] = {}


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "mock-api",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@app.get("/accounts")
def get_accounts(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    search: Optional[str] = Query(None, description="Search by name, email, company, or ID"),
    sort_by: Optional[str] = Query("created_at", description="Field to sort by"),
    sort_dir: Optional[str] = Query("desc", description="Sort direction: asc or desc"),
    status: Optional[str] = Query(None, description="Filter by status: active, trial, suspended"),
    country: Optional[str] = Query(None, description="Filter by country: US, IN, GB, CA, AU"),
    plan: Optional[str] = Query(None, description="Filter by plan: basic, pro, enterprise"),
    start_date: Optional[str] = Query(None, description="Filter signup created_at >= start_date (ISO)"),
    end_date: Optional[str] = Query(None, description="Filter signup created_at <= end_date (ISO)")
):
    # Slight dynamic simulation on refresh: adjust minutes/last_active slightly
    # (per requirement 4.10: mock accounts endpoint changes slightly between requests)
    for acc in ACCOUNTS_DB:
        if random.random() < 0.15:
            delta = random.randint(-5, 10)
            acc["monthly_minutes"] = max(0, acc["monthly_minutes"] + delta)
            acc["cost_cents"] = max(0, int((acc["monthly_minutes"] * 4.5) + (acc["monthly_sms"] * 2.0)))

    results = list(ACCOUNTS_DB)

    # Search filter
    if search:
        q = search.lower().strip()
        results = [
            a for a in results
            if q in a["name"].lower() or q in a["email"].lower() or q in a["company"].lower() or q in a["id"].lower()
        ]

    # Status filter
    if status:
        results = [a for a in results if a["status"].lower() == status.lower()]

    # Country filter
    if country:
        results = [a for a in results if a["country"].upper() == country.upper()]

    # Plan filter
    if plan:
        results = [a for a in results if a["plan"].lower() == plan.lower()]

    # Date range filters
    if start_date:
        results = [a for a in results if a["created_at"] >= start_date]
    if end_date:
        results = [a for a in results if a["created_at"] <= end_date]

    # Sorting
    reverse = (sort_dir.lower() == "desc")
    if sort_by in ["monthly_minutes", "monthly_sms", "cost_cents"]:
        results.sort(key=lambda x: x.get(sort_by, 0), reverse=reverse)
    elif sort_by in ["name", "email", "company", "country", "plan", "status", "created_at", "last_active"]:
        results.sort(key=lambda x: str(x.get(sort_by, "")).lower(), reverse=reverse)

    total = len(results)
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paginated = results[start_idx:end_idx]

    return {
        "page": page,
        "page_size": page_size,
        "total_records": total,
        "total_pages": (total + page_size - 1) // page_size if total > 0 else 0,
        "accounts": paginated
    }


@app.get("/accounts/summary")
def get_accounts_summary(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
):
    """
    Deliberately fails with HTTP 500 ~20% of the time to test dashboard resilience
    and bounded retry strategies per Section 4.6.
    """
    if random.random() < 0.20:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Transient Analytics Engine Failure (Deliberate 20% assessment scenario)"
        )

    # Filter by date range if provided
    records = list(ACCOUNTS_DB)
    if start_date:
        records = [r for r in records if r["created_at"] >= start_date]
    if end_date:
        records = [r for r in records if r["created_at"] <= end_date]

    total_accounts = len(records)
    active_count = sum(1 for a in records if a["status"] == "active")
    trial_count = sum(1 for a in records if a["status"] == "trial")
    suspended_count = sum(1 for a in records if a["status"] == "suspended")
    total_minutes = sum(a["monthly_minutes"] for a in records)
    total_sms = sum(a["monthly_sms"] for a in records)
    total_cost_cents = sum(a["cost_cents"] for a in records)

    # Generate realistic trend breakdown (e.g., last 6 months)
    trends = [
        {"month": "Jun", "minutes": 42000, "sms": 12500, "cost_cents": 214000, "signups": 5},
        {"month": "Jul", "minutes": 48500, "sms": 14200, "cost_cents": 246650, "signups": 7},
        {"month": "Aug", "minutes": 55100, "sms": 15800, "cost_cents": 279550, "signups": 9},
        {"month": "Sep", "minutes": 63200, "sms": 17400, "cost_cents": 319200, "signups": 8},
        {"month": "Oct", "minutes": 71800, "sms": 19600, "cost_cents": 362300, "signups": 11},
        {"month": "Nov", "minutes": total_minutes, "sms": total_sms, "cost_cents": total_cost_cents, "signups": total_accounts}
    ]

    return {
        "total_accounts": total_accounts,
        "active_accounts": active_count,
        "trial_accounts": trial_count,
        "suspended_accounts": suspended_count,
        "total_minutes": total_minutes,
        "total_sms": total_sms,
        "total_cost_cents": total_cost_cents,
        "trends": trends
    }


@app.get("/accounts/{account_id}")
def get_account_detail(account_id: str):
    acc = next((a for a in ACCOUNTS_DB if a["id"] == account_id), None)
    if not acc:
        raise HTTPException(status_code=404, detail="Account not found")
    return acc


@app.get("/accounts/{account_id}/settings")
def get_account_settings(account_id: str):
    """
    Returns saved draft or default configuration for the 4-step wizard.
    """
    acc = next((a for a in ACCOUNTS_DB if a["id"] == account_id), None)
    if not acc:
        raise HTTPException(status_code=404, detail="Account not found")

    draft = SETTINGS_DRAFTS.get(account_id, {
        "step1": {"name": acc["name"], "email": acc["email"]},
        "step2": {"plan": acc["plan"], "billing_country": acc["country"]},
        "step3": {"minutes_cap": None, "sms_cap": None},
        "step4": {"webhook_url": ""},
        "submitted": False
    })
    return draft


@app.put("/accounts/{account_id}/settings/step/{step}")
def save_account_settings_step(account_id: str, step: int, payload: Dict[str, Any]):
    """
    Autosaves step drafts. Contains deliberate Section 4.8 behavior:
    When step 4's draft exists, saving or re-saving step 2 may reject billing_country with
    'billing_country is required' even if previously valid!
    """
    if step not in [1, 2, 3, 4]:
        raise HTTPException(status_code=400, detail="Invalid step number (must be 1-4)")

    if account_id not in SETTINGS_DRAFTS:
        # Initialize default from account
        acc = next((a for a in ACCOUNTS_DB if a["id"] == account_id), None)
        SETTINGS_DRAFTS[account_id] = {
            "step1": {"name": acc["name"] if acc else "", "email": acc["email"] if acc else ""},
            "step2": {"plan": acc["plan"] if acc else "pro", "billing_country": acc["country"] if acc else "US"},
            "step3": {"minutes_cap": None, "sms_cap": None},
            "step4": {"webhook_url": ""},
            "submitted": False
        }

    draft = SETTINGS_DRAFTS[account_id]

    # Step 1 Validation
    if step == 1:
        name = payload.get("name", "").strip()
        email = payload.get("email", "").strip()
        if not name:
            raise HTTPException(status_code=422, detail="Name is required")
        if not email or "@" not in email:
            raise HTTPException(status_code=422, detail="Valid email containing '@' is required")
        draft["step1"] = {"name": name, "email": email}

    # Step 2 Validation & Deliberate Section 4.8 Behavior
    elif step == 2:
        plan = payload.get("plan", "pro")
        billing_country = payload.get("billing_country", "").strip()

        # Deliberate Assessment Quirky Behavior:
        # If step 4 has already been configured (e.g. non-empty webhook_url or step 4 was saved),
        # simulate the server-side rejection: "billing_country is required"
        step4_data = draft.get("step4", {})
        has_step4_draft = bool(step4_data.get("webhook_url") or draft.get("step4_saved"))

        if has_step4_draft and payload.get("_revalidated") is not True:
            # Deliberately reject with the exact assessment string
            raise HTTPException(
                status_code=422,
                detail="billing_country is required"
            )

        if not billing_country or billing_country not in ["US", "IN", "GB", "CA", "AU"]:
            raise HTTPException(status_code=422, detail="billing_country is required and must be one of: US, IN, GB, CA, AU")

        draft["step2"] = {"plan": plan, "billing_country": billing_country}

    # Step 3 Validation
    elif step == 3:
        min_cap = payload.get("minutes_cap")
        sms_cap = payload.get("sms_cap")
        if min_cap is not None and int(min_cap) < 0:
            raise HTTPException(status_code=422, detail="minutes_cap must be non-negative")
        if sms_cap is not None and int(sms_cap) < 0:
            raise HTTPException(status_code=422, detail="sms_cap must be non-negative")
        draft["step3"] = {
            "minutes_cap": int(min_cap) if min_cap is not None and str(min_cap) != "" else None,
            "sms_cap": int(sms_cap) if sms_cap is not None and str(sms_cap) != "" else None
        }

    # Step 4 Validation
    elif step == 4:
        url = payload.get("webhook_url", "").strip()
        if url and not (url.startswith("http://") or url.startswith("https://")):
            raise HTTPException(status_code=422, detail="webhook_url must begin with http:// or https://")
        draft["step4"] = {"webhook_url": url}
        draft["step4_saved"] = True

    return {
        "status": "saved",
        "step": step,
        "saved_at": datetime.now(timezone.utc).isoformat(),
        "draft": draft[f"step{step}"]
    }


@app.post("/accounts/{account_id}/settings/submit")
def submit_account_settings(account_id: str):
    draft = SETTINGS_DRAFTS.get(account_id)
    if not draft:
        raise HTTPException(status_code=400, detail="No settings draft found for this account")

    # Verify all four steps are present
    if not draft.get("step1") or not draft.get("step2") or not draft.get("step3") or not draft.get("step4"):
        raise HTTPException(status_code=422, detail="All 4 steps must be completed before submission")

    draft["submitted"] = True
    draft["submitted_at"] = datetime.now(timezone.utc).isoformat()

    # Update account in main DB
    acc = next((a for a in ACCOUNTS_DB if a["id"] == account_id), None)
    if acc:
        acc["name"] = draft["step1"]["name"]
        acc["email"] = draft["step1"]["email"]
        acc["plan"] = draft["step2"]["plan"]
        acc["country"] = draft["step2"]["billing_country"]

    return {
        "status": "success",
        "message": "Account settings successfully submitted and activated",
        "account_id": account_id,
        "updated_settings": draft
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8001, reload=True)
