import json
from datetime import datetime, timezone, timedelta
from app.models.call import Call
from app.models.monthly_usage import MonthlyUsage


def test_out_of_order_events_handling(client, db, make_signature):
    """
    Test scenario:
    1. call.ended arrives FIRST
    2. call.started arrives LATER
    Verify:
    - Call is created with ended status, duration and cost preserved.
    - When started arrives later, call status remains 'ended', started_at is updated,
      and monthly usage is NOT double-counted.
    """
    account_id = "acc_test_01"
    call_id = "call_ooo_test_01"
    month_str = datetime.now(timezone.utc).strftime("%Y-%m")

    t_start = datetime.now(timezone.utc)
    t_end = t_start + timedelta(seconds=300)

    # 1. call.ended arrives first
    ended_payload = {
        "event_id": "evt_ooo_ended",
        "event_type": "call.ended",
        "account_id": account_id,
        "call_id": call_id,
        "timestamp": t_end.isoformat(),
        "duration_seconds": 300,
        "cost_cents": 1200,
        "destination_country": "GB"
    }
    raw_ended = json.dumps(ended_payload).encode("utf-8")
    sig_ended = make_signature(raw_ended)

    res1 = client.post("/webhooks/calls", content=raw_ended, headers={"Content-Type": "application/json", "X-Signature": sig_ended})
    assert res1.status_code == 200

    # Verify call state in DB
    db.expire_all()
    call = db.query(Call).filter(Call.call_id == call_id).first()
    assert call is not None
    assert call.status == "ended"
    assert call.duration_seconds == 300
    assert call.cost_cents == 1200
    assert call.started_at is None

    # Verify usage in DB
    usage1 = db.query(MonthlyUsage).filter(MonthlyUsage.account_id == account_id, MonthlyUsage.year_month == month_str).first()
    assert usage1.total_calls == 1
    assert usage1.total_duration_seconds == 300
    assert usage1.total_cost_cents == 1200

    # 2. call.started arrives late
    started_payload = {
        "event_id": "evt_ooo_started",
        "event_type": "call.started",
        "account_id": account_id,
        "call_id": call_id,
        "timestamp": t_start.isoformat(),
        "duration_seconds": 0,
        "cost_cents": 0,
        "destination_country": "GB"
    }
    raw_started = json.dumps(started_payload).encode("utf-8")
    sig_started = make_signature(raw_started)

    res2 = client.post("/webhooks/calls", content=raw_started, headers={"Content-Type": "application/json", "X-Signature": sig_started})
    assert res2.status_code == 200

    # Final DB assertions
    db.expire_all()
    call_final = db.query(Call).filter(Call.call_id == call_id).first()
    assert call_final.status == "ended"  # NOT reverted to started
    assert call_final.duration_seconds == 300
    assert call_final.cost_cents == 1200
    assert call_final.started_at is not None

    # Crucial assertion: Total calls, duration, and cost must NOT be double-counted!
    usage2 = db.query(MonthlyUsage).filter(MonthlyUsage.account_id == account_id, MonthlyUsage.year_month == month_str).first()
    assert usage2.total_calls == 1
    assert usage2.total_duration_seconds == 300
    assert usage2.total_cost_cents == 1200
