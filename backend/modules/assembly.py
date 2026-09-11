import json
from datetime import datetime
from database import query_all, query_one, execute_commit, get_db
from modules.accounting import post_journal_entry
from modules.compatibility import validate_system_compatibility

def list_assembly_orders(status_filter=None):
    query = """
        SELECT ao.*, c.full_name as customer_name, c.phone as customer_phone,
               u.full_name as technician_name
        FROM assembly_orders ao
        JOIN customers c ON ao.customer_id = c.id
        LEFT JOIN users u ON ao.technician_id = u.id
        WHERE 1=1
    """
    params = []
    if status_filter:
        query += " AND ao.status = ?"
        params.append(status_filter)
    query += " ORDER BY ao.id DESC"
    orders = query_all(query, tuple(params))
    for o in orders:
        items = query_all("""
            SELECT ai.*, p.title as product_title, p.sku
            FROM assembly_items ai
            JOIN products p ON ai.product_id = p.id
            WHERE ai.assembly_order_id = ?
        """, (o["id"],))
        o["items"] = items
    return orders

def get_assembly_order(order_id: int):
    order = query_one("""
        SELECT ao.*, c.full_name as customer_name, c.phone as customer_phone, c.email as customer_email,
               u.full_name as technician_name
        FROM assembly_orders ao
        JOIN customers c ON ao.customer_id = c.id
        LEFT JOIN users u ON ao.technician_id = u.id
        WHERE ao.id = ?
    """, (order_id,))
    if not order:
        return None
    order["items"] = query_all("""
        SELECT ai.*, p.title as product_title, p.sku, p.image_url
        FROM assembly_items ai
        JOIN products p ON ai.product_id = p.id
        WHERE ai.assembly_order_id = ?
    """, (order["id"],))
    order["qc_records"] = query_all("""
        SELECT aqc.*, u.full_name as technician_name
        FROM assembly_qc_records aqc
        JOIN users u ON aqc.technician_id = u.id
        WHERE aqc.assembly_order_id = ?
        ORDER BY aqc.id DESC
    """, (order["id"],))
    return order

def create_assembly_order(data: dict, customer_id: int):
    parts = data.get("parts", {})  # cpu_id, mb_id, ram_id, storage_id, gpu_id, psu_id, cabinet_id, cooler_id
    
    # 1. SERVER-SIDE COMPATIBILITY VALIDATION (NON-NEGOTIABLE RULE 4)
    compat = validate_system_compatibility(parts)
    if not compat["is_compatible"]:
        mismatches = [m["message"] for m in compat["mismatches"]]
        raise ValueError(f"INCOMPATIBLE_BUILD: Cannot create assembly order. Errors: { ' | '.join(mismatches) }")
        
    with get_db() as conn:
        c = conn.cursor()
        
        # Calculate component costs and prices
        items_to_insert = []
        components_cost = 0.0
        components_selling = 0.0
        
        role_map = {
            "cpu_id": "CPU", "mb_id": "Motherboard", "ram_id": "RAM",
            "storage_id": "Storage", "gpu_id": "GPU", "psu_id": "PSU",
            "cabinet_id": "Cabinet", "cooler_id": "Cooler"
        }
        
        for key, role in role_map.items():
            pid = parts.get(key)
            if pid:
                p = c.execute("SELECT * FROM products WHERE id = ?", (pid,)).fetchone()
                if p:
                    components_cost += p["base_price"]
                    components_selling += p["selling_price"]
                    items_to_insert.append({
                        "product_id": p["id"],
                        "component_role": role,
                        "unit_cost": p["base_price"],
                        "unit_price": p["selling_price"]
                    })
                    
        assembly_charge = float(data.get("assembly_labour_charge", 2500.0))
        subtotal = components_selling + assembly_charge
        tax_amount = round(subtotal * 0.18, 2)  # 18% GST (9% CGST + 9% SGST)
        grand_total = subtotal + tax_amount
        total_wattage = compat["power_analysis"].get("estimated_total_watts", 350)
        
        # Order Number
        count_row = c.execute("SELECT COUNT(*) as cnt FROM assembly_orders").fetchone()
        asm_num = f"ASM-{datetime.now().strftime('%Y%m%d')}-{count_row['cnt'] + 1:04d}"
        
        c.execute("""
            INSERT INTO assembly_orders (assembly_number, customer_id, total_wattage, 
                                        components_cost, assembly_labour_charge, tax_amount, 
                                        total_price, compatibility_status, status, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'VERIFIED_COMPATIBLE', 'components_reserved', ?)
        """, (asm_num, customer_id, total_wattage, components_cost, assembly_charge, tax_amount, grand_total, 
                data.get("notes", "Custom PC build requested via website builder.")))
        asm_id = c.lastrowid
        
        for item in items_to_insert:
            c.execute("""
                INSERT INTO assembly_items (assembly_order_id, product_id, component_role, unit_cost, unit_price)
                VALUES (?, ?, ?, ?, ?)
            """, (asm_id, item["product_id"], item["component_role"], item["unit_cost"], item["unit_price"]))
            
        # Post Double-Entry Journal: Components issued to Assembly WIP
        # Dr 14500 Assembly WIP / Cr 14400 Raw Components
        if components_cost > 0:
            post_journal_entry(
                conn=conn,
                entry_number=f"JRN-ASM-WIP-{asm_num}",
                reference_type="ASSEMBLY_WIP",
                reference_id=asm_id,
                memo=f"Issue components for Custom PC Assembly {asm_num}",
                lines=[
                    {"account_code": "14500", "debit": components_cost, "credit": 0.0, "line_memo": f"Assembly WIP for {asm_num}"},
                    {"account_code": "14400", "debit": 0.0, "credit": components_cost, "line_memo": f"Components issued for {asm_num}"}
                ],
                user_id=customer_id
            )
            
    return {
        "assembly_id": asm_id,
        "assembly_number": asm_num,
        "total_wattage": total_wattage,
        "grand_total": grand_total,
        "compatibility": "VERIFIED_COMPATIBLE",
        "status": "components_reserved"
    }

