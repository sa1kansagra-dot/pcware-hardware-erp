import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "hardware_erp.db")
BACKEND_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "pcware_production.db")

def get_db():
    target_path = DB_PATH if os.path.exists(DB_PATH) else BACKEND_DB_PATH
    conn = sqlite3.connect(target_path)
    conn.row_factory = sqlite3.Row
    return conn

def list_inquiries(status_filter=None):
    conn = get_db()
    cursor = conn.cursor()
    if status_filter and status_filter != 'all':
        rows = cursor.execute("SELECT * FROM inquiries WHERE status = ? ORDER BY id DESC", (status_filter,)).fetchall()
    else:
        rows = cursor.execute("SELECT * FROM inquiries ORDER BY id DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def create_inquiry(data):
    customer_name = (data.get("customer_name") or "").strip()
    customer_phone = (data.get("customer_phone") or "").strip()
    product_interest = (data.get("product_interest") or "").strip()
    if not customer_name or not customer_phone or not product_interest:
        raise ValueError("Customer name, phone, and product interest are required.")

    inquiry_num = f"INQ-2026-{os.urandom(2).hex().upper()}"
    budget = float(data.get("budget", 0))
    email = data.get("customer_email", "")
    company = data.get("company_name", "")
    notes = data.get("notes", "")

    conn = get_db()
    cursor = conn.cursor()
    cols = [r[1] for r in cursor.execute("PRAGMA table_info(inquiries)").fetchall()]

    fields = ["inquiry_number", "customer_name", "customer_phone", "customer_email", "company_name", "product_interest", "budget", "notes", "status"]
    vals = [inquiry_num, customer_name, customer_phone, email, company, product_interest, budget, notes, 'new']

    if "requirement_type" in cols:
        fields.append("requirement_type")
        vals.append(product_interest or "GENERAL")

    placeholders = ", ".join(["?"] * len(fields))
    field_names = ", ".join(fields)

    cursor.execute(f"INSERT INTO inquiries ({field_names}) VALUES ({placeholders})", vals)
    inquiry_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return {
        "success": True,
        "message": f"Inquiry {inquiry_num} created successfully.",
        "inquiry_id": inquiry_id,
        "inquiry_number": inquiry_num
    }

def generate_quotation_from_inquiry(inquiry_id):
    conn = get_db()
    cursor = conn.cursor()
    inq = cursor.execute("SELECT * FROM inquiries WHERE id = ?", (inquiry_id,)).fetchone()
    if not inq:
        conn.close()
        raise ValueError(f"Inquiry ID {inquiry_id} not found.")

    quotation_num = f"QT-2026-{os.urandom(2).hex().upper()}"
    cursor.execute("UPDATE inquiries SET status = 'quoted', quotation_id = ? WHERE id = ?", (inquiry_id, inquiry_id))
    conn.commit()
    conn.close()

    return {
        "success": True,
        "message": f"Quotation {quotation_num} generated for inquiry {inq['inquiry_number']}.",
        "quotation_number": quotation_num,
        "customer_name": inq["customer_name"],
        "product_interest": inq["product_interest"],
        "amount": inq["budget"] or 25000.0
    }

def convert_inquiry_to_bill(inquiry_id, bill_data=None):
    if bill_data is None: bill_data = {}
    conn = get_db()
    cursor = conn.cursor()
    inq = cursor.execute("SELECT * FROM inquiries WHERE id = ?", (inquiry_id,)).fetchone()
    if not inq:
        conn.close()
        raise ValueError(f"Inquiry ID {inquiry_id} not found.")

    invoice_num = f"INV-2026-{os.urandom(2).hex().upper()}"
    amount = float(bill_data.get("amount") or inq["budget"] or 38000.0)

    # 1. Update Inquiry status to 'converted'
    cursor.execute("UPDATE inquiries SET status = 'converted', invoice_id = ? WHERE id = ?", (inquiry_id, inquiry_id))

    # 2. Try to deduct stock for interested product if matched
    prod_cols = [r[1] for r in cursor.execute("PRAGMA table_info(products)").fetchall()]
    name_col = "title" if "title" in prod_cols else "name"
    stock_col = "stock" if "stock" in prod_cols else "stock_quantity"

    prod = cursor.execute(f"SELECT id, {stock_col} AS stock_val FROM products WHERE LOWER({name_col}) LIKE LOWER(?) LIMIT 1",
                          (f"%{inq['product_interest']}%",)).fetchone()
    if prod and prod["stock_val"] and prod["stock_val"] > 0:
        cursor.execute(f"UPDATE products SET {stock_col} = {stock_col} - 1 WHERE id = ?", (prod["id"],))

    # 3. Schedule CRM Post-Invoice Reminders (7-day follow-up)
    import datetime
    scheduled_7d = (datetime.date.today() + datetime.timedelta(days=7)).strftime("%Y-%m-%d")
    cursor.execute("""
        INSERT INTO crm_reminders (
            invoice_id, customer_name, customer_phone, product_sold, 
            reminder_type, scheduled_date, status
        ) VALUES (?, ?, ?, ?, 'post_sale_check', ?, 'pending')
    """, (inquiry_id, inq["customer_name"], inq["customer_phone"], inq["product_interest"], scheduled_7d))

    conn.commit()
    conn.close()

    return {
        "success": True,
        "message": f"Inquiry {inq['inquiry_number']} converted to Invoice {invoice_num}! Stock deducted & CRM reminder scheduled for {scheduled_7d}.",
        "invoice_number": invoice_num,
        "amount": amount,
        "crm_reminder_date": scheduled_7d
    }

def mark_inquiry_lost(inquiry_id, loss_reason):
    reason = (loss_reason or "Customer postponed purchase").strip()
    conn = get_db()
    cursor = conn.cursor()
    inq = cursor.execute("SELECT * FROM inquiries WHERE id = ?", (inquiry_id,)).fetchone()
    if not inq:
        conn.close()
        raise ValueError(f"Inquiry ID {inquiry_id} not found.")

    cursor.execute("UPDATE inquiries SET status = 'lost', loss_reason = ? WHERE id = ?", (reason, inquiry_id))
    conn.commit()
    conn.close()

    return {
        "success": True,
        "message": f"Inquiry {inq['inquiry_number']} marked as Lost. Reason logged: {reason}",
        "inquiry_number": inq["inquiry_number"],
        "status": "lost"
    }
