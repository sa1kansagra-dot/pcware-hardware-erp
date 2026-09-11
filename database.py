import sqlite3
import os
import json
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

DB_PATH = os.path.join(os.path.dirname(__file__), 'hardware_erp.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()

    # Drop existing tables to ensure clean schema initialization
    tables = [
        'audit_logs', 'referral_ledger', 'referral_users', 'assembly_qc', 'assembly_orders',
        'repair_tickets', 'order_items', 'orders', 'hardware_specs', 'inwards', 'qc_inspections',
        'serialized_units', 'qc_checklists', 'receiving_records', 'suppliers', 'products',
        'categories', 'roles', 'users'
    ]
    for table in tables:
        cursor.execute(f"DROP TABLE IF EXISTS {table}")

    # 1. Users & Roles
    cursor.execute('''
    CREATE TABLE users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'staff',
        full_name TEXT NOT NULL,
        phone TEXT,
        status TEXT NOT NULL DEFAULT 'active',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # 2. Suppliers
    cursor.execute('''
    CREATE TABLE suppliers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_name TEXT NOT NULL,
        contact_person TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        phone TEXT NOT NULL,
        address TEXT,
        status TEXT DEFAULT 'active',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # 3. Refurbishment Receiving Records (Step 1 Intake)
    cursor.execute('''
    CREATE TABLE receiving_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        receiving_number TEXT UNIQUE NOT NULL,
        supplier_id INTEGER,
        purchase_ref TEXT NOT NULL,
        product_type TEXT NOT NULL, -- laptop, desktop, server, workstation, component
        brand TEXT NOT NULL,
        model TEXT NOT NULL,
        quantity INTEGER NOT NULL DEFAULT 1,
        unit_cost REAL NOT NULL,
        physical_condition TEXT NOT NULL,
        accessories_received TEXT,
        warehouse_location TEXT DEFAULT 'Receiving Bay A',
        notes TEXT,
        status TEXT NOT NULL DEFAULT 'received', -- received, qc_in_progress, completed
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
    )
    ''')

    # 4. Serialized Units (Individual Serialized Hardware Tracking)
    cursor.execute('''
    CREATE TABLE serialized_units (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        serial_number TEXT UNIQUE NOT NULL,
        receiving_id INTEGER NOT NULL,
        product_id INTEGER,
        product_title TEXT NOT NULL,
        product_type TEXT NOT NULL,
        current_status TEXT NOT NULL DEFAULT 'received', 
        -- Statuses: received, qc_pending, qc_testing, qc_failed, repair_required, qc_passed, inwarded, available, reserved, sold, scrap, returned_to_supplier
        warehouse_location TEXT DEFAULT 'Receiving Bay A',
        bin_location TEXT DEFAULT 'BIN-01',
        cost_price REAL NOT NULL,
        selling_price REAL NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (receiving_id) REFERENCES receiving_records(id)
    )
    ''')

    # 5. Quality Control Inspections (Step 2 QC Result Engine)
    cursor.execute('''
    CREATE TABLE qc_inspections (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        serial_unit_id INTEGER NOT NULL,
        technician_id INTEGER NOT NULL,
        overall_result TEXT NOT NULL, -- qc_passed, qc_failed
        failure_reason TEXT,
        checklist_results TEXT NOT NULL, -- JSON formatted test checklist
        thermal_cpu_peak REAL,
        thermal_gpu_peak REAL,
        battery_health_percentage INTEGER,
        notes TEXT,
        completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (serial_unit_id) REFERENCES serialized_units(id),
        FOREIGN KEY (technician_id) REFERENCES users(id)
    )
    ''')

    # 6. Inward Records (Step 3 Sellable Inventory Transition)
    cursor.execute('''
    CREATE TABLE inwards (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        inward_number TEXT UNIQUE NOT NULL,
        qc_inspection_id INTEGER NOT NULL,
        serial_unit_id INTEGER NOT NULL,
        inwarded_by INTEGER NOT NULL,
        warehouse_location TEXT NOT NULL DEFAULT 'Main Warehouse',
        inward_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (qc_inspection_id) REFERENCES qc_inspections(id),
        FOREIGN KEY (serial_unit_id) REFERENCES serialized_units(id),
        FOREIGN KEY (inwarded_by) REFERENCES users(id)
    )
    ''')

    # 7. Hardware Specs & Compatibility Matrix
    cursor.execute('''
    CREATE TABLE hardware_specs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER UNIQUE NOT NULL,
        socket TEXT, -- AM5, LGA1700, AM4, LGA1200
        chipset TEXT, -- B650, Z790, X670
        ram_generation TEXT, -- DDR4, DDR5
        ram_type TEXT, -- DIMM, SODIMM
        max_ram_gb INTEGER,
        ram_slots INTEGER,
        m2_nvme_slots INTEGER,
        sata_ports INTEGER,
        form_factor TEXT, -- ATX, Micro-ATX, Mini-ITX
        tdp_wattage INTEGER,
        psu_wattage_req INTEGER,
        gpu_length_clearance_mm INTEGER,
        cooler_height_clearance_mm INTEGER,
        ecc_supported INTEGER DEFAULT 0,
        FOREIGN KEY (product_id) REFERENCES products(id)
    )
    ''')

    # 8. Storefront Categories & Products
    cursor.execute('''
    CREATE TABLE categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        slug TEXT UNIQUE NOT NULL,
        icon TEXT NOT NULL
    )
    ''')

    cursor.execute('''
    CREATE TABLE products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        category_slug TEXT NOT NULL,
        price REAL NOT NULL,
        original_price REAL,
        cost_price REAL NOT NULL,
        stock INTEGER NOT NULL DEFAULT 0,
        image_url TEXT NOT NULL,
        description TEXT NOT NULL,
        condition_grade TEXT DEFAULT 'Grade A Refurbished',
        rating REAL DEFAULT 4.9,
        reviews_count INTEGER DEFAULT 120,
        badge TEXT,
        badge_color TEXT,
        specs_json TEXT NOT NULL,
        is_available INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # 9. Assembly Orders & Custom PC QC
    cursor.execute('''
    CREATE TABLE assembly_orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        assembly_number TEXT UNIQUE NOT NULL,
        customer_id INTEGER,
        customer_name TEXT NOT NULL,
        components_json TEXT NOT NULL,
        total_watts INTEGER NOT NULL,
        assembly_charge REAL DEFAULT 2500.0,
        total_price REAL NOT NULL,
        compatibility_status TEXT NOT NULL DEFAULT 'VERIFIED_COMPATIBLE',
        status TEXT NOT NULL DEFAULT 'assembly_pending',
        -- Statuses: configuration_created, components_reserved, assembly_pending, assembly_in_progress, assembly_completed, qc_pending, qc_passed, qc_failed, ready_for_dispatch, delivered
        assigned_technician_id INTEGER,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # 10. Referral Users & Append-Only Referral Ledger
    cursor.execute('''
    CREATE TABLE referral_users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER UNIQUE NOT NULL,
        referral_code TEXT UNIQUE NOT NULL,
        referrer_id INTEGER,
        total_referrals INTEGER DEFAULT 0,
        successful_referrals INTEGER DEFAULT 0,
        points_earned INTEGER DEFAULT 0,
        points_redeemed INTEGER DEFAULT 0,
        available_points INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    ''')

    cursor.execute('''
    CREATE TABLE referral_ledger (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        referrer_id INTEGER NOT NULL,
        referred_id INTEGER,
        order_id INTEGER,
        points_change INTEGER NOT NULL, -- Positive for earned, negative for redeemed
        transaction_type TEXT NOT NULL, -- earned_referral, redeemed_checkout, admin_adjustment, expired
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (referrer_id) REFERENCES users(id)
    )
    ''')

    # 11. E-Commerce Orders & Items
    cursor.execute('''
    CREATE TABLE orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_number TEXT UNIQUE NOT NULL,
        customer_id INTEGER,
        customer_name TEXT NOT NULL,
        customer_email TEXT NOT NULL,
        shipping_address TEXT NOT NULL,
        payment_method TEXT NOT NULL,
        subtotal REAL NOT NULL,
        tax REAL DEFAULT 0.0,
        discount REAL DEFAULT 0.0,
        total_amount REAL NOT NULL,
        status TEXT NOT NULL DEFAULT 'Pending',
        referral_code_used TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    cursor.execute('''
    CREATE TABLE order_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        serial_number TEXT,
        product_title TEXT NOT NULL,
        quantity INTEGER NOT NULL,
        unit_price REAL NOT NULL,
        FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE
    )
    ''')

    # 12. Repair Tickets
    cursor.execute('''
    CREATE TABLE repair_tickets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticket_number TEXT UNIQUE NOT NULL,
        customer_name TEXT NOT NULL,
        customer_phone TEXT NOT NULL,
        device_details TEXT NOT NULL,
        issue_description TEXT NOT NULL,
        estimated_cost REAL NOT NULL,
        status TEXT NOT NULL DEFAULT 'Open',
        assigned_technician_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Seed Default Users
    admin_pw = generate_password_hash('admin123', method='pbkdf2:sha256')
    staff_pw = generate_password_hash('staff123', method='pbkdf2:sha256')
    cursor.execute('''
    INSERT INTO users (email, username, password_hash, role, full_name, phone)
    VALUES 
        ('admin@pcware.com', 'admin', ?, 'admin', 'System Administrator', '+91 98765 43210'),
        ('staff@pcware.com', 'staff', ?, 'staff', 'Operations Staff', '+91 98765 43211'),
        ('tech@pcware.com', 'tech', ?, 'technician', 'Senior QC Technician', '+91 98765 43212')
    ''', (admin_pw, staff_pw, staff_pw))

    # Seed Supplier
    cursor.execute('''
    INSERT INTO suppliers (company_name, contact_person, email, phone, address)
    VALUES ('Global IT Distributors', 'Alex Johnson', 'supply@globalit.com', '+1 555 01928', 'Austin, TX Warehouse')
    ''')
    supplier_id = cursor.lastrowid

    # Seed Refurbishment Receiving Record
    cursor.execute('''
    INSERT INTO receiving_records (receiving_number, supplier_id, purchase_ref, product_type, brand, model, quantity, unit_cost, physical_condition, accessories_received, notes, status)
    VALUES ('RCV-2026-0001', ?, 'PO-99120', 'laptop', 'ASUS', 'ROG Strix Scar 18', 3, 220000.0, 'Grade A (Minor Shelf Wear)', '330W GaN Charger', 'Intake batch verified', 'qc_in_progress')
    ''', (supplier_id,))
    rcv_id = cursor.lastrowid

    # Seed Serialized Hardware Units
    serials = [
        ('ASUS-SCAR18-001', rcv_id, 'ASUS ROG Strix Scar 18 (2025) i9-14900HX RTX 4090', 'laptop', 'qc_passed', 220000.0, 289999.0),
        ('ASUS-SCAR18-002', rcv_id, 'ASUS ROG Strix Scar 18 (2025) i9-14900HX RTX 4090', 'laptop', 'qc_pending', 220000.0, 289999.0),
        ('ASUS-SCAR18-003', rcv_id, 'ASUS ROG Strix Scar 18 (2025) i9-14900HX RTX 4090', 'laptop', 'qc_failed', 220000.0, 289999.0)
    ]
    for s_num, r_id, title, p_type, status, cost, price in serials:
        cursor.execute('''
        INSERT INTO serialized_units (serial_number, receiving_id, product_title, product_type, current_status, cost_price, selling_price)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (s_num, r_id, title, p_type, status, cost, price))

    # Seed Passed QC Inspection for Unit 1
    cursor.execute('''
    INSERT INTO qc_inspections (serial_unit_id, technician_id, overall_result, checklist_results, thermal_cpu_peak, thermal_gpu_peak, battery_health_percentage, notes)
    VALUES (1, 3, 'qc_passed', '{"Power On": "PASS", "BIOS Check": "PASS", "RAM Test": "PASS", "SSD Health": "PASS (100%)", "Thermal Stress": "PASS (79C Peak)"}', 79.0, 73.0, 98, 'Passed 4-hour stress test')
    ''')
    qc_id = cursor.lastrowid

    # Strict Inward Verification: Only Unit 1 (QC Passed) is inwarded into sellable stock!
    cursor.execute('''
    INSERT INTO inwards (inward_number, qc_inspection_id, serial_unit_id, inwarded_by, warehouse_location)
    VALUES ('INW-2026-0001', ?, 1, 3, 'Austin Cleanroom Rack A-12')
    ''', (qc_id,))

    cursor.execute('''
    UPDATE serialized_units SET current_status = 'available' WHERE id = 1
    ''')

    # Seed Storefront Categories
    categories = [
        ('Laptops', 'laptops', 'fa-laptop'),
        ('CPUs & Processors', 'cpus', 'fa-microchip'),
        ('Graphics Cards', 'gpus', 'fa-gamepad'),
        ('Storage & Memory', 'storage', 'fa-hard-drive')
    ]
    for name, slug, icon in categories:
        cursor.execute('INSERT INTO categories (name, slug, icon) VALUES (?, ?, ?)', (name, slug, icon))

    # Seed Storefront Products
    specs_rog = json.dumps([
        {"label": "Processor", "value": "Intel Core i9-14900HX"},
        {"label": "Graphics", "value": "NVIDIA GeForce RTX 4090 16GB"},
        {"label": "RAM", "value": "64GB DDR5 5600MHz"},
        {"label": "Storage", "value": "2TB PCIe Gen4 NVMe SSD"}
    ])
    cursor.execute('''
    INSERT INTO products (title, category_slug, price, original_price, cost_price, stock, image_url, description, condition_grade, specs_json, is_available)
    VALUES (
        'ASUS ROG Strix Scar 18 (2025) 18.0" 2.5K 240Hz Nebula HDR, i9-14900HX, RTX 4090 16GB, 64GB DDR5, 2TB SSD',
        'laptops',
        289999.0,
        329999.0,
        220000.0,
        1, -- Exactly 1 QC Passed unit available
        'https://lh3.googleusercontent.com/aida-public/AB6AXuAUubfdaO7Ug0nf8iqN0i7hIatx52iAaDa8wW851frpm2HQZPbK1Pg3cLjZmtq-fVcM03MMFuFF0k9cSDy7QDroU3wa4kDBnSjS8YW3VcBO3A2ziA1SAk4lAR6ULo7WR8BXQBTg2oBNYzUbBDgq4OGh7YGe8scix55d8rLYL1xUDFPv9qu6EEO8S4Jeo-Nu2qPpdzIThi3WsSbT0vzOo3He93afFY_-IAc_iK6qj0bn0ebCernFrxoq2A',
        'Flagship desktop replacement laptop tested under 4-hour thermal load with Liquid Metal cooling.',
        'Grade A Refurbished',
        ?,
        1
    )
    ''', (specs_rog,))
    p_id = cursor.lastrowid

    # Seed Hardware Specs for Compatibility Matching
    cursor.execute('''
    INSERT INTO hardware_specs (product_id, socket, chipset, ram_generation, ram_type, max_ram_gb, ram_slots, m2_nvme_slots, sata_ports, form_factor, tdp_wattage, psu_wattage_req)
    VALUES (?, 'BGA1975', 'Intel HM770', 'DDR5', 'SODIMM', 64, 2, 2, 0, 'Laptop', 240, 330)
    ''', (p_id,))

    # Seed Referral User Account
    cursor.execute('''
    INSERT INTO referral_users (user_id, referral_code, total_referrals, points_earned, available_points)
    VALUES (1, 'PCWARE-ADMIN-2026', 5, 2500, 2500)
    ''')

    cursor.execute('''
    INSERT INTO referral_ledger (referrer_id, points_change, transaction_type, notes)
    VALUES (1, 2500, 'admin_adjustment', 'Initial signup referral reward points credited')
    ''')

    conn.commit()
    conn.close()

# --- STRICT BUSINESS RULE ENFORCEMENT FUNCTIONS ---

def verify_user(identifier, password):
    conn = get_db()
    identifier = identifier.strip().lower()
    user = conn.execute('SELECT * FROM users WHERE LOWER(email) = ? OR LOWER(username) = ?', (identifier, identifier)).fetchone()
    conn.close()
    if user and check_password_hash(user['password_hash'], password):
        return dict(user)
    return None

def record_receiving(data):
    conn = get_db()
    cursor = conn.cursor()
    rcv_num = f"RCV-{datetime.now().strftime('%Y%m%d')}-{cursor.execute('SELECT COUNT(*) FROM receiving_records').fetchone()[0] + 1:04d}"
    cursor.execute('''
    INSERT INTO receiving_records (receiving_number, supplier_id, purchase_ref, product_type, brand, model, quantity, unit_cost, physical_condition, accessories_received, notes, status)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'qc_in_progress')
    ''', (
        rcv_num, data.get('supplier_id'), data.get('purchase_ref', 'N/A'),
        data.get('product_type', 'laptop'), data.get('brand', 'OEM'),
        data.get('model', 'Standard Unit'), data.get('quantity', 1),
        data.get('unit_cost', 0.0), data.get('physical_condition', 'Grade A'),
        data.get('accessories_received', 'Charger'), data.get('notes', '')
    ))
    rcv_id = cursor.lastrowid

    # Create individual serialized units under receiving
    serials_created = []
    qty = int(data.get('quantity', 1))
    for i in range(qty):
        s_num = f"{data.get('brand', 'PCW').upper()}-{data.get('model', 'UNIT').replace(' ', '').upper()}-{rcv_id:03d}-{i+1:03d}"
        cursor.execute('''
        INSERT INTO serialized_units (serial_number, receiving_id, product_title, product_type, current_status, cost_price, selling_price)
        VALUES (?, ?, ?, ?, 'qc_pending', ?, ?)
        ''', (s_num, rcv_id, f"{data.get('brand')} {data.get('model')}", data.get('product_type'), data.get('unit_cost', 0.0), data.get('unit_cost', 0.0) * 1.25))
        serials_created.append(s_num)

    conn.commit()
    conn.close()
    return {'receiving_id': rcv_id, 'receiving_number': rcv_num, 'serials': serials_created}

def log_qc_inspection(serial_unit_id, technician_id, overall_result, checklist_dict, thermal_cpu=75.0, thermal_gpu=70.0, battery_health=95, notes=''):
    conn = get_db()
    cursor = conn.cursor()

    overall_result = overall_result.lower()
    if overall_result not in ['qc_passed', 'qc_failed']:
        raise ValueError("QC Result must be either 'qc_passed' or 'qc_failed'.")

    cursor.execute('''
    INSERT INTO qc_inspections (serial_unit_id, technician_id, overall_result, checklist_results, thermal_cpu_peak, thermal_gpu_peak, battery_health_percentage, notes)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (serial_unit_id, technician_id, overall_result, json.dumps(checklist_dict), thermal_cpu, thermal_gpu, battery_health, notes))
    qc_id = cursor.lastrowid

    # Update Serialized Unit status
    new_status = 'qc_passed' if overall_result == 'qc_passed' else 'qc_failed'
    cursor.execute('UPDATE serialized_units SET current_status = ? WHERE id = ?', (new_status, serial_unit_id))
    conn.commit()
    conn.close()
    return {'qc_inspection_id': qc_id, 'status': new_status}

# STRICT ENFORCEMENT RULE: Rejects inwarding if latest QC result is NOT 'qc_passed'
def inward_unit_to_sellable_stock(serial_unit_id, technician_id, warehouse_location='Austin Cleanroom'):
    conn = get_db()
    cursor = conn.cursor()

    unit = cursor.execute('SELECT * FROM serialized_units WHERE id = ?', (serial_unit_id,)).fetchone()
    if not unit:
        conn.close()
        raise ValueError(f"Serialized unit ID {serial_unit_id} not found.")

    # Fetch latest QC inspection
    latest_qc = cursor.execute('SELECT * FROM qc_inspections WHERE serial_unit_id = ? ORDER BY id DESC LIMIT 1', (serial_unit_id,)).fetchone()
    if not latest_qc:
        conn.close()
        raise ValueError("CRITICAL BUSINESS RULE VIOLATION: Unit has NO Quality Check (QC) inspection record.")

    if latest_qc['overall_result'] != 'qc_passed':
        conn.close()
        raise ValueError(f"STRICT INVENTORY RULE VIOLATION: Cannot inward unit {unit['serial_number']}. QC Status is '{latest_qc['overall_result']}'. Only 'qc_passed' units can enter sellable inventory.")

    # Log Inward Record
    inw_num = f"INW-{datetime.now().strftime('%Y%m%d')}-{cursor.execute('SELECT COUNT(*) FROM inwards').fetchone()[0] + 1:04d}"
    cursor.execute('''
    INSERT INTO inwards (inward_number, qc_inspection_id, serial_unit_id, inwarded_by, warehouse_location)
    VALUES (?, ?, ?, ?, ?)
    ''', (inw_num, latest_qc['id'], serial_unit_id, technician_id, warehouse_location))
    inward_id = cursor.lastrowid

    # Mark unit available
    cursor.execute("UPDATE serialized_units SET current_status = 'available', warehouse_location = ? WHERE id = ?", (warehouse_location, serial_unit_id))
    conn.commit()
    conn.close()
    return {'inward_id': inward_id, 'inward_number': inw_num, 'status': 'available'}

# --- HARDWARE COMPATIBILITY ENGINE ---
def validate_hardware_compatibility(cpu_socket, mb_socket, mb_ram_gen, ram_gen, mb_ram_type, ram_type, est_watts, psu_watts):
    errors = []
    warnings = []

    # Rule 1: Socket match
    if cpu_socket and mb_socket and cpu_socket.upper() != mb_socket.upper():
        errors.append(f"Incompatible Socket: CPU socket ({cpu_socket}) does not match Motherboard socket ({mb_socket}).")

    # Rule 2: RAM Generation match
    if mb_ram_gen and ram_gen and mb_ram_gen.upper() != ram_gen.upper():
        errors.append(f"Incompatible Memory: Motherboard requires {mb_ram_gen} RAM, but {ram_gen} RAM was selected.")

    # Rule 3: RAM Form Factor (DIMM vs SODIMM)
    if mb_ram_type and ram_type and mb_ram_type.upper() != ram_type.upper():
        errors.append(f"Incompatible RAM Form Factor: Motherboard takes {mb_ram_type}, selected RAM is {ram_type}.")

    # Rule 4: PSU Headroom
    recommended_psu = est_watts + 100
    if psu_watts < recommended_psu:
        warnings.append(f"Power Supply Warning: Total draw is {est_watts}W. Minimum recommended PSU is {recommended_psu}W (Selected: {psu_watts}W).")

    return {
        'is_compatible': len(errors) == 0,
        'errors': errors,
        'warnings': warnings,
        'estimated_watts': est_watts,
        'recommended_psu_watts': recommended_psu
    }

# --- REFERRAL POINTS IMMUTABLE LEDGER ---
def add_referral_points_ledger(referrer_id, points_change, transaction_type, referred_id=None, order_id=None, notes=''):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
    INSERT INTO referral_ledger (referrer_id, referred_id, order_id, points_change, transaction_type, notes)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', (referrer_id, referred_id, order_id, points_change, transaction_type, notes))

    # Update total available points
    cursor.execute('''
    INSERT INTO referral_users (user_id, referral_code, available_points)
    VALUES (?, ?, ?)
    ON CONFLICT(user_id) DO UPDATE SET 
        available_points = MAX(0, available_points + ?),
        points_earned = points_earned + CASE WHEN ? > 0 THEN ? ELSE 0 END,
        points_redeemed = points_redeemed + CASE WHEN ? < 0 THEN ABS(?) ELSE 0 END
    ''', (referrer_id, f"PCW-USER-{referrer_id}", max(0, points_change), points_change, points_change, points_change, points_change, points_change))

    conn.commit()
    conn.close()
    return True
