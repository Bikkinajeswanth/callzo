from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.deps import get_db, authenticate_api_key
from app.schemas.usage import ReconciliationResponse
from app.services.reconciliation_service import ReconciliationService
from app.workers.retry_worker import RetryWorker

router = APIRouter(prefix="/reconciliation", tags=["Reconciliation & Workers"], dependencies=[Depends(authenticate_api_key)])


@router.post("/{account_id}/{year_month}", response_model=ReconciliationResponse)
def reconcile_account_month(
    account_id: str,
    year_month: str,
    db: Session = Depends(get_db)
):
    """
    Triggers an idempotent reconciliation run that verifies stored monthly aggregates
    against raw calls. Corrects any drift and returns the audit comparison.
    """
    result = ReconciliationService.reconcile_monthly_usage(db, account_id, year_month)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account '{account_id}' not found"
        )
    return result


@router.post("/retries/process", summary="Execute Pending Retry Worker Cycle")
def execute_retry_cycle(
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """
    Manually triggers a retry worker cycle for pending failed webhook events.
    """
    processed = RetryWorker.process_pending_retries(db, limit=limit)
    return {
        "status": "success",
        "processed_retries": processed
    }
