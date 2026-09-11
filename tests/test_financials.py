import sys
import os
sys.path.insert(0, os.path.abspath("backend"))
from modules.modification import calculate_configured_price

def run_tests():
    print(">>> Running Server-Side Financials & Upgrade Calculation Tests (Rule 8)...")
    
    # Dell Latitude 5420 (Base: ₹23,500 discount price)
    # Upgrade 1: 16GB RAM (+₹1,800 + ₹200 labour = ₹2,000)
    # Upgrade 3: 512GB NVMe (+₹2,200 + ₹250 labour = ₹2,450)
    # Subtotal: 23,500 + 4,450 = 27,950
    # CGST (9%): 2,515.50
    # SGST (9%): 2,515.50
    # Total Tax: 5,031.00
    # Grand Total: 32,981.00
    
    res = calculate_configured_price(base_product_id=1, selected_upgrade_ids=[1, 3])
    
    assert res["base_price"] == 23500.0, f"Expected 23500.0, got {res['base_price']}"
    assert res["subtotal"] == 27950.0, f"Expected 27950.0, got {res['subtotal']}"
    assert res["cgst_amount"] == 2515.50, f"Expected 2515.50, got {res['cgst_amount']}"
    assert res["sgst_amount"] == 2515.50, f"Expected 2515.50, got {res['sgst_amount']}"
    assert res["grand_total"] == 32981.0, f"Expected 32981.0, got {res['grand_total']}"
    
    print(f"  [PASS] Server-Side Financials Verified: Subtotal ₹{res['subtotal']}, Tax ₹{res['total_tax']}, Grand Total ₹{res['grand_total']}")
    print("ALL FINANCIAL INTEGRITY TESTS PASSED SUCCESSFULLY!\n")

if __name__ == "__main__":
    run_tests()
