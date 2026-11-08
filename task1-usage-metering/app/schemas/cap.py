from typing import Optional
from pydantic import BaseModel, Field


class UsageCapBase(BaseModel):
    monthly_minutes_cap: Optional[int] = Field(None, ge=0, description="Monthly minutes limit")
    monthly_cost_cents_cap: Optional[int] = Field(None, ge=0, description="Monthly cost limit in cents")
    is_hard_cap: bool = Field(True, description="True blocks/flags hard violation, False allows soft warning")
    cap_action: str = Field("flag_exceeded", description="Action taken when cap exceeded")


class UsageCapUpdate(UsageCapBase):
    pass


class UsageCapResponse(UsageCapBase):
    account_id: str
    current_month_minutes: int
    current_month_cost_cents: int
    minutes_utilization_pct: Optional[float]
    cost_utilization_pct: Optional[float]
    cap_breached: bool
