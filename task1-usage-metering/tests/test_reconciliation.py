import json
from datetime import datetime, timezone
from app.models.account import Account
from app.models.monthly_usage import MonthlyUsage
from app.models.call import Call


def test_reconciliation_heals_drift(client, db, make_signature, auth_headers):
    account_id = "acc_recon_test"
    cur_month = datetime.now(timezone.utc).strftime("%Y-%m")
    now_dt = datetime.now(timezone.utc)

    # 0. Seed Account
    acc = Account(
        id=account_id,
        name="Recon Test Account",
        email="recon@example.com",
        country="US",
        plan="pro",
        status="active"
    )
    db.add(acc)
    db.commit()

    # 1. Simulate 2 calls recorded in calls table
    c1 = Call(
        call_id="call_rec_1",
        account_id=account_id,
        status="ended",
        started_at=now_dt,
        ended_at=now_dt,
        duration_seconds=120,
        cost_cents=480,
        destination_country="US"
    )
    c2 = Call(
        call_id="call_rec_2",
        account_id=account_id,
        status="ended",
        started_at=now_dt,
        ended_at=now_dt,
        duration_seconds=180,
        cost_cents=720,
        destination_country="US"
    )
    db.add(c1)
    db.add(c2)

    # 2. Deliberately insert an out-of-sync/corrupted MonthlyUsage record
    corrupt_usage = MonthlyUsage(
        account_id=account_id,
        year_month=cur_month,
        total_calls=1,               # Corrupt: should be 2
        total_duration_seconds=50,   # Corrupt: should be 300
        total_cost_cents=200         # Corrupt: should be 1200
    )
    db.add(corrupt_usage)
    db.commit()

    # 3. Trigger reconciliation endpoint
    recon_res = client.post(f"/api/v1/reconciliation/{account_id}/{cur_month}", headers=auth_headers)
    assert recon_res.status_code == 200
    data = recon_res.json()
    assert data["reconciled"] is True
    assert data["discrepancy_detected"] is True
    assert data["calls_count_raw"] == 2
    assert data["duration_seconds_raw"] == 300
    assert data["cost_cents_raw"] == 1200

    # 4. Verify that MonthlyUsage in DB was auto-healed
    db.expire_all()
    healed = db.query(MonthlyUsage).filter(MonthlyUsage.account_id == account_id, MonthlyUsage.year_month == cur_month).first()
    assert healed.total_calls == 2
    assert healed.total_duration_seconds == 300
    assert healed.total_cost_cents == 1200

    # 5. Repeat reconciliation run (idempotent: discrepancy should now be False)
    recon_res_2 = client.post(f"/api/v1/reconciliation/{account_id}/{cur_month}", headers=auth_headers)
    assert recon_res_2.status_code == 200
    assert recon_res_2.json()["discrepancy_detected"] is False
