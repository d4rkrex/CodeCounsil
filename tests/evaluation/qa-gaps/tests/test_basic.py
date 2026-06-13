from app import calculate_discount

def test_gold_discount():
    # Only the happy path is tested
    assert calculate_discount(100, "gold") == 90.0

# Missing tests:
# - platinum + promo combination
# - promo code stacking limits
# - zero/negative prices
# - refund integration tests
