import json
from datetime import datetime, timezone


def test_malformed_json_rejected(client, make_signature):
    bad_bytes = b'{"event_id": "bad", broken json'
    sig = make_signature(bad_bytes)

    res = client.post("/webhooks/calls", content=bad_bytes, headers={"Content-Type": "application/json", "X-Signature": sig})
    assert res.status_code == 400
    assert "Malformed JSON" in res.json()["detail"]


def test_missing_required_fields_rejected(client, make_signature):
    payload = {
        "event_id": "evt_missing_fields",
        "event_type": "call.started"
        # Missing account_id, call_id, timestamp, destination_country
    }
    raw_bytes = json.dumps(payload).encode("utf-8")
    sig = make_signature(raw_bytes)

    res = client.post("/webhooks/calls", content=raw_bytes, headers={"Content-Type": "application/json", "X-Signature": sig})
    assert res.status_code == 422


def test_invalid_event_type_rejected(client, make_signature):
    payload = {
        "event_id": "evt_invalid_type",
        "event_type": "call.conference_joined",  # Not supported
        "account_id": "acc_test_01",
        "call_id": "call_inv_01",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "duration_seconds": 0,
        "cost_cents": 0,
        "destination_country": "US"
    }
    raw_bytes = json.dumps(payload).encode("utf-8")
    sig = make_signature(raw_bytes)

    res = client.post("/webhooks/calls", content=raw_bytes, headers={"Content-Type": "application/json", "X-Signature": sig})
    assert res.status_code == 422


def test_negative_duration_or_cost_rejected(client, make_signature):
    payload = {
        "event_id": "evt_negative_val",
        "event_type": "call.ended",
        "account_id": "acc_test_01",
        "call_id": "call_neg_01",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "duration_seconds": -50,  # Negative duration invalid
        "cost_cents": 100,
        "destination_country": "US"
    }
    raw_bytes = json.dumps(payload).encode("utf-8")
    sig = make_signature(raw_bytes)

    res = client.post("/webhooks/calls", content=raw_bytes, headers={"Content-Type": "application/json", "X-Signature": sig})
    assert res.status_code == 422
