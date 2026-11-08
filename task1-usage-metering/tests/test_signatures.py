import json
from datetime import datetime, timezone


def test_valid_signature_accepted(client, make_signature):
    payload = {
        "event_id": "evt_sig_valid",
        "event_type": "call.started",
        "account_id": "acc_test_01",
        "call_id": "call_sig_01",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "duration_seconds": 0,
        "cost_cents": 0,
        "destination_country": "US"
    }
    raw_bytes = json.dumps(payload).encode("utf-8")
    sig = make_signature(raw_bytes)

    res = client.post("/webhooks/calls", content=raw_bytes, headers={"Content-Type": "application/json", "X-Signature": sig})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "processed"
    assert data["event_id"] == "evt_sig_valid"


def test_missing_signature_rejected(client):
    payload = {"event_id": "evt_sig_missing"}
    raw_bytes = json.dumps(payload).encode("utf-8")

    res = client.post("/webhooks/calls", content=raw_bytes, headers={"Content-Type": "application/json"})
    assert res.status_code == 401
    assert "Missing signature header" in res.json()["detail"]


def test_invalid_signature_rejected(client):
    payload = {
        "event_id": "evt_sig_invalid",
        "event_type": "call.started",
        "account_id": "acc_test_01",
        "call_id": "call_sig_02",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "duration_seconds": 0,
        "cost_cents": 0,
        "destination_country": "US"
    }
    raw_bytes = json.dumps(payload).encode("utf-8")
    fake_sig = "a" * 64

    res = client.post("/webhooks/calls", content=raw_bytes, headers={"Content-Type": "application/json", "X-Signature": fake_sig})
    assert res.status_code == 401
    assert "Invalid webhook signature" in res.json()["detail"]


def test_tampered_payload_rejected(client, make_signature):
    payload = {
        "event_id": "evt_sig_tamper",
        "event_type": "call.started",
        "account_id": "acc_test_01",
        "call_id": "call_sig_03",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "duration_seconds": 0,
        "cost_cents": 0,
        "destination_country": "US"
    }
    original_bytes = json.dumps(payload).encode("utf-8")
    sig = make_signature(original_bytes)

    # Alter byte content after signing
    tampered_bytes = original_bytes.replace(b"call_sig_03", b"call_sig_HACK")

    res = client.post("/webhooks/calls", content=tampered_bytes, headers={"Content-Type": "application/json", "X-Signature": sig})
    assert res.status_code == 401
    assert "Invalid webhook signature" in res.json()["detail"]
