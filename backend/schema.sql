-- ==============================================================================
-- PC WARE ENTERPRISE ERP & E-COMMERCE DATABASE SCHEMA
-- Canonical 34-Entity Normalized Relational Schema (PostgreSQL & SQLite Compatible)
-- ==============================================================================

-- 1. Roles
CREATE TABLE IF NOT EXISTS roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(50) NOT NULL UNIQUE,
    slug VARCHAR(50) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Permissions
CREATE TABLE IF NOT EXISTS permissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    module VARCHAR(50) NOT NULL,
    action VARCHAR(50) NOT NULL,
    description TEXT,
    UNIQUE(module, action)
);

-- 3. Role Permissions Mapping
CREATE TABLE IF NOT EXISTS role_permissions (
    role_id INTEGER NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    permission_id INTEGER NOT NULL REFERENCES permissions(id) ON DELETE CASCADE,
    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY(role_id, permission_id)
);

-- 4. Users (Staff & Admin)
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role_id INTEGER NOT NULL REFERENCES roles(id),
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    is_active INTEGER NOT NULL DEFAULT 1,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. Customers (B2C & B2B)
CREATE TABLE IF NOT EXISTS customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    customer_code VARCHAR(50) NOT NULL UNIQUE,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    phone VARCHAR(20) NOT NULL,
    company_name VARCHAR(120),
    gstin VARCHAR(20),
    address_line1 TEXT NOT NULL,
    address_line2 TEXT,
    city VARCHAR(50) NOT NULL,
    state VARCHAR(50) NOT NULL DEFAULT 'Gujarat',
    pincode VARCHAR(10) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 6. Suppliers (IT Asset Disposal / Corporate Liquidation Sources)
CREATE TABLE IF NOT EXISTS suppliers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    supplier_code VARCHAR(50) NOT NULL UNIQUE,
    company_name VARCHAR(120) NOT NULL,
    contact_person VARCHAR(100),
    phone VARCHAR(20) NOT NULL,
    email VARCHAR(100),
    gstin VARCHAR(20),
    address TEXT,
    payment_terms VARCHAR(50) DEFAULT 'Immediate',
    status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK(status IN ('active', 'inactive', 'blacklisted')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 7. Warehouses & Physical Storage Bins
CREATE TABLE IF NOT EXISTS warehouses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code VARCHAR(20) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    location TEXT NOT NULL,
    is_quarantine INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 8. Product Categories
CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    parent_id INTEGER REFERENCES categories(id) ON DELETE SET NULL,
    name VARCHAR(80) NOT NULL,
    slug VARCHAR(80) NOT NULL UNIQUE,
    description TEXT,
    icon VARCHAR(50),
    is_active INTEGER NOT NULL DEFAULT 1
);

-- 9. Brands
CREATE TABLE IF NOT EXISTS brands (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(80) NOT NULL UNIQUE,
    slug VARCHAR(80) NOT NULL UNIQUE,
    logo_url TEXT,
    is_active INTEGER NOT NULL DEFAULT 1
);

-- 10. Products Catalog
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id INTEGER NOT NULL REFERENCES categories(id),
    brand_id INTEGER NOT NULL REFERENCES brands(id),
    sku VARCHAR(60) NOT NULL UNIQUE,
    title VARCHAR(200) NOT NULL,
    slug VARCHAR(200) NOT NULL UNIQUE,
    product_type VARCHAR(30) NOT NULL CHECK(product_type IN ('laptop', 'desktop', 'server', 'workstation', 'component', 'accessory')),
    condition_grade VARCHAR(20) NOT NULL DEFAULT 'Grade A' CHECK(condition_grade IN ('Brand New', 'Grade A', 'Grade B', 'Refurbished')),
    base_price DECIMAL(12,2) NOT NULL,
    selling_price DECIMAL(12,2) NOT NULL,
    discount_price DECIMAL(12,2),
    is_serialized INTEGER NOT NULL DEFAULT 1,
    stock_quantity INTEGER NOT NULL DEFAULT 0,
    warranty_months INTEGER NOT NULL DEFAULT 6,
    description TEXT,
    image_url TEXT,
    is_active INTEGER NOT NULL DEFAULT 1,
    featured INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 11. Parametric Product Specifications (For Compatibility & Filtering)
