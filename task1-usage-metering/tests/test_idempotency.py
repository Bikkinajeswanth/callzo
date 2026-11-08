import json
from datetime import datetime, timezone
from app.models.monthly_usage import MonthlyUsage
from app.models.call import Call


def test_duplicate_event_idempotency(client, db, make_signature):
    now_str = datetime.now(timezone.utc).isoformat()
    month_str = datetime.now(timezone.utc).strftime("%Y-%m")
    event_id = "evt_idempotent_test_01"
    call_id = "call_idempotent_01"
    account_id = "acc_test_01"

    payload = {
        "event_id": event_id,
        "event_type": "call.ended",
        "account_id": account_id,
        "call_id": call_id,
        "timestamp": now_str,
        "duration_seconds": 180,
        "cost_cents": 720,
        "destination_country": "US"
    }
    raw_bytes = json.dumps(payload).encode("utf-8")
    sig = make_signature(raw_bytes)
    headers = {"Content-Type": "application/json", "X-Signature": sig}

    # First delivery
    res1 = client.post("/webhooks/calls", content=raw_bytes, headers=headers)
    assert res1.status_code == 200
    assert res1.json()["status"] == "processed"

    # Verify usage in DB
    usage1 = db.query(MonthlyUsage).filter(MonthlyUsage.account_id == account_id, MonthlyUsage.year_month == month_str).first()
    assert usage1 is not None
    assert usage1.total_calls == 1
    assert usage1.total_duration_seconds == 180
    assert usage1.total_cost_cents == 720

    # Second delivery (Duplicate event_id)
    res2 = client.post("/webhooks/calls", content=raw_bytes, headers=headers)
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["status"] == "duplicate"
    assert "already been processed" in data2["message"]

    # Third delivery (Duplicate again)
    res3 = client.post("/webhooks/calls", content=raw_bytes, headers=headers)
    assert res3.status_code == 200
    assert res3.json()["status"] == "duplicate"

    # Crucial assertion: Stored usage must NOT increase
    db.expire_all()
    usage2 = db.query(MonthlyUsage).filter(MonthlyUsage.account_id == account_id, MonthlyUsage.year_month == month_str).first()
    assert usage2.total_calls == 1
    assert usage2.total_duration_seconds == 180
    assert usage2.total_cost_cents == 720
