"""
Tests for the account management endpoints:
  POST /api/v1/accounts
  GET  /api/v1/accounts
  GET  /api/v1/accounts/{id}
  PATCH /api/v1/accounts/{id}
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
# Fixtures are auto-discovered from conftest.py — no explicit import needed


def test_create_account(client, auth_headers):
    payload = {
        "id": "acct_mgmt_test",
        "name": "ACME Corp",
        "email": "admin@acme.example.com",
        "company": "ACME Corporation",
        "country": "US",
        "plan": "enterprise",
        "status": "active",
    }
    res = client.post("/api/v1/accounts", json=payload, headers=auth_headers)
    assert res.status_code == 201, res.text
    body = res.json()
    assert body["id"] == "acct_mgmt_test"
    assert body["plan"] == "enterprise"
    assert body["email"] == "admin@acme.example.com"


def test_create_account_duplicate_returns_409(client, auth_headers):
    payload = {
        "id": "acct_dup_test",
        "name": "Dupe Account",
        "email": "dupe@example.com",
        "country": "US",
        "plan": "basic",
        "status": "trial",
    }
    res1 = client.post("/api/v1/accounts", json=payload, headers=auth_headers)
    assert res1.status_code == 201

    res2 = client.post("/api/v1/accounts", json=payload, headers=auth_headers)
    assert res2.status_code == 409
    assert "already exists" in res2.json()["detail"]


def test_list_accounts(client, auth_headers):
    # Seed an account first
    client.post("/api/v1/accounts", json={
        "id": "acct_list_test",
        "name": "List Test",
        "email": "list@test.com",
        "country": "US",
        "plan": "pro",
        "status": "active",
    }, headers=auth_headers)

    res = client.get("/api/v1/accounts", headers=auth_headers)
    assert res.status_code == 200
    body = res.json()
    assert isinstance(body, list)
    ids = [a["id"] for a in body]
    assert "acct_list_test" in ids


def test_get_account_by_id(client, auth_headers):
    client.post("/api/v1/accounts", json={
        "id": "acct_get_test",
        "name": "Get Test",
        "email": "gettest@example.com",
        "country": "GB",
        "plan": "basic",
        "status": "trial",
    }, headers=auth_headers)

    res = client.get("/api/v1/accounts/acct_get_test", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["country"] == "GB"


def test_get_account_not_found(client, auth_headers):
    res = client.get("/api/v1/accounts/nonexistent_account_xyz", headers=auth_headers)
    assert res.status_code == 404


def test_update_account(client, auth_headers):
    client.post("/api/v1/accounts", json={
        "id": "acct_patch_test",
        "name": "Original Name",
        "email": "patch@test.com",
        "country": "US",
        "plan": "basic",
        "status": "active",
    }, headers=auth_headers)

    res = client.patch("/api/v1/accounts/acct_patch_test",
                       json={"status": "suspended", "plan": "pro"},
                       headers=auth_headers)
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "suspended"
    assert body["plan"] == "pro"
    assert body["name"] == "Original Name"  # Unchanged


def test_accounts_require_auth(client):
    res = client.get("/api/v1/accounts")
    assert res.status_code == 401
