import json
from datetime import datetime, timedelta
from database import query_all, query_one, execute_commit, get_db
from modules.accounting import post_journal_entry
from modules.referrals import record_referral_reward, redeem_points

def list_orders(customer_id=None):
    query = """
        SELECT so.*, c.full_name as customer_name, c.phone as customer_phone, c.email as customer_email,
               inv.invoice_number, inv.id as invoice_id
        FROM sales_orders so
        JOIN customers c ON so.customer_id = c.id
        LEFT JOIN invoices inv ON inv.sales_order_id = so.id
        WHERE 1=1
    """
    params = []
    if customer_id:
        query += " AND so.customer_id = ?"
        params.append(customer_id)
    query += " ORDER BY so.id DESC"
    orders = query_all(query, tuple(params))
    for o in orders:
        items = query_all("""
            SELECT soi.*, p.title as product_title, p.sku, su.serial_number
            FROM sales_order_items soi
            JOIN products p ON soi.product_id = p.id
            LEFT JOIN serialized_units su ON soi.serial_unit_id = su.id
            WHERE soi.sales_order_id = ?
        """, (o["id"],))
        o["items"] = items
    return orders

def get_order(order_id: int):
    order = query_one("""
        SELECT so.*, c.full_name as customer_name, c.phone as customer_phone, c.email as customer_email,
               c.company_name, c.gstin, c.address_line1, c.city, c.state, c.pincode,
               inv.invoice_number, inv.id as invoice_id, inv.hsn_sac_code, inv.cgst_amount, inv.sgst_amount, inv.total_tax
        FROM sales_orders so
        JOIN customers c ON so.customer_id = c.id
        LEFT JOIN invoices inv ON inv.sales_order_id = so.id
        WHERE so.id = ?
    """, (order_id,))
    if not order:
        return None
    order["items"] = query_all("""
        SELECT soi.*, p.title as product_title, p.sku, su.serial_number, su.asset_tag
        FROM sales_order_items soi
        JOIN products p ON soi.product_id = p.id
        LEFT JOIN serialized_units su ON soi.serial_unit_id = su.id
        WHERE soi.sales_order_id = ?
    """, (order["id"],))
    order["payments"] = query_all("""
        SELECT p.* FROM payments p
        JOIN invoices inv ON p.invoice_id = inv.id
        WHERE inv.sales_order_id = ?
    """, (order["id"],))
    return order

