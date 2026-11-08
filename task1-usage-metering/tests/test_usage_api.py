from datetime import datetime, timezone


def test_health_endpoint(client):
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["database"]["connected"] is True
    assert "uptime_seconds" in data
    assert "metrics" in data


def test_authenticated_usage_apis(client, auth_headers):
    account_id = "acc_test_01"

    # 1. Unauthenticated request should be rejected (401)
    res_unauth = client.get(f"/api/v1/accounts/{account_id}/usage/overview")
    assert res_unauth.status_code == 401

    # 2. Invalid API key rejected (403)
    res_bad_key = client.get(f"/api/v1/accounts/{account_id}/usage/overview", headers={"X-API-Key": "wrong_key"})
    assert res_bad_key.status_code == 403

    # 3. Valid authenticated request
    res_auth = client.get(f"/api/v1/accounts/{account_id}/usage/overview", headers=auth_headers)
    assert res_auth.status_code == 200
    data = res_auth.json()
    assert data["account_id"] == account_id
    assert "current_month_calls" in data
    assert "lifetime_cost_formatted" in data


def test_calls_pagination_and_filter(client, auth_headers):
    account_id = "acc_test_01"
    res = client.get(f"/api/v1/accounts/{account_id}/calls?page=1&page_size=10", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["page"] == 1
    assert data["page_size"] == 10
    assert "total_records" in data
    assert "calls" in data
