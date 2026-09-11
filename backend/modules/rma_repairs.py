from datetime import datetime
from database import query_all, query_one, execute_commit, get_db

def track_repair_job(query_term: str):
    q = query_term.strip().upper()
    ticket = query_one("""
        SELECT rt.*, c.full_name as customer_name, c.phone as customer_phone,
               u.full_name as technician_name
        FROM repair_tickets rt
        JOIN customers c ON rt.customer_id = c.id
        LEFT JOIN users u ON rt.technician_id = u.id
        WHERE UPPER(rt.ticket_number) = ? OR UPPER(rt.serial_or_imei) = ? OR c.phone LIKE ?
        ORDER BY rt.id DESC LIMIT 1
    """, (q, q, f"%{q}%"))
    return ticket

def list_repair_tickets():
    return query_all("""
        SELECT rt.*, c.full_name as customer_name, c.phone as customer_phone,
               u.full_name as technician_name
        FROM repair_tickets rt
        JOIN customers c ON rt.customer_id = c.id
        LEFT JOIN users u ON rt.technician_id = u.id
        ORDER BY rt.id DESC
    """)

def create_repair_ticket(data: dict, technician_id: int = 6):
    customer_id = int(data.get("customer_id", 1))
    device_model = data.get("device_brand_model", "Laptop").strip()
    serial_or_imei = data.get("serial_or_imei", "").strip().upper()
    fault_desc = data.get("fault_description", "Fault diagnosis requested").strip()
    accessories = data.get("accessories_included", "Adapter / Power Cord")
    est_cost = float(data.get("estimated_cost", 1500.0))
    
    with get_db() as conn:
        c = conn.cursor()
        cnt = c.execute("SELECT COUNT(*) as cnt FROM repair_tickets").fetchone()
        t_num = f"JS-{datetime.now().strftime('%Y')}-{cnt['cnt'] + 1001}"
        
        c.execute("""
            INSERT INTO repair_tickets (ticket_number, customer_id, device_brand_model, 
                                       serial_or_imei, fault_description, accessories_included, 
                                       technician_id, estimated_cost, repair_status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'received')
        """, (t_num, customer_id, device_model, serial_or_imei, fault_desc, accessories, technician_id, est_cost))
        t_id = c.lastrowid
        
    return {
        "ticket_id": t_id,
        "ticket_number": t_num,
        "device": device_model,
        "status": "received",
        "message": f"Job Sheet {t_num} generated successfully."
    }

def update_repair_ticket(ticket_id: int, data: dict, technician_id: int):
    new_status = data.get("repair_status", "in_repair")
    diagnostic = data.get("diagnostic_report")
    final_cost = float(data.get("final_cost", 0.0))
    closed_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S") if new_status in ["delivered", "cancelled"] else None
    
    with get_db() as conn:
        c = conn.cursor()
        c.execute("""
            UPDATE repair_tickets
            SET repair_status = ?, diagnostic_report = COALESCE(?, diagnostic_report),
                final_cost = ?, technician_id = ?, closed_at = ?
            WHERE id = ?
        """, (new_status, diagnostic, final_cost, technician_id, closed_at, ticket_id))
        
    return {"ticket_id": ticket_id, "repair_status": new_status, "final_cost": final_cost}

def list_warranties(customer_id=None):
    query = """
        SELECT w.*, su.serial_number, p.title as product_title, p.sku,
               c.full_name as customer_name, c.phone as customer_phone
        FROM warranties w
        JOIN serialized_units su ON w.serial_unit_id = su.id
        JOIN products p ON su.product_id = p.id
        JOIN customers c ON w.customer_id = c.id
        WHERE 1=1
    """
    params = []
    if customer_id:
        query += " AND w.customer_id = ?"
        params.append(customer_id)
    query += " ORDER BY w.id DESC"
    return query_all(query, tuple(params))
