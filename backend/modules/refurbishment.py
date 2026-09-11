import json
from datetime import datetime
from database import query_all, query_one, execute_commit, get_db
from modules.accounting import post_journal_entry

def list_receiving():
    records = query_all("""
        SELECT r.*, s.company_name as supplier_name, s.supplier_code,
               w.name as warehouse_name, u.full_name as created_by_name,
               (SELECT COUNT(*) FROM serialized_units su WHERE su.receiving_id = r.id) as actual_units_count
        FROM receiving_records r
        JOIN suppliers s ON r.supplier_id = s.id
        JOIN warehouses w ON r.warehouse_id = w.id
        LEFT JOIN users u ON r.created_by = u.id
        ORDER BY r.id DESC
    """)
    return records

def create_receiving(data: dict, user_id: int):
    supplier_id = int(data.get("supplier_id", 1))
    warehouse_id = int(data.get("warehouse_id", 1))
    item_type = data.get("item_type", "Laptop")
    brand_id = int(data.get("brand_id", 1))
    model_name = data.get("model_name", "Refurbished Hardware Lot").strip()
    product_id = int(data.get("product_id", 1))
    quantity = int(data.get("quantity", 1))
    unit_cost = float(data.get("unit_cost", 20000.0))
    total_cost = unit_cost * quantity
    invoice_ref = data.get("invoice_ref", f"INV-{datetime.now().strftime('%Y%m%d')}")
    condition_notes = data.get("physical_condition_notes", "Clean lot received from corporate lease return.")
    accessories = data.get("accessories_received", "Power adapters and cables included.")
    provided_serials = data.get("serial_numbers", [])  # Optional list of exact serial numbers
    
    with get_db() as conn:
        c = conn.cursor()
        
        # 1. Generate Receiving Number
        count_row = c.execute("SELECT COUNT(*) as cnt FROM receiving_records").fetchone()
        rcv_num = f"RCV-{datetime.now().strftime('%Y%m%d')}-{count_row['cnt'] + 1:04d}"
        
        c.execute("""
            INSERT INTO receiving_records (receiving_number, supplier_id, warehouse_id, invoice_ref, 
                                          item_type, brand_id, model_name, expected_qty, received_qty, 
                                          purchase_cost_total, physical_condition_notes, accessories_received, 
                                          status, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'received', ?)
        """, (rcv_num, supplier_id, warehouse_id, invoice_ref, item_type, brand_id, model_name, 
                quantity, quantity, total_cost, condition_notes, accessories, user_id))
        rcv_id = c.lastrowid
        
        # 2. Look up product selling price
        prod = c.execute("SELECT selling_price, sku FROM products WHERE id = ?", (product_id,)).fetchone()
        selling_price = prod["selling_price"] if prod else unit_cost * 1.25
        sku_prefix = prod["sku"] if prod else "PCW-HW"
        
        # 3. Create Serialized Units with status qc_pending (NEVER sellable yet)
        created_serials = []
        for i in range(quantity):
            if i < len(provided_serials) and provided_serials[i].strip():
                sn = provided_serials[i].strip().upper()
            else:
                sn = f"{sku_prefix}-{datetime.now().strftime('%y%m')}-{rcv_id:03d}{i+1:03d}"
                
            asset_tag = f"ASSET-{sn[-8:]}"
            c.execute("""
                INSERT INTO serialized_units (product_id, receiving_id, serial_number, asset_tag, 
                                             purchase_cost, selling_price, condition_grade, warehouse_id, 
                                             location_rack, current_status, notes)
                VALUES (?, ?, ?, ?, ?, ?, 'Grade A', ?, 'Intake Queue', 'qc_pending', ?)
            """, (product_id, rcv_id, sn, asset_tag, unit_cost, selling_price, warehouse_id, 
                    f"Received via {rcv_num} from supplier lot."))
            unit_id = c.lastrowid
            created_serials.append({"id": unit_id, "serial_number": sn, "status": "qc_pending"})
            
            # Log movement
            c.execute("""
                INSERT INTO inventory_movements (serial_unit_id, product_id, from_status, to_status, 
                                                from_warehouse_id, to_warehouse_id, reference_type, 
                                                reference_id, moved_by, notes)
                VALUES (?, ?, 'received', 'qc_pending', ?, ?, 'Receiving Intake', ?, ?, ?)
            """, (unit_id, product_id, warehouse_id, warehouse_id, rcv_num, user_id, 
                    f"Unit serialized and queued for Quality Check inspection."))
                    
    
        # 4. Post Double-Entry Journal for GRN Intake:
        # Dr 14100 Inventory - GRN Clearing / Cr 20100 Accounts Payable
        post_journal_entry(
            conn=conn,
            entry_number=f"JRN-GRN-{rcv_num}",
            reference_type="GRN",
            reference_id=rcv_id,
            memo=f"Goods Receipt Note {rcv_num}: {quantity}x {model_name} from Supplier ID {supplier_id}",
            lines=[
                {"account_code": "14100", "debit": total_cost, "credit": 0.0, "line_memo": f"GRN Inward Clearing {rcv_num}"},
                {"account_code": "20100", "debit": 0.0, "credit": total_cost, "line_memo": f"AP Supplier Payable for {rcv_num}"}
            ],
            user_id=user_id
        )

    return {
        "receiving_id": rcv_id,
        "receiving_number": rcv_num,
        "units_created": len(created_serials),
        "serials": created_serials
    }

