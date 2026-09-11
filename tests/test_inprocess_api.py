import sys
import os
import io
import json

sys.path.insert(0, os.path.abspath("backend"))
from app import PCWareRequestHandler

class MockSocket:
    def __init__(self, data=b""):
        self.rfile = io.BytesIO(data)
        self.wfile = io.BytesIO()

    def makefile(self, mode, *args, **kwargs):
        if "r" in mode:
            return self.rfile
        elif "w" in mode or "b" in mode:
            return self.wfile

    def sendall(self, b):
        self.wfile.write(b)

    def recv(self, n):
        return self.rfile.read(n)

def simulate_request(method, path, body_dict=None, headers_dict=None):
    headers_dict = headers_dict or {}
    raw_body = b""
    if body_dict is not None:
        raw_body = json.dumps(body_dict).encode("utf-8")
        headers_dict["Content-Length"] = str(len(raw_body))
        headers_dict["Content-Type"] = "application/json"
    
    req_lines = [f"{method} {path} HTTP/1.1"]
    for k, v in headers_dict.items():
        req_lines.append(f"{k}: {v}")
    req_lines.append("")
    req_lines.append("")
    
    raw_req = "\r\n".join(req_lines).encode("utf-8") + raw_body
    sock = MockSocket(raw_req)
    
    # Instantiate handler
    handler = PCWareRequestHandler(sock, ("127.0.0.1", 12345), None)
    
    # Parse output
    sock.wfile.seek(0)
    raw_output = sock.wfile.read()
    
    header_end = raw_output.find(b"\r\n\r\n")
    if header_end == -1:
        return 500, {}, raw_output
        
    header_bytes = raw_output[:header_end].decode("utf-8")
    body_bytes = raw_output[header_end+4:]
    
    status_line = header_bytes.split("\r\n")[0]
    status_code = int(status_line.split(" ")[1])
    
    try:
        parsed_body = json.loads(body_bytes.decode("utf-8"))
    except:
        parsed_body = body_bytes.decode("utf-8")
        
    return status_code, parsed_body

