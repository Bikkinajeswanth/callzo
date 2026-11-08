"""
Callzo Telephony Webhook Simulator and Scenario Runner
Used to simulate real-world VoIP telephony webhook streams against the metering service.
"""

import sys
import os
import json
import time
import uuid
import hmac
import hashlib
from datetime import datetime, timezone, timedelta
import httpx

WEBHOOK_URL = os.getenv("WEBHOOK_URL", "http://localhost:8000/webhooks/calls")
SECRET = os.getenv("WEBHOOK_SECRET", "callzo_test_secret_change_me")


def sign(payload_bytes: bytes, secret: str = SECRET) -> str:
    return hmac.new(secret.encode("utf-8"), payload_bytes, hashlib.sha256).hexdigest()


def send_event(payload: dict, custom_sig: str | None = None, mutate_body: bool = False) -> httpx.Response:
    body_str = json.dumps(payload)
    body_bytes = body_str.encode("utf-8")

    if custom_sig is not None:
        sig = custom_sig
    else:
        sig = sign(body_bytes)

    if mutate_body:
        body_bytes = body_bytes + b"tampered"

    headers = {
        "Content-Type": "application/json",
        "X-Signature": sig
    }

    try:
        response = httpx.post(WEBHOOK_URL, content=body_bytes, headers=headers, timeout=10.0)
        return response
    except Exception as e:
        print(f"Connection error to {WEBHOOK_URL}: {e}")
        return None


def run_scenario_1_normal():
    print("\n--- Running Scenario 1: Normal Call Lifecycle ---")
    account_id = "acc_corp_01"
    call_id = f"call_{uuid.uuid4().hex[:8]}"

    # 1. Started
    started_payload = {
        "event_id": f"evt_{uuid.uuid4().hex}",
        "event_type": "call.started",
        "account_id": account_id,
        "call_id": call_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "duration_seconds": 0,
        "cost_cents": 0,
        "destination_country": "US"
    }
    r1 = send_event(started_payload)
    print(f"  call.started: HTTP {r1.status_code if r1 else 'ERR'} -> {r1.text if r1 else ''}")

    # 2. Ended
    ended_payload = {
        "event_id": f"evt_{uuid.uuid4().hex}",
        "event_type": "call.ended",
        "account_id": account_id,
        "call_id": call_id,
        "timestamp": (datetime.now(timezone.utc) + timedelta(seconds=120)).isoformat(),
        "duration_seconds": 120,
        "cost_cents": 480,  # $4.80
        "destination_country": "US"
    }
    r2 = send_event(ended_payload)
    print(f"  call.ended:   HTTP {r2.status_code if r2 else 'ERR'} -> {r2.text if r2 else ''}")


def run_scenario_2_duplicates():
    print("\n--- Running Scenario 2: Deliberate Duplicate Events ---")
    account_id = "acc_corp_01"
    call_id = f"call_{uuid.uuid4().hex[:8]}"
    dup_event_id = f"evt_dup_{uuid.uuid4().hex[:8]}"

    payload = {
        "event_id": dup_event_id,
        "event_type": "call.started",
        "account_id": account_id,
        "call_id": call_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "duration_seconds": 0,
        "cost_cents": 0,
        "destination_country": "GB"
    }

    r1 = send_event(payload)
    print(f"  Initial event delivery:    HTTP {r1.status_code if r1 else 'ERR'} -> {r1.text if r1 else ''}")

    r2 = send_event(payload)
    print(f"  Duplicate event delivery:  HTTP {r2.status_code if r2 else 'ERR'} -> {r2.text if r2 else ''}")


def run_scenario_3_out_of_order():
    print("\n--- Running Scenario 3: Out-of-Order Delivery (Ended before Started) ---")
    account_id = "acc_corp_02"
    call_id = f"call_ooo_{uuid.uuid4().hex[:8]}"
    t_start = datetime.now(timezone.utc)
    t_end = t_start + timedelta(seconds=240)

    # Ended event sent FIRST
    ended_payload = {
        "event_id": f"evt_{uuid.uuid4().hex}",
        "event_type": "call.ended",
        "account_id": account_id,
        "call_id": call_id,
        "timestamp": t_end.isoformat(),
        "duration_seconds": 240,
        "cost_cents": 960,
        "destination_country": "IN"
    }
    r1 = send_event(ended_payload)
    print(f"  Step 1 (call.ended first):   HTTP {r1.status_code if r1 else 'ERR'} -> {r1.text if r1 else ''}")

    # Started event sent SECOND
    started_payload = {
        "event_id": f"evt_{uuid.uuid4().hex}",
        "event_type": "call.started",
        "account_id": account_id,
        "call_id": call_id,
        "timestamp": t_start.isoformat(),
        "duration_seconds": 0,
        "cost_cents": 0,
        "destination_country": "IN"
    }
    r2 = send_event(started_payload)
    print(f"  Step 2 (call.started late):  HTTP {r2.status_code if r2 else 'ERR'} -> {r2.text if r2 else ''}")


