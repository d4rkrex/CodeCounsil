"""
Deliberately vulnerable FastAPI application for CodeCounsil evaluation.
DO NOT use this code in production.

NOTE: This file intentionally contains security vulnerabilities for testing.
All secrets here are fake and used only for evaluation purposes.
"""

from fastapi import FastAPI, HTTPException
import logging
import psycopg2

# KD-002: Hardcoded database credentials — INTENTIONAL for evaluation
# pragma: allowlist secret
_EVAL_DB_PASS = "eval_fixture_fake_password_notreal"  # noqa: S105
DB_URL = f"postgresql://admin:{_EVAL_DB_PASS}@db.internal/appdb"  # noqa: S105

app = FastAPI()
logger = logging.getLogger(__name__)


@app.get("/users/{user_id}")
def get_user(user_id: int, current_user_id: int = 0):
    # KD-001: IDOR — no ownership check before returning user data
    # Any authenticated user can read any other user's profile
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    cur.execute("SELECT id, email, name, ssn FROM users WHERE id = %s", (user_id,))
    row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="User not found")
    return {"id": row[0], "email": row[1], "name": row[2], "ssn": row[3]}


@app.get("/profile")
def get_profile(user_id: int, request_ip: str = ""):
    # KD-003: PII logged on every request — email and user_id in application logs
    user = _get_user_from_db(user_id)
    logger.info(f"Profile accessed: user_id={user_id} email={user['email']} ip={request_ip}")
    return user


@app.post("/orders/{order_id}/retry")
def retry_order(order_id: int):
    # KD-004: Non-idempotent retry — calling this endpoint twice charges the customer twice
    # No idempotency key, no check if order is already processed
    charge_result = _charge_payment(order_id)
    if not charge_result["success"]:
        return {"status": "failed"}
    _fulfill_order(order_id)
    return {"status": "ok", "charged": charge_result["amount"]}


@app.delete("/admin/users/{user_id}")
def admin_delete_user(user_id: int, admin_token: str = ""):
    # No constant-time comparison, token checked as plain string
    if admin_token != "hardcoded_admin_token_xyz":
        raise HTTPException(status_code=403)
    _delete_user(user_id)
    return {"deleted": user_id}


def _get_user_from_db(user_id: int) -> dict:
    return {"id": user_id, "email": f"user{user_id}@example.com", "name": "Test User"}


def _charge_payment(order_id: int) -> dict:
    return {"success": True, "amount": 99.99}


def _fulfill_order(order_id: int):
    pass


def _delete_user(user_id: int):
    pass
