import json
from datetime import datetime, timezone, timedelta
from app.models.retry_record import EventRetryRecord
from app.workers.retry_worker import RetryWorker


def test_retry_worker_lifecycle(db):
    now = datetime.now(timezone.utc)
    event_id = "evt_retry_test_01"

    payload = {
        "event_id": event_id,
        "event_type": "call.started",
        "account_id": "acc_test_01",
        "call_id": "call_retry_01",
        "timestamp": now.isoformat(),
        "duration_seconds": 0,
        "cost_cents": 0,
        "destination_country": "US"
    }

    # Insert a failed retry record
    retry_rec = EventRetryRecord(
        event_id=event_id,
        payload=json.dumps(payload),
        attempts=0,
        max_attempts=3,
        status="pending",
        next_retry_at=now - timedelta(seconds=10)
    )
    db.add(retry_rec)
    db.commit()

    # Run retry worker cycle
    processed = RetryWorker.process_pending_retries(db, limit=5)
    assert processed == 1

    db.expire_all()
    updated = db.query(EventRetryRecord).filter(EventRetryRecord.event_id == event_id).first()
    assert updated.status == "completed"
    assert updated.attempts == 1
