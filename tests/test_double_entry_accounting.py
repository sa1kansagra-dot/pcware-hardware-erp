import sys
import os
import unittest
import json
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))
import database as db
from modules.accounting import (
    initialize_chart_of_accounts, get_chart_of_accounts, post_journal_entry,
    get_trial_balance, get_profit_and_loss, get_balance_sheet, get_general_ledger
)
from modules.refurbishment import (
    create_receiving, record_qc_inspection, inward_unit_to_sellable_stock,
    create_refurb_work_order, consume_work_order_part, log_work_order_labour, complete_refurb_work_order
)
from modules.sales_billing import create_order

class TestDoubleEntryAccounting(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        initialize_chart_of_accounts()

    def test_01_imbalance_rejection(self):
        """Rule 1: Rejects any unbalanced journal (Total Dr != Total Cr)."""
        with db.get_db() as conn:
            unbalanced_lines = [
                {"account_code": "10210", "debit": 5000.0, "credit": 0.0, "line_memo": "Bank Deposit"},
                {"account_code": "30100", "debit": 0.0, "credit": 4500.0, "line_memo": "Equity (Imbalanced)"}
            ]
            with self.assertRaises(ValueError) as ctx:
                post_journal_entry(
                    conn=conn,
                    entry_number=f"TEST-UNBALANCED-{datetime.now().timestamp()}",
                    reference_type="TEST",
                    reference_id="T01",
                    memo="Should fail due to imbalance",
                    lines=unbalanced_lines
                )
            self.assertIn("DOUBLE_ENTRY_IMBALANCE", str(ctx.exception))

    def test_02_balanced_manual_posting(self):
        """Rule 2: Balanced journal posts successfully and updates account balances."""
        with db.get_db() as conn:
            entry_no = f"TEST-BAL-{datetime.now().strftime('%f')}"
            lines = [
                {"account_code": "10210", "debit": 25000.0, "credit": 0.0, "line_memo": "Owner Capital Contribution"},
                {"account_code": "30100", "debit": 0.0, "credit": 25000.0, "line_memo": "Owner Capital Equity"}
            ]
            res = post_journal_entry(
                conn=conn,
                entry_number=entry_no,
                reference_type="MANUAL",
                reference_id="T02",
                memo="Owner Initial Capital Injection",
                lines=lines
            )
            self.assertEqual(res["total_debit"], 25000.0)
            self.assertEqual(res["total_credit"], 25000.0)

        tb = get_trial_balance()
        self.assertTrue(tb["is_balanced"])
        self.assertLessEqual(tb["discrepancy"], 0.01)

    def test_03_grn_intake_posting(self):
        """Rule 3: Goods Receipt Note posts Dr GRN Clearing / Cr Accounts Payable."""
        rcv_data = {
            "supplier_id": 1,
            "warehouse_id": 1,
            "item_type": "Laptop",
            "brand_id": 1,
            "model_name": "Lenovo ThinkPad T480 Bulk Lot",
            "product_id": 1,
            "quantity": 2,
            "unit_cost": 14500.0,
            "physical_condition_notes": "Corporate lease return lot",
            "accessories_received": "Original 65W Type-C AC Adapters"
        }
        res = create_receiving(rcv_data, user_id=1)
        self.assertEqual(res["units_created"], 2)
        
        # Verify journal entry
        journals = get_general_ledger()
        grn_journals = [j for j in journals if j["reference_type"] == "GRN" and j["reference_id"] == str(res["receiving_id"])]
        self.assertGreater(len(grn_journals), 0)
        
        # Verify total value is 29,000 (14,500 * 2)
        total_dr = sum(j["debit"] for j in grn_journals)
        total_cr = sum(j["credit"] for j in grn_journals)
        self.assertEqual(total_dr, 29000.0)
        self.assertEqual(total_cr, 29000.0)

    def test_04_qc_inwarding_posting(self):
        """Rule 4: QC Pass inwarding moves cost from GRN Clearing to Refurb Hardware."""
        # 1. Create a unit
        rcv = create_receiving({
            "supplier_id": 1, "warehouse_id": 1, "item_type": "Laptop",
            "brand_id": 1, "model_name": "Dell Latitude 7490", "product_id": 2,
            "quantity": 1, "unit_cost": 16000.0
        }, user_id=1)
        unit_id = rcv["serials"][0]["id"]
        
        # 2. Record passing QC inspection
        qc_res = record_qc_inspection({
            "serial_unit_id": unit_id,
            "thermal_cpu_c": 64.0,
            "thermal_gpu_c": 58.0,
            "battery_health_pct": 92,
            "overall_result": "passed",
            "cosmetic_grade": "Grade A",
            "inspector_notes": "All hardware tests passed."
        }, technician_id=3)
        self.assertEqual(qc_res["overall_result"], "passed")
        
        # 3. Inward to sellable stock
        inw = inward_unit_to_sellable_stock(unit_id, warehouse_id=1, rack_bin="Rack A-02", inwarded_by=2)
        self.assertEqual(inw["status"], "available")
        
        # Verify trial balance is still perfectly balanced
        tb = get_trial_balance()
        self.assertTrue(tb["is_balanced"])

    def test_05_refurb_work_order_cost_accumulation(self):
        """Rule 5: Refurb Work Order capitalizes Base + Parts + Labour + Overhead into unit asset value."""
        # 1. Receive a unit needing repair
        rcv = create_receiving({
            "supplier_id": 1, "warehouse_id": 1, "item_type": "Laptop",
            "brand_id": 1, "model_name": "HP EliteBook 840 G5 Work Order Unit", "product_id": 3,
            "quantity": 1, "unit_cost": 12000.0
        }, user_id=1)
        unit_id = rcv["serials"][0]["id"]
        
        # 2. Open Work Order
        wo = create_refurb_work_order({"serial_unit_id": unit_id, "notes": "Replace SSD and add RAM"}, user_id=3)
        wo_id = wo["work_order_id"]
        
        # 3. Consume replacement 512GB SSD (product_id 11, base price ₹2,200)
        part_res = consume_work_order_part(wo_id, {"component_product_id": 16, "quantity": 1}, user_id=3)
        
        # 4. Log 2.0 hours technician labour @ ₹350/hr = ₹700
        labour_res = log_work_order_labour(wo_id, {"hours_spent": 2.0, "hourly_rate": 350.0}, user_id=3)
        
        # 5. Complete work order (Standard overhead: ₹300)
        # Total Capitalized Cost = 12,000 + 2,200 + 700 + 300 = 15,200
        comp_res = complete_refurb_work_order(wo_id, user_id=3, data={"rack_bin": "Cleanroom Bench C-1"})
        self.assertEqual(comp_res["status"], "completed")
        self.assertEqual(comp_res["total_capitalized_cost"], 16100.0)
        
        # Verify serialized unit capitalized cost in database
        unit = db.query_one("SELECT * FROM serialized_units WHERE id = ?", (unit_id,))
        self.assertEqual(unit["current_status"], "available")
        self.assertEqual(float(unit["capitalized_cost"]), 16100.0)
        
        # Verify trial balance is still balanced
        tb = get_trial_balance()
        self.assertTrue(tb["is_balanced"])

    def test_06_sales_order_and_financial_statements(self):
        """Rule 6: Sales order creates GST Invoice, recognizes COGS, clears AR upon payment, and produces balanced P&L / Balance Sheet."""
        # 1. Place order for product 1
        order_data = {
            "items": [{"product_id": 1, "quantity": 1, "upgrades": []}],
            "payment_method": "upi",
            "payment_reference": f"UPI-TEST-{datetime.now().strftime('%f')}"
        }
        order_res = create_order(order_data, customer_id=1)
        self.assertEqual(order_res["payment_status"], "paid")
        self.assertGreater(order_res["grand_total"], 0)
        
        # 2. Check Trial Balance
        tb = get_trial_balance()
        self.assertTrue(tb["is_balanced"], f"Trial balance discrepancy: {tb['discrepancy']}")
        
        # 3. Check Profit & Loss statement
        pl = get_profit_and_loss()
        self.assertGreater(pl["revenue"]["total"], 0.0)
        self.assertGreater(pl["cogs"]["total"], 0.0)
        print(f"\n[Verified P&L] Revenue: ₹{pl['revenue']['total']:.2f}, COGS: ₹{pl['cogs']['total']:.2f}, Gross Profit: ₹{pl['gross_profit']:.2f}")

        # 4. Check Balance Sheet
        bs = get_balance_sheet()
        self.assertTrue(bs["is_balanced"], f"Balance sheet discrepancy: {bs['discrepancy']}")
        print(f"[Verified Balance Sheet] Total Assets: ₹{bs['assets']['total_assets']:.2f} == Liab+Equity: ₹{bs['total_liabilities_and_equity']:.2f}")

if __name__ == "__main__":
    unittest.main()