def get_qc_checklist(category_id: int = 1):
    checklist = query_one("""
        SELECT * FROM qc_checklists 
        WHERE (category_id = ? OR category_id IS NULL) AND is_active = 1
        ORDER BY id ASC
    """, (category_id,))
    if not checklist:
        # Fallback to general laptop checklist
        checklist = query_one("SELECT * FROM qc_checklists WHERE id = 1")
        
    if checklist and checklist.get("items_json"):
        try:
            checklist["items"] = json.loads(checklist["items_json"])
        except:
            checklist["items"] = []
    return checklist

def list_qc_pending_units():
    units = query_all("""
        SELECT su.*, p.title as product_title, p.sku, p.product_type, p.category_id,
               c.name as category_name, b.name as brand_name,
               w.name as warehouse_name
        FROM serialized_units su
        JOIN products p ON su.product_id = p.id
        JOIN categories c ON p.category_id = c.id
        JOIN brands b ON p.brand_id = b.id
        JOIN warehouses w ON su.warehouse_id = w.id
        WHERE su.current_status IN ('qc_pending', 'qc_testing', 'retest_required')
        ORDER BY su.id ASC
    """)
    return units

def list_qc_failed_units():
    units = query_all("""
        SELECT su.*, p.title as product_title, p.sku, p.product_type,
               qi.failure_reason, qi.remediation_action, qi.inspected_at,
               u.full_name as technician_name
        FROM serialized_units su
        JOIN products p ON su.product_id = p.id
        LEFT JOIN qc_inspections qi ON qi.serial_unit_id = su.id
        LEFT JOIN users u ON qi.technician_id = u.id
        WHERE su.current_status IN ('qc_failed', 'repair_required', 'supplier_return', 'scrap', 'hold')
        ORDER BY su.id DESC
    """)
    return units

