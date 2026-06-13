"""App with critical business logic but insufficient test coverage."""

def calculate_discount(price: float, user_tier: str, promo_code: str = None) -> float:
    """
    Complex discount logic — no tests exist for edge cases.
    KD-QA-001: No tests for promo_code combinations with tier discounts
    KD-QA-002: No tests for negative price, zero price, price > 10000
    """
    discount = 0.0
    if user_tier == "gold":
        discount += 0.10
    elif user_tier == "platinum":
        discount += 0.20
    if promo_code == "SAVE10":
        discount += 0.10
    elif promo_code == "HALFOFF":
        discount += 0.50
    return price * (1 - discount)

def process_refund(order_id: int, amount: float, reason: str) -> dict:
    """
    KD-QA-003: Refund flow has no integration test.
    Only a smoke test exists, not testing actual refund state machine.
    """
    return {"refunded": amount, "order_id": order_id}
