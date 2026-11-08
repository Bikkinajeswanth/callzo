from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class CallRecord(BaseModel):
    call_id: str
    account_id: str
    status: str
    started_at: Optional[datetime]
    ended_at: Optional[datetime]
    duration_seconds: int
    cost_cents: int
    destination_country: Optional[str]
    created_at: datetime


class MonthlyUsageRecord(BaseModel):
    account_id: str
    year_month: str
    total_calls: int
    total_duration_seconds: int
    total_duration_minutes: float
    total_cost_cents: int
    total_cost_formatted: str
    updated_at: datetime


class UsageOverviewResponse(BaseModel):
    account_id: str
    account_name: str
    account_status: str
    current_month: str
    current_month_calls: int
    current_month_minutes: float
    current_month_cost_cents: int
    current_month_cost_formatted: str
    lifetime_calls: int
    lifetime_minutes: float
    lifetime_cost_cents: int
    lifetime_cost_formatted: str
    cap_status: str
    cap_details: Optional[dict] = None


class ReconciliationResponse(BaseModel):
    account_id: str
    year_month: str
    reconciled: bool
    calls_count_raw: int
    calls_count_aggregated: int
    duration_seconds_raw: int
    duration_seconds_aggregated: int
    cost_cents_raw: int
    cost_cents_aggregated: int
    discrepancy_detected: bool
    discrepancy_details: Optional[dict] = None