def record_qc_inspection(data: dict, technician_id: int):
    serial_unit_id = int(data.get("serial_unit_id"))
    overall_result = data.get("overall_result", "passed").strip().lower()  # passed, failed, needs_rework
    checklist_id = data.get("checklist_id", 1)
    thermal_cpu = float(data.get("thermal_cpu_c", 72.0))
    thermal_gpu = float(data.get("thermal_gpu_c", 68.0))
    battery_health = int(data.get("battery_health_pct", 95))
    failure_reason = data.get("failure_reason")
    remediation = data.get("remediation_action")
    inspector_notes = data.get("inspector_notes", "QC inspection completed.")
    checklist_items = data.get("checklist_items", {})  # dict of test_key -> {"status": "pass"/"fail", "notes": "..."}
    
    with get_db() as conn:
        c = conn.cursor()
        
        # Verify unit exists
        unit = c.execute("SELECT * FROM serialized_units WHERE id = ?", (serial_unit_id,)).fetchone()
        if not unit:
            raise ValueError(f"Serialized unit with ID {serial_unit_id} not found.")
            
        prev_status = unit["current_status"]
        
        # Determine new status based on overall result
        if overall_result == "passed":
            new_status = "qc_passed"
            passed_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            c.execute("""
                UPDATE serialized_units 
                SET current_status = ?, qc_passed_at = ?, notes = ?
                WHERE id = ?
            """, (new_status, passed_at, f"QC Passed by Tech #{technician_id}: {inspector_notes}", serial_unit_id))
        else:
            # Failed or needs rework
            new_status = data.get("failure_status", "qc_failed")
            if new_status not in ["qc_failed", "repair_required", "supplier_return", "scrap", "hold"]:
                new_status = "qc_failed"
                
            # Automatically route to quarantine warehouse (WH-QUARANTINE = ID 3)
            c.execute("""
                UPDATE serialized_units 
                SET current_status = ?, warehouse_id = 3, location_rack = 'Quarantine Bin Q-01', 
                    notes = ?
                WHERE id = ?
            """, (new_status, f"QC FAILED: {failure_reason}. Remediation: {remediation}", serial_unit_id))
            
        # Log QC Inspection
        c.execute("""
            INSERT INTO qc_inspections (serial_unit_id, technician_id, checklist_id, 
                                       thermal_cpu_c, thermal_gpu_c, battery_health_pct, 
                                       overall_result, failure_reason, remediation_action, 
                                       inspector_notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (serial_unit_id, technician_id, checklist_id, thermal_cpu, thermal_gpu, 
                battery_health, overall_result, failure_reason, remediation, inspector_notes))
        inspection_id = c.lastrowid
        
        # Log individual checklist items
        for test_key, item_val in checklist_items.items():
            if isinstance(item_val, dict):
                st = item_val.get("status", "pass")
                notes = item_val.get("notes", "")
                lbl = item_val.get("label", test_key)
            else:
                st = "pass" if item_val in [True, "pass", 1] else "fail"
                notes = ""
                lbl = test_key
                
            c.execute("""
                INSERT INTO qc_inspection_items (qc_inspection_id, test_key, test_label, status, technician_notes)
                VALUES (?, ?, ?, ?, ?)
            """, (inspection_id, test_key, lbl, st, notes))
            
        # Log Inventory Movement
        c.execute("""
            INSERT INTO inventory_movements (serial_unit_id, product_id, from_status, to_status, 
                                            from_warehouse_id, to_warehouse_id, reference_type, 
                                            reference_id, moved_by, notes)
            VALUES (?, ?, ?, ?, ?, ?, 'QC Inspection', ?, ?, ?)
        """, (serial_unit_id, unit["product_id"], prev_status, new_status, unit["warehouse_id"], 
                (3 if overall_result != "passed" else unit["warehouse_id"]), 
                f"QC-INSP-{inspection_id:04d}", technician_id, 
                f"QC Inspection result: {overall_result.upper()}. {inspector_notes}"))
                
    return {
        "inspection_id": inspection_id,
        "serial_unit_id": serial_unit_id,
        "overall_result": overall_result,
        "new_status": new_status
    }

# ==============================================================================
# NON-NEGOTIABLE CORE BUSINESS RULE:
# A refurbished product cannot enter sellable store inventory until it passes QC.
# ==============================================================================
def inward_unit_to_sellable_stock(serial_unit_id: int, warehouse_id: int, rack_bin: str, inwarded_by: int, notes: str = ""):
    with get_db() as conn:
        c = conn.cursor()
        
        unit = c.execute("""
            SELECT su.*, p.title as product_title, p.stock_quantity
            FROM serialized_units su
            JOIN products p ON su.product_id = p.id
            WHERE su.id = ?
        """, (serial_unit_id,)).fetchone()
        
        if not unit:
            raise ValueError(f"Serialized unit with ID {serial_unit_id} does not exist.")
            
        current_status = unit["current_status"]
        
        # STRICT BUSINESS RULE ENFORCEMENT:
        if current_status != "qc_passed":
            raise ValueError(
                f"QC_RULE_VIOLATION: Unit '{unit['serial_number']}' cannot enter sellable store inventory. "
                f"Current status is '{current_status}'. Only units with 'qc_passed' status can be inwarded."
            )
            
        # Unit is verified QC_PASSED -> Proceed with inwarding to available inventory
        inward_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        count_row = c.execute("SELECT COUNT(*) as cnt FROM inward_records").fetchone()
        inward_num = f"INW-{datetime.now().strftime('%Y%m%d')}-{count_row['cnt'] + 1:04d}"
        
        # 1. Update Serial Unit to AVAILABLE
        c.execute("""
            UPDATE serialized_units
            SET current_status = 'available',
                warehouse_id = ?,
                location_rack = ?,
                inwarded_at = ?,
                notes = ?
            WHERE id = ?
        """, (warehouse_id, rack_bin, inward_date, f"Inwarded to sellable inventory. {notes}", serial_unit_id))
        
        # 2. Record Inwarding
        c.execute("""
            INSERT INTO inward_records (inward_number, serial_unit_id, warehouse_id, rack_bin, inwarded_by, inward_date, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (inward_num, serial_unit_id, warehouse_id, rack_bin, inwarded_by, inward_date, notes))
        inward_id = c.lastrowid
        
        # 3. Increment sellable stock quantity on product catalog
        c.execute("""
            UPDATE products 
            SET stock_quantity = stock_quantity + 1
            WHERE id = ?
        """, (unit["product_id"],))
        
        # 4. Log Inventory Movement
        c.execute("""
            INSERT INTO inventory_movements (serial_unit_id, product_id, from_status, to_status, 
                                            from_warehouse_id, to_warehouse_id, reference_type, 
                                            reference_id, moved_by, notes)
            VALUES (?, ?, 'qc_passed', 'available', ?, ?, 'Inward Gate', ?, ?, ?)
        """, (serial_unit_id, unit["product_id"], unit["warehouse_id"], warehouse_id, 
                inward_num, inwarded_by, f"Inwarded to {rack_bin} as sellable store stock."))
                
    
        # 5. Post Double-Entry Journal for QC Passed Inwarding:
        # Dr 14200 Inventory Asset - Refurb Hardware / Cr 14100 Inventory - GRN Clearing
        unit_cost = float(unit.get("capitalized_cost") or unit.get("purchase_cost") or 0.0)
        if unit_cost > 0:
            post_journal_entry(
                conn=conn,
                entry_number=f"JRN-INW-{inward_num}",
                reference_type="QC_INWARD",
                reference_id=inward_id,
                memo=f"QC Passed Inward {inward_num}: Serial {unit['serial_number']} ({unit['product_title']})",
                lines=[
                    {"account_code": "14200", "debit": unit_cost, "credit": 0.0, "line_memo": f"Sellable Refurb Asset {unit['serial_number']}"},
                    {"account_code": "14100", "debit": 0.0, "credit": unit_cost, "line_memo": f"Clear GRN Interim for {unit['serial_number']}"}
                ],
                user_id=inwarded_by
            )

    return {
        "inward_id": inward_id,
        "inward_number": inward_num,
        "serial_unit_id": serial_unit_id,
        "serial_number": unit["serial_number"],
        "status": "available",
        "warehouse_id": warehouse_id,
        "rack_bin": rack_bin,
        "message": f"Unit {unit['serial_number']} is now AVAILABLE for sale."
    }


# ==============================================================================
# REFURBISHMENT WORK ORDERS & CLOSED-LOOP COST CAPITALIZATION
# ==============================================================================

def list_work_orders(status_filter=None):
    query = """
        SELECT wo.*, su.serial_number, su.condition_grade, su.purchase_cost,
               p.title as product_title, p.sku, u.full_name as technician_name
        FROM refurb_work_orders wo
        JOIN serialized_units su ON wo.serial_unit_id = su.id
        JOIN products p ON su.product_id = p.id
        LEFT JOIN users u ON wo.technician_id = u.id
        WHERE 1=1
    """
    params = []
    if status_filter:
        query += " AND wo.status = ?"
        params.append(status_filter)
    query += " ORDER BY wo.id DESC"
    orders = query_all(query, tuple(params))
    for o in orders:
        o["parts"] = query_all("""
            SELECT wop.*, p.title as part_title, p.sku
            FROM work_order_parts wop
            JOIN products p ON wop.component_product_id = p.id
            WHERE wop.work_order_id = ?
        """, (o["id"],))
        o["labour"] = query_all("""
            SELECT wol.*, u.full_name as tech_name
            FROM work_order_labour wol
            JOIN users u ON wol.technician_id = u.id
            WHERE wol.work_order_id = ?
        """, (o["id"],))
    return orders

def get_work_order(wo_id: int):
    wo = query_one("""
        SELECT wo.*, su.serial_number, su.condition_grade, su.purchase_cost,
               p.title as product_title, p.sku, u.full_name as technician_name
        FROM refurb_work_orders wo
        JOIN serialized_units su ON wo.serial_unit_id = su.id
        JOIN products p ON su.product_id = p.id
        LEFT JOIN users u ON wo.technician_id = u.id
        WHERE wo.id = ?
    """, (wo_id,))
    if not wo:
        return None
    wo["parts"] = query_all("""
        SELECT wop.*, p.title as part_title, p.sku
        FROM work_order_parts wop
        JOIN products p ON wop.component_product_id = p.id
        WHERE wop.work_order_id = ?
    """, (wo_id,))
    wo["labour"] = query_all("""
        SELECT wol.*, u.full_name as tech_name
        FROM work_order_labour wol
        JOIN users u ON wol.technician_id = u.id
        WHERE wol.work_order_id = ?
    """, (wo_id,))
    return wo

def create_refurb_work_order(data: dict, user_id: int):
    serial_unit_id = int(data["serial_unit_id"])
    technician_id = int(data.get("technician_id", user_id))
    notes = data.get("notes", "Diagnostic work order created.").strip()
    
    with get_db() as conn:
        c = conn.cursor()
        unit = c.execute("SELECT su.*, p.title as product_title FROM serialized_units su JOIN products p ON su.product_id = p.id WHERE su.id = ?", (serial_unit_id,)).fetchone()
        if not unit:
            raise ValueError(f"Serialized unit ID {serial_unit_id} not found.")
            
        cnt = c.execute("SELECT COUNT(*) as cnt FROM refurb_work_orders").fetchone()
        wo_num = f"WO-{datetime.now().strftime('%Y%m%d')}-{cnt['cnt'] + 1:04d}"
        
        c.execute("""
            INSERT INTO refurb_work_orders (wo_number, serial_unit_id, technician_id, status, notes)
            VALUES (?, ?, ?, 'in_progress', ?)
        """, (wo_num, serial_unit_id, technician_id, notes))
        wo_id = c.lastrowid
        
        c.execute("UPDATE serialized_units SET current_status = 'repair_required' WHERE id = ?", (serial_unit_id,))
        
        base_cost = float(unit["purchase_cost"])
        post_journal_entry(
            conn=conn,
            entry_number=f"JRN-WO-INIT-{wo_num}",
            reference_type="REFURB_WIP",
            reference_id=wo_id,
            memo=f"Transfer Serial {unit['serial_number']} to Refurb WIP for {wo_num}",
            lines=[
                {"account_code": "14300", "debit": base_cost, "credit": 0.0, "line_memo": f"Refurb WIP Base Cost for {unit['serial_number']}"},
                {"account_code": "14100", "debit": 0.0, "credit": base_cost, "line_memo": f"Clear Intake for {unit['serial_number']}"}
            ],
            user_id=user_id
        )
        
    return {"work_order_id": wo_id, "wo_number": wo_num, "status": "in_progress"}

def consume_work_order_part(wo_id: int, data: dict, user_id: int):
    component_product_id = int(data["component_product_id"])
    quantity = int(data.get("quantity", 1))
    
    with get_db() as conn:
        c = conn.cursor()
        wo = c.execute("SELECT * FROM refurb_work_orders WHERE id = ?", (wo_id,)).fetchone()
        if not wo:
            raise ValueError(f"Work order ID {wo_id} not found.")
            
        part = c.execute("SELECT * FROM products WHERE id = ?", (component_product_id,)).fetchone()
        if not part:
            raise ValueError(f"Part product ID {component_product_id} not found.")
            
        unit_cost = float(part["base_price"])
        total_cost = round(unit_cost * quantity, 2)
        
        c.execute("""
            INSERT INTO work_order_parts (work_order_id, component_product_id, quantity, unit_cost, total_cost)
            VALUES (?, ?, ?, ?, ?)
        """, (wo_id, component_product_id, quantity, unit_cost, total_cost))
        
        c.execute("UPDATE products SET stock_quantity = MAX(0, stock_quantity - ?) WHERE id = ?", (quantity, component_product_id))
        c.execute("UPDATE refurb_work_orders SET total_part_cost = total_part_cost + ? WHERE id = ?", (total_cost, wo_id))
        
        cnt = c.execute("SELECT COUNT(*) as cnt FROM journals").fetchone()
        j_num = f"JRN-WOP-{wo['wo_number']}-{cnt['cnt'] + 1:04d}"
        post_journal_entry(
            conn=conn,
            entry_number=j_num,
            reference_type="REFURB_PART",
            reference_id=wo_id,
            memo=f"Requisition {quantity}x {part['title']} for {wo['wo_number']}",
            lines=[
                {"account_code": "14300", "debit": total_cost, "credit": 0.0, "line_memo": f"Part consumed for {wo['wo_number']}"},
                {"account_code": "14400", "debit": 0.0, "credit": total_cost, "line_memo": f"Raw component reduction for {wo['wo_number']}"}
            ],
            user_id=user_id
        )
        
    return {"message": f"Part {part['title']} consumed.", "total_part_cost": total_cost}

def log_work_order_labour(wo_id: int, data: dict, user_id: int):
    technician_id = int(data.get("technician_id", user_id))
    hours_spent = float(data["hours_spent"])
    hourly_rate = float(data.get("hourly_rate", 350.0))
    notes = data.get("notes", "Diagnostic and component replacement labour.").strip()
    
    total_labour_cost = round(hours_spent * hourly_rate, 2)
    
    with get_db() as conn:
        c = conn.cursor()
        wo = c.execute("SELECT * FROM refurb_work_orders WHERE id = ?", (wo_id,)).fetchone()
        if not wo:
            raise ValueError(f"Work order ID {wo_id} not found.")
            
        c.execute("""
            INSERT INTO work_order_labour (work_order_id, technician_id, hours_spent, hourly_rate, total_labour_cost, notes)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (wo_id, technician_id, hours_spent, hourly_rate, total_labour_cost, notes))
        
        c.execute("UPDATE refurb_work_orders SET total_labour_cost = total_labour_cost + ? WHERE id = ?", (total_labour_cost, wo_id))
        
        cnt = c.execute("SELECT COUNT(*) as cnt FROM journals").fetchone()
        j_num = f"JRN-WOL-{wo['wo_number']}-{cnt['cnt'] + 1:04d}"
        post_journal_entry(
            conn=conn,
            entry_number=j_num,
            reference_type="REFURB_LABOUR",
            reference_id=wo_id,
            memo=f"Direct Labour {hours_spent}h @ ₹{hourly_rate}/h on {wo['wo_number']}",
            lines=[
                {"account_code": "14300", "debit": total_labour_cost, "credit": 0.0, "line_memo": f"Absorb Direct Labour on {wo['wo_number']}"},
                {"account_code": "50300", "debit": 0.0, "credit": total_labour_cost, "line_memo": "Direct Labour Absorbed Credit"}
            ],
            user_id=user_id
        )
        
    return {"message": f"Logged {hours_spent} hours of labour.", "total_labour_cost": total_labour_cost}

def complete_refurb_work_order(wo_id: int, user_id: int, data: dict = None):
    data = data or {}
    warehouse_id = int(data.get("warehouse_id", 1))
    rack_bin = data.get("rack_bin", "Cleanroom Shelf B-4").strip()
    notes = data.get("notes", "Refurbishment complete, 24-point QC clear.").strip()
    overhead = 300.00
    
    with get_db() as conn:
        c = conn.cursor()
        wo = c.execute("""
            SELECT wo.*, su.purchase_cost, su.product_id, su.serial_number, p.title as product_title
            FROM refurb_work_orders wo
            JOIN serialized_units su ON wo.serial_unit_id = su.id
            JOIN products p ON su.product_id = p.id
            WHERE wo.id = ?
        """, (wo_id,)).fetchone()
        if not wo:
            raise ValueError(f"Work order ID {wo_id} not found.")
            
        base_cost = float(wo["purchase_cost"])
        part_cost = float(wo["total_part_cost"])
        labour_cost = float(wo["total_labour_cost"])
        
        cnt = c.execute("SELECT COUNT(*) as cnt FROM journals").fetchone()
        j_ovh = f"JRN-OVH-{wo['wo_number']}-{cnt['cnt'] + 1:04d}"
        post_journal_entry(
            conn=conn,
            entry_number=j_ovh,
            reference_type="REFURB_OVERHEAD",
            reference_id=wo_id,
            memo=f"Standard Refurb Overhead ₹{overhead} for {wo['wo_number']}",
            lines=[
                {"account_code": "14300", "debit": overhead, "credit": 0.0, "line_memo": f"Overhead Absorbed for {wo['wo_number']}"},
                {"account_code": "60250", "debit": 0.0, "credit": overhead, "line_memo": "Overhead Recovery Offset"}
            ],
            user_id=user_id
        )
        
        total_capitalized = round(base_cost + part_cost + labour_cost + overhead, 2)
        
        cnt = c.execute("SELECT COUNT(*) as cnt FROM journals").fetchone()
        j_cap = f"JRN-CAP-{wo['wo_number']}-{cnt['cnt'] + 1:04d}"
        post_journal_entry(
            conn=conn,
            entry_number=j_cap,
            reference_type="REFURB_FINISH",
            reference_id=wo_id,
            memo=f"Capitalize Refurb Unit {wo['serial_number']}: Base ₹{base_cost} + Parts ₹{part_cost} + Labour ₹{labour_cost} + Overhead ₹{overhead} = ₹{total_capitalized}",
            lines=[
                {"account_code": "14200", "debit": total_capitalized, "credit": 0.0, "line_memo": f"Finished Goods Asset for {wo['serial_number']}"},
                {"account_code": "14300", "debit": 0.0, "credit": total_capitalized, "line_memo": f"Clear Refurb WIP for {wo['serial_number']}"}
            ],
            user_id=user_id
        )
        
        c.execute("""
            UPDATE serialized_units
            SET current_status = 'available',
                capitalized_cost = ?,
                warehouse_id = ?,
                location_rack = ?,
                inwarded_at = CURRENT_TIMESTAMP,
                notes = ?
            WHERE id = ?
        """, (total_capitalized, warehouse_id, rack_bin, f"Completed via {wo['wo_number']}. {notes}", wo["serial_unit_id"]))
        
        c.execute("UPDATE products SET stock_quantity = stock_quantity + 1 WHERE id = ?", (wo["product_id"],))
        
        c.execute("""
            UPDATE refurb_work_orders
            SET status = 'completed',
                total_overhead_cost = ?,
                total_capitalized_cost = ?,
                completed_at = CURRENT_TIMESTAMP,
                notes = ?
            WHERE id = ?
        """, (overhead, total_capitalized, notes, wo_id))
        
        c.execute("""
            INSERT INTO inventory_movements (serial_unit_id, product_id, from_status, to_status,
                                            from_warehouse_id, to_warehouse_id, reference_type,
                                            reference_id, moved_by, notes)
            VALUES (?, ?, 'repair_required', 'available', ?, ?, 'Refurb Complete', ?, ?, ?)
        """, (wo["serial_unit_id"], wo["product_id"], warehouse_id, warehouse_id,
                wo["wo_number"], user_id, f"Refurb complete. Capitalized cost ₹{total_capitalized}."))
                
    return {
        "work_order_id": wo_id,
        "status": "completed",
        "total_capitalized_cost": total_capitalized,
        "serial_number": wo["serial_number"],
        "message": f"Work order {wo['wo_number']} completed. Capitalized cost ₹{total_capitalized:.2f}. Unit is sellable."
    }