CREATE TABLE IF NOT EXISTS product_specifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL UNIQUE REFERENCES products(id) ON DELETE CASCADE,
    cpu_model VARCHAR(100),
    cpu_socket VARCHAR(50),
    cpu_generation VARCHAR(50),
    cpu_tdp_watts INTEGER DEFAULT 65,
    ram_type VARCHAR(30),
    ram_gen VARCHAR(20),
    ram_capacity_gb INTEGER DEFAULT 0,
    ram_slots_total INTEGER DEFAULT 2,
    ram_slots_free INTEGER DEFAULT 1,
    max_ram_supported_gb INTEGER DEFAULT 64,
    storage_type VARCHAR(50),
    storage_capacity_gb INTEGER DEFAULT 256,
    storage_interface VARCHAR(40),
    m2_slots INTEGER DEFAULT 1,
    sata_ports INTEGER DEFAULT 2,
    gpu_model VARCHAR(100),
    gpu_vram_gb INTEGER DEFAULT 0,
    gpu_length_mm INTEGER DEFAULT 0,
    psu_wattage INTEGER DEFAULT 65,
    form_factor VARCHAR(40),
    display_size VARCHAR(30),
    battery_health_percentage INTEGER DEFAULT 95,
    os_installed VARCHAR(80) DEFAULT 'Windows 11 Pro',
    raw_specs_json TEXT
);

-- 12. Receiving Records (Supplier Inward Intake)
CREATE TABLE IF NOT EXISTS receiving_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    receiving_number VARCHAR(60) NOT NULL UNIQUE,
    supplier_id INTEGER NOT NULL REFERENCES suppliers(id),
    warehouse_id INTEGER NOT NULL REFERENCES warehouses(id),
    invoice_ref VARCHAR(80),
    item_type VARCHAR(40) NOT NULL,
    brand_id INTEGER REFERENCES brands(id),
    model_name VARCHAR(120) NOT NULL,
    expected_qty INTEGER NOT NULL DEFAULT 1,
    received_qty INTEGER NOT NULL DEFAULT 1,
    purchase_cost_total DECIMAL(12,2) NOT NULL,
    physical_condition_notes TEXT,
    accessories_received TEXT,
    status VARCHAR(30) NOT NULL DEFAULT 'received' CHECK(status IN ('received', 'qc_in_progress', 'partially_inwarded', 'completed', 'rejected')),
    created_by INTEGER REFERENCES users(id),
    received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 13. Serialized Units (Individually Traceable Hardware Units)
CREATE TABLE IF NOT EXISTS serialized_units (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL REFERENCES products(id),
    receiving_id INTEGER REFERENCES receiving_records(id),
    serial_number VARCHAR(100) NOT NULL UNIQUE,
    asset_tag VARCHAR(100),
    purchase_cost DECIMAL(12,2) NOT NULL,
    selling_price DECIMAL(12,2) NOT NULL,
    condition_grade VARCHAR(20) DEFAULT 'Grade A',
    warehouse_id INTEGER NOT NULL REFERENCES warehouses(id),
    location_rack VARCHAR(60) DEFAULT 'Intake Bay',
    current_status VARCHAR(30) NOT NULL DEFAULT 'received' CHECK(current_status IN (
        'received', 'qc_pending', 'qc_testing', 'qc_passed', 'qc_failed', 
        'repair_required', 'retest_required', 'supplier_return', 'scrap', 
        'hold', 'inwarded', 'available', 'reserved', 'sold', 'warranty_hold', 'scrapped'
    )),
    qc_passed_at TIMESTAMP,
    inwarded_at TIMESTAMP,
    sold_at TIMESTAMP,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 14. QC Checklists (Configurable Test Suites)
CREATE TABLE IF NOT EXISTS qc_checklists (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id INTEGER REFERENCES categories(id),
    name VARCHAR(100) NOT NULL,
    checklist_version VARCHAR(20) NOT NULL DEFAULT '1.0',
    items_json TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 15. QC Inspections (Results of hardware testing)
CREATE TABLE IF NOT EXISTS qc_inspections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    serial_unit_id INTEGER NOT NULL REFERENCES serialized_units(id),
    technician_id INTEGER NOT NULL REFERENCES users(id),
    checklist_id INTEGER REFERENCES qc_checklists(id),
    thermal_cpu_c DECIMAL(5,2),
    thermal_gpu_c DECIMAL(5,2),
    battery_health_pct INTEGER,
    overall_result VARCHAR(20) NOT NULL CHECK(overall_result IN ('passed', 'failed', 'needs_rework')),
    failure_reason TEXT,
    remediation_action VARCHAR(50),
    inspector_notes TEXT,
    evidence_photos_json TEXT,
    inspected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 16. QC Inspection Individual Items
CREATE TABLE IF NOT EXISTS qc_inspection_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    qc_inspection_id INTEGER NOT NULL REFERENCES qc_inspections(id) ON DELETE CASCADE,
    test_key VARCHAR(80) NOT NULL,
    test_label VARCHAR(120) NOT NULL,
    status VARCHAR(20) NOT NULL CHECK(status IN ('pass', 'fail', 'not_applicable')),
    technician_notes TEXT
);

-- 17. Inward Records (Formal Inwarding of QC-Passed Units)
CREATE TABLE IF NOT EXISTS inward_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    inward_number VARCHAR(60) NOT NULL UNIQUE,
    serial_unit_id INTEGER NOT NULL UNIQUE REFERENCES serialized_units(id),
    warehouse_id INTEGER NOT NULL REFERENCES warehouses(id),
    rack_bin VARCHAR(60) NOT NULL,
    inwarded_by INTEGER NOT NULL REFERENCES users(id),
    inward_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT
);

