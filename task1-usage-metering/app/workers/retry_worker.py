import json
import time
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from app.models.retry_record import EventRetryRecord
from app.schemas.webhook import WebhookCallEvent
from app.services.webhook_service import WebhookService
from app.core.config import settings
from app.core.logging import logger


class RetryWorker:
    """
    Background worker that continuously or on-demand polls for failed webhook events
    and retries processing using exponential backoff.
    """

    @staticmethod
    def process_pending_retries(db: Session, limit: int = 10) -> int:
        now = datetime.now(timezone.utc)
        pending = (
            db.query(EventRetryRecord)
            .filter(
                EventRetryRecord.status.in_(["pending", "in_progress"]),
                EventRetryRecord.next_retry_at <= now,
                EventRetryRecord.attempts < EventRetryRecord.max_attempts
            )
            .limit(limit)
            .all()
        )

        processed_count = 0

        for record in pending:
            record.status = "in_progress"
            record.attempts += 1
            db.commit()

            try:
                payload_data = json.loads(record.payload)
                event = WebhookCallEvent(**payload_data)

                # Attempt replay
                result = WebhookService.process_call_event(
                    db=db,
                    event=event,
                    raw_body=record.payload.encode("utf-8"),
                    signature=None  # Signature verified on initial ingress
                )

                record.status = "completed"
                record.last_error = None
                db.commit()
                processed_count += 1
                logger.info(f"Retry worker successfully resolved event {record.event_id}")

            except Exception as e:
                db.rollback()
                record.last_error = str(e)

                if record.attempts >= record.max_attempts:
                    record.status = "exhausted"
                    logger.error(f"Event {record.event_id} permanently failed after {record.attempts} attempts")
                else:
                    record.status = "pending"
                    # Exponential backoff: base_seconds * (2 ** (attempt - 1))
                    backoff = settings.INITIAL_RETRY_BACKOFF_SECONDS * (2 ** (record.attempts - 1))
                    record.next_retry_at = datetime.now(timezone.utc) + timedelta(seconds=backoff)
                    logger.warning(f"Event {record.event_id} failed attempt {record.attempts}. Next retry in {backoff}s")

                db.commit()

        return processed_count
