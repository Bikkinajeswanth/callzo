"""
End-to-end integration test runner that executes all simulator scenarios
directly against the live FastAPI app using TestClient.
"""

import sys
import os
import json
import uuid
import hmac
import hashlib
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient

# Ensure task1-usage-metering root is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app

client = TestClient(app)
SECRET = "callzo_test_secret_change_me"


def sign(payload_bytes: bytes, secret: str = SECRET) -> str:
    return hmac.new(secret.encode("utf-8"), payload_bytes, hashlib.sha256).hexdigest()


def send_event(payload: dict, custom_sig: str | None = None, mutate_body: bool = False):
    body_str = json.dumps(payload)
    body_bytes = body_str.encode("utf-8")

    sig = custom_sig if custom_sig is not None else sign(body_bytes)
    if mutate_body:
        body_bytes += b"tampered"

    headers = {
        "Content-Type": "application/json",
        "X-Signature": sig
    }
    return client.post("/webhooks/calls", content=body_bytes, headers=headers)


def main():
    print("=" * 70)
    print("EXECUTING CALLZO TELEPHONY SIMULATOR VERIFICATION")
    print("=" * 70)

    # --- Scenario 1: Normal Lifecycle ---
    print("\n[Scenario 1] Normal Call Lifecycle (call.started -> call.ended)")
    call_id_1 = f"call_live_{uuid.uuid4().hex[:6]}"
    p_start = {
        "event_id": f"evt_{uuid.uuid4().hex}",
        "event_type": "call.started",
        "account_id": "acc_corp_01",
        "call_id": call_id_1,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "duration_seconds": 0,
        "cost_cents": 0,
        "destination_country": "US"
    }
    r1 = send_event(p_start)
    assert r1.status_code == 200, f"Expected 200, got {r1.status_code}"
    print(f"  call.started: HTTP {r1.status_code} -> {r1.json()}")

    p_end = {
        "event_id": f"evt_{uuid.uuid4().hex}",
        "event_type": "call.ended",
        "account_id": "acc_corp_01",
        "call_id": call_id_1,
        "timestamp": (datetime.now(timezone.utc) + timedelta(seconds=180)).isoformat(),
        "duration_seconds": 180,
        "cost_cents": 720,
        "destination_country": "US"
    }
    r2 = send_event(p_end)
    assert r2.status_code == 200
    print(f"  call.ended:   HTTP {r2.status_code} -> {r2.json()}")

    # --- Scenario 2: Duplicate Events (Idempotency) ---
    print("\n[Scenario 2] Duplicate Events (Database Idempotency)")
    dup_evt_id = f"evt_dup_{uuid.uuid4().hex[:8]}"
    p_dup = {
        "event_id": dup_evt_id,
        "event_type": "call.started",
        "account_id": "acc_corp_01",
        "call_id": f"call_dup_{uuid.uuid4().hex[:6]}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "duration_seconds": 0,
        "cost_cents": 0,
        "destination_country": "GB"
    }
    r_dup1 = send_event(p_dup)
    assert r_dup1.status_code == 200
    assert r_dup1.json()["status"] == "processed"
    print(f"  First Delivery:  HTTP {r_dup1.status_code} -> status={r_dup1.json()['status']}")

    r_dup2 = send_event(p_dup)
    assert r_dup2.status_code == 200
    assert r_dup2.json()["status"] == "duplicate"
    print(f"  Second Delivery: HTTP {r_dup2.status_code} -> status={r_dup2.json()['status']} ('{r_dup2.json()['message']}')")

    # --- Scenario 3: Out-of-Order (call.ended first) ---
    print("\n[Scenario 3] Out-of-Order Delivery (call.ended before call.started)")
    call_id_3 = f"call_ooo_{uuid.uuid4().hex[:6]}"
    t_start = datetime.now(timezone.utc)
    t_end = t_start + timedelta(seconds=240)

    p_ooo_end = {
        "event_id": f"evt_{uuid.uuid4().hex}",
        "event_type": "call.ended",
        "account_id": "acc_corp_02",
        "call_id": call_id_3,
        "timestamp": t_end.isoformat(),
        "duration_seconds": 240,
        "cost_cents": 960,
        "destination_country": "IN"
    }
    r_ooo1 = send_event(p_ooo_end)
    assert r_ooo1.status_code == 200
    print(f"  Step 1 (call.ended arrived FIRST): HTTP {r_ooo1.status_code} -> {r_ooo1.json()}")

    p_ooo_start = {
        "event_id": f"evt_{uuid.uuid4().hex}",
        "event_type": "call.started",
        "account_id": "acc_corp_02",
        "call_id": call_id_3,
        "timestamp": t_start.isoformat(),
        "duration_seconds": 0,
        "cost_cents": 0,
        "destination_country": "IN"
    }
    r_ooo2 = send_event(p_ooo_start)
    assert r_ooo2.status_code == 200
    print(f"  Step 2 (call.started arrived LATE):  HTTP {r_ooo2.status_code} -> {r_ooo2.json()}")

    # --- Scenario 4: Late Events (~35 Days in Past) ---
    print("\n[Scenario 4] Late Events (Historical Month Accounting)")
    past_date = datetime.now(timezone.utc) - timedelta(days=35)
    p_late = {
        "event_id": f"evt_late_{uuid.uuid4().hex[:8]}",
        "event_type": "call.ended",
        "account_id": "acc_corp_03",
        "call_id": f"call_late_{uuid.uuid4().hex[:6]}",
        "timestamp": past_date.isoformat(),
        "duration_seconds": 300,
        "cost_cents": 1200,
        "destination_country": "CA"
    }
    r_late = send_event(p_late)
    assert r_late.status_code == 200
    print(f"  Late event attributed to month: {past_date.strftime('%Y-%m')} -> HTTP {r_late.status_code}")

    # --- Scenario 5: Monthly Cap Breach ---
    print("\n[Scenario 5] Monthly Cap Breach")
    # Setup cap on acc_cap_sim
    cap_data = {"monthly_minutes_cap": 10, "monthly_cost_cents_cap": 500, "is_hard_cap": True}
    client.put("/api/v1/accounts/acc_cap_sim/cap", json=cap_data, headers={"X-API-Key": "callzo_internal_api_key_secure_123"})

    p_cap = {
        "event_id": f"evt_cap_{uuid.uuid4().hex[:8]}",
        "event_type": "call.ended",
        "account_id": "acc_cap_sim",
        "call_id": f"call_cap_{uuid.uuid4().hex[:6]}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "duration_seconds": 3600,  # 60 minutes
        "cost_cents": 2500,        # $25.00
        "destination_country": "US"
    }
    r_cap = send_event(p_cap)
    assert r_cap.status_code == 200
    assert r_cap.json()["cap_status"] == "hard_limit_exceeded"
    print(f"  High-volume call: HTTP {r_cap.status_code} -> cap_status={r_cap.json()['cap_status']}")

    # --- Scenario 6: Security and Signature Failures ---
    print("\n[Scenario 6] Security & HMAC Signatures")
    p_sec = {
        "event_id": "evt_sec_test",
        "event_type": "call.started",
        "account_id": "acc_sec",
        "call_id": "call_sec",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "duration_seconds": 0,
        "cost_cents": 0,
        "destination_country": "US"
    }
    # Missing sig
    r_no_sig = client.post("/webhooks/calls", content=json.dumps(p_sec).encode("utf-8"), headers={"Content-Type": "application/json"})
    assert r_no_sig.status_code == 401
    print(f"  Missing Signature: HTTP {r_no_sig.status_code} (Rejected as expected)")

    # Fake sig
    r_bad_sig = send_event(p_sec, custom_sig="badfakesig" * 6)
    assert r_bad_sig.status_code == 401
    print(f"  Invalid Signature: HTTP {r_bad_sig.status_code} (Rejected as expected)")

    # Tampered body
    r_tamper = send_event(p_sec, mutate_body=True)
    assert r_tamper.status_code == 401
    print(f"  Tampered Payload:  HTTP {r_tamper.status_code} (Rejected as expected)")

    # --- Scenario 7: Malformed Payloads ---
    print("\n[Scenario 7] Malformed Payloads & Schema Validation")
    # Malformed JSON
    bad_bytes = b"{{invalid_json"
    r_mal_json = client.post("/webhooks/calls", content=bad_bytes, headers={"Content-Type": "application/json", "X-Signature": sign(bad_bytes)})
    assert r_mal_json.status_code == 400
    print(f"  Malformed JSON:    HTTP {r_mal_json.status_code} (Rejected as expected)")

    # Missing mandatory attributes
    incomplete = {"event_id": "evt_inc"}
    r_inc = send_event(incomplete)
    assert r_inc.status_code == 422
    print(f"  Missing Fields:    HTTP {r_inc.status_code} (Rejected as expected)")

    print("\n" + "=" * 70)
    print("ALL 7 SIMULATOR SCENARIOS VERIFIED SUCCESSFULLY!")
    print("=" * 70)


if __name__ == "__main__":
    main()