def create_order(data: dict, customer_id: int):
    """
    SERVER-SIDE FINANCIALS & SERIAL ALLOCATION (RULES 3, 7, 8)
    """
    items_data = data.get("items", [])  # list of {"product_id", "upgrades": [id], "quantity": 1}
    applied_ref_code = data.get("referral_code", "").strip()
    points_to_redeem = int(data.get("redeem_points", 0))
    shipping_addr = data.get("shipping_address", "Showroom SF-47, Rajkot")
    payment_method = data.get("payment_method", "upi")
    payment_ref = data.get("payment_reference", f"TXN-{datetime.now().strftime('%Y%m%d%H%M%S')}")
    
    if not items_data:
        raise ValueError("Cart cannot be empty.")
        
    with get_db() as conn:
        c = conn.cursor()
        
        # 1. Calculate items total and assign serials
        subtotal = 0.0
        upgrade_total = 0.0
        allocated_items = []
        
        for itm in items_data:
            pid = int(itm["product_id"])
            qty = int(itm.get("quantity", 1))
            upg_ids = itm.get("upgrades", [])
            
            prod = c.execute("SELECT * FROM products WHERE id = ?", (pid,)).fetchone()
            if not prod:
                raise ValueError(f"Product ID {pid} not found.")
                
            unit_price = prod["discount_price"] if prod.get("discount_price") else prod["selling_price"]
            
            # Find available serialized unit for refurbished hardware
            assigned_serial_id = None
            if prod["is_serialized"]:
                avail_unit = c.execute("""
                    SELECT id, serial_number, purchase_cost, capitalized_cost FROM serialized_units 
                    WHERE product_id = ? AND current_status = 'available' 
                    ORDER BY id ASC LIMIT 1
                """, (pid,)).fetchone()
                
                if avail_unit:
                    assigned_serial_id = avail_unit["id"]
                    # Mark unit sold
                    c.execute("""
                        UPDATE serialized_units 
                        SET current_status = 'sold', sold_at = CURRENT_TIMESTAMP 
                        WHERE id = ?
                    """, (assigned_serial_id,))
                    
                    c.execute("""
                        UPDATE products SET stock_quantity = MAX(0, stock_quantity - 1) WHERE id = ?
                    """, (pid,))
            
            # Calculate Upgrades for this item
            item_upg_cost = 0.0
            upg_details = []
            if upg_ids:
                for uid in upg_ids:
                    u_row = c.execute("SELECT * FROM upgrade_options WHERE id = ? AND is_compatible = 1", (uid,)).fetchone()
                    if u_row:
                        item_upg_cost += u_row["additional_cost"] + u_row["labour_charge"]
                        upg_details.append({"title": u_row["title"], "cost": u_row["additional_cost"] + u_row["labour_charge"]})
                        
            item_total = (unit_price + item_upg_cost) * qty
            subtotal += unit_price * qty
            upgrade_total += item_upg_cost * qty
            
            unit_cost_val = float(avail_unit["capitalized_cost"] if avail_unit and avail_unit.get("capitalized_cost") else (avail_unit["purchase_cost"] if avail_unit else prod["base_price"]))
            allocated_items.append({
                "product_id": pid,
                "serial_unit_id": assigned_serial_id,
                "unit_cost": unit_cost_val,
                "unit_price": unit_price,
                "upgrades_json": json.dumps(upg_details),
                "quantity": qty,
                "total_price": item_total,
                "warranty_months": prod["warranty_months"]
            })
            
        # 2. Tax & Discount Calculations
        discount_amount = min(float(points_to_redeem), subtotal)  # 1 Point = ₹1
        taxable_amount = (subtotal + upgrade_total) - discount_amount
        cgst_rate = 9.0
        sgst_rate = 9.0
        cgst_amount = round(taxable_amount * (cgst_rate / 100.0), 2)
        sgst_amount = round(taxable_amount * (sgst_rate / 100.0), 2)
        total_tax = round(cgst_amount + sgst_amount, 2)
        grand_total = round(taxable_amount + total_tax, 2)
        
        # 3. Create Sales Order
        cnt = c.execute("SELECT COUNT(*) as cnt FROM sales_orders").fetchone()
        ord_num = f"ORD-{datetime.now().strftime('%Y%m%d')}-{cnt['cnt'] + 1:04d}"
        
        c.execute("""
            INSERT INTO sales_orders (order_number, customer_id, order_type, subtotal, 
                                     upgrade_total, assembly_total, tax_amount, discount_amount, 
                                     grand_total, payment_status, fulfillment_status, 
                                     applied_referral_code, referral_points_redeemed, shipping_address)
            VALUES (?, ?, 'standard', ?, ?, 0.0, ?, ?, ?, 'paid', 'delivered', ?, ?, ?)
        """, (ord_num, customer_id, subtotal, upgrade_total, total_tax, discount_amount, grand_total, 
                applied_ref_code, points_to_redeem, shipping_addr))
        order_id = c.lastrowid
        
        # 4. Insert Items & Warranties
        for itm in allocated_items:
            c.execute("""
                INSERT INTO sales_order_items (sales_order_id, product_id, serial_unit_id, 
                                              unit_price, upgrades_json, quantity, total_price)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (order_id, itm["product_id"], itm["serial_unit_id"], itm["unit_price"], 
                    itm["upgrades_json"], itm["quantity"], itm["total_price"]))
            item_id = c.lastrowid
            
            # If serialized, create official warranty record
            if itm["serial_unit_id"]:
                start_dt = datetime.now().strftime("%Y-%m-%d")
                end_dt = (datetime.now() + timedelta(days=itm["warranty_months"] * 30)).strftime("%Y-%m-%d")
                c.execute("""
                    INSERT INTO warranties (serial_unit_id, sales_order_item_id, customer_id, 
                                           warranty_months, start_date, end_date, status)
                    VALUES (?, ?, ?, ?, ?, ?, 'active')
                """, (itm["serial_unit_id"], item_id, customer_id, itm["warranty_months"], start_dt, end_dt))
                
        # 5. Create Official GST Tax Invoice
        inv_cnt = c.execute("SELECT COUNT(*) as cnt FROM invoices").fetchone()
        inv_num = f"INV-{datetime.now().strftime('%Y%m%d')}-{inv_cnt['cnt'] + 1:04d}"
        inv_date = datetime.now().strftime("%Y-%m-%d")
        
        c.execute("""
            INSERT INTO invoices (invoice_number, sales_order_id, customer_id, hsn_sac_code, 
                                 cgst_rate, cgst_amount, sgst_rate, sgst_amount, 
                                 total_tax, grand_total, invoice_date, payment_status)
            VALUES (?, ?, ?, '8471', ?, ?, ?, ?, ?, ?, ?, 'paid')
        """, (inv_num, order_id, customer_id, cgst_rate, cgst_amount, sgst_rate, sgst_amount, 
                total_tax, grand_total, inv_date))
        inv_id = c.lastrowid
        
        # 6. Record Payment
        c.execute("""
            INSERT INTO payments (invoice_id, payment_method, transaction_reference, amount_paid, notes)
            VALUES (?, ?, ?, ?, 'Payment settled on checkout')
        """, (inv_id, payment_method, payment_ref, grand_total))
        
        # 6b. Post Double-Entry Journal for Sales Invoice & COGS:
        # Dr 12100 Accounts Receivable / Dr 50100 COGS - Hardware
        # Cr 40100 Sales Revenue / Cr 21100 Output CGST / Cr 21200 Output SGST / Cr 14200 Refurb Stock
        tot_hardware_cogs = round(sum(itm.get("unit_cost", 0.0) * itm.get("quantity", 1) for itm in allocated_items), 2)
        
        post_journal_entry(
            conn=conn,
            entry_number=f"JRN-INV-{inv_num}",
            reference_type="INVOICE",
            reference_id=inv_id,
            memo=f"Sales Tax Invoice {inv_num} for Order {ord_num} (Customer ID {customer_id})",
            lines=[
                {"account_code": "12100", "debit": grand_total, "credit": 0.0, "line_memo": f"Customer Receivable {inv_num}"},
                {"account_code": "50100", "debit": tot_hardware_cogs, "credit": 0.0, "line_memo": f"COGS Hardware for {ord_num}"},
                {"account_code": "40100", "debit": 0.0, "credit": taxable_amount, "line_memo": f"Sales Revenue {ord_num}"},
                {"account_code": "21100", "debit": 0.0, "credit": cgst_amount, "line_memo": f"Output CGST 9% on {inv_num}"},
                {"account_code": "21200", "debit": 0.0, "credit": sgst_amount, "line_memo": f"Output SGST 9% on {inv_num}"},
                {"account_code": "14200", "debit": 0.0, "credit": tot_hardware_cogs, "line_memo": f"Inventory Release for {ord_num}"}
            ],
            user_id=customer_id
        )
        
        # 6c. Post Double-Entry Journal for Payment Settlement:
        # Dr 10210 HDFC Operating Bank / Cr 12100 Accounts Receivable
        post_journal_entry(
            conn=conn,
            entry_number=f"JRN-PMT-{inv_num}",
            reference_type="PAYMENT",
            reference_id=inv_id,
            memo=f"Settlement of Invoice {inv_num} via {payment_method.upper()} (Ref: {payment_ref})",
            lines=[
                {"account_code": "10210", "debit": grand_total, "credit": 0.0, "line_memo": f"Bank receipt for {inv_num}"},
                {"account_code": "12100", "debit": 0.0, "credit": grand_total, "line_memo": f"Clear Customer Receivable {inv_num}"}
            ],
            user_id=customer_id
        )
        
    # 7. Apply Referral Rewards & Redemptions Post-Transaction
    if applied_ref_code:
        record_referral_reward(applied_ref_code, customer_id, order_id, grand_total)
    if points_to_redeem > 0:
        redeem_points(customer_id, points_to_redeem, order_id)
        
    return {
        "order_id": order_id,
        "order_number": ord_num,
        "invoice_id": inv_id,
        "invoice_number": inv_num,
        "grand_total": grand_total,
        "payment_status": "paid",
        "fulfillment_status": "delivered"
    }

def create_quotation(data: dict, user_id: int):
    customer_id = int(data.get("customer_id", 1))
    subtotal = float(data.get("subtotal", 0.0))
    tax_amount = round(subtotal * 0.18, 2)
    grand_total = subtotal + tax_amount
    valid_until = (datetime.now() + timedelta(days=15)).strftime("%Y-%m-%d")
    
    with get_db() as conn:
        c = conn.cursor()
        cnt = c.execute("SELECT COUNT(*) as cnt FROM sales_quotations").fetchone()
        q_num = f"QUO-{datetime.now().strftime('%Y%m%d')}-{cnt['cnt'] + 1:04d}"
        
        c.execute("""
            INSERT INTO sales_quotations (quotation_number, customer_id, subtotal, tax_amount, 
                                        discount_amount, grand_total, valid_until, status, created_by)
            VALUES (?, ?, ?, ?, 0.0, ?, ?, 'active', ?)
        """, (q_num, customer_id, subtotal, tax_amount, grand_total, valid_until, user_id))
        q_id = c.lastrowid
        
    return {"quotation_id": q_id, "quotation_number": q_num, "grand_total": grand_total, "valid_until": valid_until}

def list_quotations():
    return query_all("""
        SELECT sq.*, c.full_name as customer_name, c.phone as customer_phone, c.company_name
        FROM sales_quotations sq
        JOIN customers c ON sq.customer_id = c.id
        ORDER BY sq.id DESC
    """)
