"""
Payment processing — KD-004: Non-idempotent retry endpoint.
"""

import uuid

# In-memory store (would be DB in real app)
_processed_orders = {}


def process_payment(order_id: int, amount: float) -> dict:
    """
    KD-004: This function has NO idempotency check.
    If called twice with the same order_id (e.g., on retry after network timeout),
    the customer is charged twice.
    """
    transaction_id = str(uuid.uuid4())
    # Missing: if order_id in _processed_orders: return _processed_orders[order_id]
    result = _charge_card(amount)
    _processed_orders[order_id] = {"transaction_id": transaction_id, "amount": amount}
    return {"success": True, "transaction_id": transaction_id, "amount": amount}


def _charge_card(amount: float) -> dict:
    """Simulate payment gateway call."""
    return {"charged": amount, "gateway": "stripe"}
