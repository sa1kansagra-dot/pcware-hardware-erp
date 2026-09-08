import sqlite3
import os
import json
from datetime import datetime, timedelta

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "hardware_erp.db")
SEED_JSON_PATH = os.path.join(BASE_DIR, "static", "seed_data.json")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(force_reseed=False):
    conn = get_connection()
    cursor = conn.cursor()

    if force_reseed:
        cursor.execute("DROP TABLE IF EXISTS stock_transfers")
        cursor.execute("DROP TABLE IF EXISTS warehouse_stocks")
        cursor.execute("DROP TABLE IF EXISTS warehouses")
        cursor.execute("DROP TABLE IF EXISTS branches")
        cursor.execute("DROP TABLE IF EXISTS staff_members")
        cursor.execute("DROP TABLE IF EXISTS ledger_entries")
        cursor.execute("DROP TABLE IF EXISTS parties")
        cursor.execute("DROP TABLE IF EXISTS purchase_orders")
        cursor.execute("DROP TABLE IF EXISTS quotations")
        cursor.execute("DROP TABLE IF EXISTS inquiries")
        cursor.execute("DROP TABLE IF EXISTS invoice_items")
        cursor.execute("DROP TABLE IF EXISTS invoices")
        cursor.execute("DROP TABLE IF EXISTS job_sheet_logs")
        cursor.execute("DROP TABLE IF EXISTS job_sheets")
        cursor.execute("DROP TABLE IF EXISTS serial_numbers")
        cursor.execute("DROP TABLE IF EXISTS amc_contracts")
        cursor.execute("DROP TABLE IF EXISTS orders")
        cursor.execute("DROP TABLE IF EXISTS products")
        cursor.execute("DROP TABLE IF EXISTS store_settings")

    # 1. Products Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sku TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        brand TEXT NOT NULL,
        model TEXT,
        hsn_code TEXT DEFAULT '8471',
        cost_price REAL NOT NULL,
        selling_price REAL NOT NULL,
        gst_rate REAL DEFAULT 18.0,
        stock_quantity INTEGER DEFAULT 0,
        low_stock_threshold INTEGER DEFAULT 2,
        specs TEXT,
        wattage INTEGER DEFAULT 0,
        socket TEXT,
        memory_type TEXT,
        image_url TEXT,
        created_at TEXT
    )
    """)

    # 2. Hardware Serial Numbers
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS serial_numbers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER,
        serial_number TEXT UNIQUE NOT NULL,
        supplier_name TEXT,
        purchase_date TEXT,
        warranty_months INTEGER DEFAULT 36,
        status TEXT DEFAULT 'IN_STOCK',
        customer_name TEXT,
        customer_phone TEXT,
        invoice_number TEXT,
        sold_date TEXT,
        notes TEXT,
        FOREIGN KEY(product_id) REFERENCES products(id)
    )
    """)

    # 3. Job Sheets (Service / Repair Center Management)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS job_sheets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_sheet_number TEXT UNIQUE NOT NULL,
        customer_name TEXT NOT NULL,
        customer_phone TEXT NOT NULL,
        customer_email TEXT,
        customer_address TEXT,
        device_type TEXT NOT NULL,
        device_brand TEXT NOT NULL,
        device_model TEXT NOT NULL,
        device_serial TEXT,
        accessories_received TEXT,
        physical_condition TEXT,
        reported_problem TEXT NOT NULL,
        technician_notes TEXT,
        status TEXT DEFAULT 'RECEIVED',
        service_tier TEXT DEFAULT 'PAID_SERVICE',
        service_category TEXT DEFAULT 'HARDWARE',
        estimated_cost REAL DEFAULT 0,
        final_cost REAL DEFAULT 0,
        advance_paid REAL DEFAULT 0,
        assigned_technician TEXT,
        created_at TEXT,
        updated_at TEXT,
        delivered_at TEXT
    )
    """)

    # 4. Job Sheet Timeline Logs
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS job_sheet_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_sheet_id INTEGER NOT NULL,
        status TEXT NOT NULL,
        note TEXT,
        created_at TEXT,
        FOREIGN KEY(job_sheet_id) REFERENCES job_sheets(id)
    )
    """)

    # 5. GST Invoices
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS invoices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_number TEXT UNIQUE NOT NULL,
        customer_name TEXT NOT NULL,
        customer_phone TEXT NOT NULL,
        customer_email TEXT,
        customer_address TEXT,
        customer_gstin TEXT,
        invoice_date TEXT NOT NULL,
        subtotal REAL NOT NULL,
        cgst REAL NOT NULL,
        sgst REAL NOT NULL,
        igst REAL DEFAULT 0,
        discount REAL DEFAULT 0,
        grand_total REAL NOT NULL,
        payment_method TEXT DEFAULT 'CASH',
        payment_status TEXT DEFAULT 'PAID',
        fulfillment_mode TEXT DEFAULT 'SHOWROOM_VISIT',
        notes TEXT,
        created_at TEXT
    )
    """)

    # 6. Invoice Line Items
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS invoice_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_id INTEGER,
        product_id INTEGER,
        item_name TEXT NOT NULL,
        hsn_code TEXT DEFAULT '8471',
        serial_number TEXT,
        quantity INTEGER NOT NULL,
        unit_price REAL NOT NULL,
        gst_rate REAL DEFAULT 18.0,
        total REAL NOT NULL,
        FOREIGN KEY(invoice_id) REFERENCES invoices(id)
    )
    """)

    # 7. AMC Contracts
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS amc_contracts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        contract_number TEXT UNIQUE NOT NULL,
        client_name TEXT NOT NULL,
        contact_person TEXT,
        phone TEXT NOT NULL,
        email TEXT,
        address TEXT,
        total_systems INTEGER DEFAULT 1,
        contract_value REAL NOT NULL,
        start_date TEXT NOT NULL,
        end_date TEXT NOT NULL,
        visit_frequency TEXT DEFAULT 'MONTHLY',
        status TEXT DEFAULT 'ACTIVE',
        notes TEXT
    )
    """)

    # 8. Orders (E-Commerce Web Orders)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_number TEXT UNIQUE NOT NULL,
        customer_name TEXT NOT NULL,
        customer_phone TEXT NOT NULL,
        customer_email TEXT,
        customer_address TEXT NOT NULL,
        order_type TEXT DEFAULT 'HARDWARE',
        items_json TEXT NOT NULL,
        total_amount REAL NOT NULL,
        status TEXT DEFAULT 'CONFIRMED',
        payment_method TEXT DEFAULT 'COD',
        fulfillment_mode TEXT DEFAULT 'SHOWROOM_VISIT',
        created_at TEXT
    )
    """)

    # 9. Store Profile / Settings
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS store_settings (
        key TEXT PRIMARY KEY,
        value TEXT
    )
    """)

    # 10. Customer Inquiries & Leads (with Staff Assignment & Fulfillment Mode)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS inquiries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        inquiry_number TEXT UNIQUE NOT NULL,
        customer_name TEXT NOT NULL,
        customer_phone TEXT NOT NULL,
        customer_email TEXT,
        customer_address TEXT,
        requirement_type TEXT NOT NULL,
        items_requested TEXT,
        custom_specs TEXT,
        estimated_budget REAL DEFAULT 0,
        status TEXT DEFAULT 'NEW',
        source TEXT DEFAULT 'Web',
        fulfillment_mode TEXT DEFAULT 'SHOWROOM_VISIT',
        assigned_staff_id INTEGER,
        assigned_staff_name TEXT,
        delivery_tracking_no TEXT,
        notes TEXT,
        created_at TEXT
    )
    """)

    # 11. Quotations / Estimates
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS quotations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        quotation_number TEXT UNIQUE NOT NULL,
        inquiry_id INTEGER,
        customer_name TEXT NOT NULL,
        customer_phone TEXT NOT NULL,
        customer_email TEXT,
        customer_address TEXT,
        customer_gstin TEXT,
        items_json TEXT NOT NULL,
        subtotal REAL NOT NULL,
        gst_amount REAL NOT NULL,
        grand_total REAL NOT NULL,
        valid_until TEXT,
        status TEXT DEFAULT 'SENT',
        notes TEXT,
        created_at TEXT,
        FOREIGN KEY(inquiry_id) REFERENCES inquiries(id)
    )
    """)

    # 12. Supplier Purchase Orders (PO)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS purchase_orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        po_number TEXT UNIQUE NOT NULL,
        supplier_id INTEGER,
        supplier_name TEXT NOT NULL,
        supplier_phone TEXT,
        supplier_gstin TEXT,
        order_date TEXT NOT NULL,
        expected_date TEXT,
        items_json TEXT NOT NULL,
        subtotal REAL NOT NULL,
        gst_amount REAL NOT NULL,
        total_amount REAL NOT NULL,
        status TEXT DEFAULT 'ORDERED',
        payment_status TEXT DEFAULT 'UNPAID',
        notes TEXT,
        created_at TEXT
    )
    """)

    # 13. Customer & Supplier Accounts
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS parties (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        party_type TEXT NOT NULL,
        name TEXT NOT NULL,
        contact_person TEXT,
        phone TEXT NOT NULL,
        email TEXT,
        address TEXT,
        gstin TEXT,
        opening_balance REAL DEFAULT 0,
        current_balance REAL DEFAULT 0,
        created_at TEXT
    )
    """)

    # 14. Double-entry Party Ledger Entries
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ledger_entries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        party_id INTEGER NOT NULL,
        party_type TEXT NOT NULL,
        entry_date TEXT NOT NULL,
        voucher_type TEXT NOT NULL,
        voucher_no TEXT NOT NULL,
        narration TEXT,
        debit REAL DEFAULT 0,
        credit REAL DEFAULT 0,
        running_balance REAL DEFAULT 0,
        created_at TEXT,
        FOREIGN KEY(party_id) REFERENCES parties(id)
    )
    """)

    # 15. Staff Members (8 Team Members Directory)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS staff_members (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        role TEXT NOT NULL,
        department TEXT NOT NULL,
        phone TEXT NOT NULL,
        email TEXT,
        username TEXT UNIQUE,
        password TEXT,
        pin TEXT DEFAULT '1234',
        permissions TEXT,
        last_login TEXT,
        active_leads_count INTEGER DEFAULT 0,
        status TEXT DEFAULT 'ACTIVE',
        created_at TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS staff_sessions (
        token TEXT PRIMARY KEY,
        staff_id INTEGER,
        created_at TEXT,
        expires_at TEXT
    )
    """)

    # 16. Multi-Godown / Warehouses
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS warehouses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        location TEXT NOT NULL,
        contact_person TEXT,
        phone TEXT,
        is_primary INTEGER DEFAULT 0
    )
    """)

    # 17. Warehouse Specific Stocks
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS warehouse_stocks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        warehouse_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity INTEGER DEFAULT 0,
        updated_at TEXT,
        FOREIGN KEY(warehouse_id) REFERENCES warehouses(id),
        FOREIGN KEY(product_id) REFERENCES products(id),
        UNIQUE(warehouse_id, product_id)
    )
    """)

    # 18. Inter-Godown Stock Transfers
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS stock_transfers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        transfer_no TEXT UNIQUE NOT NULL,
        from_warehouse_id INTEGER NOT NULL,
        to_warehouse_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        transferred_by TEXT,
        notes TEXT,
        status TEXT DEFAULT 'COMPLETED',
        created_at TEXT,
        FOREIGN KEY(from_warehouse_id) REFERENCES warehouses(id),
        FOREIGN KEY(to_warehouse_id) REFERENCES warehouses(id),
        FOREIGN KEY(product_id) REFERENCES products(id)
    )
    """)

    # 19. Branches (Franchise & Multi-Location Architecture)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS branches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        city TEXT NOT NULL,
        address TEXT,
        phone TEXT,
        is_hq INTEGER DEFAULT 0,
        status TEXT DEFAULT 'ACTIVE',
        created_at TEXT
    )
    """)

    conn.commit()
    seed_data(conn)
    conn.close()
    print("Database seeded successfully with PCWARE Enterprise records.")

def seed_data(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM products")
    if cursor.fetchone()[0] > 0:
        return

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Store Settings
    default_settings = [
        ("store_name", "PCWARE"),
        ("tagline", "Computer Hardware, Custom PC Builds, Networking & IT Care"),
        ("phone", "+91 94261 83934"),
        ("phone_ceo", "9426183934"),
        ("phone_service", "8000780704"),
        ("phone_inquiry", "7016737271"),
        ("email", "info@pcware.in"),
        ("address", "Shop No. SF, 47, 48, 49, Suvarnabhumi Complex, opp. Speedwell Party Plot, Ambika Twp, Mota Mava, Rajkot, Gujarat 360005"),
        ("gstin", "24AABCP1234F1Z5"),
        ("bank_name", "HDFC Bank Ltd / State Bank of India"),
        ("account_no", "50200094261839"),
        ("ifsc_code", "HDFC0001234"),
        ("upi_id", "9426183934@upi"),
        ("gemini_api_key", ""),
        ("gemini_model", "gemini-1.5-flash")
    ]
    cursor.executemany("INSERT OR REPLACE INTO store_settings (key, value) VALUES (?, ?)", default_settings)

    # 8 Staff Members
    staff_data = [
        ("Nilesh Vaghasiya", "CEO & Managing Director", "Management", "9426183934", "nilesh@pcware.in", 0, "ACTIVE", now_str),
        ("Hardik Patel", "Senior Sales Executive", "Sales & Inquiries", "7016737271", "hardik.sales@pcware.in", 3, "ACTIVE", now_str),
        ("Pratik Dave", "Corporate B2B & Workstation Specialist", "B2B Sales", "9825123456", "pratik.b2b@pcware.in", 2, "ACTIVE", now_str),
        ("Jignesh Mehta", "Lead Hardware Chip-Level Engineer", "Lab & Service", "8000780704", "jignesh.tech@pcware.in", 4, "ACTIVE", now_str),
        ("Vishal Vala", "Custom PC & Server Assembly Tech", "Assembly & QC", "9712345678", "vishal.build@pcware.in", 2, "ACTIVE", now_str),
        ("Ravi Kothari", "Network Security & AMC Field Engineer", "Networking & AMC", "9924567890", "ravi.network@pcware.in", 3, "ACTIVE", now_str),
        ("Sanjay Rathod", "Store Keeper & Multi-Godown Logistics", "Logistics & Stock", "9876543210", "sanjay.stock@pcware.in", 0, "ACTIVE", now_str),
        ("Mehul Trivedi", "Senior Accountant & Billing Executive", "Accounts & Finance", "9428765432", "mehul.accounts@pcware.in", 0, "ACTIVE", now_str),
    ]
    cursor.executemany("""
    INSERT INTO staff_members (name, role, department, phone, email, active_leads_count, status, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, staff_data)

    # 3 Warehouses
    warehouse_data = [
        ("WH-SHOWROOM", "PCWARE Main Showroom & Store", "Suvarnabhumi Complex, Mota Mava, Rajkot", "Nilesh Vaghasiya", "9426183934", 1),
        ("WH-GODOWN1", "Godown 1 - Central Bulk Storage", "Kalawad Road, Ambika Twp, Rajkot", "Sanjay Rathod", "9876543210", 0),
        ("WH-LAB", "Service & Custom Upgrade Lab", "Hardware Lab Floor 2, Rajkot", "Jignesh Mehta", "8000780704", 0)
    ]
    cursor.executemany("""
    INSERT INTO warehouses (code, name, location, contact_person, phone, is_primary)
    VALUES (?, ?, ?, ?, ?, ?)
    """, warehouse_data)

    # Branches (Franchise-Ready Architecture)
    branch_data = [
        ("BR-RJK-01", "PCWARE Rajkot HQ (Flagship Store)", "Rajkot", "Suvarnabhumi Complex, Mota Mava, Rajkot", "+91 94261 83934", 1, "ACTIVE", now_str),
        ("BR-AHM-01", "PCWARE Ahmedabad Franchise", "Ahmedabad", "Near Iscon Cross Road, SG Highway, Ahmedabad", "+91 98250 99887", 0, "ACTIVE", now_str),
        ("BR-SRT-01", "PCWARE Surat Franchise", "Surat", "Ring Road Electronics Market, Surat", "+91 99090 11223", 0, "ACTIVE", now_str),
    ]
    cursor.executemany("""
    INSERT INTO branches (code, name, city, address, phone, is_hq, status, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, branch_data)

    # Products Catalog
    products_data = [
        # Processors (CPUs)
        ("CPU-INT-12100F", "Intel Core i3-12100F Processor (4 Cores, 8 Threads, Up to 4.3 GHz)", "processor", "Intel", "Core i3-12100F", "8471", 6800, 7900, 18.0, 15, 3, "LGA1700, 4 Cores / 8 Threads, 12MB Cache, 58W TDP", 58, "LGA1700", None, "https://images.unsplash.com/photo-1591799264318-7e6ef8ddb7ea?w=400"),
        ("CPU-INT-12400F", "Intel Core i5-12400F Processor (6 Cores, 12 Threads, Up to 4.4 GHz)", "processor", "Intel", "Core i5-12400F", "8471", 9800, 11500, 18.0, 20, 3, "LGA1700, 6 P-Cores / 12 Threads, 18MB Cache, 65W TDP", 65, "LGA1700", None, "https://images.unsplash.com/photo-1591799264318-7e6ef8ddb7ea?w=400"),
        ("CPU-INT-13400F", "Intel Core i5-13400F Processor (10 Cores, Up to 4.6 GHz)", "processor", "Intel", "Core i5-13400F", "8471", 16200, 18500, 18.0, 12, 2, "LGA1700, 10 Cores (6P+4E), 20MB Cache, 65W TDP", 65, "LGA1700", None, "https://images.unsplash.com/photo-1591799264318-7e6ef8ddb7ea?w=400"),
        ("CPU-INT-13600K", "Intel Core i5-13600K Processor (14 Cores, Up to 5.1 GHz)", "processor", "Intel", "Core i5-13600K", "8471", 24500, 27900, 18.0, 8, 2, "LGA1700, 14 Cores (6P+8E), 24MB Cache, 125W TDP, Unlocked", 125, "LGA1700", None, "https://images.unsplash.com/photo-1591799264318-7e6ef8ddb7ea?w=400"),
        ("CPU-INT-14700K", "Intel Core i7-14700K 14th Gen Processor (20 Cores, Up to 5.6 GHz)", "processor", "Intel", "Core i7-14700K", "8471", 33500, 37500, 18.0, 6, 1, "LGA1700, 20 Cores (8P+12E), 33MB Cache, Intel UHD 770", 125, "LGA1700", None, "https://images.unsplash.com/photo-1591799264318-7e6ef8ddb7ea?w=400"),
        ("CPU-INT-14900K", "Intel Core i9-14900K Flagship Processor (24 Cores, Up to 6.0 GHz)", "processor", "Intel", "Core i9-14900K", "8471", 49000, 54500, 18.0, 4, 1, "LGA1700, 24 Cores (8P+16E), 36MB Cache, Extreme Performance", 150, "LGA1700", None, "https://images.unsplash.com/photo-1591799264318-7e6ef8ddb7ea?w=400"),
        ("CPU-INT-10105F", "Intel Core i3-10105F Comet Lake Processor (4 Cores, Up to 4.4 GHz)", "processor", "Intel", "Core i3-10105F", "8471", 5200, 6200, 18.0, 10, 2, "LGA1200, 4 Cores / 8 Threads, 6MB Cache, 65W TDP", 65, "LGA1200", None, "https://images.unsplash.com/photo-1591799264318-7e6ef8ddb7ea?w=400"),
        ("CPU-INT-10400F", "Intel Core i5-10400F Desktop Processor (6 Cores, Up to 4.3 GHz)", "processor", "Intel", "Core i5-10400F", "8471", 7900, 9400, 18.0, 8, 2, "LGA1200, 6 Cores / 12 Threads, 12MB Cache, 65W TDP", 65, "LGA1200", None, "https://images.unsplash.com/photo-1591799264318-7e6ef8ddb7ea?w=400"),
        ("CPU-AMD-3600", "AMD Ryzen 5 3600 Desktop Processor (6 Cores, Up to 4.2 GHz)", "processor", "AMD", "Ryzen 5 3600", "8471", 6900, 8200, 18.0, 12, 3, "AM4, 6 Cores / 12 Threads, 35MB GameCache, 65W TDP", 65, "AM4", None, "https://images.unsplash.com/photo-1591799264318-7e6ef8ddb7ea?w=400"),
        ("CPU-AMD-5600", "AMD Ryzen 5 5600 Desktop Processor (6 Cores, Up to 4.4 GHz)", "processor", "AMD", "Ryzen 5 5600", "8471", 9600, 11200, 18.0, 14, 3, "AM4, 6 Cores / 12 Threads, 35MB Cache, Wraith Stealth Cooler", 65, "AM4", None, "https://images.unsplash.com/photo-1591799264318-7e6ef8ddb7ea?w=400"),
        ("CPU-AMD-5700X", "AMD Ryzen 7 5700X 8-Core Desktop Processor (Up to 4.6 GHz)", "processor", "AMD", "Ryzen 7 5700X", "8471", 14500, 16800, 18.0, 8, 2, "AM4, 8 Cores / 16 Threads, 36MB Cache, 65W TDP", 65, "AM4", None, "https://images.unsplash.com/photo-1591799264318-7e6ef8ddb7ea?w=400"),
        ("CPU-AMD-7600X", "AMD Ryzen 5 7600X Desktop Processor (6 Cores, Up to 5.3 GHz)", "processor", "AMD", "Ryzen 5 7600X", "8471", 17500, 19900, 18.0, 10, 2, "AM5, 6 Cores / 12 Threads, 38MB Cache, 105W TDP", 105, "AM5", None, "https://images.unsplash.com/photo-1591799264318-7e6ef8ddb7ea?w=400"),
        ("CPU-AMD-7800X3D", "AMD Ryzen 7 7800X3D Gaming Processor (3D V-Cache)", "processor", "AMD", "Ryzen 7 7800X3D", "8471", 33000, 37900, 18.0, 6, 2, "AM5, 8 Cores / 16 Threads, 104MB Cache, 120W TDP", 120, "AM5", None, "https://images.unsplash.com/photo-1591799264318-7e6ef8ddb7ea?w=400"),

        # Motherboards
        ("MB-MSI-H610", "MSI PRO H610M-E DDR4 Micro-ATX Motherboard", "motherboard", "MSI", "PRO H610M-E DDR4", "8471", 5600, 6600, 18.0, 15, 3, "LGA1700, DDR4 up to 3200MHz, PCIe 4.0 x16, M.2 NVMe", 25, "LGA1700", "DDR4", "https://images.unsplash.com/photo-1518770660439-4636190af475?w=400"),
        ("MB-GIGA-B760D4", "Gigabyte B760M DS3H DDR4 Motherboard", "motherboard", "Gigabyte", "B760M DS3H DDR4", "8471", 9400, 10900, 18.0, 10, 2, "LGA1700, Dual PCIe 4.0 M.2, 4x DDR4 Slots", 30, "LGA1700", "DDR4", "https://images.unsplash.com/photo-1518770660439-4636190af475?w=400"),
        ("MB-GIGA-B760D5", "Gigabyte B760 Gaming X AX DDR5 ATX Motherboard", "motherboard", "Gigabyte", "B760 Gaming X AX DDR5", "8471", 14800, 16900, 18.0, 8, 2, "LGA1700, 4x DDR5 up to 7600MHz, 3x M.2 PCIe 4.0, Wi-Fi 6E", 35, "LGA1700", "DDR5", "https://images.unsplash.com/photo-1518770660439-4636190af475?w=400"),
        ("MB-ASUS-ROG-Z790", "ASUS ROG Strix Z790-F Gaming WiFi II DDR5", "motherboard", "ASUS", "ROG Strix Z790-F", "8471", 34000, 38900, 18.0, 4, 1, "LGA1700, DDR5 up to 8000+MHz, PCIe 5.0, WiFi 7", 45, "LGA1700", "DDR5", "https://images.unsplash.com/photo-1518770660439-4636190af475?w=400"),
        ("MB-ASUS-H510", "ASUS Prime H510M-E Micro-ATX Motherboard", "motherboard", "ASUS", "Prime H510M-E", "8471", 5200, 6100, 18.0, 10, 2, "LGA1200, DDR4 up to 3200MHz, M.2 slot", 25, "LGA1200", "DDR4", "https://images.unsplash.com/photo-1518770660439-4636190af475?w=400"),
        ("MB-GIGA-A520", "Gigabyte A520M K V2 Ultra Durable Motherboard", "motherboard", "Gigabyte", "A520M K V2", "8471", 4400, 5200, 18.0, 12, 3, "AM4, Dual DDR4 up to 5100(OC), PCIe 3.0 x4 NVMe M.2", 25, "AM4", "DDR4", "https://images.unsplash.com/photo-1518770660439-4636190af475?w=400"),
        ("MB-MSI-B550", "MSI B550M PRO-VDH WiFi AM4 Motherboard", "motherboard", "MSI", "B550M PRO-VDH WiFi", "8471", 8600, 9900, 18.0, 10, 2, "AM4, DDR4 Boost, Lightning Gen 4 M.2, Wi-Fi AC", 30, "AM4", "DDR4", "https://images.unsplash.com/photo-1518770660439-4636190af475?w=400"),
        ("MB-MSI-B650P", "MSI Pro B650M-P AM5 DDR5 Micro-ATX Motherboard", "motherboard", "MSI", "Pro B650M-P", "8471", 9900, 11500, 18.0, 9, 2, "AM5, DDR5 up to 6400+ MHz, PCIe 4.0 M.2, 2.5G LAN", 30, "AM5", "DDR5", "https://images.unsplash.com/photo-1518770660439-4636190af475?w=400"),
        ("MB-GIGA-B650E", "Gigabyte B650 AORUS Elite AX AM5 ATX Motherboard", "motherboard", "Gigabyte", "B650 AORUS Elite AX", "8471", 18800, 21500, 18.0, 6, 1, "AM5, DDR5 EXPO & XMP, PCIe 5.0 M.2, AMD Wi-Fi 6E", 40, "AM5", "DDR5", "https://images.unsplash.com/photo-1518770660439-4636190af475?w=400"),

        # RAM
        ("RAM-CRU-8D4", "Crucial Basics 8GB DDR4 3200MHz Desktop RAM", "ram", "Crucial", "Basics DDR4", "8471", 1400, 1750, 18.0, 25, 4, "1x8GB, DDR4 3200MHz, UDIMM, 1.2V", 4, None, "DDR4", "https://images.unsplash.com/photo-1562976540-1502c2145186?w=400"),
        ("RAM-COR-16D4", "Corsair Vengeance LPX 16GB DDR4 3200MHz Desktop RAM", "ram", "Corsair", "Vengeance LPX", "8471", 2700, 3300, 18.0, 30, 5, "1x16GB, DDR4 3200MHz, CL16, Aluminum Spreader", 5, None, "DDR4", "https://images.unsplash.com/photo-1562976540-1502c2145186?w=400"),
        ("RAM-KING-16D5", "Kingston FURY Beast 16GB DDR5 5200MHz Desktop RAM", "ram", "Kingston", "FURY Beast DDR5", "8471", 4200, 4990, 18.0, 18, 3, "1x16GB, DDR5 5200MHz, On-die ECC, Intel XMP 3.0", 6, None, "DDR5", "https://images.unsplash.com/photo-1562976540-1502c2145186?w=400"),
        ("RAM-COR-32D5", "Corsair Vengeance 32GB (16GBx2) DDR5 5600MHz RAM", "ram", "Corsair", "Vengeance DDR5", "8471", 7900, 9200, 18.0, 14, 2, "32GB Dual Channel, DDR5 5600MHz, Intel XMP & AMD EXPO", 7, None, "DDR5", "https://images.unsplash.com/photo-1562976540-1502c2145186?w=400"),

        # Storage (SSDs & HDDs)
        ("SSD-WD-BLUE-500", "Western Digital Blue SA510 500GB 2.5 SATA SSD", "storage", "WD", "SA510 500GB", "8471", 2800, 3400, 18.0, 15, 3, "2.5 Inch SATA III, Read up to 560 MB/s, 3 Years Warranty", 3, None, None, "https://images.unsplash.com/photo-1597872200969-2b65d56bd16b?w=400"),
        ("SSD-CRU-P3P-1TB", "Crucial P3 Plus 1TB PCIe M.2 2280 Gen4 NVMe SSD", "storage", "Crucial", "P3 Plus 1TB", "8471", 4900, 5800, 18.0, 20, 4, "Read up to 5000 MB/s, Write up to 4200 MB/s, 5 Years Warranty", 5, None, None, "https://images.unsplash.com/photo-1597872200969-2b65d56bd16b?w=400"),
        ("SSD-KING-NV2-2TB", "Kingston NV2 2TB M.2 NVMe PCIe 4.0 SSD", "storage", "Kingston", "NV2 2TB", "8471", 8900, 10500, 18.0, 8, 2, "Up to 3,500MB/s Read, 2,800MB/s Write", 5, None, None, "https://images.unsplash.com/photo-1597872200969-2b65d56bd16b?w=400"),
        ("HDD-SEAG-2TB", "Seagate BarraCuda 2TB 7200 RPM 3.5 SATA Hard Drive", "storage", "Seagate", "BarraCuda 2TB", "8471", 4100, 4850, 18.0, 12, 3, "2TB, 7200RPM, 256MB Cache, SATA 6Gb/s", 8, None, None, "https://images.unsplash.com/photo-1597872200969-2b65d56bd16b?w=400"),

        # Graphic Cards (GPUs)
        ("GPU-ASUS-1650", "ASUS Phoenix GeForce GTX 1650 4GB GDDR6", "gpu", "ASUS", "Phoenix GTX 1650", "8471", 11200, 12990, 18.0, 8, 2, "4GB GDDR6, Turing Architecture, Compact single-fan design", 75, None, None, "https://images.unsplash.com/photo-1587202372775-e229f172b9d7?w=400"),
        ("GPU-MSI-3060-12G", "MSI GeForce RTX 3060 Ventus 2X 12G OC", "gpu", "MSI", "RTX 3060 Ventus 2X", "8471", 22500, 25800, 18.0, 10, 2, "12GB GDDR6, Ray Tracing, DLSS, Dual Fan Cooling", 170, None, None, "https://images.unsplash.com/photo-1587202372775-e229f172b9d7?w=400"),
        ("GPU-GIGA-4060-8G", "Gigabyte GeForce RTX 4060 WINDFORCE OC 8G", "gpu", "Gigabyte", "RTX 4060 WINDFORCE", "8471", 26200, 29500, 18.0, 7, 2, "8GB GDDR6, Ada Lovelace, DLSS 3, Dual 80mm Fans", 115, None, None, "https://images.unsplash.com/photo-1587202372775-e229f172b9d7?w=400"),
        ("GPU-ASUS-4070S", "ASUS Dual GeForce RTX 4070 SUPER 12GB GDDR6X", "gpu", "ASUS", "Dual RTX 4070 Super", "8471", 53500, 59900, 18.0, 4, 1, "12GB GDDR6X, 2.56-slot, Axial-tech fan design, 0dB tech", 220, None, None, "https://images.unsplash.com/photo-1587202372775-e229f172b9d7?w=400"),

        # Power Supplies (SMPS)
        ("PSU-ANTI-550W", "Ant Esports VS550L 550 Watt Non-Modular Power Supply", "psu", "Ant Esports", "VS550L", "8471", 1750, 2190, 18.0, 15, 3, "550W, 120mm Silent Fan, Over Voltage Protection", 0, None, None, "https://images.unsplash.com/photo-1587202372634-32705e3bf49c?w=400"),
        ("PSU-COR-650W", "Corsair CX650 650 Watt 80 Plus Bronze Power Supply", "psu", "Corsair", "CX650", "8471", 4200, 4990, 18.0, 12, 3, "650W, 80 PLUS Bronze Certified, Low-noise 120mm fan", 0, None, None, "https://images.unsplash.com/photo-1587202372634-32705e3bf49c?w=400"),
        ("PSU-COR-850W", "Corsair RM850e 850 Watt 80 Plus Gold Fully Modular", "psu", "Corsair", "RM850e ATX 3.0", "8471", 9400, 10800, 18.0, 6, 2, "850W, 80 PLUS Gold, ATX 3.0 & PCIe 5.0 12VHPWR Ready", 0, None, None, "https://images.unsplash.com/photo-1587202372634-32705e3bf49c?w=400"),

        # Cabinets
        ("CAB-ANTI-ICE100", "Ant Esports ICE-100 Air Mini Mesh Micro-ATX Case", "cabinet", "Ant Esports", "ICE-100 Air", "8471", 2400, 2990, 18.0, 10, 2, "Mesh Front Panel, 2x 120mm Front Fans + 1x Rear, Tempered Glass", 0, None, None, "https://images.unsplash.com/photo-1587202372775-e229f172b9d7?w=400"),
        ("CAB-COR-4000D", "Corsair 4000D Airflow Tempered Glass Mid-Tower Case", "cabinet", "Corsair", "4000D Airflow", "8471", 5600, 6700, 18.0, 7, 2, "High-airflow front panel, RapidRoute cable management, 2x AirGuide fans", 0, None, None, "https://images.unsplash.com/photo-1587202372775-e229f172b9d7?w=400"),

        # Coolers & Fans
        ("CLR-DEEP-AG400", "Deepcool AG400 Single-Tower 120mm CPU Air Cooler", "cooler", "Deepcool", "AG400", "8471", 1450, 1799, 18.0, 15, 3, "4 Direct Touch Copper Heatpipes, 220W TDP Cooling Power", 15, None, None, "https://images.unsplash.com/photo-1587202372634-32705e3bf49c?w=400"),
        ("CLR-DEEP-LE520", "Deepcool LE520 240mm All-In-One Liquid CPU Cooler", "cooler", "Deepcool", "LE520 240mm", "8471", 4800, 5700, 18.0, 8, 2, "240mm Radiator, Dual ARGB Fans, Anti-Leak Technology, 220W TDP", 20, None, None, "https://images.unsplash.com/photo-1587202372634-32705e3bf49c?w=400"),

        # Laptops (Business, Gaming & Tested Refurbished)
        ("LAP-DELL-5430", "Dell Latitude 5430 Corporate Business Laptop (Core i5 12th Gen, 8GB DDR4, 512GB NVMe, 14 FHD)", "laptop", "Dell", "Latitude 5430", "8471", 46000, 53500, 18.0, 8, 2, "Intel Core i5-1235U, Base 8GB RAM, 512GB NVMe, 14 FHD IPS, Win 11 Pro, Backlit KB, Upgradeable RAM & SSD", 45, None, "DDR4", "https://images.unsplash.com/photo-1588872657578-7efd1f1555ed?w=400"),
        ("LAP-LENOVO-T14", "Lenovo ThinkPad T14 Gen 3 Professional (Ryzen 7 PRO 6850U, 16GB DDR5, 512GB Gen4)", "laptop", "Lenovo", "ThinkPad T14 Gen 3", "8471", 68000, 77500, 18.0, 5, 2, "AMD Ryzen 7 PRO 6850U, 16GB DDR5, 512GB Gen4 NVMe, 14 WUXGA, Win 11 Pro, TrackPoint, Upgradeable", 50, None, "DDR5", "https://images.unsplash.com/photo-1588872657578-7efd1f1555ed?w=400"),
        ("LAP-HP-450G9", "HP ProBook 450 G9 Commercial Laptop (Core i5-1240P, 8GB DDR4, 512GB SSD, 15.6 FHD)", "laptop", "HP", "ProBook 450 G9", "8471", 44000, 51000, 18.0, 7, 2, "Intel Core i5-1240P 12-Core, 8GB DDR4, 512GB SSD, 15.6 FHD with Numpad, Win 11 Home, Upgradeable", 45, None, "DDR4", "https://images.unsplash.com/photo-1588872657578-7efd1f1555ed?w=400"),
        ("LAP-ASUS-G16", "Asus ROG Strix G16 Gaming Laptop (Core i7 13th Gen, 16GB DDR5, 1TB Gen4, RTX 4060 6GB)", "laptop", "Asus", "ROG Strix G16", "8471", 98000, 112000, 18.0, 4, 1, "Intel Core i7-13650HX 14-Core, 16GB DDR5, 1TB Gen4 SSD, 6GB Nvidia RTX 4060, 16 FHD+ 165Hz, RGB", 140, None, "DDR5", "https://images.unsplash.com/photo-1603302576837-37561b2e2302?w=400"),
        ("LAP-REF-DELL7490", "Dell Latitude 7490 Refurbished Corporate Laptop (Core i7 8th Gen, 8GB DDR4, 256GB SSD)", "laptop", "Dell", "Latitude 7490 (Refurb)", "8471", 16500, 21500, 18.0, 12, 3, "Grade A+ Refurbished, Intel Core i7-8650U, 8GB DDR4, 256GB SSD, 14.0 FHD Touch, 6 Months PCWARE Store Warranty", 35, None, "DDR4", "https://images.unsplash.com/photo-1588872657578-7efd1f1555ed?w=400"),
        ("LAP-REF-THINKL480", "Lenovo ThinkPad L480 Corporate Return Laptop (Core i5 8th Gen, 8GB DDR4, 256GB NVMe)", "laptop", "Lenovo", "ThinkPad L480 (Refurb)", "8471", 14000, 18500, 18.0, 15, 3, "Grade A Corporate Refurbished, Intel Core i5-8250U, 8GB DDR4, 256GB NVMe, 14.0 Anti-Glare, 6 Months Store Warranty", 35, None, "DDR4", "https://images.unsplash.com/photo-1588872657578-7efd1f1555ed?w=400"),

        # Desktop Workstations (CAD, 3D, Video Editing, AI)
        ("WKS-HP-Z4", "HP Z4 G4 Professional Workstation (Intel Xeon W-2223, 32GB ECC, 1TB NVMe, Nvidia RTX A2000)", "workstation", "HP", "Z4 G4 Workstation", "8471", 85000, 98000, 18.0, 3, 1, "Intel Xeon W-2223 4-Core, 32GB DDR4 ECC RAM, 1TB NVMe SSD, Nvidia RTX A2000 6GB Workstation GPU, 750W 90% PSU, Win 11 Pro for Workstations", 350, None, "DDR4", "https://images.unsplash.com/photo-1593640408182-31c70c8268f5?w=400"),
        ("WKS-DELL-3660", "Dell Precision 3660 Tower Workstation (Core i7-13700K, 32GB DDR5, 1TB Gen4, RTX 4070 12GB)", "workstation", "Dell", "Precision 3660", "8471", 115000, 129000, 18.0, 2, 1, "Intel Core i7-13700K 16-Core, 32GB DDR5 RAM, 1TB Gen4 NVMe, Nvidia RTX 4070 12GB, 500W Platinum PSU, AutoCAD / SolidWorks Certified", 450, None, "DDR5", "https://images.unsplash.com/photo-1593640408182-31c70c8268f5?w=400"),
        ("WKS-CUSTOM-AI", "PCWARE AI Studio Deep Learning Workstation (Ryzen 9 7950X, 64GB DDR5, Dual 2TB SSD, RTX 4080)", "workstation", "PCWARE", "AI Studio 7950X", "8471", 235000, 265000, 18.0, 2, 1, "AMD Ryzen 9 7950X 16-Core, 64GB DDR5 6000MHz, Dual 2TB Gen4 SSDs (RAID-0), Nvidia RTX 4080 16GB, 1000W Platinum SMPS, Liquid Cooled", 650, "AM5", "DDR5", "https://images.unsplash.com/photo-1593640408182-31c70c8268f5?w=400"),

        # Servers (Tower, Rackmount, Storage)
        ("SRV-DELL-T350", "Dell PowerEdge T350 Tower Server (Intel Xeon E-2336, 32GB ECC, 2x 2TB SATA RAID-1, iDRAC9)", "server", "Dell", "PowerEdge T350", "8471", 110000, 125000, 18.0, 2, 1, "Intel Xeon E-2336 6C/12T, 32GB ECC UDIMM, 2x 2TB Enterprise Enterprise SATA HDD, PERC H355 RAID Controller, Dual Redundant 600W Hot-Plug PSUs, iDRAC9 Enterprise", 350, None, "DDR4", "https://images.unsplash.com/photo-1558494949-ef010cbdcc31?w=400"),
        ("SRV-HP-DL380", "HPE ProLiant DL380 Gen10 2U Rack Server (Xeon Silver 4210R, 64GB DDR4, 4x 1.2TB SAS 10K)", "server", "HPE", "ProLiant DL380 Gen10", "8471", 185000, 210000, 18.0, 1, 1, "Intel Xeon Silver 4210R 10C/20T, 64GB DDR4 Registered SmartMemory, 4x 1.2TB SAS 10K Hot-Plug HDDs, P408i-a RAID 2GB Cache, Dual 800W Flex Slot Titanium PSUs", 500, None, "DDR4", "https://images.unsplash.com/photo-1558494949-ef010cbdcc31?w=400"),
        ("SRV-NAS-TRUENAS", "PCWARE Business TrueNAS File & Backup Server (Core i3 12th Gen, 32GB ECC, 4x 4TB WD Red)", "server", "PCWARE", "TrueNAS Backup Box", "8471", 54000, 62000, 18.0, 3, 1, "Intel Core i3 12th Gen, 32GB RAM, 4x 4TB WD Red Plus NAS HDDs in RAID-Z2 (8TB Usable Redundant), Dual 2.5GbE LAN, TrueNAS Core Enterprise OS Pre-configured", 180, "LGA1700", "DDR4", "https://images.unsplash.com/photo-1558494949-ef010cbdcc31?w=400"),

        # CyberSecurity & Firewalls & Managed Switches
        ("NET-SOPHOS-XGS116", "Sophos XGS 116 Next-Gen Hardware Firewall Appliance (1-Year Standard Protection)", "firewall_networking", "Sophos", "XGS 116", "8517", 42000, 48500, 18.0, 4, 1, "Dual-Engine Architecture, 11x GbE Ports, 1x SFP Port, Deep Packet Inspection, Sandstorm Cloud Sandbox, IPS, Zero-Day Threat Protection, 1-Year Standard License", 40, None, None, "https://images.unsplash.com/photo-1544197150-b99a580bb7a8?w=400"),
        ("NET-FORTI-40F", "Fortinet FortiGate 40F Enterprise Network Firewall (1-Year UTM Bundle)", "firewall_networking", "Fortinet", "FortiGate 40F", "8517", 34000, 39900, 18.0, 5, 2, "SOC4 Processor, 5x GE RJ45 Ports, IPsec VPN up to 4.4 Gbps, Advanced Threat Protection, Web Filtering, Application Control, 1-Year FortiCare License", 35, None, None, "https://images.unsplash.com/photo-1544197150-b99a580bb7a8?w=400"),
        ("NET-DLINK-24POE", "D-Link DGS-1210-28P 24-Port Gigabit Smart Managed PoE+ Switch", "firewall_networking", "D-Link", "DGS-1210-28P", "8517", 18500, 21500, 18.0, 6, 2, "24x Gigabit PoE+ Ports, 4x Gigabit SFP Ports, 193W Total PoE Budget, Surveillance VLAN, Layer 2 Management", 45, None, None, "https://images.unsplash.com/photo-1544197150-b99a580bb7a8?w=400"),
        ("NET-CISCO-C250", "Cisco Business 250 CBS250-24T-4G Smart Switch (24x Gigabit, 4x 1G SFP)", "firewall_networking", "Cisco", "CBS250-24T-4G", "8517", 22000, 25500, 18.0, 4, 1, "24x 10/100/1000 Ports, 4x Gigabit SFP Uplinks, Layer 3 Static Routing, QoS, Energy Efficient Ethernet", 35, None, None, "https://images.unsplash.com/photo-1544197150-b99a580bb7a8?w=400"),
        ("NET-RACK-9U", "Netrack 9U Wall Mount Server & Network Rack with PDU & Cooling Fan", "firewall_networking", "Netrack", "9U Wall Mount Rack", "8517", 4200, 5200, 18.0, 8, 2, "9U Depth 550mm, Toughened Glass Door with Lock, 6-Socket 5A PDU Strip, 2x High-CFM Cooling Fans, 1x Cable Manager", 0, None, None, "https://images.unsplash.com/photo-1558494949-ef010cbdcc31?w=400"),

        # Antivirus & Security Software
        ("SW-QH-TS-1U1Y", "Quick Heal Total Security 1 User 1 Year License Key Box", "antivirus_software", "Quick Heal", "Total Security 1U1Y", "8523", 480, 699, 18.0, 50, 10, "1 PC / 1 Year, Ransomware Protection, Safe Banking, Firewall, Anti-Malware, Parental Control, Automatic Updates", 0, None, None, "https://images.unsplash.com/photo-1563986768609-322da13575f3?w=400"),
        ("SW-QH-TS-1U3Y", "Quick Heal Total Security 1 User 3 Years License Key Box", "antivirus_software", "Quick Heal", "Total Security 1U3Y", "8523", 1150, 1499, 18.0, 35, 10, "1 PC / 3 Years, Advanced DNA Scan, Anti-Phishing, Web Security, Zero-day Attack Shield, Unbreakable Warranty", 0, None, None, "https://images.unsplash.com/photo-1563986768609-322da13575f3?w=400"),
        ("SW-KASP-TS-3U", "Kaspersky Total Security 3 Devices 1 Year License Key", "antivirus_software", "Kaspersky", "Total Security 3D1Y", "8523", 1100, 1450, 18.0, 25, 5, "3 PCs/Macs/Android, Real-time Antivirus, Smart VPN, Password Manager, Payment Protection, Webcam Privacy", 0, None, None, "https://images.unsplash.com/photo-1563986768609-322da13575f3?w=400"),
        ("SW-SEQRITE-EPS", "Seqrite Endpoint Security Cloud (5-User Pack 1-Year SMB License)", "antivirus_software", "Seqrite", "EPS Cloud 5U", "8523", 6200, 7800, 18.0, 10, 2, "5 Endpoints, Centralized Cloud Management, Data Loss Prevention (DLP), Device Control, Asset Management, Vulnerability Scan", 0, None, None, "https://images.unsplash.com/photo-1563986768609-322da13575f3?w=400"),

        # Peripherals
        ("PRN-HP-108W", "HP Laser 108w Single Function Wireless Monochrome Laser Printer", "peripheral", "HP", "Laser 108w", "8443", 11500, 13490, 18.0, 6, 2, "Mono Laser, 20 ppm, WiFi Direct, Hi-Speed USB 2.0, Compact Size", 0, None, None, "https://images.unsplash.com/photo-1612815154858-60aa4c59eaa6?w=400"),
        ("MON-DELL-24", "Dell 24 Inch Full HD IPS Bezel-Less Monitor (HDMI, VGA, 75Hz)", "peripheral", "Dell", "S2421HN", "8528", 8200, 9600, 18.0, 10, 3, "24.0 FHD IPS Display, 75Hz Refresh Rate, AMD FreeSync, Dual HDMI Ports", 20, None, None, "https://images.unsplash.com/photo-1527443224154-c4a3942d3acf?w=400"),
        ("KB-LOGI-MK295", "Logitech MK295 Silent Wireless Keyboard and Mouse Combo", "peripheral", "Logitech", "MK295 Silent", "8471", 1950, 2390, 18.0, 15, 3, "SilentTouch Technology (90% noise reduction), 2.4GHz Wireless, 36-month battery", 0, None, None, "https://images.unsplash.com/photo-1587829741301-dc798b83add3?w=400")
    ]

    cursor.executemany("""
    INSERT INTO products (sku, name, category, brand, model, hsn_code, cost_price, selling_price, gst_rate, stock_quantity, low_stock_threshold, specs, wattage, socket, memory_type, image_url, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, [(p[0], p[1], p[2], p[3], p[4], p[5], p[6], p[7], p[8], p[9], p[10], p[11], p[12], p[13], p[14], p[15], now_str) for p in products_data])

    # Populate Warehouse Stocks (split between Showroom, Godown 1, and Lab)
    cursor.execute("SELECT id, stock_quantity FROM products")
    prods = cursor.fetchall()
    for pid, qty in prods:
        sh_qty = max(1, int(qty * 0.4))
        gd_qty = max(0, int(qty * 0.5))
        lb_qty = max(0, qty - sh_qty - gd_qty)
        cursor.execute("INSERT INTO warehouse_stocks (warehouse_id, product_id, quantity, updated_at) VALUES (1, ?, ?, ?)", (pid, sh_qty, now_str))
        cursor.execute("INSERT INTO warehouse_stocks (warehouse_id, product_id, quantity, updated_at) VALUES (2, ?, ?, ?)", (pid, gd_qty, now_str))
        cursor.execute("INSERT INTO warehouse_stocks (warehouse_id, product_id, quantity, updated_at) VALUES (3, ?, ?, ?)", (pid, lb_qty, now_str))

    # Sample Stock Transfers
    transfers = [
        ("TRF-2026-001", 2, 1, 1, 5, "Sanjay Rathod", "Bulk CPU stock moved to Showroom counter", "COMPLETED", now_str),
        ("TRF-2026-002", 2, 3, 14, 3, "Sanjay Rathod", "Laptop units sent to Lab for RAM & SSD upgrade testing", "COMPLETED", now_str),
    ]
    cursor.executemany("""
    INSERT INTO stock_transfers (transfer_no, from_warehouse_id, to_warehouse_id, product_id, quantity, transferred_by, notes, status, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, transfers)

    # Sample Parties (Customers & Suppliers)
    parties_data = [
        ("CUSTOMER", "Vortex Digital Agency", "Bhavesh Patel", "9825123456", "billing@vortexdigital.in", "Kalawad Road, Rajkot, Gujarat", "24AABCV9918K1ZM", 0, 61360.0, now_str),
        ("CUSTOMER", "Apex Global Logistics", "Chetan Shah", "9898033445", "accounts@apexlogistic.in", "GIDC Metoda, Lodhika, Rajkot", "24AABCA1209D1ZQ", 0, 14500.0, now_str),
        ("CUSTOMER", "Dr. Rohan Bhatt (Bhatt Clinic)", "Dr. Rohan", "9426011223", "dr.bhatt@gmail.com", "Tagore Road, Rajkot", None, 0, 0.0, now_str),
        ("CUSTOMER", "Shree Ram Engineering Works", "Rameshbhai", "9724155667", "shreeram.rajkot@yahoo.com", "Aji GIDC Phase II, Rajkot", "24ABJPR4590H1Z3", 0, 32000.0, now_str),
        ("CUSTOMER", "Kavya Infotech Solutions", "Kavya Mehta", "7016022334", "kavya@kavyainfotech.com", "150 Feet Ring Road, Rajkot", "24AADCK5612R1ZU", 0, 0.0, now_str),
        ("SUPPLIER", "Redington India Ltd", "Manish Joshi", "9820011223", "orders.west@redington.co.in", "Bhiwandi Hub & Ahmedabad Depot", "24AAACR1234F1Z8", 0, 185000.0, now_str),
        ("SUPPLIER", "Ingram Micro India Pvt Ltd", "Suresh Nair", "9819044556", "sales.rajkot@ingrammicro.com", "Changodar Distribution Center, Ahmedabad", "24AAACI5566K1Z2", 0, 94000.0, now_str),
        ("SUPPLIER", "Supertron Electronics Pvt Ltd", "Deepak Roy", "9830077889", "west.supertron@supertron.in", "Prahladnagar, Ahmedabad", "24AAACS7890M1Z5", 0, 52000.0, now_str),
        ("SUPPLIER", "Neoteric Infomatique Ltd", "Amit Trivedi", "9821033445", "corporate@neoteric.com", "C.G. Road, Ahmedabad", "24AAACN3412B1Z7", 0, 0.0, now_str),
        ("SUPPLIER", "Savex Technologies Pvt Ltd", "Kiran Varma", "9822066778", "gujarat.sales@savex.org", "GIDC Vatva, Ahmedabad", "24AAACS9988C1Z9", 0, 38000.0, now_str)
    ]
    cursor.executemany("""
    INSERT INTO parties (party_type, name, contact_person, phone, email, address, gstin, opening_balance, current_balance, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, parties_data)

    # Inquiries & Leads
    inquiries_data = [
        ("INQ-2026-101", "Vortex Digital Agency", "9825123456", "billing@vortexdigital.in", "Kalawad Road, Rajkot", "WORKSTATION", "1x Dell Precision 3660 Workstation + 32GB RAM Upgrade for 3D Studio Max", '{"ram_upgrade":"32GB DDR5","ssd_upgrade":"1TB Gen4 NVMe","antivirus":"1-Year Quick Heal Total Security"}', 135000, "NEW", "WhatsApp Store", "SHOWROOM_VISIT", 3, "Pratik Dave", None, "Client wants live showroom demonstration before buying.", now_str),
        ("INQ-2026-102", "Apex Global Logistics", "9898033445", "accounts@apexlogistic.in", "GIDC Metoda, Rajkot", "LAPTOP", "3x Dell Latitude 5430 Laptops for field billing staff", '{"ram_upgrade":"16GB DDR4","ssd_upgrade":"512GB SSD","warranty":"1-Year Store Warranty"}', 160000, "NEW", "Web Form", "COURIER_DISPATCH", 2, "Hardik Patel", "TRK-BLUEDART-88219", "Delivery via BlueDart courier to Metoda factory.", now_str),
        ("INQ-2026-103", "Shree Ram Engineering", "9724155667", "shreeram.rajkot@yahoo.com", "Aji GIDC Phase II, Rajkot", "SERVER", "1x Dell PowerEdge T350 Tower Server for ERP database & backup", '{"storage_raid":"RAID-1 2x2TB","ups":"1KVA Online UPS"}', 140000, "QUALIFIED", "Phone Call", "SHOWROOM_VISIT", 3, "Pratik Dave", None, "Discussion ongoing on RAID configuration.", now_str),
        ("INQ-2026-104", "Dr. Rohan Bhatt", "9426011223", "dr.bhatt@gmail.com", "Tagore Road, Rajkot", "FIREWALL_NETWORKING", "Clinic Firewall Security (Sophos XGS 116) + 2x WiFi Access Points", '{"firewall":"Sophos XGS 116","license":"1-Year Standard Protection"}', 55000, "NEW", "WhatsApp Store", "SHOWROOM_VISIT", 6, "Ravi Kothari", None, "Wants hospital patient data secured with firewall.", now_str)
    ]
    cursor.executemany("""
    INSERT INTO inquiries (inquiry_number, customer_name, customer_phone, customer_email, customer_address, requirement_type, items_requested, custom_specs, estimated_budget, status, source, fulfillment_mode, assigned_staff_id, assigned_staff_name, delivery_tracking_no, notes, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, inquiries_data)

    # Job Sheets
    jobsheets_data = [
        ("JS-2026-1001", "Kunal Vyas", "9825011223", "kunal@gmail.com", "Amin Marg, Rajkot", "Laptop", "Dell", "Inspiron 15 3511", "SN-DELL-883192", "Laptop, Original 65W Dell Adapter, Bag", "Scratched top lid, hinge tight", "Blue screen watchdog violation and automatic reboot every 15 minutes. Heavy heating.", "Cleaned heatsink, replaced thermal paste with Arctic MX-4. Stress test passed.", "REPAIRED", "PAID_SERVICE", "HARDWARE", 1500, 1200, 500, "Jignesh Mehta", now_str, now_str, None),
        ("JS-2026-1002", "Apex Global Logistics", "9898033445", "accounts@apexlogistic.in", "GIDC Metoda, Rajkot", "Desktop Workstation", "PCWARE Custom", "Ryzen 5 Workstation", "SN-PCW-WKS-1092", "CPU Cabinet only", "Good condition", "System not turning on, no display, RAM beep sound on motherboard.", "Diagnosed bad DDR4 stick in slot 2. Replaced under PCWARE 3-Year Warranty at 0 cost.", "REPAIRED", "FREE_WARRANTY", "HARDWARE", 0, 0, 0, "Vishal Vala", now_str, now_str, None),
        ("JS-2026-1003", "Dr. Rohan Bhatt", "9426011223", "dr.bhatt@gmail.com", "Tagore Road, Rajkot", "Network & Firewall", "Sophos", "XGS 116 Firewall", "SN-SOPHOS-7712", "Firewall unit, power adapter", "Mounted on clinic wall rack", "Ransomware alert in reception computer, need Sophos firewall inspection and Quick Heal clean.", "Configured IPS policies on Sophos XGS, installed Quick Heal on 4 client systems.", "REPAIRED", "AMC_CONTRACT", "NETWORKING_FIREWALL", 0, 0, 0, "Ravi Kothari", now_str, now_str, now_str),
    ]
    cursor.executemany("""
    INSERT INTO job_sheets (job_sheet_number, customer_name, customer_phone, customer_email, customer_address, device_type, device_brand, device_model, device_serial, accessories_received, physical_condition, reported_problem, technician_notes, status, service_tier, service_category, estimated_cost, final_cost, advance_paid, assigned_technician, created_at, updated_at, delivered_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, jobsheets_data)

    # Invoices & Items
    cursor.execute("""
    INSERT INTO invoices (invoice_number, customer_name, customer_phone, customer_email, customer_address, customer_gstin, invoice_date, subtotal, cgst, sgst, igst, discount, grand_total, payment_method, payment_status, fulfillment_mode, notes, created_at)
    VALUES ('INV-2026-0101', 'Vortex Digital Agency', '9825123456', 'billing@vortexdigital.in', 'Kalawad Road, Rajkot, Gujarat', '24AABCV9918K1ZM', '2026-09-01', 52000.0, 4680.0, 4680.0, 0.0, 0.0, 61360.0, 'BANK_TRANSFER', 'PAID', 'SHOWROOM_VISIT', 'High-performance editing workstation parts with serial warranty', ?)
    """, (now_str,))
    inv_id = cursor.lastrowid

    inv_items = [
        (inv_id, 3, "Intel Core i5-13400F Processor", "8471", "SN-INT134-88712", 1, 18500.0, 18.0, 18500.0),
        (inv_id, 16, "Gigabyte B760 Gaming X AX DDR5 ATX Motherboard", "8471", "SN-GIGAB760-9921", 1, 16900.0, 18.0, 16900.0),
        (inv_id, 25, "Corsair Vengeance 32GB (16GBx2) DDR5 5600MHz RAM", "8471", "SN-COR32D5-5512", 1, 9200.0, 18.0, 9200.0),
        (inv_id, 27, "Crucial P3 Plus 1TB PCIe M.2 2280 Gen4 NVMe SSD", "8471", "SN-CRUP3-7718", 1, 5800.0, 18.0, 5800.0),
        (inv_id, 45, "Quick Heal Total Security 1 User 1 Year License Key Box", "8523", "SN-QHTS-112233", 1, 699.0, 18.0, 699.0)
    ]
    cursor.executemany("""
    INSERT INTO invoice_items (invoice_id, product_id, item_name, hsn_code, serial_number, quantity, unit_price, gst_rate, total)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, inv_items)

    # Quotations
    quotes_data = [
        ("QT-2026-0501", 1, "Vortex Digital Agency", "9825123456", "billing@vortexdigital.in", "Kalawad Road, Rajkot", "24AABCV9918K1ZM",
         '[{"product_id":37,"name":"HP Z4 G4 Professional Workstation","price":98000,"quantity":1,"total":98000},{"product_id":25,"name":"Corsair Vengeance 32GB DDR5 RAM Upgrade","price":9200,"quantity":1,"total":9200},{"product_id":47,"name":"Quick Heal Total Security 1 Year","price":699,"quantity":1,"total":699}]',
         107899.0, 19421.82, 127320.82, (datetime.now() + timedelta(days=15)).strftime("%Y-%m-%d"), "CONVERTED", "Approved by CEO Bhavesh Patel", now_str),
    ]
    cursor.executemany("""
    INSERT INTO quotations (quotation_number, inquiry_id, customer_name, customer_phone, customer_email, customer_address, customer_gstin, items_json, subtotal, gst_amount, grand_total, valid_until, status, notes, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, quotes_data)

    # Purchase Orders
    po_data = [
        ("PO-2026-0801", 6, "Redington India Ltd", "9820011223", "24AAACR1234F1Z8", "2026-09-02", "2026-09-05",
         '[{"product_id":1,"name":"Intel Core i3-12100F Processor","price":6800,"quantity":10,"total":68000},{"product_id":2,"name":"Intel Core i5-12400F Processor","price":9800,"quantity":10,"total":98000}]',
         166000.0, 29880.0, 195880.0, "DELIVERED", "PAID", "Delivered to Godown 1 via SafeXpress", now_str)
    ]
    cursor.executemany("""
    INSERT INTO purchase_orders (po_number, supplier_id, supplier_name, supplier_phone, supplier_gstin, order_date, expected_date, items_json, subtotal, gst_amount, total_amount, status, payment_status, notes, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, po_data)

    # Ledger Entries
    ledger_data = [
        (1, "CUSTOMER", "2026-09-01", "SALES_INVOICE", "INV-2026-0101", "Sale of Workstation Components & Antivirus", 61360.0, 0.0, 61360.0, now_str),
        (6, "SUPPLIER", "2026-09-02", "PURCHASE_BILL", "PO-2026-0801", "Purchase of Intel Core i3 & i5 CPUs", 0.0, 195880.0, 195880.0, now_str),
    ]
    cursor.executemany("""
    INSERT INTO ledger_entries (party_id, party_type, entry_date, voucher_type, voucher_no, narration, debit, credit, running_balance, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, ledger_data)

    # AMC Contracts
    amc_data = [
        ("AMC-2026-001", "Apex Global Logistics", "Chetan Shah", "9898033445", "accounts@apexlogistic.in", "GIDC Metoda, Rajkot", 18, 45000.0, "2026-01-01", "2026-12-31", "MONTHLY", "ACTIVE", "18 Desktops, 2 Printers, Sophos Firewall & LAN Maintenance"),
        ("AMC-2026-002", "Dr. Rohan Bhatt Clinic", "Dr. Rohan", "9426011223", "dr.bhatt@gmail.com", "Tagore Road, Rajkot", 6, 18000.0, "2026-04-01", "2027-03-31", "QUARTERLY", "ACTIVE", "6 Laptops, Patient Management Server & Sophos Firewall"),
    ]
    cursor.executemany("""
    INSERT INTO amc_contracts (contract_number, client_name, contact_person, phone, email, address, total_systems, contract_value, start_date, end_date, visit_frequency, status, notes)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, amc_data)

    conn.commit()

def export_seed_json():
    conn = get_connection()
    cursor = conn.cursor()

    def fetch_all(table):
        cursor.execute(f"SELECT * FROM {table}")
        rows = cursor.fetchall()
        return [dict(r) for r in rows]

    data = {
        "products": fetch_all("products"),
        "staff": fetch_all("staff_members"),
        "warehouses": fetch_all("warehouses"),
        "warehouse_stocks": fetch_all("warehouse_stocks"),
        "stock_transfers": fetch_all("stock_transfers"),
        "branches": fetch_all("branches"),
        "inquiries": fetch_all("inquiries"),
        "quotations": fetch_all("quotations"),
        "orders": fetch_all("orders"),
        "purchase_orders": fetch_all("purchase_orders"),
        "parties": fetch_all("parties"),
        "ledger": fetch_all("ledger_entries"),
        "jobsheets": fetch_all("job_sheets"),
        "invoices": fetch_all("invoices"),
        "amc": fetch_all("amc_contracts")
    }

    # Fetch store settings
    cursor.execute("SELECT key, value FROM store_settings")
    settings = {r["key"]: r["value"] for r in cursor.fetchall()}
    data["settings"] = settings

    # Fetch invoice items nested
    for inv in data["invoices"]:
        cursor.execute("SELECT * FROM invoice_items WHERE invoice_id = ?", (inv["id"],))
        inv["items"] = [dict(r) for r in cursor.fetchall()]

    conn.close()

    os.makedirs(os.path.dirname(SEED_JSON_PATH), exist_ok=True)
    with open(SEED_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Exported seed data to {SEED_JSON_PATH} ({len(data['products'])} products, {len(data['staff'])} staff, {len(data['warehouses'])} warehouses)")

if __name__ == "__main__":
    init_db(force_reseed=True)
    export_seed_json()