-- 18. Inventory Movements & Audit Logs
CREATE TABLE IF NOT EXISTS inventory_movements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    serial_unit_id INTEGER REFERENCES serialized_units(id),
    product_id INTEGER NOT NULL REFERENCES products(id),
    from_status VARCHAR(30) NOT NULL,
    to_status VARCHAR(30) NOT NULL,
    from_warehouse_id INTEGER REFERENCES warehouses(id),
    to_warehouse_id INTEGER REFERENCES warehouses(id),
    reference_type VARCHAR(50) NOT NULL,
    reference_id VARCHAR(50),
    moved_by INTEGER REFERENCES users(id),
    movement_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT
);

-- 19. Hardware Compatibility Rules
CREATE TABLE IF NOT EXISTS compatibility_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    component_type_a VARCHAR(40) NOT NULL,
    component_type_b VARCHAR(40) NOT NULL,
    rule_name VARCHAR(100) NOT NULL,
    rule_attribute VARCHAR(50) NOT NULL,
    match_operator VARCHAR(20) NOT NULL CHECK(match_operator IN ('equals', 'in_list', 'less_or_equal', 'greater_or_equal')),
    expression_json TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1
);

-- 20. Upgrade Options (For Refurbished Laptops & Desktops)
CREATE TABLE IF NOT EXISTS upgrade_options (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    base_product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    upgrade_type VARCHAR(30) NOT NULL CHECK(upgrade_type IN ('ram', 'storage', 'gpu', 'os', 'warranty')),
    title VARCHAR(120) NOT NULL,
    component_product_id INTEGER REFERENCES products(id),
    spec_change VARCHAR(100) NOT NULL,
    additional_cost DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    labour_charge DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    is_compatible INTEGER NOT NULL DEFAULT 1,
    sort_order INTEGER DEFAULT 0
);

-- 21. Custom PC Build Presets
CREATE TABLE IF NOT EXISTS pc_build_presets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title VARCHAR(120) NOT NULL,
    slug VARCHAR(120) NOT NULL UNIQUE,
    use_case VARCHAR(60) NOT NULL,
    budget_tier VARCHAR(40) NOT NULL,
    components_json TEXT NOT NULL,
    base_price DECIMAL(12,2) NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1
);

