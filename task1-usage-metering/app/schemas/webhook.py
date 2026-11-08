from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class WebhookEventType(str, Enum):
    CALL_STARTED = "call.started"
    CALL_ENDED = "call.ended"
    CALL_FAILED = "call.failed"


class WebhookCallEvent(BaseModel):
    event_id: str = Field(..., min_length=1, description="Unique event identifier")
    event_type: WebhookEventType = Field(..., description="Type of call event")
    account_id: str = Field(..., min_length=1, description="Target customer account ID")
    call_id: str = Field(..., min_length=1, description="Unique call session ID")
    timestamp: datetime = Field(..., description="Event generation timestamp in UTC")
    duration_seconds: int = Field(default=0, ge=0, description="Duration of call in seconds")
    cost_cents: int = Field(default=0, ge=0, description="Cost in integer cents")
    destination_country: str = Field(..., min_length=2, max_length=8, description="ISO destination country code")

    @field_validator("destination_country")
    @classmethod
    def validate_country(cls, v: str) -> str:
        return v.upper().strip()


class WebhookResponse(BaseModel):
    status: str
    event_id: str
    call_id: str
    account_id: str
    message: Optional[str] = None
    cap_status: Optional[str] = "ok"  # ok, soft_limit_exceeded, hard_limit_exceeded
