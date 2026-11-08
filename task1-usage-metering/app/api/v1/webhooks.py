import json
from fastapi import APIRouter, Depends, Request, Header, HTTPException, status
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_raw_body
from app.core.security import verify_webhook_signature
from app.schemas.webhook import WebhookCallEvent, WebhookResponse
from app.services.webhook_service import WebhookService
from app.core.logging import logger

router = APIRouter(tags=["Webhooks"])


@router.post(
    "/webhooks/calls",
    response_model=WebhookResponse,
    summary="Receive Call Events from Telephony Simulator"
)
async def receive_call_webhook(
    request: Request,
    raw_body: bytes = Depends(get_raw_body),
    x_signature: str | None = Header(None, alias="X-Signature"),
    db: Session = Depends(get_db)
):
    """
    Receives and processes telephony call lifecycle webhooks:
    - Verifies raw bytes against HMAC-SHA256 signature
    - Strictly validates JSON payload schema
    - Enforces idempotency via database unique constraints
    - Handles out-of-order event sequences (ended before started)
    - Records late events against their historical billing month
    - Checks account usage caps with row-level transactional safety
    """
    # 1. Verify Signature on Raw Request Bytes
    verify_webhook_signature(raw_body, x_signature)

    # 2. Parse and Validate JSON Schema
    try:
        payload_dict = json.loads(raw_body.decode("utf-8"))
    except Exception as e:
        logger.warning(f"Malformed JSON received in webhook: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Malformed JSON payload: {str(e)}"
        )

    try:
        event = WebhookCallEvent(**payload_dict)
    except Exception as e:
        logger.warning(f"Payload schema validation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid event schema: {str(e)}"
        )

    # 3. Process Event
    try:
        response = WebhookService.process_call_event(
            db=db,
            event=event,
            raw_body=raw_body,
            signature=x_signature
        )
        return response
    except Exception as e:
        # Fallback to retry queue for unexpected runtime errors
        WebhookService.record_failed_event(
            db=db,
            event_id=event.event_id,
            payload_str=raw_body.decode("utf-8", errors="replace"),
            error_msg=str(e)
        )
        logger.error(f"Error processing webhook event {event.event_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing event; queued for background retry"
        )
