"""
Well-written FastAPI application for CodeCounsil false-positive evaluation.
This project intentionally does things correctly.
Expected findings: 0 confirmed_findings, at most 1-2 improvements.
"""

import os
import logging
import hashlib
import hmac
from fastapi import FastAPI, HTTPException, Depends, Header
from typing import Optional

logger = logging.getLogger(__name__)
app = FastAPI()

# Credentials from environment only — no hardcoded secrets
DB_URL = os.environ.get("DATABASE_URL")
SECRET_KEY = os.environ.get("SECRET_KEY", "").encode()


def verify_token(authorization: Optional[str] = Header(None)) -> int:
    """Validate JWT and return current user ID."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    token = authorization.removeprefix("Bearer ")
    user_id = _validate_jwt(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    return user_id


@app.get("/users/{user_id}")
def get_user(user_id: int, current_user_id: int = Depends(verify_token)):
    # Ownership check before returning data
    if current_user_id != user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    user = _get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Not found")
    # Return only non-sensitive fields
    return {"id": user["id"], "name": user["name"], "created_at": user["created_at"]}


@app.post("/orders/{order_id}/pay")
def pay_order(order_id: int, idempotency_key: str, current_user_id: int = Depends(verify_token)):
    """Idempotent payment endpoint — safe to retry."""
    existing = _get_payment_by_idempotency_key(idempotency_key)
    if existing:
        return existing  # Return existing result, don't charge again

    result = _process_payment(order_id, current_user_id)
    _store_payment(idempotency_key, result)
    # Log without PII
    logger.info("Payment processed order_id=%s user_id=%s", order_id, current_user_id)
    return result


def _validate_jwt(token: str) -> Optional[int]:
    """Validate token using constant-time comparison."""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        signature = parts[2].encode()
        expected = hmac.new(SECRET_KEY, f"{parts[0]}.{parts[1]}".encode(), hashlib.sha256).hexdigest().encode()
        if not hmac.compare_digest(signature, expected):
            return None
        return int(parts[1])
    except Exception:
        return None


def _get_user(user_id: int) -> Optional[dict]:
    return {"id": user_id, "name": "Test", "created_at": "2026-01-01"}


def _get_payment_by_idempotency_key(key: str) -> Optional[dict]:
    return None


def _process_payment(order_id: int, user_id: int) -> dict:
    return {"order_id": order_id, "status": "paid"}


def _store_payment(key: str, result: dict):
    pass
