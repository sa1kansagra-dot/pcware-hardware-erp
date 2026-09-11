import sys
import os
sys.path.insert(0, os.path.abspath("backend"))
import database as db
from modules.refurbishment import create_receiving, record_qc_inspection, inward_unit_to_sellable_stock

def run_tests():
    print(">>> Running QC Inward Gatekeeper Tests (Rules 1 & 2)...")
    
    # 1. Create a fresh intake receiving lot
    rec_res = create_receiving({
        "supplier_id": 1,
        "warehouse_id": 1,
        "product_id": 1,
        "quantity": 2,
        "unit_cost": 21000.0,
        "model_name": "Dell Latitude 5420 Test Batch"
    }, user_id=1)
    
    serials = rec_res["serials"]
    assert len(serials) == 2, f"Expected 2 serials, got {len(serials)}"
    unit_a_id = serials[0]["id"]
    unit_b_id = serials[1]["id"]
    
    # Verify initial status is qc_pending (NEVER sellable)
    u_a = db.query_one("SELECT * FROM serialized_units WHERE id = ?", (unit_a_id,))
    assert u_a["current_status"] == "qc_pending", f"Expected qc_pending, got {u_a['current_status']}"
    print("  [PASS] Unit initially created in qc_pending status.")
    
    # 2. ATTEMPT INWARDING BEFORE QC -> MUST FAIL (Rule 1)
    try:
        inward_unit_to_sellable_stock(unit_a_id, warehouse_id=1, rack_bin="Rack A-01", inwarded_by=2)
        assert False, "CRITICAL ERROR: System allowed inwarding of unit before passing QC!"
    except ValueError as e:
        assert "QC_RULE_VIOLATION" in str(e), f"Expected QC_RULE_VIOLATION error, got: {e}"
        print(f"  [PASS] Blocked un-inspected unit inwarding: {e}")

    # 3. SUBMIT QC FAILURE FOR UNIT B -> MUST DIVERT TO QUARANTINE & BLOCK INWARDING (Rule 2)
    record_qc_inspection({
        "serial_unit_id": unit_b_id,
        "overall_result": "failed",
        "failure_reason": "Broken LCD backlight",
        "remediation_action": "Divert to scrap/parts bin",
        "failure_status": "qc_failed"
    }, technician_id=3)
    
    u_b = db.query_one("SELECT * FROM serialized_units WHERE id = ?", (unit_b_id,))
    assert u_b["current_status"] == "qc_failed", f"Expected qc_failed, got {u_b['current_status']}"
    assert u_b["warehouse_id"] == 3, f"Expected quarantine warehouse ID 3, got {u_b['warehouse_id']}"
    print("  [PASS] Failed unit automatically sequestered to Quarantine Warehouse.")
    
    try:
        inward_unit_to_sellable_stock(unit_b_id, warehouse_id=1, rack_bin="Rack A-01", inwarded_by=2)
        assert False, "CRITICAL ERROR: System allowed inwarding of QC-failed unit!"
    except ValueError as e:
        assert "QC_RULE_VIOLATION" in str(e)
        print(f"  [PASS] Blocked QC-failed unit from sellable inventory: {e}")

    # 4. SUBMIT QC PASS FOR UNIT A -> MUST BECOME INWARDABLE
    record_qc_inspection({
        "serial_unit_id": unit_a_id,
        "overall_result": "passed",
        "thermal_cpu_c": 71.0,
        "battery_health_pct": 94,
        "inspector_notes": "Clean boot, perfect thermals."
    }, technician_id=3)
    
    u_a_passed = db.query_one("SELECT * FROM serialized_units WHERE id = ?", (unit_a_id,))
    assert u_a_passed["current_status"] == "qc_passed", f"Expected qc_passed, got {u_a_passed['current_status']}"
    
    # Now inward unit A
    prev_stock = db.query_one("SELECT stock_quantity FROM products WHERE id = 1")["stock_quantity"]
    inw_res = inward_unit_to_sellable_stock(unit_a_id, warehouse_id=1, rack_bin="Rack A-01", inwarded_by=2)
    assert inw_res["status"] == "available"
    
    new_stock = db.query_one("SELECT stock_quantity FROM products WHERE id = 1")["stock_quantity"]
    assert new_stock == prev_stock + 1, f"Expected stock {prev_stock + 1}, got {new_stock}"
    print("  [PASS] QC-passed unit successfully inwarded into sellable stock with inventory increment.")
    print("ALL QC INWARD GATEKEEPER TESTS PASSED SUCCESSFULLY!\n")

if __name__ == "__main__":
    run_tests()