def run_scenario_4_late_events():
    print("\n--- Running Scenario 4: Late Events (~35 Days in Past) ---")
    account_id = "acc_corp_03"
    call_id = f"call_late_{uuid.uuid4().hex[:8]}"
    past_timestamp = datetime.now(timezone.utc) - timedelta(days=35)

    payload = {
        "event_id": f"evt_late_{uuid.uuid4().hex[:8]}",
        "event_type": "call.ended",
        "account_id": account_id,
        "call_id": call_id,
        "timestamp": past_timestamp.isoformat(),
        "duration_seconds": 300,
        "cost_cents": 1200,
        "destination_country": "CA"
    }
    r = send_event(payload)
    print(f"  Late event (target month: {past_timestamp.strftime('%Y-%m')}): HTTP {r.status_code if r else 'ERR'} -> {r.text if r else ''}")


def run_scenario_5_cap_breach():
    print("\n--- Running Scenario 5: Monthly Cap Breach ---")
    account_id = "acc_capped_user"
    call_id = f"call_cap_{uuid.uuid4().hex[:8]}"

    payload = {
        "event_id": f"evt_cap_{uuid.uuid4().hex[:8]}",
        "event_type": "call.ended",
        "account_id": account_id,
        "call_id": call_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "duration_seconds": 36000,  # 600 minutes
        "cost_cents": 150000,       # $1,500
        "destination_country": "US"
    }
    r = send_event(payload)
    print(f"  Massive usage event: HTTP {r.status_code if r else 'ERR'} -> {r.text if r else ''}")


def run_scenario_6_security():
    print("\n--- Running Scenario 6: Security and Signature Failures ---")
    account_id = "acc_sec_test"
    payload = {
        "event_id": f"evt_sec_{uuid.uuid4().hex[:8]}",
        "event_type": "call.started",
        "account_id": account_id,
        "call_id": "call_sec_01",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "duration_seconds": 0,
        "cost_cents": 0,
        "destination_country": "US"
    }

    # Missing signature
    headers_no_sig = {"Content-Type": "application/json"}
    r1 = httpx.post(WEBHOOK_URL, content=json.dumps(payload).encode("utf-8"), headers=headers_no_sig)
    print(f"  Missing X-Signature: HTTP {r1.status_code} (Expected 401)")

    # Invalid signature
    r2 = send_event(payload, custom_sig="invalidsignature9876543210abcdef")
    print(f"  Invalid signature:   HTTP {r2.status_code} (Expected 401)")

    # Tampered payload
    r3 = send_event(payload, mutate_body=True)
    print(f"  Tampered payload:    HTTP {r3.status_code} (Expected 401)")


def run_scenario_7_malformed():
    print("\n--- Running Scenario 7: Malformed Payloads ---")
    # Malformed JSON
    headers = {"Content-Type": "application/json", "X-Signature": sign(b"{invalid_json")}
    r1 = httpx.post(WEBHOOK_URL, content=b"{invalid_json", headers=headers)
    print(f"  Malformed JSON:      HTTP {r1.status_code} (Expected 400)")

    # Missing required fields
    incomplete = {"event_id": "incomplete_123"}
    r2 = send_event(incomplete)
    print(f"  Missing fields:      HTTP {r2.status_code} (Expected 422)")


def run_all():
    print("=" * 60)
    print(f"Callzo Telephony Simulator running against: {WEBHOOK_URL}")
    print("=" * 60)
    run_scenario_1_normal()
    run_scenario_2_duplicates()
    run_scenario_3_out_of_order()
    run_scenario_4_late_events()
    run_scenario_5_cap_breach()
    run_scenario_6_security()
    run_scenario_7_malformed()
    print("\n" + "=" * 60)
    print("Simulator Scenarios Complete.")
    print("=" * 60)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1].lower()
        if "1" in cmd or "norm" in cmd:
            run_scenario_1_normal()
        elif "2" in cmd or "dup" in cmd:
            run_scenario_2_duplicates()
        elif "3" in cmd or "order" in cmd:
            run_scenario_3_out_of_order()
        elif "4" in cmd or "late" in cmd:
            run_scenario_4_late_events()
        elif "5" in cmd or "cap" in cmd:
            run_scenario_5_cap_breach()
        elif "6" in cmd or "sec" in cmd:
            run_scenario_6_security()
        elif "7" in cmd or "mal" in cmd:
            run_scenario_7_malformed()
        else:
            run_all()
    else:
        run_all()
