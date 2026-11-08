from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.deps import get_db, authenticate_api_key
from app.schemas.cap import UsageCapResponse, UsageCapUpdate
from app.services.cap_service import CapService

router = APIRouter(prefix="/accounts", tags=["Usage Caps"], dependencies=[Depends(authenticate_api_key)])


@router.get("/{account_id}/cap", response_model=UsageCapResponse)
def get_account_cap(
    account_id: str,
    db: Session = Depends(get_db)
):
    cap = CapService.get_account_cap(db, account_id)
    if not cap:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account '{account_id}' not found"
        )
    return cap


@router.put("/{account_id}/cap", response_model=UsageCapResponse)
def update_account_cap(
    account_id: str,
    cap_update: UsageCapUpdate,
    db: Session = Depends(get_db)
):
    return CapService.update_account_cap(db, account_id, cap_update)
