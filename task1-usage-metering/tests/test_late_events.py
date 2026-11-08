import json
from datetime import datetime, timezone, timedelta
from app.models.monthly_usage import MonthlyUsage


def test_late_event_historical_month_accounting(client, db, make_signature):
    """
    Test scenario:
    Event arrives today, but timestamp is 35 days in the past (e.g. previous month).
    Verify:
    - The usage is attributed strictly to that historical month.
    - The current month's usage is unaffected and not inflated.
    """
    account_id = "acc_test_01"
    cur_month = datetime.now(timezone.utc).strftime("%Y-%m")
    past_date = datetime.now(timezone.utc) - timedelta(days=35)
    past_month = past_date.strftime("%Y-%m")

    assert past_month != cur_month, "Test requires past month to be distinct from current month"

    payload = {
        "event_id": "evt_late_accounting_01",
        "event_type": "call.ended",
        "account_id": account_id,
        "call_id": "call_late_01",
        "timestamp": past_date.isoformat(),
        "duration_seconds": 600,
        "cost_cents": 2400,
        "destination_country": "US"
    }
    raw_bytes = json.dumps(payload).encode("utf-8")
    sig = make_signature(raw_bytes)

    res = client.post("/webhooks/calls", content=raw_bytes, headers={"Content-Type": "application/json", "X-Signature": sig})
    assert res.status_code == 200

    db.expire_all()
    # Check historical month record
    past_usage = db.query(MonthlyUsage).filter(MonthlyUsage.account_id == account_id, MonthlyUsage.year_month == past_month).first()
    assert past_usage is not None
    assert past_usage.total_calls == 1
    assert past_usage.total_duration_seconds == 600
    assert past_usage.total_cost_cents == 2400

    # Check current month record (should be untouched or non-existent)
    cur_usage = db.query(MonthlyUsage).filter(MonthlyUsage.account_id == account_id, MonthlyUsage.year_month == cur_month).first()
    if cur_usage:
        assert cur_usage.total_calls == 0
        assert cur_usage.total_duration_seconds == 0