def run_tests():
    print("============================================================")
    print(">>> RUNNING IN-PROCESS HTTP REQUEST HANDLER TESTS")
    print("============================================================")
    
    # 1. Test Static Routes
    st, body = simulate_request("GET", "/")
    assert st == 200, f"Expected 200, got {st}"
    assert "<!DOCTYPE html>" in body
    print("  [PASS] GET / -> HTTP 200 OK (HTML Document)")
    
    st, body = simulate_request("GET", "/shop")
    assert st == 200
    assert "Certified IT Hardware Catalog" in body
    print("  [PASS] GET /shop -> HTTP 200 OK")
    
    st, body = simulate_request("GET", "/laptops")
    assert st == 200
    print("  [PASS] GET /laptops -> HTTP 200 OK")
    
    st, body = simulate_request("GET", "/products/dell-latitude-5420-i5")
    assert st == 200
    assert "Product Details & Custom Upgrades" in body
    print("  [PASS] GET /products/dell-latitude-5420-i5 -> HTTP 200 OK")
    
    st, body = simulate_request("GET", "/custom-pc")
    assert st == 200
    assert "Custom PC Configurator Studio" in body
    print("  [PASS] GET /custom-pc -> HTTP 200 OK")

    st, body = simulate_request("GET", "/erp")
    assert st == 200
    assert "PC WARE Enterprise ERP System" in body
    print("  [PASS] GET /erp -> HTTP 200 OK")

    # 2. REST API: Catalog
    st, prods = simulate_request("GET", "/api/v1/catalog/products")
    assert st == 200
    assert len(prods) >= 10
    print(f"  [PASS] GET /api/v1/catalog/products -> HTTP 200 ({len(prods)} products)")

    st, prod = simulate_request("GET", "/api/v1/catalog/products/dell-latitude-5420-i5")
    assert st == 200
    assert prod["sku"] == "PCW-LT-DEL-5420"
    print(f"  [PASS] GET /api/v1/catalog/products/dell-latitude-5420-i5 -> SKU: {prod['sku']}, Grade: {prod['condition_grade']}")

    # 3. Dynamic Upgrade Price Calculation
    st, calc = simulate_request("POST", "/api/v1/products/calculate-price", {
        "base_product_id": 1,
        "upgrade_ids": [1, 3]
    })
    assert st == 200
    assert calc["grand_total"] == 32981.0
    print(f"  [PASS] POST /api/v1/products/calculate-price -> Total ₹{calc['grand_total']}")

    # 4. Hardware Compatibility Engine (Pass)
    st, compat = simulate_request("POST", "/api/v1/compatibility/validate", {
        "cpu_id": 7, "mb_id": 10, "ram_id": 12, "storage_id": 15,
        "gpu_id": 17, "psu_id": 18, "cabinet_id": 19, "cooler_id": 20
    })
    assert st == 200
    assert compat["is_compatible"] == True
    print("  [PASS] POST /api/v1/compatibility/validate -> Compatible Rig Verified")

    # 5. Hardware Compatibility Engine (Fail Socket Mismatch)
    st, bad_compat = simulate_request("POST", "/api/v1/compatibility/validate", {
        "cpu_id": 7, "mb_id": 11
    })
    assert st == 200
    assert bad_compat["is_compatible"] == False
    assert any(m["rule"] == "CPU_SOCKET_MISMATCH" for m in bad_compat["mismatches"])
    print("  [PASS] POST /api/v1/compatibility/validate -> Socket Mismatch Caught")

    # 6. Authentication
    st, auth_res = simulate_request("POST", "/api/v1/auth/login", {
        "identifier": "admin@pcware.in",
        "password": "Admin@123"
    })
    assert st == 200
    token = auth_res["token"]
    print(f"  [PASS] POST /api/v1/auth/login -> Authenticated as {auth_res['user']['full_name']}")

    # 7. STRICT QC RULE 1 & 2 ENFORCEMENT VIA HTTP HANDLER
    import database as db
    non_passed = db.query_one("SELECT id, current_status FROM serialized_units WHERE current_status != 'qc_passed' LIMIT 1")
    target_id = non_passed["id"] if non_passed else 1
    st, err_res = simulate_request("POST", "/api/v1/inventory/inward", {
        "serial_unit_id": target_id,
        "warehouse_id": 1,
        "rack_bin": "Rack A-01"
    }, headers_dict={"Authorization": f"Bearer {token}"})
    assert st == 422
    assert err_res["code"] == "QC_RULE_VIOLATION"
    print(f"  [PASS] POST /api/v1/inventory/inward -> Correctly rejected non-passed unit ({non_passed['current_status']}) with HTTP 422 ({err_res['code']})")

    # 8. Dashboard Metrics
    st, metrics = simulate_request("GET", "/api/v1/dashboard/metrics")
    assert st == 200
    assert metrics["inventory"]["total_units_tracked"] >= 10
    print(f"  [PASS] GET /api/v1/dashboard/metrics -> {metrics['inventory']['total_units_tracked']} units tracked")

    # 9. Repair Job-Sheet Public Track
    st, ticket = simulate_request("GET", "/api/v1/repair/track?token=JS-2026-1001")
    assert st == 200
    assert ticket["ticket_number"] == "JS-2026-1001"
    print(f"  [PASS] GET /api/v1/repair/track?token=JS-2026-1001 -> Ticket: {ticket['ticket_number']} ({ticket['repair_status']})")

    
    # 10. DOUBLE-ENTRY ACCOUNTING & WORK ORDER ENDPOINTS
    st, tb = simulate_request("GET", "/api/v1/accounting/trial-balance")
    assert st == 200
    assert tb["is_balanced"] == True
    print(f"  [PASS] GET /api/v1/accounting/trial-balance -> 100% Balanced (Dr ₹{tb['total_debit']:,.2f})")

    st, coa = simulate_request("GET", "/api/v1/accounting/coa")
    assert st == 200
    assert len(coa) >= 35
    print(f"  [PASS] GET /api/v1/accounting/coa -> {len(coa)} Accounts in Chart of Accounts")

    st, pl = simulate_request("GET", "/api/v1/accounting/pl")
    assert st == 200
    print(f"  [PASS] GET /api/v1/accounting/pl -> P&L Gross Profit: ₹{pl['gross_profit']:,.2f}")

    st, bs = simulate_request("GET", "/api/v1/accounting/balance-sheet")
    assert st == 200
    assert bs["is_balanced"] == True
    print(f"  [PASS] GET /api/v1/accounting/balance-sheet -> Verified Assets == Liab+Eq (₹{bs['assets']['total_assets']:,.2f})")

    st, wos = simulate_request("GET", "/api/v1/refurbishment/work-orders")
    assert st == 200
    print(f"  [PASS] GET /api/v1/refurbishment/work-orders -> {len(wos)} Refurb Work Orders tracked")

    print("============================================================")
    print("🎉 ALL IN-PROCESS HTTP HANDLER & BUSINESS RULE TESTS PASSED!")
    print("============================================================")

if __name__ == "__main__":
    run_tests()
