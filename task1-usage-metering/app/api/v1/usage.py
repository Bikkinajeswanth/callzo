from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.api.deps import get_db, authenticate_api_key
from app.schemas.usage import UsageOverviewResponse, MonthlyUsageRecord, CallRecord
from app.services.usage_service import UsageService

router = APIRouter(prefix="/accounts", tags=["Usage APIs"], dependencies=[Depends(authenticate_api_key)])


@router.get("/{account_id}/usage/overview", response_model=UsageOverviewResponse)
def get_account_usage_overview(
    account_id: str,
    db: Session = Depends(get_db)
):
    overview = UsageService.get_account_overview(db, account_id)
    if not overview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account '{account_id}' not found"
        )
    return overview


@router.get("/{account_id}/usage/monthly", response_model=List[MonthlyUsageRecord])
def get_account_monthly_usage(
    account_id: str,
    year_month: Optional[str] = Query(None, pattern=r"^\d{4}-\d{2}$", description="Filter by YYYY-MM"),
    db: Session = Depends(get_db)
):
    return UsageService.get_monthly_usage(db, account_id, year_month)


@router.get("/{account_id}/calls")
def get_account_call_history(
    account_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None, pattern="^(started|ended|failed)$"),
    country: Optional[str] = Query(None, min_length=2, max_length=8),
    db: Session = Depends(get_db)
):
    calls, total = UsageService.get_calls_history(
        db, account_id, page=page, page_size=page_size, status=status, destination_country=country
    )
    return {
        "account_id": account_id,
        "page": page,
        "page_size": page_size,
        "total_records": total,
        "total_pages": (total + page_size - 1) // page_size if total > 0 else 0,
        "calls": calls
    }