-- 22. Assembly Orders (Custom PC Builds)
CREATE TABLE IF NOT EXISTS assembly_orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    assembly_number VARCHAR(60) NOT NULL UNIQUE,
    customer_id INTEGER NOT NULL REFERENCES customers(id),
    total_wattage INTEGER NOT NULL DEFAULT 250,
    components_cost DECIMAL(12,2) NOT NULL,
    assembly_labour_charge DECIMAL(10,2) NOT NULL DEFAULT 2500.00,
    tax_amount DECIMAL(10,2) NOT NULL,
    total_price DECIMAL(12,2) NOT NULL,
    compatibility_status VARCHAR(30) NOT NULL DEFAULT 'VERIFIED_COMPATIBLE',
    technician_id INTEGER REFERENCES users(id),
    final_serial_number VARCHAR(80),
    status VARCHAR(30) NOT NULL DEFAULT 'configuration_created' CHECK(status IN (
        'draft', 'configuration_created', 'components_reserved', 'assembly_in_progress', 
        'assembly_completed', 'qc_pending', 'qc_passed', 'qc_failed', 'ready', 'delivered', 'cancelled'
    )),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- 23. Assembly Items (Components Reserved for a Build)
CREATE TABLE IF NOT EXISTS assembly_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    assembly_order_id INTEGER NOT NULL REFERENCES assembly_orders(id) ON DELETE CASCADE,
    product_id INTEGER NOT NULL REFERENCES products(id),
    serial_unit_id INTEGER REFERENCES serialized_units(id),
    component_role VARCHAR(40) NOT NULL,
    unit_cost DECIMAL(10,2) NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL
);

-- 24. Assembly QC Records
CREATE TABLE IF NOT EXISTS assembly_qc_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    assembly_order_id INTEGER NOT NULL REFERENCES assembly_orders(id) ON DELETE CASCADE,
    technician_id INTEGER NOT NULL REFERENCES users(id),
    boot_test INTEGER NOT NULL DEFAULT 0,
    bios_config INTEGER NOT NULL DEFAULT 0,
    cpu_stress_pass INTEGER NOT NULL DEFAULT 0,
    gpu_stress_pass INTEGER NOT NULL DEFAULT 0,
    ram_memtest_pass INTEGER NOT NULL DEFAULT 0,
    storage_smart_pass INTEGER NOT NULL DEFAULT 0,
    cooling_efficiency VARCHAR(30) DEFAULT 'Optimal',
    cable_management_grade VARCHAR(20) DEFAULT 'A',
    overall_status VARCHAR(20) NOT NULL CHECK(overall_status IN ('passed', 'failed')),
    notes TEXT,
    inspected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 25. Referral Codes
CREATE TABLE IF NOT EXISTS referral_codes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    code VARCHAR(40) NOT NULL UNIQUE,
    points_per_referral INTEGER NOT NULL DEFAULT 500,
    min_order_value DECIMAL(10,2) NOT NULL DEFAULT 10000.00,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 26. Referral Relationships
CREATE TABLE IF NOT EXISTS referral_relationships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    referrer_customer_id INTEGER NOT NULL REFERENCES customers(id),
    referred_customer_id INTEGER NOT NULL REFERENCES customers(id),
    referral_code_id INTEGER NOT NULL REFERENCES referral_codes(id),
    status VARCHAR(20) NOT NULL DEFAULT 'qualified' CHECK(status IN ('pending', 'qualified', 'rewarded', 'cancelled', 'expired')),
    first_order_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 27. Immutable Referral Points Ledger