def record_assembly_qc(order_id: int, qc_data: dict, technician_id: int):
    boot_test = 1 if qc_data.get("boot_test") else 0
    bios_config = 1 if qc_data.get("bios_config") else 0
    cpu_stress = 1 if qc_data.get("cpu_stress_pass") else 0
    gpu_stress = 1 if qc_data.get("gpu_stress_pass") else 0
    ram_memtest = 1 if qc_data.get("ram_memtest_pass") else 0
    storage_smart = 1 if qc_data.get("storage_smart_pass") else 0
    cooling = qc_data.get("cooling_efficiency", "Optimal")
    cable_mgmt = qc_data.get("cable_management_grade", "A")
    notes = qc_data.get("notes", "Assembly QC test completed.")
    
    # Check all critical tests
    all_passed = (boot_test and bios_config and cpu_stress and gpu_stress and ram_memtest and storage_smart)
    overall_status = "passed" if all_passed else "failed"
    
    with get_db() as conn:
        c = conn.cursor()
        
        c.execute("""
            INSERT INTO assembly_qc_records (assembly_order_id, technician_id, boot_test, bios_config, 
                                            cpu_stress_pass, gpu_stress_pass, ram_memtest_pass, 
                                            storage_smart_pass, cooling_efficiency, cable_management_grade, 
                                            overall_status, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (order_id, technician_id, boot_test, bios_config, cpu_stress, gpu_stress, ram_memtest, 
                storage_smart, cooling, cable_mgmt, overall_status, notes))
        
        if overall_status == "passed":
            final_serial = f"PCW-RIG-{datetime.now().strftime('%Y')}-{order_id:04d}"
            asm_order = c.execute("SELECT * FROM assembly_orders WHERE id = ?", (order_id,)).fetchone()
            comp_cost = float(asm_order["components_cost"])
            labour_chg = float(asm_order["assembly_labour_charge"])
            total_custom_cost = round(comp_cost + labour_chg, 2)
            
            # Post Labour Absorption: Dr 14500 Assembly WIP / Cr 50400 Assembly Labour Absorbed
            post_journal_entry(
                conn=conn,
                entry_number=f"JRN-ASM-LAB-{asm_order['assembly_number']}",
                reference_type="ASSEMBLY_LABOUR",
                reference_id=order_id,
                memo=f"Assembly Labour ₹{labour_chg} for {asm_order['assembly_number']}",
                lines=[
                    {"account_code": "14500", "debit": labour_chg, "credit": 0.0, "line_memo": f"Absorb Labour on {asm_order['assembly_number']}"},
                    {"account_code": "50400", "debit": 0.0, "credit": labour_chg, "line_memo": f"Assembly Labour Absorbed Offset"}
                ],
                user_id=technician_id
            )
            
            # Post Finished Custom PC Transfer: Dr 14250 Custom PCs / Cr 14500 Assembly WIP
            post_journal_entry(
                conn=conn,
                entry_number=f"JRN-ASM-FIN-{asm_order['assembly_number']}",
                reference_type="ASSEMBLY_FINISH",
                reference_id=order_id,
                memo=f"Finished Custom PC Asset {final_serial}: Components ₹{comp_cost} + Labour ₹{labour_chg} = ₹{total_custom_cost}",
                lines=[
                    {"account_code": "14250", "debit": total_custom_cost, "credit": 0.0, "line_memo": f"Finished Custom PC Asset {final_serial}"},
                    {"account_code": "14500", "debit": 0.0, "credit": total_custom_cost, "line_memo": f"Clear Assembly WIP for {asm_order['assembly_number']}"}
                ],
                user_id=technician_id
            )

            c.execute("""
                UPDATE assembly_orders
                SET status = 'ready', final_serial_number = ?, completed_at = CURRENT_TIMESTAMP, 
                    technician_id = ?
                WHERE id = ?
            """, (final_serial, technician_id, order_id))
        else:
            c.execute("""
                UPDATE assembly_orders
                SET status = 'qc_failed', technician_id = ?
                WHERE id = ?
            """, (technician_id, order_id))
            
    return {
        "assembly_order_id": order_id,
        "overall_status": overall_status,
        "final_serial_number": final_serial if overall_status == "passed" else None,
        "new_status": "ready" if overall_status == "passed" else "qc_failed"
    }
