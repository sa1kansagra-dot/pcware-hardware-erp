# PC WARE — Refurbished IT Hardware Website & Enterprise ERP System
> **Certified Refurbished Laptops, Desktops, Servers, Workstations & Custom PC System Integration**
> **Address:** Shop No. SF, 47, 48, 49, Suvarnabhumi Complex, opp. Speedwell Party Plot, Ambika Twp, Mota Mava, Rajkot, Gujarat 360005  
> **Contact:** CEO: +91 94261 83934 | Technical Service: +91 80007 80704 | Inquiry: +91 70167 37271

---

## 🌟 Architectural Pillars & The 10 Critical Rules

1. **Strict QC Inwarding Gate (Rule 1 & 2)**:
   No refurbished unit can enter sellable store stock until it passes Quality Check. If a unit fails QC, it is automatically sequestered to Quarantine Bay (`WH-QUARANTINE`) and mechanically blocked from being inwarded (`HTTP 422: QC_RULE_VIOLATION`).
2. **Serialized Traceability (Rule 3)**:
   Every individual physical unit is tracked by its unique serial number from receiving intake lot, through 24-point QC thermal diagnostics, inward shelf location, sales order allocation, GST invoice, and warranty RMA history.
3. **8-Vector Hardware Compatibility Engine (Rule 4 & 5)**:
   Compatibility is verified on both the client (instant UX feedback) and authoritative backend (rejection of mismatches). Evaluates:
   - CPU Socket vs Motherboard Socket (e.g., AM5 vs LGA1700)
   - Motherboard RAM Gen vs RAM Module (DDR4 vs DDR5)
   - Form Factor (DIMM vs SODIMM; ATX vs mATX)
   - Storage Interface (PCIe Gen4 NVMe vs SATA)
   - GPU Length Clearance vs Chassis Dimensions
   - Power Supply Headroom (PSU Watts >= System TDP * 1.30)
4. **Refurbished Hardware Upgrades (Rule 6)**:
   Dedicated product detail pages (`/products/:slug`) support live RAM & SSD dynamic upgrade selections with real-time price recalculations (`Base Price + Upgrades + Labour + GST`).
5. **Immutable Referral Points Ledger (Rule 7)**:
   Referral rewards are credited into a double-entry transaction ledger (`referral_point_ledger`) ensuring full auditability and preventing balance tampering.
6. **Server-Side Financial Integrity (Rule 8)**:
   All financial subtotals, labour charges, HSN 8471 GST (9% CGST + 9% SGST), and referral discounts are calculated authoritatively on the backend.
7. **Movement Logs & Audit Trail (Rule 9 & 10)**:
   Every status transition and shelf movement is recorded in `inventory_movements`.

---

## 🚀 How to Run

### Option 1: One-Click Mac Launcher
Double-click `run.command` in the project root:
```bash
./run.command
```
This launches the server and automatically opens `http://localhost:8080` in your default browser.

### Option 2: Terminal Launch
```bash
python3 server.py
```
Visit:
* **Public Website**: [http://localhost:8080](http://localhost:8080)
* **Product Detail & Upgrades**: [http://localhost:8080/products/dell-latitude-5420-i5](http://localhost:8080/products/dell-latitude-5420-i5)
* **Custom PC Builder**: [http://localhost:8080/custom-pc](http://localhost:8080/custom-pc)
* **24/7 Live Job Sheet Tracker**: [http://localhost:8080/repair-tracking](http://localhost:8080/repair-tracking)
* **Enterprise ERP Workspace**: [http://localhost:8080/erp](http://localhost:8080/erp)

### Staff Credentials for ERP
* **Executive Administrator**: `admin@pcware.in` / `Admin@123`
* **Lead QC Technician**: `qc@pcware.in` / `Tech@123`
* **Registered Customer**: `raj.patel@gmail.com` / `Customer@123`

---

## 🧪 Automated Test Suites

Run the automated tests verifying all business rules:
```bash
# Test Strict QC Inward Gatekeeper (Rules 1 & 2)
python3 tests/test_qc_gate.py

# Test 8-Vector Hardware Compatibility Engine (Rules 4 & 5)
python3 tests/test_compatibility.py

# Test Server-Side Financials & GST Calculation (Rule 8)
python3 tests/test_financials.py

# Test Immutable Referral Points Ledger (Rule 7)
python3 tests/test_referral_ledger.py

# Test In-Process HTTP Gateway & Routing
python3 tests/test_inprocess_api.py
```
