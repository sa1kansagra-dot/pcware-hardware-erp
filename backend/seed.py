# Seed generator
import os
import sys
sys.path.insert(0, os.path.abspath("backend"))
import database as db
import hashlib
import json

def hash_pw(password: str) -> str:
    salt = b"pcware_salt_2026_secure"
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)
    return key.hex()

def seed_all():
    db.init_db(force_reset=True)
    with db.get_db() as conn:
        c = conn.cursor()
        
        # 1. Roles
        roles_data = [
            (1, "Super Admin", "super_admin", "Complete system administration and financial authorization"),
            (2, "Operations Lead", "operations_lead", "Inventory, procurement, pricing, and fulfillment management"),
            (3, "Inventory Specialist", "inventory_specialist", "Receiving intake, warehouse binning, and stock movements"),
            (4, "QC Technician", "qc_technician", "Multi-point hardware inspection, diagnostic testing, and pass/fail verdicts"),
            (5, "Assembly Engineer", "assembly_engineer", "Custom PC building, upgrades modification, and assembly stress testing"),
            (6, "Sales Executive", "sales_executive", "Customer quotations, sales orders, GST billing, and referral tracking"),
            (7, "RMA Technician", "rma_technician", "Warranty claims, component-level repairs, and diagnostic job sheets"),
            (8, "Customer", "customer", "Public website customer and B2B registered client")
        ]
        c.executemany("INSERT INTO roles (id, name, slug, description) VALUES (?, ?, ?, ?)", roles_data)
        
        # 2. Permissions
        perms_data = [
            ("catalog", "view", "View products and categories"),
            ("catalog", "manage", "Create, edit, and delete products and specs"),
            ("refurbishment", "receive", "Create intake records and generate serials"),
            ("refurbishment", "qc_inspect", "Perform and record QC testing"),
            ("refurbishment", "inward", "Inward QC-passed units into sellable inventory"),
            ("inventory", "view", "Search and view serialized inventory"),
            ("inventory", "move", "Transfer units between warehouse locations"),
            ("compatibility", "manage", "Manage compatibility rules"),
            ("assembly", "build", "Build and test custom PC orders"),
            ("sales", "order", "Create and process sales orders"),
            ("sales", "invoice", "Issue official GST tax invoices"),
            ("rma", "manage", "Manage warranty claims and repair job sheets"),
            ("referrals", "manage", "Manage referral program rules and ledger"),
            ("reports", "view", "View financial and inventory analytics")
        ]
        c.executemany("INSERT INTO permissions (module, action, description) VALUES (?, ?, ?)", perms_data)
        
        for p_id in range(1, len(perms_data) + 1):
            c.execute("INSERT INTO role_permissions (role_id, permission_id) VALUES (1, ?)", (p_id,))
            
        for p_id in [1, 4, 6]:
            c.execute("INSERT INTO role_permissions (role_id, permission_id) VALUES (4, ?)", (p_id,))
            
        for p_id in [1, 3, 5, 6, 7]:
            c.execute("INSERT INTO role_permissions (role_id, permission_id) VALUES (3, ?)", (p_id,))

        # 4. Users
        users_data = [
            (1, 1, "admin", "admin@pcware.in", hash_pw("Admin@123"), "Executive Admin", "+91 94261 83934", 1),
            (2, 2, "ops_lead", "ops@pcware.in", hash_pw("Ops@123"), "Hareshbhai Patel", "+91 80007 80704", 1),
            (3, 4, "tech_qc", "qc@pcware.in", hash_pw("Tech@123"), "Keval Joshi (Lead QC)", "+91 70167 37271", 1),
            (4, 5, "tech_asm", "assembly@pcware.in", hash_pw("Tech@123"), "Sanjay Varma (System Builder)", "+91 98250 11223", 1),
            (5, 6, "sales_lead", "sales@pcware.in", hash_pw("Sales@123"), "Pooja Trivedi", "+91 94088 55443", 1),
            (6, 7, "rma_lead", "rma@pcware.in", hash_pw("Tech@123"), "Amit Parmar (RMA Tech)", "+91 99790 33441", 1),
            (7, 8, "customer_raj", "raj.patel@gmail.com", hash_pw("Customer@123"), "Rajesh Patel", "+91 98980 12345", 1)
        ]
        c.executemany("INSERT INTO users (id, role_id, username, email, password_hash, full_name, phone, is_active) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", users_data)
        
        # 5. Customers
        customers_data = [
            (1, 7, "CUST-2026-001", "Rajesh Patel", "raj.patel@gmail.com", "+91 98980 12345", "Patel Infotech Solutions", "24AAECP1234F1Z5", "SF-12, Speedwell Complex", "Ambika Twp", "Rajkot", "Gujarat", "360005"),
            (2, None, "CUST-2026-002", "Deepak Solanki", "deepak@solankidesigns.in", "+91 97240 55667", "Solanki Architecture Studio", "24ABCDE5678G2Z1", "Near Indira Circle, 150ft Ring Rd", None, "Rajkot", "Gujarat", "360004"),
            (3, None, "CUST-2026-003", "Mehul Mehta", "mehul.mehta@yahoo.com", "+91 94280 88990", None, None, "4, Krishna Park Society", "Mota Mava", "Rajkot", "Gujarat", "360005")
        ]
        c.executemany("INSERT INTO customers (id, user_id, customer_code, full_name, email, phone, company_name, gstin, address_line1, address_line2, city, state, pincode) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", customers_data)
        
        # 6. Suppliers
        suppliers_data = [
            (1, "SUP-2026-01", "Dell Corporate Remarketing Direct", "Vipin Sharma", "+91 80400 11223", "vipin.s@dellremarketing.in", "29AAACD1337H1Z2", "Dell Tech Center, Domlur, Bengaluru", "Net 15", "active"),
            (2, "SUP-2026-02", "HP Enterprise Asset Recovery Services", "Sunil Nair", "+91 80234 55667", "sunil.n@hpar.in", "29AAACH1889M1Z8", "Whitefield Global IT Park, Bengaluru", "Immediate", "active"),
            (3, "SUP-2026-03", "Global IT Liquidation Hub", "Ramesh Chawla", "+91 22400 77889", "ramesh@globalitliquidators.com", "27AABCG4567P1Z3", "Andheri East SEZ, Mumbai", "Net 7", "active")
        ]
        c.executemany("INSERT INTO suppliers (id, supplier_code, company_name, contact_person, phone, email, gstin, address, payment_terms, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", suppliers_data)
        
        # 7. Warehouses
        warehouses_data = [
            (1, "WH-MAIN", "PC Ware Main Showroom & Storage", "SF 47-48 Suvarnabhumi Complex, Mota Mava, Rajkot", 0),
            (2, "WH-LAB", "QC Diagnostic Lab & Cleanroom", "SF 49 Cleanroom Suite, Suvarnabhumi Complex, Rajkot", 0),
            (3, "WH-QUARANTINE", "QC Quarantine & Diagnostic Holding", "SF 49 Bay-C Quarantine Section, Rajkot", 1)
        ]
        c.executemany("INSERT INTO warehouses (id, code, name, location, is_quarantine) VALUES (?, ?, ?, ?, ?)", warehouses_data)
        
        # 8. Categories
        categories_data = [
            (1, None, "Refurbished Laptops", "laptops", "Commercial business, ultrabooks, and gaming laptops", "laptop", 1),
            (2, None, "Refurbished Desktops", "desktops", "Enterprise slim PCs, towers, and mini workstations", "desktop", 1),
            (3, None, "Refurbished Servers", "servers", "Enterprise rackmount and tower server nodes", "server", 1),
            (4, None, "Refurbished Workstations", "workstations", "High-performance CAD, 3D rendering and ECC workstations", "cpu", 1),
            (5, None, "Processors (CPUs)", "processors", "Intel Core and AMD Ryzen desktop & server CPUs", "microchip", 1),
            (6, None, "Motherboards", "motherboards", "LGA1700, AM5, AM4, and Server boards", "circuit-board", 1),
            (7, None, "Memory (RAM)", "ram", "DDR4, DDR5, DIMM and SODIMM memory modules", "memory", 1),
            (8, None, "Storage (SSD/HDD)", "storage", "NVMe PCIe Gen4/Gen3 and SATA solid state drives", "hard-drive", 1),
            (9, None, "Graphics Cards", "gpus", "NVIDIA RTX and AMD Radeon graphics cards", "monitor", 1),
            (10, None, "Power Supplies", "psus", "80+ Bronze, Gold, and Platinum power supply units", "zap", 1),
            (11, None, "Cabinets & Cases", "cabinets", "Airflow and tempered glass mid-tower and full-tower cases", "box", 1),
            (12, None, "Cooling Solutions", "cooling", "Air coolers and 240mm/360mm AIO liquid coolers", "wind", 1)
        ]
        c.executemany("INSERT INTO categories (id, parent_id, name, slug, description, icon, is_active) VALUES (?, ?, ?, ?, ?, ?, ?)", categories_data)
        
        # 9. Brands
        brands_data = [
            (1, "Dell", "dell", "/static/images/brands/dell.png", 1),
            (2, "HP", "hp", "/static/images/brands/hp.png", 1),
            (3, "Lenovo", "lenovo", "/static/images/brands/lenovo.png", 1),
            (4, "Apple", "apple", "/static/images/brands/apple.png", 1),
            (5, "Intel", "intel", "/static/images/brands/intel.png", 1),
            (6, "AMD", "amd", "/static/images/brands/amd.png", 1),
            (7, "ASUS", "asus", "/static/images/brands/asus.png", 1),
            (8, "Crucial", "crucial", "/static/images/brands/crucial.png", 1),
            (9, "Kingston", "kingston", "/static/images/brands/kingston.png", 1),
            (10, "Samsung", "samsung", "/static/images/brands/samsung.png", 1),
            (11, "DeepCool", "deepcool", "/static/images/brands/deepcool.png", 1),
            (12, "Corsair", "corsair", "/static/images/brands/corsair.png", 1),
            (13, "ZOTAC", "zotac", "/static/images/brands/zotac.png", 1)
        ]
        c.executemany("INSERT INTO brands (id, name, slug, logo_url, is_active) VALUES (?, ?, ?, ?, ?)", brands_data)
        
        # 10. Products Catalog
        products_data = [
            (1, 1, 1, "PCW-LT-DEL-5420", "Dell Latitude 5420 (i5 11th Gen / 8GB / 256GB NVMe)", "dell-latitude-5420-i5", "laptop", "Grade A", 21000.0, 24500.0, 23500.0, 1, 12, 12, "Enterprise 14-inch commercial laptop with Intel Iris Xe, backlit keyboard, FHD display, and military-grade durability. Tested with 24-point QC.", "https://images.unsplash.com/photo-1588872657578-7efd1f1555ed?w=800", 1, 1),
            (2, 1, 3, "PCW-LT-LEN-T14G2", "Lenovo ThinkPad T14 Gen 2 (Ryzen 5 Pro 5650U / 16GB / 512GB NVMe)", "lenovo-thinkpad-t14-gen2", "laptop", "Grade A", 26000.0, 29999.0, 28999.0, 1, 8, 12, "Legendary ThinkPad ergonomics with AMD Ryzen 6-core processing, spill-resistant keyboard, and dual thermal heat-pipes.", "https://images.unsplash.com/photo-1541807084-5c52b6b3adef?w=800", 1, 1),
            (3, 1, 2, "PCW-LT-HP-840G8", "HP EliteBook 840 G8 (i7 11th Gen / 16GB / 512GB NVMe / FHD)", "hp-elitebook-840-g8-i7", "laptop", "Grade A", 30000.0, 34500.0, 33500.0, 1, 5, 12, "Precision aluminum unibody, Bang & Olufsen tuned audio, Intel Core i7 performance with Wi-Fi 6.", "https://images.unsplash.com/photo-1525547719571-a2d4ac8945e2?w=800", 1, 1),
            (4, 2, 1, "PCW-DT-DEL-7080SFF", "Dell OptiPlex 7080 SFF Desktop (i7 10th Gen / 16GB / 512GB NVMe)", "dell-optiplex-7080-sff", "desktop", "Grade A", 22000.0, 26500.0, 25500.0, 1, 15, 12, "Compact Small Form Factor workstation desktop supporting up to 3 4K monitors and high-speed PCIe NVMe.", "https://images.unsplash.com/photo-1593640408182-31c70c8268f5?w=800", 1, 1),
            (5, 3, 1, "PCW-SV-DEL-R740", "Dell PowerEdge R740 2U Rack Server (2x Xeon Silver 4210 / 64GB / 4x 1.2TB SAS)", "dell-poweredge-r740-2u", "server", "Grade A", 95000.0, 115000.0, 112000.0, 1, 3, 24, "Dual-socket 2U enterprise virtualization workhorse with redundant 750W Titanium PSUs and iDRAC9 Enterprise remote management.", "https://images.unsplash.com/photo-1558494949-ef010cbdcc31?w=800", 1, 1),
            (6, 4, 1, "PCW-WS-DEL-5820", "Dell Precision 5820 Tower (Xeon W-2223 / 32GB ECC / 1TB NVMe / RTX 4000)", "dell-precision-5820-workstation", "workstation", "Grade A", 62000.0, 74500.0, 72000.0, 1, 4, 12, "ISV-Certified engineering workstation with ECC registered memory and Nvidia Quadro ray-tracing GPU for SolidWorks and Blender.", "https://images.unsplash.com/photo-1587202372775-e229f172b9d7?w=800", 1, 1),
            (7, 5, 6, "CMP-CPU-AMD-7600X", "AMD Ryzen 5 7600X Desktop Processor (6C/12T, AM5)", "amd-ryzen-5-7600x", "component", "Brand New", 18500.0, 20999.0, None, 0, 20, 36, "6 Cores, 12 Threads, 4.7GHz Base, 5.3GHz Boost, Socket AM5, 105W TDP.", "https://images.unsplash.com/photo-1591799264318-7e6ef8ddb7ea?w=800", 1, 0),
            (8, 5, 6, "CMP-CPU-AMD-7800X3D", "AMD Ryzen 7 7800X3D Gaming Processor (8C/16T, AM5)", "amd-ryzen-7-7800x3d", "component", "Brand New", 34000.0, 38500.0, None, 0, 10, 36, "World best gaming CPU with 3D V-Cache, 120W TDP, AM5 Socket.", "https://images.unsplash.com/photo-1591799264318-7e6ef8ddb7ea?w=800", 1, 0),
            (9, 5, 5, "CMP-CPU-INT-14600K", "Intel Core i5-14600K Desktop Processor (14C/20T, LGA1700)", "intel-core-i5-14600k", "component", "Brand New", 26500.0, 29500.0, None, 0, 15, 36, "14 Cores (6P + 8E), Up to 5.3GHz, LGA1700 Socket, 125W Base TDP.", "https://images.unsplash.com/photo-1555680202-c86f0e12f086?w=800", 1, 0),
            (10, 6, 7, "CMP-MB-ASU-B650P", "ASUS TUF Gaming B650-PLUS WiFi Motherboard (AM5, DDR5, ATX)", "asus-tuf-b650-plus-wifi", "component", "Brand New", 19500.0, 22400.0, None, 0, 12, 36, "Socket AM5, DDR5 6400MHz+, 3x M.2 NVMe, PCIe 5.0, 2.5Gb LAN, WiFi 6.", "https://images.unsplash.com/photo-1518770660439-4636190af475?w=800", 1, 0),
            (11, 6, 7, "CMP-MB-MSI-B760MA", "MSI PRO B760M-A WiFi Motherboard (LGA1700, DDR5, mATX)", "msi-pro-b760m-a-wifi", "component", "Brand New", 14200.0, 16500.0, None, 0, 14, 36, "LGA1700 Socket, DDR5 up to 128GB, 2x M.2 Gen4 slots, Micro-ATX.", "https://images.unsplash.com/photo-1518770660439-4636190af475?w=800", 1, 0),
            (12, 7, 9, "CMP-RAM-KNG-D5-16G", "Kingston Fury Beast 16GB DDR5 5200MHz Desktop RAM (DIMM)", "kingston-fury-16gb-ddr5", "component", "Brand New", 4200.0, 4999.0, None, 0, 30, 36, "High-performance DDR5 desktop module with aluminum heat spreader.", "https://images.unsplash.com/photo-1562976540-1502c2145186?w=800", 1, 0),
            (13, 7, 8, "CMP-RAM-CRU-D4-16G", "Crucial 16GB DDR4 3200MHz Desktop RAM (DIMM)", "crucial-16gb-ddr4-3200-dimm", "component", "Brand New", 2400.0, 2999.0, None, 0, 40, 36, "Reliable DDR4 desktop memory module with lifetime warranty.", "https://images.unsplash.com/photo-1562976540-1502c2145186?w=800", 1, 0),
            (14, 7, 10, "CMP-RAM-SAM-D4-16G-SO", "Samsung 16GB DDR4 3200MHz Laptop RAM (SODIMM)", "samsung-16gb-ddr4-sodimm", "component", "Grade A", 1600.0, 2100.0, None, 0, 50, 12, "Low-voltage 1.2V DDR4 SODIMM for Dell, HP, Lenovo refurbished laptop upgrades.", "https://images.unsplash.com/photo-1562976540-1502c2145186?w=800", 1, 0),
            (15, 8, 10, "CMP-SSD-SAM-980P-1TB", "Samsung 980 Pro 1TB PCIe 4.0 NVMe M.2 SSD", "samsung-980-pro-1tb-nvme", "component", "Brand New", 7500.0, 8900.0, None, 0, 25, 60, "Blazing 7,000 MB/s sequential read, Gen4 M.2 2280 form factor.", "https://images.unsplash.com/photo-1597872200969-2b65d56bd16b?w=800", 1, 0),
            (16, 8, 8, "CMP-SSD-CRU-P3-500G", "Crucial P3 Plus 500GB PCIe 4.0 NVMe M.2 SSD", "crucial-p3-plus-500gb-nvme", "component", "Brand New", 3100.0, 3700.0, None, 0, 40, 36, "500GB M.2 2280 NVMe SSD with 5000 MB/s speed.", "https://images.unsplash.com/photo-1597872200969-2b65d56bd16b?w=800", 1, 0),
            (17, 9, 7, "CMP-GPU-ASU-4070S", "ASUS Dual GeForce RTX 4070 Super 12GB GDDR6X", "asus-dual-rtx-4070-super-12gb", "component", "Brand New", 55000.0, 62500.0, None, 0, 8, 36, "Dual-fan compact 267mm design, DLSS 3, 220W TDP, 12GB GDDR6X.", "https://images.unsplash.com/photo-1587202372775-e229f172b9d7?w=800", 1, 0),
            (18, 10, 12, "CMP-PSU-COR-RM850E", "Corsair RM850e 850W 80+ Gold Fully Modular ATX PSU", "corsair-rm850e-850w-gold", "component", "Brand New", 9400.0, 10800.0, None, 0, 15, 60, "ATX 3.0 & PCIe 5.0 ready, 105C Japanese capacitors, zero RPM fan mode.", "https://images.unsplash.com/photo-1587202372634-32705e3bf49c?w=800", 1, 0),
            (19, 11, 11, "CMP-CAB-DEP-CC560", "DeepCool CC560 V2 Airflow Mid-Tower Cabinet (4 LED Fans)", "deepcool-cc560-v2-cabinet", "component", "Brand New", 3600.0, 4299.0, None, 0, 18, 12, "High-airflow mesh front panel, supports up to ATX motherboards, 370mm GPU clearance.", "https://images.unsplash.com/photo-1587202372583-49330a15584d?w=800", 1, 0),
            (20, 12, 11, "CMP-CLR-DEP-AK400", "DeepCool AK400 Zero Dark High-Efficiency CPU Cooler", "deepcool-ak400-cpu-cooler", "component", "Brand New", 2100.0, 2599.0, None, 0, 22, 36, "Direct touch heat pipes, 220W cooling capacity, fits AM5 and LGA1700.", "https://images.unsplash.com/photo-1587202372775-e229f172b9d7?w=800", 1, 0)
        ]
        c.executemany("INSERT INTO products (id, category_id, brand_id, sku, title, slug, product_type, condition_grade, base_price, selling_price, discount_price, is_serialized, stock_quantity, warranty_months, description, image_url, is_active, featured) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", products_data)
        
        # 11. Parametric Product Specifications
        specs_data = [
            (1, 1, "Intel Core i5-1135G7", "BGA1449", "11th Gen", 28, "SODIMM", "DDR4", 8, 2, 1, 64, "NVMe SSD", 256, "PCIe Gen 3.0 x4", 1, 0, "Intel Iris Xe Graphics", 0, 0, 65, "Laptop", "14.0 inch FHD Anti-Glare", 96, "Windows 11 Pro", json.dumps({"ports": ["2x Thunderbolt 4", "2x USB 3.2 Gen 1", "1x HDMI 2.0", "RJ-45 LAN", "uSD 4.0 Card Reader"], "weight_kg": 1.40})),
            (2, 2, "AMD Ryzen 5 Pro 5650U", "FP6", "Zen 3", 15, "DDR4", "DDR4", 16, 2, 1, 48, "NVMe SSD", 512, "PCIe Gen 3.0 x4", 1, 0, "AMD Radeon Vega 7", 0, 0, 65, "Laptop", "14.0 inch FHD IPS", 98, "Windows 11 Pro", json.dumps({"ports": ["2x USB-C", "2x USB 3.2", "HDMI 2.0", "Ethernet"], "weight_kg": 1.53})),
            (3, 3, "Intel Core i7-1165G7", "BGA1449", "11th Gen", 28, "SODIMM", "DDR4", 16, 2, 0, 64, "NVMe SSD", 512, "PCIe Gen 3.0 x4", 1, 0, "Intel Iris Xe Graphics", 0, 0, 65, "Laptop", "14.0 inch FHD IPS", 94, "Windows 11 Pro", json.dumps({"audio": "Bang & Olufsen", "weight_kg": 1.35})),
            (4, 4, "Intel Core i7-10700", "LGA1200", "10th Gen", 65, "DIMM", "DDR4", 16, 4, 2, 128, "NVMe SSD", 512, "PCIe Gen 3.0 x4", 2, 3, "Intel UHD 630", 0, 0, 200, "SFF Desktop", None, None, "Windows 11 Pro", json.dumps({"form_factor": "SFF", "expansion_slots": "1x PCIe x16, 1x PCIe x4"})),
            (5, 5, "2x Intel Xeon Silver 4210", "LGA3647", "Cascade Lake", 170, "ECC Registered", "DDR4", 64, 24, 20, 3072, "SAS 10K RPM", 4800, "SAS 12Gbps", 4, 8, "Matrox G200eR2", 0, 0, 750, "2U Rack Server", None, None, "VMware ESXi / Proxmox Ready", json.dumps({"raid_controller": "PERC H730P 2GB NV Cache", "idrac": "iDRAC9 Enterprise"})),
            (6, 6, "Intel Xeon W-2223", "LGA2066", "Cascade Lake", 120, "ECC Registered", "DDR4", 32, 8, 4, 256, "NVMe SSD", 1000, "PCIe Gen 3.0 x4", 2, 4, "NVIDIA Quadro RTX 4000", 8, 241, 950, "Tower Workstation", None, None, "Windows 11 Pro for Workstations", json.dumps({"isv_certifications": ["SolidWorks", "AutoCAD", "Revit", "Premiere Pro"]})),
            (7, 7, "AMD Ryzen 5 7600X", "AM5", "Zen 4", 105, "DIMM", "DDR5", 0, 0, 0, 128, None, 0, None, 0, 0, "AMD Radeon Graphics (2 CU)", 0, 0, 105, "CPU", None, None, None, json.dumps({"cores": 6, "threads": 12, "socket": "AM5"})),
            (8, 8, "AMD Ryzen 7 7800X3D", "AM5", "Zen 4", 120, "DIMM", "DDR5", 0, 0, 0, 128, None, 0, None, 0, 0, "AMD Radeon Graphics (2 CU)", 0, 0, 120, "CPU", None, None, None, json.dumps({"cores": 8, "threads": 16, "socket": "AM5", "v_cache_mb": 96})),
            (9, 9, "Intel Core i5-14600K", "LGA1700", "14th Gen Raptor Lake", 125, "DIMM", "DDR5", 0, 0, 0, 192, None, 0, None, 0, 0, "Intel UHD Graphics 770", 0, 0, 125, "CPU", None, None, None, json.dumps({"p_cores": 6, "e_cores": 8, "threads": 20, "socket": "LGA1700"})),
            (10, 10, None, "AM5", "B650", 0, "DIMM", "DDR5", 0, 4, 4, 128, None, 0, "M.2 NVMe & SATA", 3, 4, None, 0, 0, 0, "ATX", None, None, None, json.dumps({"socket": "AM5", "ram_gen": "DDR5", "form_factor": "ATX", "m2_count": 3})),
            (11, 11, None, "LGA1700", "B760", 0, "DIMM", "DDR5", 0, 4, 4, 128, None, 0, "M.2 NVMe & SATA", 2, 4, None, 0, 0, 0, "Micro-ATX", None, None, None, json.dumps({"socket": "LGA1700", "ram_gen": "DDR5", "form_factor": "Micro-ATX", "m2_count": 2})),
            (12, 12, None, None, None, 0, "DIMM", "DDR5", 16, 1, 0, 16, None, 0, None, 0, 0, None, 0, 0, 10, "Desktop RAM", None, None, None, json.dumps({"ram_gen": "DDR5", "ram_type": "DIMM", "speed_mhz": 5200})),
            (13, 13, None, None, None, 0, "DIMM", "DDR4", 16, 1, 0, 16, None, 0, None, 0, 0, None, 0, 0, 10, "Desktop RAM", None, None, None, json.dumps({"ram_gen": "DDR4", "ram_type": "DIMM", "speed_mhz": 3200})),
            (14, 14, None, None, None, 0, "SODIMM", "DDR4", 16, 1, 0, 16, None, 0, None, 0, 0, None, 0, 0, 10, "Laptop RAM", None, None, None, json.dumps({"ram_gen": "DDR4", "ram_type": "SODIMM", "speed_mhz": 3200})),
            (15, 15, None, None, None, 0, None, None, 0, 0, 0, 0, "NVMe SSD", 1000, "PCIe Gen 4.0 x4", 1, 0, None, 0, 0, 7, "M.2 2280", None, None, None, json.dumps({"read_mbps": 7000, "write_mbps": 5000})),
            (16, 16, None, None, None, 0, None, None, 0, 0, 0, 0, "NVMe SSD", 500, "PCIe Gen 4.0 x4", 1, 0, None, 0, 0, 5, "M.2 2280", None, None, None, json.dumps({"read_mbps": 5000, "write_mbps": 3600})),
            (17, 17, None, None, None, 0, None, None, 0, 0, 0, 0, None, 0, None, 0, 0, "NVIDIA GeForce RTX 4070 Super", 12, 267, 220, "PCIe Card", None, None, None, json.dumps({"gpu_tdp_watts": 220, "length_mm": 267, "recommended_psu": 650})),
            (18, 18, None, None, None, 0, None, None, 0, 0, 0, 0, None, 0, None, 0, 0, None, 0, 0, 850, "ATX PSU", None, None, None, json.dumps({"rated_watts": 850, "modular": "Fully Modular", "efficiency": "80+ Gold"})),
            (19, 19, None, None, None, 0, None, None, 0, 0, 0, 0, None, 0, None, 0, 0, None, 0, 0, 0, "Mid Tower ATX", None, None, None, json.dumps({"max_gpu_len_mm": 370, "supported_mb": ["ATX", "Micro-ATX", "Mini-ITX"]})),
            (20, 20, None, None, None, 0, None, None, 0, 0, 0, 0, None, 0, None, 0, 0, None, 0, 0, 220, "CPU Air Cooler", None, None, None, json.dumps({"tdp_support_watts": 220, "supported_sockets": ["AM5", "AM4", "LGA1700", "LGA1200"]}))
        ]
        c.executemany("INSERT INTO product_specifications (id, product_id, cpu_model, cpu_socket, cpu_generation, cpu_tdp_watts, ram_type, ram_gen, ram_capacity_gb, ram_slots_total, ram_slots_free, max_ram_supported_gb, storage_type, storage_capacity_gb, storage_interface, m2_slots, sata_ports, gpu_model, gpu_vram_gb, gpu_length_mm, psu_wattage, form_factor, display_size, battery_health_percentage, os_installed, raw_specs_json) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", specs_data)
        
        # 12. Receiving Records
        receiving_data = [
            (1, "RCV-2026-0301", 1, 1, "INV-DEL-9844", "Laptop", 1, "Dell Latitude 5420 Batch", 5, 5, 105000.0, "Refurbished grade A commercial lease returns. Clean hinges, no structural cracks.", "Original Dell 65W USB-C Adapters included", "completed", 1),
            (2, "RCV-2026-0302", 2, 1, "INV-HP-4410", "Desktop", 2, "HP ProDesk 600 G6 Batch", 4, 4, 88000.0, "Corporate desktops, dust cleaned from fan intakes.", "Power cords", "partially_inwarded", 1),
            (3, "RCV-2026-0303", 1, 2, "INV-DEL-SERVER-12", "Server", 1, "Dell PowerEdge R740", 1, 1, 95000.0, "Datacenter decommission, dual redundant power supplies, clean chassis.", "Front Bezel, ReadyRails Kit", "qc_in_progress", 1)
        ]
        c.executemany("INSERT INTO receiving_records (id, receiving_number, supplier_id, warehouse_id, invoice_ref, item_type, brand_id, model_name, expected_qty, received_qty, purchase_cost_total, physical_condition_notes, accessories_received, status, created_by) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", receiving_data)
        
        # 13. Serialized Units
        units_data = [
            (1, 1, 1, "PCW-LT-DEL-5420-001", "ASSET-DEL-101", 21000.0, 24500.0, "Grade A", 1, "Rack A-01", "available", "2026-03-01 14:30:00", "2026-03-01 16:00:00", None, "Unit inspected 100% functional, new thermal paste applied."),
            (2, 1, 1, "PCW-LT-DEL-5420-002", "ASSET-DEL-102", 21000.0, 24500.0, "Grade A", 1, "Rack A-01", "available", "2026-03-01 14:45:00", "2026-03-01 16:05:00", None, "Battery tested 96% health, pristine cosmetic condition."),
            (3, 2, 1, "PCW-LT-LEN-T14-001", "ASSET-LEN-201", 26000.0, 29999.0, "Grade A", 1, "Rack A-03", "available", "2026-03-02 11:00:00", "2026-03-02 12:15:00", None, "Ryzen 5 Pro passed 30m Prime95 stress test."),
            (4, 4, 2, "PCW-DT-DEL-7080-001", "ASSET-OPT-301", 22000.0, 26500.0, "Grade A", 1, "Shelf B-02", "available", "2026-03-03 10:30:00", "2026-03-03 11:45:00", None, "Dell OptiPlex inwarded with clean Windows 11 Pro install."),
            (5, 1, 1, "PCW-LT-DEL-5420-003", "ASSET-DEL-103", 21000.0, 24500.0, "Grade A", 2, "QC Lab Table 1", "qc_passed", "2026-03-04 09:30:00", None, None, "Passed all 24 QC checklist items. Awaiting warehouse inwarding rack scan."),
            (6, 1, 1, "PCW-LT-DEL-5420-004", "ASSET-DEL-104", 21000.0, 24500.0, "Grade A", 2, "Intake Queue", "qc_pending", None, None, None, "Awaiting technician allocation."),
            (7, 3, 1, "PCW-LT-HP-840G8-001", "ASSET-HP-401", 30000.0, 34500.0, "Grade A", 2, "Intake Queue", "qc_pending", None, None, None, "Awaiting technician allocation."),
            (8, 5, 3, "PCW-SV-DEL-R740-001", "ASSET-SVR-501", 95000.0, 115000.0, "Grade A", 2, "Server Bench 2", "qc_testing", None, None, None, "Currently undergoing 48-hour ECC MemTest & RAID burn-in."),
            (9, 1, 1, "PCW-LT-DEL-5420-005", "ASSET-DEL-105", 21000.0, 24500.0, "Grade B", 3, "Quarantine Bin Q-01", "qc_failed", None, None, None, "FAILED DISPLAY TEST: Vertical pink line across panel. Flagged for internal screen replacement."),
            (10, 2, 1, "PCW-LT-LEN-T14-002", "ASSET-LEN-202", 26000.0, 29999.0, "Grade B", 3, "Quarantine Bin Q-02", "repair_required", None, None, None, "FAILED KEYBOARD TEST: Keys W, E, R not registering. Replacement keyboard ordered.")
        ]
        c.executemany("INSERT INTO serialized_units (id, product_id, receiving_id, serial_number, asset_tag, purchase_cost, selling_price, condition_grade, warehouse_id, location_rack, current_status, qc_passed_at, inwarded_at, sold_at, notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", units_data)
        
        # 14. QC Checklists
        laptop_qc_items = [
            {"key": "power_on", "label": "Power On / Clean Boot", "required": True},
            {"key": "bios_check", "label": "BIOS Entry, UEFI Secure Boot & Battery Clock Check", "required": True},
            {"key": "processor_test", "label": "CPU Stress Test (Cinebench / Prime95 15min)", "required": True},
            {"key": "ram_memtest", "label": "RAM Integrity Test (MemTest86 Clean)", "required": True},
            {"key": "storage_smart", "label": "SSD SMART Health >= 90% & Read/Write Benchmark", "required": True},
            {"key": "display_test", "label": "Display Panel: Dead Pixels, White Spots, Backlight Bleed", "required": True},
            {"key": "keyboard_test", "label": "Full Keyboard Matrix (Every Key Registered & Responsive)", "required": True},
            {"key": "touchpad_test", "label": "Touchpad Surface, Multi-touch Gestures & Physical Clickers", "required": True},
            {"key": "webcam_test", "label": "HD Webcam Visual Feed & Privacy Shutter", "required": True},
            {"key": "speaker_test", "label": "Internal Stereo Speakers (Left/Right Frequency Sweep)", "required": True},
            {"key": "mic_test", "label": "Microphone Array Noise Canceling & Clarity", "required": True},
            {"key": "wifi_test", "label": "Wi-Fi 2.4GHz & 5GHz Connection & Signal Range", "required": True},
            {"key": "bluetooth_test", "label": "Bluetooth Pairing & Audio Handshake", "required": True},
            {"key": "lan_test", "label": "RJ-45 Gigabit Ethernet Loopback & Link Speed", "required": False},
            {"key": "usb_ports", "label": "All USB 3.0 / USB-C Ports Transfer & Power Verification", "required": True},
            {"key": "hdmi_dp_test", "label": "HDMI / DisplayPort 4K External Video Output", "required": True},
            {"key": "audio_jack", "label": "3.5mm Headphone / Mic Combo Jack Audio Passthrough", "required": True},
            {"key": "charging_port", "label": "DC / USB-C Power Delivery Wattage Negotiation", "required": True},
            {"key": "battery_health", "label": "Battery Health Capacity >= 80% and Wear Level Verification", "required": True},
            {"key": "charger_test", "label": "OEM Charger Voltage Stability & Cable Flex Integrity", "required": True},
            {"key": "cosmetic_condition", "label": "Chassis, Hinge Torque, Rubber Feet & Casing Cleanliness", "required": True},
            {"key": "os_activation", "label": "Genuine Windows Digital License / OS Activation", "required": True},
            {"key": "thermal_bench", "label": "Thermal Benchmark (CPU Peak < 85C under Full Load)", "required": True},
            {"key": "fan_acoustics", "label": "Cooling Fan Bearing Acoustics & RPM Modulation", "required": True}
        ]
        
        desktop_qc_items = [
            {"key": "post_boot", "label": "POST & BIOS Check", "required": True},
            {"key": "motherboard_capacitors", "label": "Motherboard VRM & Capacitor Inspection", "required": True},
            {"key": "cpu_stress", "label": "CPU Full Load Thermal & Stability Test", "required": True},
            {"key": "ram_slots", "label": "All RAM Channels Tested & Verified", "required": True},
            {"key": "storage_health", "label": "SSD/HDD SMART Diagnostics", "required": True},
            {"key": "gpu_outputs", "label": "Dedicated / Integrated GPU Outputs & FurMark Test", "required": True},
            {"key": "psu_rails", "label": "SMPS / PSU 12V, 5V, 3.3V Rail Voltage Stability", "required": True},
            {"key": "io_ports", "label": "Front & Rear USB, LAN, Audio Ports", "required": True},
            {"key": "cooling_fans", "label": "Case & CPU Fan Airflow Operation", "required": True},
            {"key": "dust_thermal_paste", "label": "Internal Dust Free & Fresh MX-4 Thermal Paste Applied", "required": True},
            {"key": "os_fresh_image", "label": "Clean OS Installed with OEM Drivers", "required": True},
            {"key": "cosmetic_case", "label": "Chassis Condition & Drive Bay Locks", "required": True}
        ]
        
        c.execute("INSERT INTO qc_checklists (id, category_id, name, checklist_version, items_json, is_active) VALUES (1, 1, 'Standard 24-Point Refurbished Laptop Checklist', '2.1', ?, 1)", (json.dumps(laptop_qc_items),))
        c.execute("INSERT INTO qc_checklists (id, category_id, name, checklist_version, items_json, is_active) VALUES (2, 2, 'Enterprise Desktop 12-Point Checklist', '1.5', ?, 1)", (json.dumps(desktop_qc_items),))
        
        # 15. QC Inspection Logs
        c.execute("INSERT INTO qc_inspections (id, serial_unit_id, technician_id, checklist_id, thermal_cpu_c, thermal_gpu_c, battery_health_pct, overall_result, failure_reason, remediation_action, inspector_notes) VALUES (1, 1, 3, 1, 72.5, 68.0, 96, 'passed', NULL, 'Inward to Store', 'Excellent condition. Battery cycle count 142. New thermal paste applied.')")
        c.execute("INSERT INTO qc_inspections (id, serial_unit_id, technician_id, checklist_id, thermal_cpu_c, thermal_gpu_c, battery_health_pct, overall_result, failure_reason, remediation_action, inspector_notes) VALUES (2, 9, 3, 1, 69.0, 65.0, 88, 'failed', 'LCD display internal trace damage causing vertical line', 'Move to repair workshop for LCD replacement', 'Unit halted from sellable stock. Quarantine Bin Q-01.')")
        
        # 16. Inward Records
        c.execute("INSERT INTO inward_records (id, inward_number, serial_unit_id, warehouse_id, rack_bin, inwarded_by, notes) VALUES (1, 'INW-2026-0001', 1, 1, 'Rack A-01', 2, 'Inwarded to sellable inventory following QC pass.')")
        c.execute("INSERT INTO inward_records (id, inward_number, serial_unit_id, warehouse_id, rack_bin, inwarded_by, notes) VALUES (2, 'INW-2026-0002', 2, 1, 'Rack A-01', 2, 'Inwarded to sellable inventory following QC pass.')")
        
        # 17. Upgrade Options
        upgrade_data = [
            (1, "ram", "Upgrade to 16GB High-Speed DDR4 RAM", 14, "8GB -> 16GB DDR4", 1800.0, 200.0, 1, 1),
            (1, "ram", "Upgrade to 32GB Dual-Channel DDR4 RAM", 14, "8GB -> 32GB DDR4", 3800.0, 250.0, 1, 2),
            (1, "storage", "Upgrade to 512GB PCIe NVMe High-Speed SSD", 16, "256GB -> 512GB NVMe", 2200.0, 250.0, 1, 3),
            (1, "storage", "Upgrade to 1TB Samsung 980 Pro PCIe NVMe SSD", 15, "256GB -> 1TB NVMe", 5500.0, 300.0, 1, 4),
            (1, "warranty", "Extended 2-Year Total Hardware Care Warranty", None, "12 Mo -> 24 Mo Warranty", 1999.0, 0.0, 1, 5),
            (2, "ram", "Upgrade to 32GB DDR4 RAM", 14, "16GB -> 32GB DDR4", 2200.0, 200.0, 1, 1),
            (2, "storage", "Upgrade to 1TB Samsung 980 Pro NVMe SSD", 15, "512GB -> 1TB NVMe", 4800.0, 250.0, 1, 2),
            (2, "warranty", "Extended 2-Year Total Hardware Care Warranty", None, "12 Mo -> 24 Mo Warranty", 2499.0, 0.0, 1, 3)
        ]
        c.executemany("INSERT INTO upgrade_options (base_product_id, upgrade_type, title, component_product_id, spec_change, additional_cost, labour_charge, is_compatible, sort_order) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", upgrade_data)
        
        # 18. Compatibility Rules
        compat_rules = [
            ("motherboard", "cpu", "Socket Compatibility Check", "cpu_socket", "equals", json.dumps({"description": "Motherboard socket must match CPU socket (e.g. AM5 == AM5)"})),
            ("motherboard", "ram", "RAM Generation Match", "ram_gen", "equals", json.dumps({"description": "Motherboard DDR generation must match RAM generation (DDR5 == DDR5)"})),
            ("motherboard", "ram", "RAM Form Factor Match", "ram_type", "equals", json.dumps({"description": "Desktop motherboard requires DIMM; Laptop motherboard requires SODIMM"})),
            ("cabinet", "motherboard", "Form Factor Enclosure Check", "form_factor", "in_list", json.dumps({"description": "ATX cases fit ATX, Micro-ATX, Mini-ITX"})),
            ("psu", "build_wattage", "Power Supply Headroom Rule", "psu_wattage", "greater_or_equal", json.dumps({"multiplier": 1.30, "description": "PSU rated wattage must exceed total system TDP by 30%"}))
        ]
        c.executemany("INSERT INTO compatibility_rules (component_type_a, component_type_b, rule_name, rule_attribute, match_operator, expression_json) VALUES (?, ?, ?, ?, ?, ?)", compat_rules)
        
        # 19. Referral Codes & Ledger
        c.execute("INSERT INTO referral_codes (id, customer_id, code, points_per_referral, min_order_value, is_active) VALUES (1, 1, 'PCW-RAJ-1001', 500, 10000.0, 1)")
        c.execute("INSERT INTO referral_relationships (id, referrer_customer_id, referred_customer_id, referral_code_id, status, first_order_id) VALUES (1, 1, 2, 1, 'rewarded', 1)")
        c.execute("INSERT INTO referral_point_ledger (id, customer_id, transaction_type, points_in, points_out, running_balance, sales_order_id, referral_relationship_id, reason) VALUES (1, 1, 'earned_referral', 500, 0, 500, 1, 1, 'Customer Deepak Solanki completed eligible order #ORD-2026-001')")
        
        # 20. Repair Tickets
        c.execute("INSERT INTO repair_tickets (id, ticket_number, customer_id, serial_unit_id, device_brand_model, serial_or_imei, fault_description, accessories_included, technician_id, estimated_cost, final_cost, repair_status, diagnostic_report) VALUES (1, 'JS-2026-1001', 1, NULL, 'HP Pavilion Gaming 15-dk', 'CND94812LK', 'Laptop shuts down abruptly during 3D gaming. Heavy thermal throttling.', 'Original 150W HP Charger + Laptop Bag', 6, 2500.0, 2200.0, 'repaired', 'GPU & CPU thermal paste completely calcified. Dual cooling fans cleaned with isopropyl alcohol, repasted with Arctic MX-4. 1 hour FurMark test passed at 71C peak.')")
        c.execute("INSERT INTO repair_tickets (id, ticket_number, customer_id, serial_unit_id, device_brand_model, serial_or_imei, fault_description, accessories_included, technician_id, estimated_cost, final_cost, repair_status, diagnostic_report) VALUES (2, 'JS-2026-1002', 3, NULL, 'Apple MacBook Air M1 2020', 'FVFD388NQ6L4', 'Liquid spill on trackpad area. Left speaker distorted.', 'MacBook Only (No charger)', 6, 4500.0, 0.0, 'diagnosing', 'Logic board clean; audio daughterboard requires ultrasonic bath and trackpad flex replacement.')")
        
        # 21. Custom PC Preset & Assembly Order
        asm_components = {
            "cpu_id": 7, "cpu_title": "AMD Ryzen 5 7600X", "cpu_price": 20999.0,
            "mb_id": 10, "mb_title": "ASUS TUF Gaming B650-PLUS WiFi", "mb_price": 22400.0,
            "ram_id": 12, "ram_title": "Kingston Fury Beast 16GB DDR5 5200MHz", "ram_price": 4999.0,
            "storage_id": 15, "storage_title": "Samsung 980 Pro 1TB NVMe M.2 SSD", "storage_price": 8900.0,
            "gpu_id": 17, "gpu_title": "ASUS Dual GeForce RTX 4070 Super 12GB", "gpu_price": 62500.0,
            "psu_id": 18, "psu_title": "Corsair RM850e 850W Gold Modular PSU", "psu_price": 10800.0,
            "cabinet_id": 19, "cabinet_title": "DeepCool CC560 V2 Airflow Mid-Tower", "cabinet_price": 4299.0,
            "cooler_id": 20, "cooler_title": "DeepCool AK400 High-Efficiency CPU Cooler", "cooler_price": 2599.0
        }
        c.execute("INSERT INTO pc_build_presets (id, title, slug, use_case, budget_tier, components_json, base_price, is_active) VALUES (1, 'Apex Predator RTX 4070 Super Rig', 'apex-predator-rtx-4070s', 'High-FPS 1440p Gaming & Unreal Engine 5 Dev', 'Enthusiast Tier', ?, 137496.0, 1)", (json.dumps(asm_components),))
        c.execute("INSERT INTO assembly_orders (id, assembly_number, customer_id, total_wattage, components_cost, assembly_labour_charge, tax_amount, total_price, compatibility_status, technician_id, final_serial_number, status, notes) VALUES (1, 'ASM-2026-0001', 2, 455, 137496.0, 2500.0, 25199.28, 165195.28, 'VERIFIED_COMPATIBLE', 4, 'PCW-RIG-2026-0001', 'ready', 'System assembled with premium cable management. BIOS XMP/EXPO enabled.')")
        c.execute("INSERT INTO assembly_qc_records (id, assembly_order_id, technician_id, boot_test, bios_config, cpu_stress_pass, gpu_stress_pass, ram_memtest_pass, storage_smart_pass, cooling_efficiency, cable_management_grade, overall_status, notes) VALUES (1, 1, 3, 1, 1, 1, 1, 1, 1, 'Optimal (CPU Peak 72C, GPU Peak 66C)', 'Grade A+ Stealth Routing', 'passed', 'Assembly QC passed 100%. Certified ready for customer handover.')")
        
        # 22. Invoiced Order with GST
        c.execute("INSERT INTO sales_orders (id, order_number, customer_id, order_type, subtotal, upgrade_total, assembly_total, tax_amount, discount_amount, grand_total, payment_status, fulfillment_status, applied_referral_code, shipping_address) VALUES (1, 'ORD-2026-001', 2, 'standard', 24500.0, 2000.0, 0.0, 4770.0, 0.0, 31270.0, 'paid', 'delivered', 'PCW-RAJ-1001', 'SF-12, Speedwell Complex, Rajkot')")
        c.execute("INSERT INTO sales_order_items (id, sales_order_id, product_id, serial_unit_id, unit_price, upgrades_json, quantity, total_price) VALUES (1, 1, 1, 1, 24500.0, '[{\"title\": \"Upgrade to 16GB RAM\", \"cost\": 2000.0}]', 1, 26500.0)")
        c.execute("INSERT INTO invoices (id, invoice_number, sales_order_id, customer_id, hsn_sac_code, cgst_rate, cgst_amount, sgst_rate, sgst_amount, total_tax, grand_total, invoice_date, payment_status) VALUES (1, 'INV-2026-0101', 1, 2, '8471', 9.0, 2385.0, 9.0, 2385.0, 4770.0, 31270.0, '2026-03-05', 'paid')")
        c.execute("INSERT INTO payments (id, invoice_id, payment_method, transaction_reference, amount_paid, notes) VALUES (1, 1, 'upi', 'UPI/20260305/982348123', 31270.0, 'HDFC Bank UPI Payment Received')")
        c.execute("INSERT INTO warranties (id, serial_unit_id, sales_order_item_id, customer_id, warranty_months, start_date, end_date, status) VALUES (1, 1, 1, 2, 12, '2026-03-05', '2027-03-05', 'active')")
        
    print("Database seeding completed successfully with realistic PC Ware hardware data!")

if __name__ == "__main__":
    seed_all()
