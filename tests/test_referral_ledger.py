import sys
import os
sys.path.insert(0, os.path.abspath("backend"))
import database as db
from modules.referrals import record_referral_reward, redeem_points, get_or_create_referral_code

def run_tests():
    print(">>> Running Immutable Referral Points Ledger Tests (Rule 7)...")
    
    # Customer 1 (Rajesh Patel) has referral code PCW-RAJ-1001
    info = get_or_create_referral_code(1)
    init_bal = info["available_points"]
    
    # Customer 3 makes an eligible purchase with Customer 1 code
    res = record_referral_reward("PCW-RAJ-1001", buyer_customer_id=3, order_id=999, order_total=25000.0)
    assert res["status"] == "rewarded"
    assert res["points_awarded"] == 500
    assert res["new_balance"] == init_bal + 500
    print(f"  [PASS] Reward recorded to ledger. New balance: {res['new_balance']}")
    
    # Customer 1 redeems 200 points
    red_res = redeem_points(customer_id=1, points=200, order_id=1000)
    assert red_res["remaining_balance"] == init_bal + 300
    print(f"  [PASS] Points redeemed from ledger. New balance: {red_res['remaining_balance']}")
    
    # Attempt to over-redeem
    try:
        redeem_points(customer_id=1, points=99999, order_id=1001)
        assert False, "System allowed over-redemption of points!"
    except ValueError as e:
        print(f"  [PASS] Over-redemption blocked by ledger: {e}")
        
    print("ALL REFERRAL LEDGER TESTS PASSED SUCCESSFULLY!\n")

if __name__ == "__main__":
    run_tests()
