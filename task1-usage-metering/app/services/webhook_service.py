import json
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.models.account import Account
from app.models.webhook_event import RawWebhookEvent
from app.models.call import Call
from app.models.monthly_usage import MonthlyUsage
from app.models.usage_cap import UsageCap
from app.models.retry_record import EventRetryRecord
from app.schemas.webhook import WebhookCallEvent, WebhookEventType, WebhookResponse
from app.core.logging import logger


class WebhookService:
    @staticmethod
    def process_call_event(
        db: Session,
        event: WebhookCallEvent,
        raw_body: bytes,
        signature: str | None
    ) -> WebhookResponse:
        """
        Processes an incoming webhook call event with transactional idempotency,
        out-of-order resolution, late-event handling, and monthly cap verification.
        """
        # 1. Idempotency Check at Database Level
        existing_event = db.query(RawWebhookEvent).filter(RawWebhookEvent.event_id == event.event_id).first()
        if existing_event:
            logger.info(
                f"Duplicate event received and skipped: {event.event_id}",
                extra={"correlation_id": event.event_id, "extra_data": {"call_id": event.call_id}}
            )
            return WebhookResponse(
                status="duplicate",
                event_id=event.event_id,
                call_id=event.call_id,
                account_id=event.account_id,
                message="Event has already been processed",
                cap_status="ok"
            )

        # 2. Ensure Account exists (auto-provision default if new)
        account = db.query(Account).filter(Account.id == event.account_id).first()
        if not account:
            account = Account(
                id=event.account_id,
                name=f"Account {event.account_id}",
                email=f"{event.account_id}@callzo-customer.io",
                country=event.destination_country or "US",
                plan="pro",
                status="active"
            )
            db.add(account)
            db.flush()

        # 3. Insert Raw Event Immutably
        raw_record = RawWebhookEvent(
            event_id=event.event_id,
            event_type=event.event_type.value,
            account_id=event.account_id,
            call_id=event.call_id,
            payload=raw_body.decode("utf-8", errors="replace"),
            signature=signature,
            received_at=datetime.now(timezone.utc),
            processing_status="processed"
        )
        db.add(raw_record)

        try:
            db.flush()
        except IntegrityError:
            # Concurrent duplicate arrival
            db.rollback()
            logger.info(f"Concurrent duplicate event caught via unique constraint: {event.event_id}")
            return WebhookResponse(
                status="duplicate",
                event_id=event.event_id,
                call_id=event.call_id,
                account_id=event.account_id,
                message="Event was concurrently processed",
                cap_status="ok"
            )

        # 4. Determine Accounting Month (uses original event timestamp for late events)
        event_time = event.timestamp
        year_month = event_time.strftime("%Y-%m")

        # 5. Fetch or Create Monthly Usage record with row lock for correctness
        monthly_usage = (
            db.query(MonthlyUsage)
            .filter(MonthlyUsage.account_id == event.account_id, MonthlyUsage.year_month == year_month)
            .with_for_update()
            .first()
        )
        if not monthly_usage:
            monthly_usage = MonthlyUsage(
                account_id=event.account_id,
                year_month=year_month,
                total_calls=0,
                total_duration_seconds=0,
                total_cost_cents=0
            )
            db.add(monthly_usage)
            db.flush()

        # 6. Out-of-Order Call State Resolution
        call = db.query(Call).filter(Call.call_id == event.call_id).with_for_update().first()

        if event.event_type == WebhookEventType.CALL_STARTED:
            if not call:
                call = Call(
                    call_id=event.call_id,
                    account_id=event.account_id,
                    status="started",
                    started_at=event_time,
                    destination_country=event.destination_country,
                    duration_seconds=0,
                    cost_cents=0
                )
                db.add(call)
                monthly_usage.total_calls += 1
            else:
                # Call already recorded (e.g. call.ended arrived before call.started)
                if not call.started_at:
                    call.started_at = event_time

        elif event.event_type == WebhookEventType.CALL_ENDED:
            if not call:
                # Out-of-order: call.ended arrived before call.started!
                call = Call(
                    call_id=event.call_id,
                    account_id=event.account_id,
                    status="ended",
                    started_at=None,
                    ended_at=event_time,
                    destination_country=event.destination_country,
                    duration_seconds=event.duration_seconds,
                    cost_cents=event.cost_cents
                )
                db.add(call)
                monthly_usage.total_calls += 1
                monthly_usage.total_duration_seconds += event.duration_seconds
                monthly_usage.total_cost_cents += event.cost_cents
            else:
                # Normal order or repeated update
                if call.status != "ended":
                    call.status = "ended"
                    call.ended_at = event_time
                    call.duration_seconds = event.duration_seconds
                    call.cost_cents = event.cost_cents
                    # Total calls was already counted on call.started; add duration and cost now
                    monthly_usage.total_duration_seconds += event.duration_seconds
                    monthly_usage.total_cost_cents += event.cost_cents

        elif event.event_type == WebhookEventType.CALL_FAILED:
            if not call:
                call = Call(
                    call_id=event.call_id,
                    account_id=event.account_id,
                    status="failed",
                    started_at=event_time,
                    ended_at=event_time,
                    destination_country=event.destination_country,
                    duration_seconds=event.duration_seconds,
                    cost_cents=event.cost_cents
                )
                db.add(call)
                monthly_usage.total_calls += 1
                monthly_usage.total_duration_seconds += event.duration_seconds
                monthly_usage.total_cost_cents += event.cost_cents
            else:
                call.status = "failed"
                call.ended_at = event_time

        # 7. Evaluate Usage Caps
        cap_status = "ok"
        usage_cap = db.query(UsageCap).filter(UsageCap.account_id == event.account_id).first()
        if usage_cap:
            minutes_used = monthly_usage.total_duration_seconds / 60.0
            cost_used = monthly_usage.total_cost_cents

            minutes_breached = bool(usage_cap.monthly_minutes_cap and minutes_used > usage_cap.monthly_minutes_cap)
            cost_breached = bool(usage_cap.monthly_cost_cents_cap and cost_used > usage_cap.monthly_cost_cents_cap)

            if minutes_breached or cost_breached:
                if usage_cap.is_hard_cap:
                    cap_status = "hard_limit_exceeded"
                else:
                    cap_status = "soft_limit_exceeded"

        # Commit transaction
        db.commit()

        logger.info(
            f"Successfully processed webhook {event.event_type.value} for call {event.call_id}",
            extra={
                "correlation_id": event.event_id,
                "extra_data": {
                    "account_id": event.account_id,
                    "event_type": event.event_type.value,
                    "cap_status": cap_status
                }
            }
        )

        return WebhookResponse(
            status="processed",
            event_id=event.event_id,
            call_id=event.call_id,
            account_id=event.account_id,
            message="Webhook event processed successfully",
            cap_status=cap_status
        )

    @staticmethod
    def record_failed_event(db: Session, event_id: str, payload_str: str, error_msg: str):
        """
        Saves a failed event to the retry table for background re-processing.
        """
        try:
            retry_record = EventRetryRecord(
                event_id=event_id,
                payload=payload_str,
                attempts=1,
                last_error=error_msg,
                status="pending"
            )
            db.add(retry_record)
            db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to record retry entry for event {event_id}: {str(e)}")
