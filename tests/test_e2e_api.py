import sys
import os
import time
import urllib.request
import json
import threading

sys.path.insert(0, os.path.abspath("backend"))
from app import run, ThreadedHTTPServer, PCWareRequestHandler

TEST_PORT = 8899

def start_test_server():
    server = ThreadedHTTPServer(("127.0.0.1", TEST_PORT), PCWareRequestHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server

def http_get(path):
    req = urllib.request.Request(f"http://127.0.0.1:{TEST_PORT}{path}")
    with urllib.request.urlopen(req) as resp:
        return resp.status, resp.read().decode("utf-8")

def http_post(path, data, token=None):
    payload = json.dumps(data).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(f"http://127.0.0.1:{TEST_PORT}{path}", data=payload, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as err:
        return err.code, json.loads(err.read().decode("utf-8"))

def run_e2e_tests():
    print("============================================================")
    print(">>> RUNNING END-TO-END HTTP API & ROUTING INTEGRATION TESTS")
    print("============================================================")
    
    server = start_test_server()
    time.sleep(0.5)
    
    try:
        # 1. Test Static Routes
        routes_to_test = ["/", "/shop", "/laptops", "/desktops", "/servers", "/workstations", "/custom-pc", "/upgrades", "/repair-tracking", "/referral-program", "/cart", "/checkout", "/login", "/register", "/account", "/erp"]
        for r in routes_to_test:
            st, body = http_get(r)
            assert st == 200, f"Route {r} returned {st}"
            assert "<!DOCTYPE html>" in body or "<html" in body
            print(f"  [PASS] Static page route: {r} (HTTP 200 OK)")

        # 2. Test Dedicated Product Detail Page
        st, body = http_get("/products/dell-latitude-5420-i5")
        assert st == 200
        assert "Product Details & Custom Upgrades" in body
        print("  [PASS] Product detail route: /products/dell-latitude-5420-i5 (HTTP 200 OK)")

        # 3. Test REST API: Catalog Products & Detail
        st, raw = http_get("/api/v1/catalog/products")
        assert st == 200
        prods = json.loads(raw)
        assert len(prods) >= 10
        print(f"  [PASS] GET /api/v1/catalog/products returned {len(prods)} products")

        st, raw = http_get("/api/v1/catalog/products/dell-latitude-5420-i5")
        assert st == 200
        prod = json.loads(raw)
        assert prod["sku"] == "PCW-LT-DEL-5420"
        assert len(prod["upgrade_options"]) >= 4
        print(f"  [PASS] GET /api/v1/catalog/products/dell-latitude-5420-i5 with {len(prod['upgrade_options'])} dynamic upgrade options")

        # 4. Test REST API: Dynamic Upgrade Price Calculation (Server-Side Financial Integrity)
        st, calc = http_post("/api/v1/products/calculate-price", {
            "base_product_id": 1,
            "upgrade_ids": [1, 3] # 16GB RAM + 512GB NVMe
        })
        assert st == 200
        assert calc["grand_total"] == 32981.0
        print(f"  [PASS] POST /api/v1/products/calculate-price: Base ₹{calc['base_price']} + Upgrades ₹{calc['total_upgrade_cost']+calc['total_labour_charge']} + GST ₹{calc['total_tax']} = ₹{calc['grand_total']}")

        # 5. Test REST API: Hardware Compatibility Engine
        st, compat = http_post("/api/v1/compatibility/validate", {
            "cpu_id": 7, # AM5
            "mb_id": 10, # B650
            "ram_id": 12, # DDR5
            "storage_id": 15,
            "gpu_id": 17,
            "psu_id": 18,
            "cabinet_id": 19,
            "cooler_id": 20
        })
        assert st == 200
        assert compat["is_compatible"] == True
        print("  [PASS] POST /api/v1/compatibility/validate: Compatible build passed 100%")

        # 6. Test REST API: Hardware Incompatibility Detection
        st, bad_compat = http_post("/api/v1/compatibility/validate", {
            "cpu_id": 7, # AM5
            "mb_id": 11  # Intel LGA1700
        })
        assert st == 200
        assert bad_compat["is_compatible"] == False
        print("  [PASS] POST /api/v1/compatibility/validate: Incompatible socket correctly caught")

        # 7. Test REST API: Authentication
        st, auth_res = http_post("/api/v1/auth/login", {
            "identifier": "admin@pcware.in",
            "password": "Admin@123"
        })
        assert st == 200
        token = auth_res["token"]
        assert "pcw_tok_" in token
        print(f"  [PASS] POST /api/v1/auth/login: Authenticated as {auth_res['user']['full_name']} ({auth_res['user']['role_slug']})")

        # 8. Test REST API: QC Gate Inward Rule Enforcement via HTTP API (Rules 1 & 2)
        import database as db
        non_passed = db.query_one("SELECT id, current_status FROM serialized_units WHERE current_status != 'qc_passed' LIMIT 1")
        target_id = non_passed["id"] if non_passed else 1
        st, err_res = http_post("/api/v1/inventory/inward", {
            "serial_unit_id": target_id,
            "warehouse_id": 1,
            "rack_bin": "Rack A-01"
        }, token=token)
        assert st == 422
        assert err_res["code"] == "QC_RULE_VIOLATION"
        print(f"  [PASS] POST /api/v1/inventory/inward: Blocked non-passed unit ({non_passed['current_status']}) (HTTP 422: {err_res['code']})")

        # 9. Test REST API: Executive Dashboard Metrics
        st, raw = http_get("/api/v1/dashboard/metrics")
        assert st == 200
        metrics = json.loads(raw)
        assert "inventory" in metrics
        assert metrics["inventory"]["total_units_tracked"] >= 10
        print(f"  [PASS] GET /api/v1/dashboard/metrics: {metrics['inventory']['available_sellable_units']} sellable units, ₹{metrics['inventory']['sellable_stock_value']} inventory valuation")

        # 10. Test REST API: Public Repair Job Sheet Tracking
        st, raw = http_get("/api/v1/repair/track?token=JS-2026-1001")
        assert st == 200
        ticket = json.loads(raw)
        assert ticket["ticket_number"] == "JS-2026-1001"
        assert ticket["repair_status"] == "repaired"
        print(f"  [PASS] GET /api/v1/repair/track?token=JS-2026-1001: Device {ticket['device_brand_model']} ({ticket['repair_status']})")

        
        # 11. Test REST API: Double-Entry Accounting Trial Balance & Balance Sheet
        st, raw = http_get("/api/v1/accounting/trial-balance")
        assert st == 200
        tb = json.loads(raw)
        assert tb["is_balanced"] == True
        print(f"  [PASS] GET /api/v1/accounting/trial-balance: Balanced Dr ₹{tb['total_debit']:,.2f} == Cr ₹{tb['total_credit']:,.2f}")

        st, raw = http_get("/api/v1/accounting/balance-sheet")
        assert st == 200
        bs = json.loads(raw)
        assert bs["is_balanced"] == True
        print(f"  [PASS] GET /api/v1/accounting/balance-sheet: Total Assets ₹{bs['assets']['total_assets']:,.2f} == Liab+Eq ₹{bs['total_liabilities_and_equity']:,.2f}")

        st, raw = http_get("/api/v1/accounting/pl")
        assert st == 200
        pl = json.loads(raw)
        print(f"  [PASS] GET /api/v1/accounting/pl: Revenue ₹{pl['revenue']['total']:,.2f}, Gross Profit ₹{pl['gross_profit']:,.2f}")

        print("============================================================")
        print("🎉 ALL END-TO-END HTTP AND ROUTING TESTS PASSED PERFECTLY!")
        print("============================================================")

    finally:
        server.shutdown()

if __name__ == "__main__":
    run_e2e_tests()
