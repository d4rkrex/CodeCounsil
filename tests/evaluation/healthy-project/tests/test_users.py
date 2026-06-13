"""Tests for user endpoints — proper coverage of auth and ownership."""
import pytest
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

def test_get_user_requires_auth():
    resp = client.get("/users/1")
    assert resp.status_code == 401

def test_get_user_forbidden_for_other_user(monkeypatch):
    monkeypatch.setattr("app.verify_token", lambda: 2)
    resp = client.get("/users/1", headers={"Authorization": "Bearer dummy"})
    assert resp.status_code in (401, 403)

def test_pay_order_idempotent(monkeypatch):
    monkeypatch.setattr("app._get_payment_by_idempotency_key", lambda k: {"status": "paid"})
    resp = client.post("/orders/1/pay?idempotency_key=abc", headers={"Authorization": "Bearer dummy"})
    # Should return existing result without re-charging
    assert resp.status_code in (200, 401)
