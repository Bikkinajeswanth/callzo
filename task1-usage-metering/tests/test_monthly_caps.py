import json
from datetime import datetime, timezone
from app.models.usage_cap import UsageCap


def test_monthly_cap_enforcement(client, db, make_signature, auth_headers):
    account_id = "acc_cap_test_01"
    now_str = datetime.now(timezone.utc).isoformat()

    # Configure a cap of 10 minutes (600 seconds) and $5.00 (500 cents)
    cap_setup = {
        "monthly_minutes_cap": 10,
        "monthly_cost_cents_cap": 500,
        "is_hard_cap": True,
        "cap_action": "flag_exceeded"
    }
    client.put(f"/api/v1/accounts/{account_id}/cap", json=cap_setup, headers=auth_headers)

    # Event 1: 5 minutes ($2.50) -> Within limits
    p1 = {
        "event_id": "evt_cap_under",
        "event_type": "call.ended",
        "account_id": account_id,
        "call_id": "call_under_01",
        "timestamp": now_str,
        "duration_seconds": 300,
        "cost_cents": 250,
        "destination_country": "US"
    }
    r1_bytes = json.dumps(p1).encode("utf-8")
    r1 = client.post("/webhooks/calls", content=r1_bytes, headers={"Content-Type": "application/json", "X-Signature": make_signature(r1_bytes)})
    assert r1.status_code == 200
    assert r1.json()["cap_status"] == "ok"

    # Event 2: 8 minutes ($4.00) -> Total 13 minutes, $6.50 -> Exceeds 10m cap!
    p2 = {
        "event_id": "evt_cap_over",
        "event_type": "call.ended",
        "account_id": account_id,
        "call_id": "call_over_02",
        "timestamp": now_str,
        "duration_seconds": 480,
        "cost_cents": 400,
        "destination_country": "US"
    }
    r2_bytes = json.dumps(p2).encode("utf-8")
    r2 = client.post("/webhooks/calls", content=r2_bytes, headers={"Content-Type": "application/json", "X-Signature": make_signature(r2_bytes)})
    assert r2.status_code == 200
    assert r2.json()["cap_status"] == "hard_limit_exceeded"

    # Check cap status endpoint
    cap_res = client.get(f"/api/v1/accounts/{account_id}/cap", headers=auth_headers)
    assert cap_res.status_code == 200
    cap_data = cap_res.json()
    assert cap_data["cap_breached"] is True
    assert cap_data["current_month_minutes"] == 13
    assert cap_data["current_month_cost_cents"] == 650
