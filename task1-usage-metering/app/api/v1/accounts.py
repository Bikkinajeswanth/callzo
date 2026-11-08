"""
Accounts management API endpoints.

Provides CRUD operations for accounts. Accounts are also auto-provisioned
when a webhook event arrives for an unknown account_id — these endpoints
allow explicit management and listing.
"""
from typing import List, Optional
from datetime import datetime, timezone
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, authenticate_api_key
from app.models.account import Account
from app.schemas.account import AccountCreate, AccountResponse
from app.models.usage_cap import UsageCap

router = APIRouter(
    prefix="/accounts",
    tags=["Accounts"],
    dependencies=[Depends(authenticate_api_key)]
)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@router.post("", response_model=AccountResponse, status_code=status.HTTP_201_CREATED,
             summary="Create a new account")
def create_account(payload: AccountCreate, db: Session = Depends(get_db)):
    """
    Explicitly create an account with a known ID.
    If an account with the same ID already exists a 409 Conflict is returned.
    A default UsageCap row is created alongside the account.
    """
    existing = db.query(Account).filter(Account.id == payload.id).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Account '{payload.id}' already exists"
        )

    account = Account(
        id=payload.id,
        name=payload.name,
        email=payload.email,
        company=payload.company,
        country=payload.country,
        plan=payload.plan,
        status=payload.status,
        created_at=_utc_now(),
        updated_at=_utc_now(),
    )
    db.add(account)

    # Provision a default usage cap so the account is fully configured
    cap = UsageCap(
        account_id=payload.id,
        monthly_minutes_cap=None,   # Unlimited by default
        monthly_cost_cents_cap=None,  # Unlimited by default
        is_hard_cap=False,
        created_at=_utc_now(),
        updated_at=_utc_now(),
    )
    db.add(cap)
    db.commit()
    db.refresh(account)
    return account


@router.get("", response_model=List[AccountResponse], summary="List all accounts")
def list_accounts(
    status: Optional[str] = Query(None, pattern="^(active|trial|suspended)$"),
    plan: Optional[str] = Query(None, pattern="^(basic|pro|enterprise)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """
    Return a paginated list of all accounts.
    Supports filtering by status and plan.
    """
    q = db.query(Account)
    if status:
        q = q.filter(Account.status == status)
    if plan:
        q = q.filter(Account.plan == plan)
    q = q.order_by(Account.created_at.desc())
    offset = (page - 1) * page_size
    return q.offset(offset).limit(page_size).all()


@router.get("/{account_id}", response_model=AccountResponse, summary="Get account details")
def get_account(account_id: str, db: Session = Depends(get_db)):
    """Return a single account by ID."""
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account '{account_id}' not found"
        )
    return account


@router.patch("/{account_id}", response_model=AccountResponse, summary="Update account fields")
def update_account(
    account_id: str,
    payload: dict,
    db: Session = Depends(get_db)
):
    """
    Partial update — only the fields present in the request body are updated.
    Allowed fields: name, email, company, country, plan, status.
    """
    allowed = {"name", "email", "company", "country", "plan", "status"}
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account '{account_id}' not found"
        )

    for field, value in payload.items():
        if field in allowed:
            setattr(account, field, value)

    account.updated_at = _utc_now()
    db.commit()
    db.refresh(account)
    return account
