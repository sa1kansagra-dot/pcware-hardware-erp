from database import query_all, query_one

def list_serialized_units(filters=None):
    filters = filters or {}
    query = """
        SELECT su.*, p.title as product_title, p.sku, p.product_type,
               c.name as category_name, b.name as brand_name,
               w.name as warehouse_name, w.code as warehouse_code,
               r.receiving_number, s.company_name as supplier_name
        FROM serialized_units su
        JOIN products p ON su.product_id = p.id
        JOIN categories c ON p.category_id = c.id
        JOIN brands b ON p.brand_id = b.id
        JOIN warehouses w ON su.warehouse_id = w.id
        LEFT JOIN receiving_records r ON su.receiving_id = r.id
        LEFT JOIN suppliers s ON r.supplier_id = s.id
        WHERE 1=1
    """
    params = []
    
    if filters.get("serial_number"):
        query += " AND UPPER(su.serial_number) LIKE ?"
        params.append(f"%{filters['serial_number'].strip().upper()}%")
    if filters.get("status"):
        query += " AND su.current_status = ?"
        params.append(filters["status"])
    if filters.get("warehouse_id"):
        query += " AND su.warehouse_id = ?"
        params.append(int(filters["warehouse_id"]))
    if filters.get("product_id"):
        query += " AND su.product_id = ?"
        params.append(int(filters["product_id"]))
    if filters.get("search"):
        q = f"%{filters['search'].strip().upper()}%"
        query += " AND (UPPER(su.serial_number) LIKE ? OR UPPER(su.asset_tag) LIKE ? OR UPPER(p.title) LIKE ?)"
        params.extend([q, q, q])
        
    query += " ORDER BY su.id DESC"
    return query_all(query, tuple(params))

def get_unit_history(serial_number: str):
    unit = query_one("""
        SELECT su.*, p.title as product_title, p.sku, p.product_type, p.condition_grade,
               c.name as category_name, b.name as brand_name,
               w.name as warehouse_name, w.code as warehouse_code,
               r.receiving_number, r.invoice_ref, r.received_at,
               s.company_name as supplier_name, s.supplier_code
        FROM serialized_units su
        JOIN products p ON su.product_id = p.id
        JOIN categories c ON p.category_id = c.id
        JOIN brands b ON p.brand_id = b.id
        JOIN warehouses w ON su.warehouse_id = w.id
        LEFT JOIN receiving_records r ON su.receiving_id = r.id
        LEFT JOIN suppliers s ON r.supplier_id = s.id
        WHERE UPPER(su.serial_number) = ?
    """, (serial_number.strip().upper(),))
    
    if not unit:
        return None
        
    # QC Inspections History
    inspections = query_all("""
        SELECT qi.*, u.full_name as technician_name, qc.name as checklist_name
        FROM qc_inspections qi
        JOIN users u ON qi.technician_id = u.id
        LEFT JOIN qc_checklists qc ON qi.checklist_id = qc.id
        WHERE qi.serial_unit_id = ?
        ORDER BY qi.id DESC
    """, (unit["id"],))
    
    # Inward Details
    inward = query_one("""
        SELECT iw.*, u.full_name as inwarded_by_name, w.name as warehouse_name
        FROM inward_records iw
        JOIN users u ON iw.inwarded_by = u.id
        JOIN warehouses w ON iw.warehouse_id = w.id
        WHERE iw.serial_unit_id = ?
    """, (unit["id"],))
    
    # Movement Logs
    movements = query_all("""
        SELECT im.*, u.full_name as moved_by_name,
               w1.name as from_warehouse_name, w2.name as to_warehouse_name
        FROM inventory_movements im
        LEFT JOIN users u ON im.moved_by = u.id
        LEFT JOIN warehouses w1 ON im.from_warehouse_id = w1.id
        LEFT JOIN warehouses w2 ON im.to_warehouse_id = w2.id
        WHERE im.serial_unit_id = ?
        ORDER BY im.id ASC
    """, (unit["id"],))
    
    # Sales and Warranty Information
    warranty = query_one("""
        SELECT w.*, c.full_name as customer_name, c.phone as customer_phone
        FROM warranties w
        JOIN customers c ON w.customer_id = c.id
        WHERE w.serial_unit_id = ?
    """, (unit["id"],))
    
    return {
        "unit": unit,
        "inspections": inspections,
        "inward": inward,
        "movements": movements,
        "warranty": warranty
    }

def list_warehouses():
    return query_all("""
        SELECT w.*, 
               (SELECT COUNT(*) FROM serialized_units su WHERE su.warehouse_id = w.id AND su.current_status = 'available') as available_units,
               (SELECT COUNT(*) FROM serialized_units su WHERE su.warehouse_id = w.id AND su.current_status IN ('qc_pending', 'qc_testing')) as qc_pending_units,
               (SELECT COUNT(*) FROM serialized_units su WHERE su.warehouse_id = w.id AND su.current_status IN ('qc_failed', 'repair_required')) as quarantine_units
        FROM warehouses w
        ORDER BY w.id ASC
    """)
