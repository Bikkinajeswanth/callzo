from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class AccountBase(BaseModel):
    name: str = Field(..., min_length=1)
    email: EmailStr
    company: Optional[str] = None
    country: str = Field("US", min_length=2, max_length=8)
    plan: str = Field("pro", pattern="^(basic|pro|enterprise)$")
    status: str = Field("active", pattern="^(active|trial|suspended)$")


class AccountCreate(AccountBase):
    id: str = Field(..., min_length=1)


class AccountResponse(AccountBase):
    id: str
    created_at: datetime
    updated_at: datetime