CREATE TABLE IF NOT EXISTS referral_point_ledger (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL REFERENCES customers(id),
    transaction_type VARCHAR(40) NOT NULL CHECK(transaction_type IN ('earned_referral', 'redeemed_discount', 'manual_adjustment', 'points_reversal')),
    points_in INTEGER NOT NULL DEFAULT 0,
    points_out INTEGER NOT NULL DEFAULT 0,
    running_balance INTEGER NOT NULL,
    sales_order_id INTEGER,
    referral_relationship_id INTEGER REFERENCES referral_relationships(id),
    reason TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 28. Sales Quotations
CREATE TABLE IF NOT EXISTS sales_quotations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    quotation_number VARCHAR(60) NOT NULL UNIQUE,
    customer_id INTEGER NOT NULL REFERENCES customers(id),
    subtotal DECIMAL(12,2) NOT NULL,
    tax_amount DECIMAL(12,2) NOT NULL,
    discount_amount DECIMAL(12,2) DEFAULT 0.00,
    grand_total DECIMAL(12,2) NOT NULL,
    valid_until DATE NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK(status IN ('draft', 'active', 'accepted', 'rejected', 'expired')),
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 29. Sales Orders
CREATE TABLE IF NOT EXISTS sales_orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_number VARCHAR(60) NOT NULL UNIQUE,
    customer_id INTEGER NOT NULL REFERENCES customers(id),
    order_type VARCHAR(30) NOT NULL DEFAULT 'standard' CHECK(order_type IN ('standard', 'modified_refurb', 'custom_pc', 'wholesale')),
    subtotal DECIMAL(12,2) NOT NULL,
    upgrade_total DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    assembly_total DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    tax_amount DECIMAL(12,2) NOT NULL,
    discount_amount DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    grand_total DECIMAL(12,2) NOT NULL,
    payment_status VARCHAR(20) NOT NULL DEFAULT 'unpaid' CHECK(payment_status IN ('unpaid', 'partially_paid', 'paid', 'refunded')),
    fulfillment_status VARCHAR(30) NOT NULL DEFAULT 'pending' CHECK(fulfillment_status IN ('pending', 'processing', 'assembled', 'shipped', 'delivered', 'cancelled')),
    applied_referral_code VARCHAR(40),
    referral_points_redeemed INTEGER DEFAULT 0,
    shipping_address TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 30. Sales Order Items
CREATE TABLE IF NOT EXISTS sales_order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sales_order_id INTEGER NOT NULL REFERENCES sales_orders(id) ON DELETE CASCADE,
    product_id INTEGER NOT NULL REFERENCES products(id),
    serial_unit_id INTEGER REFERENCES serialized_units(id),
    assembly_order_id INTEGER REFERENCES assembly_orders(id),
    unit_price DECIMAL(12,2) NOT NULL,
    upgrades_json TEXT,
    quantity INTEGER NOT NULL DEFAULT 1,
    total_price DECIMAL(12,2) NOT NULL
);

-- 31. GST Compliant Invoices
CREATE TABLE IF NOT EXISTS invoices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_number VARCHAR(60) NOT NULL UNIQUE,
    sales_order_id INTEGER NOT NULL REFERENCES sales_orders(id),
    customer_id INTEGER NOT NULL REFERENCES customers(id),
    hsn_sac_code VARCHAR(20) NOT NULL DEFAULT '8471',
    cgst_rate DECIMAL(5,2) NOT NULL DEFAULT 9.00,
    cgst_amount DECIMAL(10,2) NOT NULL,
    sgst_rate DECIMAL(5,2) NOT NULL DEFAULT 9.00,
    sgst_amount DECIMAL(10,2) NOT NULL,
    igst_rate DECIMAL(5,2) NOT NULL DEFAULT 0.00,
    igst_amount DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    total_tax DECIMAL(10,2) NOT NULL,
    grand_total DECIMAL(12,2) NOT NULL,
    invoice_date DATE NOT NULL,
    payment_status VARCHAR(20) NOT NULL DEFAULT 'unpaid' CHECK(payment_status IN ('unpaid', 'paid', 'cancelled'))
);

-- 32. Payments
CREATE TABLE IF NOT EXISTS payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_id INTEGER NOT NULL REFERENCES invoices(id) ON DELETE CASCADE,
    payment_method VARCHAR(40) NOT NULL CHECK(payment_method IN ('upi', 'bank_transfer', 'cash', 'card', 'cheque')),
    transaction_reference VARCHAR(100),
    amount_paid DECIMAL(12,2) NOT NULL,
    payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT
);

-- 33. Warranties & Warranty Claims
CREATE TABLE IF NOT EXISTS warranties (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    serial_unit_id INTEGER NOT NULL REFERENCES serialized_units(id),
    sales_order_item_id INTEGER REFERENCES sales_order_items(id),
    customer_id INTEGER NOT NULL REFERENCES customers(id),
    warranty_months INTEGER NOT NULL DEFAULT 6,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK(status IN ('active', 'expired', 'claimed', 'voided'))
);

CREATE TABLE IF NOT EXISTS warranty_claims (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    claim_number VARCHAR(60) NOT NULL UNIQUE,
    warranty_id INTEGER NOT NULL REFERENCES warranties(id),
    customer_id INTEGER NOT NULL REFERENCES customers(id),
    reported_issue TEXT NOT NULL,
    claim_status VARCHAR(30) NOT NULL DEFAULT 'pending' CHECK(claim_status IN ('pending', 'under_review', 'approved', 'rejected', 'resolved')),
    resolution_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 34. In-Shop Repair Job Sheets & Service Tickets
CREATE TABLE IF NOT EXISTS repair_tickets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_number VARCHAR(60) NOT NULL UNIQUE,
    customer_id INTEGER NOT NULL REFERENCES customers(id),
    serial_unit_id INTEGER REFERENCES serialized_units(id),
    device_brand_model VARCHAR(120) NOT NULL,
    serial_or_imei VARCHAR(80),
    fault_description TEXT NOT NULL,
    accessories_included TEXT,
    technician_id INTEGER REFERENCES users(id),
    estimated_cost DECIMAL(10,2) DEFAULT 0.00,
    final_cost DECIMAL(10,2) DEFAULT 0.00,
    repair_status VARCHAR(30) NOT NULL DEFAULT 'received' CHECK(repair_status IN (
        'received', 'diagnosing', 'waiting_approval', 'in_repair', 'repaired', 'delivered', 'cancelled'
    )),
    diagnostic_report TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    closed_at TIMESTAMP
);

-- 35. Audit Logs (System Action History)
CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES users(id),
    action VARCHAR(80) NOT NULL,
    entity_type VARCHAR(60) NOT NULL,
    entity_id VARCHAR(60),
    old_value_json TEXT,
    new_value_json TEXT,
    ip_address VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Performance Indexes
CREATE INDEX IF NOT EXISTS idx_serialized_units_sn ON serialized_units(serial_number);
CREATE INDEX IF NOT EXISTS idx_serialized_units_status ON serialized_units(current_status);
CREATE INDEX IF NOT EXISTS idx_products_slug ON products(slug);
CREATE INDEX IF NOT EXISTS idx_products_sku ON products(sku);
CREATE INDEX IF NOT EXISTS idx_qc_inspections_serial ON qc_inspections(serial_unit_id);
CREATE INDEX IF NOT EXISTS idx_inventory_movements_serial ON inventory_movements(serial_unit_id);
CREATE INDEX IF NOT EXISTS idx_sales_orders_customer ON sales_orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_invoices_order ON invoices(sales_order_id);
CREATE INDEX IF NOT EXISTS idx_referral_ledger_customer ON referral_point_ledger(customer_id);
CREATE INDEX IF NOT EXISTS idx_repair_tickets_num ON repair_tickets(ticket_number);

-- ==============================================================================
-- 36. DOUBLE-ENTRY ACCOUNTING & MATERIAL MANAGEMENT EXTENSIONS
-- ==============================================================================

-- 36. Chart of Accounts (Hierarchical 5-Digit Standard)
CREATE TABLE IF NOT EXISTS accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code VARCHAR(20) NOT NULL UNIQUE,
    name VARCHAR(120) NOT NULL,
    type VARCHAR(30) NOT NULL CHECK(type IN ('ASSET', 'LIABILITY', 'EQUITY', 'REVENUE', 'EXPENSE', 'COGS')),
    subtype VARCHAR(60),
    balance DECIMAL(14,2) NOT NULL DEFAULT 0.00,
    is_reconciled INTEGER NOT NULL DEFAULT 1,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 37. Accounting Periods & Fiscal Calendar
CREATE TABLE IF NOT EXISTS accounting_periods (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fiscal_year VARCHAR(20) NOT NULL,
    period_name VARCHAR(40) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    is_closed INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 38. General Ledger Journal Entries
CREATE TABLE IF NOT EXISTS journals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_number VARCHAR(60) NOT NULL UNIQUE,
    posting_date DATE NOT NULL,
    reference_type VARCHAR(50) NOT NULL,
    reference_id VARCHAR(60),
    memo TEXT NOT NULL,
    total_debit DECIMAL(14,2) NOT NULL,
    total_credit DECIMAL(14,2) NOT NULL,
    is_posted INTEGER NOT NULL DEFAULT 1,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 39. General Ledger Journal Lines (Double-Entry Invariant: Sum(Dr) = Sum(Cr))
CREATE TABLE IF NOT EXISTS journal_lines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    journal_id INTEGER NOT NULL REFERENCES journals(id) ON DELETE CASCADE,
    account_id INTEGER NOT NULL REFERENCES accounts(id),
    debit DECIMAL(14,2) NOT NULL DEFAULT 0.00 CHECK(debit >= 0),
    credit DECIMAL(14,2) NOT NULL DEFAULT 0.00 CHECK(credit >= 0),
    line_memo VARCHAR(255)
);

-- 40. Tax Rates (Indian GST Engine & HSN Classification)
CREATE TABLE IF NOT EXISTS tax_rates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(60) NOT NULL,
    hsn_code VARCHAR(20) NOT NULL,
    cgst_rate DECIMAL(5,2) NOT NULL DEFAULT 9.00,
    sgst_rate DECIMAL(5,2) NOT NULL DEFAULT 9.00,
    igst_rate DECIMAL(5,2) NOT NULL DEFAULT 18.00,
    is_active INTEGER NOT NULL DEFAULT 1
);

-- 41. Refurbishment Work Orders (Closed-loop cost accumulation)
CREATE TABLE IF NOT EXISTS refurb_work_orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    wo_number VARCHAR(60) NOT NULL UNIQUE,
    serial_unit_id INTEGER NOT NULL REFERENCES serialized_units(id),
    technician_id INTEGER REFERENCES users(id),
    status VARCHAR(30) NOT NULL DEFAULT 'open' CHECK(status IN ('open', 'in_progress', 'parts_issued', 'qc_pending', 'completed', 'cancelled')),
    initial_qc_inspection_id INTEGER REFERENCES qc_inspections(id),
    total_part_cost DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    total_labour_cost DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    total_overhead_cost DECIMAL(12,2) NOT NULL DEFAULT 300.00,
    total_capitalized_cost DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    notes TEXT,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- 42. Work Order Parts Consumption (Requisitioned component tracking)
CREATE TABLE IF NOT EXISTS work_order_parts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    work_order_id INTEGER NOT NULL REFERENCES refurb_work_orders(id) ON DELETE CASCADE,
    component_product_id INTEGER NOT NULL REFERENCES products(id),
    quantity INTEGER NOT NULL DEFAULT 1,
    unit_cost DECIMAL(12,2) NOT NULL,
    total_cost DECIMAL(12,2) NOT NULL,
    issued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 43. Work Order Direct Labour Logging
CREATE TABLE IF NOT EXISTS work_order_labour (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    work_order_id INTEGER NOT NULL REFERENCES refurb_work_orders(id) ON DELETE CASCADE,
    technician_id INTEGER NOT NULL REFERENCES users(id),
    hours_spent DECIMAL(5,2) NOT NULL,
    hourly_rate DECIMAL(10,2) NOT NULL DEFAULT 350.00,
    total_labour_cost DECIMAL(10,2) NOT NULL,
    notes TEXT,
    logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 44. Bill of Materials (BOM) for Assembly & Custom PC Workstations
CREATE TABLE IF NOT EXISTS boms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER REFERENCES products(id),
    name VARCHAR(120) NOT NULL,
    version VARCHAR(20) NOT NULL DEFAULT '1.0',
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 45. BOM Items (Standard component recipe)
CREATE TABLE IF NOT EXISTS bom_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bom_id INTEGER NOT NULL REFERENCES boms(id) ON DELETE CASCADE,
    component_product_id INTEGER NOT NULL REFERENCES products(id),
    quantity INTEGER NOT NULL DEFAULT 1,
    is_mandatory INTEGER NOT NULL DEFAULT 1
);

-- Accounting & Material Indexes
CREATE INDEX IF NOT EXISTS idx_accounts_code ON accounts(code);
CREATE INDEX IF NOT EXISTS idx_journals_entry_num ON journals(entry_number);
CREATE INDEX IF NOT EXISTS idx_journal_lines_journal ON journal_lines(journal_id);
CREATE INDEX IF NOT EXISTS idx_journal_lines_account ON journal_lines(account_id);
CREATE INDEX IF NOT EXISTS idx_refurb_wo_serial ON refurb_work_orders(serial_unit_id);
CREATE INDEX IF NOT EXISTS idx_refurb_wo_status ON refurb_work_orders(status);
CREATE INDEX IF NOT EXISTS idx_work_order_parts_wo ON work_order_parts(work_order_id);

