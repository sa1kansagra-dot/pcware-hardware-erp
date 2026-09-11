import os
import sys
import json
import mimetypes
from urllib.parse import urlparse, parse_qs
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn

# Add backend directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import database as db
from modules.auth import verify_credentials, get_session_user, register_customer
from modules.catalog import list_products, get_product_by_slug, get_product_by_id, list_categories, list_brands
from modules.refurbishment import (
    list_receiving, create_receiving, get_qc_checklist, list_qc_pending_units,
    list_qc_failed_units, record_qc_inspection, inward_unit_to_sellable_stock,
    list_work_orders, get_work_order, create_refurb_work_order, consume_work_order_part,
    log_work_order_labour, complete_refurb_work_order
)
from modules.inventory import list_serialized_units, get_unit_history, list_warehouses
from modules.compatibility import validate_system_compatibility, get_compatible_components_list
from modules.assembly import list_assembly_orders, get_assembly_order, create_assembly_order, record_assembly_qc
from modules.modification import get_product_upgrades, calculate_configured_price
from modules.sales_billing import list_orders, get_order, create_order, create_quotation, list_quotations
from modules.referrals import get_or_create_referral_code
from modules.rma_repairs import track_repair_job, list_repair_tickets, create_repair_ticket, update_repair_ticket, list_warranties
from modules.reports import get_dashboard_metrics, get_recent_movements
from modules.bulk_inventory import process_bulk_upload
from modules.inquiries import list_inquiries, create_inquiry, generate_quotation_from_inquiry, convert_inquiry_to_bill, mark_inquiry_lost
from modules.crm import list_crm_reminders, complete_crm_reminder, reschedule_crm_reminder
from modules.accounting import (
    initialize_chart_of_accounts, get_chart_of_accounts, get_trial_balance,
    get_general_ledger, get_profit_and_loss, get_balance_sheet, post_journal_entry
)

FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "public"))

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True

class PCWareRequestHandler(BaseHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()

    def send_json(self, data, status=200):
        body = json.dumps(data, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_error_json(self, message, status=400, code="BAD_REQUEST"):
        self.send_json({"error": message, "code": code}, status=status)

    def get_json_body(self):
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            return {}
        raw = self.rfile.read(length).decode("utf-8")
        try:
            return json.loads(raw)
        except Exception:
            return {}

    def get_auth_user(self):
        auth_hdr = self.headers.get("Authorization", "")
        if auth_hdr.startswith("Bearer "):
            token = auth_hdr[7:].strip()
            return get_session_user(token)
        return None

    def serve_static_file(self, rel_path, content_type=None):
        full_path = os.path.normpath(os.path.join(FRONTEND_DIR, rel_path))
        if not full_path.startswith(FRONTEND_DIR) or not os.path.isfile(full_path):
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"404 Not Found")
            return

        if not content_type:
            content_type, _ = mimetypes.guess_type(full_path)
            content_type = content_type or "text/html"

        with open(full_path, "rb") as f:
            content = f.read()

        self.send_response(200)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8" if "text" in content_type else content_type)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)
        params = {k: v[0] for k, v in query.items()}

        # -------------------------------------------------------------
        # 1. API ROUTES
        # -------------------------------------------------------------
        try:
            if path == "/api/v1/auth/me":
                u = self.get_auth_user()
                if u:
                    return self.send_json({"user": u})
                return self.send_error_json("Unauthenticated", 401, "UNAUTHENTICATED")

            elif path == "/api/v1/catalog/products":
                return self.send_json(list_products(params))

            elif path.startswith("/api/v1/catalog/products/"):
                slug = path.replace("/api/v1/catalog/products/", "")
                prod = get_product_by_slug(slug)
                if prod:
                    return self.send_json(prod)
                return self.send_error_json("Product not found", 404, "NOT_FOUND")

            elif path == "/api/v1/catalog/categories":
                return self.send_json(list_categories())

            elif path == "/api/v1/catalog/brands":
                return self.send_json(list_brands())

            elif path == "/api/v1/receiving":
                return self.send_json(list_receiving())

            elif path.startswith("/api/v1/qc/checklists/"):
                cat_id = int(path.split("/")[-1])
                return self.send_json(get_qc_checklist(cat_id))

            elif path == "/api/v1/qc/pending":
                return self.send_json(list_qc_pending_units())

            elif path == "/api/v1/qc/failed":
                return self.send_json(list_qc_failed_units())

            elif path == "/api/v1/inventory/serials":
                return self.send_json(list_serialized_units(params))

            elif path.startswith("/api/v1/inventory/serials/"):
                sn = path.replace("/api/v1/inventory/serials/", "")
                hist = get_unit_history(sn)
                if hist:
                    return self.send_json(hist)
                return self.send_error_json(f"Serial unit {sn} not found", 404, "NOT_FOUND")

            elif path == "/api/v1/inventory/warehouses":
                return self.send_json(list_warehouses())

            elif path == "/api/v1/pc-builder/components":
                cat = params.get("category", "processors")
                return self.send_json(get_compatible_components_list(params, cat))

            elif path == "/api/v1/assembly/orders":
                st = params.get("status")
                return self.send_json(list_assembly_orders(st))

            elif path.startswith("/api/v1/assembly/orders/"):
                oid = int(path.split("/")[-1])
                o = get_assembly_order(oid)
                if o:
                    return self.send_json(o)
                return self.send_error_json("Assembly order not found", 404, "NOT_FOUND")

            elif path.startswith("/api/v1/products/") and path.endswith("/upgrades"):
                parts = path.split("/")
                pid = int(parts[4])
                return self.send_json(get_product_upgrades(pid))

            elif path == "/api/v1/orders":
                cid = int(params["customer_id"]) if params.get("customer_id") else None
                return self.send_json(list_orders(cid))

            elif path.startswith("/api/v1/orders/"):
                oid = int(path.split("/")[-1])
                o = get_order(oid)
                if o:
                    return self.send_json(o)
                return self.send_error_json("Order not found", 404, "NOT_FOUND")

            elif path == "/api/v1/quotations":
                return self.send_json(list_quotations())

            elif path == "/api/v1/referrals/my-code":
                cid = int(params.get("customer_id", 1))
                return self.send_json(get_or_create_referral_code(cid))

            elif path == "/api/v1/repair/track":
                q = params.get("token", "")
                res = track_repair_job(q)
                if res:
                    return self.send_json(res)
                return self.send_error_json(f"No repair job sheet found matching '{q}'", 404, "NOT_FOUND")

            elif path == "/api/v1/repair/tickets":
                return self.send_json(list_repair_tickets())

            elif path == "/api/v1/warranties":
                cid = int(params["customer_id"]) if params.get("customer_id") else None
                return self.send_json(list_warranties(cid))

            elif path == "/api/v1/dashboard/metrics":
                return self.send_json(get_dashboard_metrics())

            elif path == "/api/v1/dashboard/movements":
                return self.send_json(get_recent_movements())

            # ---------------------------------------------------------
            # DOUBLE-ENTRY ACCOUNTING & FINANCIAL REPORTING
            # ---------------------------------------------------------
            elif path == "/api/v1/accounting/coa":
                return self.send_json(get_chart_of_accounts())

            elif path == "/api/v1/accounting/trial-balance":
                return self.send_json(get_trial_balance())

            elif path == "/api/v1/accounting/general-ledger":
                acc = params.get("account_code")
                f_date = params.get("from_date")
                t_date = params.get("to_date")
                return self.send_json(get_general_ledger(acc, f_date, t_date))

            elif path == "/api/v1/accounting/pl":
                f_date = params.get("from_date")
                t_date = params.get("to_date")
                return self.send_json(get_profit_and_loss(f_date, t_date))

            elif path == "/api/v1/accounting/balance-sheet":
                as_of = params.get("as_of_date")
                return self.send_json(get_balance_sheet(as_of))

            # ---------------------------------------------------------
            # REFURBISHMENT WORK ORDERS
            # ---------------------------------------------------------
            elif path == "/api/v1/inquiries":
                st = params.get("status")
                return self.send_json(list_inquiries(st))

            elif path == "/api/v1/crm/reminders":
                st = params.get("status")
                return self.send_json(list_crm_reminders(st))

            elif path == "/api/v1/refurbishment/work-orders":
                st = params.get("status")
                return self.send_json(list_work_orders(st))

            elif path.startswith("/api/v1/refurbishment/work-orders/"):
                wo_id = int(path.split("/")[-1])
                wo = get_work_order(wo_id)
                if wo:
                    return self.send_json(wo)
                return self.send_error_json("Work order not found", 404, "NOT_FOUND")

        except Exception as e:
            return self.send_error_json(str(e), 500, "SERVER_ERROR")

        # -------------------------------------------------------------
        # 2. MULTI-PAGE WEBSITE & STATIC ASSET ROUTER
        # -------------------------------------------------------------
        if path == "/" or path == "/index.html":
            return self.serve_static_file("pages/index.html")
        elif path == "/shop" or path == "/shop.html":
            return self.serve_static_file("pages/shop.html")
        elif path == "/laptops":
            return self.serve_static_file("pages/laptops.html")
        elif path == "/desktops":
            return self.serve_static_file("pages/desktops.html")
        elif path == "/servers":
            return self.serve_static_file("pages/servers.html")
        elif path == "/workstations":
            return self.serve_static_file("pages/workstations.html")
        elif path.startswith("/products/"):
            return self.serve_static_file("pages/product-detail.html")
        elif path == "/custom-pc":
            return self.serve_static_file("pages/custom-pc.html")
        elif path == "/upgrades":
            return self.serve_static_file("pages/upgrades.html")
        elif path == "/referral-program" or path == "/referral":
            return self.serve_static_file("pages/referral.html")
        elif path == "/repair-tracking" or path == "/track":
            return self.serve_static_file("pages/repair-track.html")
        elif path == "/repair":
            return self.serve_static_file("pages/repair.html")
        elif path == "/warranty":
            return self.serve_static_file("pages/warranty.html")
        elif path == "/services":
            return self.serve_static_file("pages/services.html")
        elif path == "/about":
            return self.serve_static_file("pages/about.html")
        elif path == "/contact":
            return self.serve_static_file("pages/contact.html")
        elif path == "/faq":
            return self.serve_static_file("pages/faq.html")
        elif path == "/cart":
            return self.serve_static_file("pages/cart.html")
        elif path == "/checkout":
            return self.serve_static_file("pages/checkout.html")
        elif path == "/login":
            return self.serve_static_file("pages/login.html")
        elif path == "/register":
            return self.serve_static_file("pages/register.html")
        elif path == "/account":
            return self.serve_static_file("pages/account.html")
        elif path == "/erp" or path == "/erp.html":
            return self.serve_static_file("pages/erp.html")

        # Static css, js, images
        rel = path.lstrip("/")
        self.serve_static_file(rel)

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        body = self.get_json_body()

        try:
            # 1. Authentication
            if path == "/api/v1/auth/login":
                ident = body.get("email") or body.get("username") or body.get("identifier")
                pwd = body.get("password")
                if not ident or not pwd:
                    return self.send_error_json("Identifier and password are required.", 400)
                res = verify_credentials(ident, pwd)
                if res:
                    token, user = res
                    return self.send_json({"token": token, "user": user, "message": "Login successful."})
                return self.send_error_json("Invalid credentials.", 401, "INVALID_CREDENTIALS")

            elif path == "/api/v1/auth/register":
                res = register_customer(body)
                return self.send_json(res, 201)

            # 2. Refurbishment & Inwarding (RULES 1 & 2 ENFORCEMENT)
            elif path == "/api/v1/receiving":
                user = self.get_auth_user()
                uid = user["id"] if user else 1
                res = create_receiving(body, uid)
                return self.send_json(res, 201)

            elif path == "/api/v1/qc/inspect":
                user = self.get_auth_user()
                tech_id = user["id"] if user else int(body.get("technician_id", 3))
                res = record_qc_inspection(body, tech_id)
                return self.send_json(res, 201)

            elif path == "/api/v1/inventory/inward":
                user = self.get_auth_user()
                uid = user["id"] if user else int(body.get("user_id", 2))
                sn_id = int(body.get("serial_unit_id"))
                wh_id = int(body.get("warehouse_id", 1))
                rack_bin = body.get("rack_bin", "Rack A-01").strip()
                notes = body.get("notes", "")
                
                try:
                    res = inward_unit_to_sellable_stock(sn_id, wh_id, rack_bin, uid, notes)
                    return self.send_json(res, 200)
                except ValueError as ve:
                    # RULE 1 VIOLATION: Return 422 Unprocessable Entity
                    return self.send_error_json(str(ve), 422, "QC_RULE_VIOLATION")

            # 3. Compatibility Engine (RULE 4 & 5 ENFORCEMENT)
            elif path == "/api/v1/compatibility/validate":
                parts = body.get("parts", body)
                res = validate_system_compatibility(parts)
                return self.send_json(res)

            # 4. Custom PC Assembly (RULE 4 & 5 ENFORCEMENT)
            elif path == "/api/v1/assembly/orders":
                user = self.get_auth_user()
                cid = user["id"] if user else int(body.get("customer_id", 1))
                try:
                    res = create_assembly_order(body, cid)
                    return self.send_json(res, 201)
                except ValueError as ve:
                    return self.send_error_json(str(ve), 422, "COMPATIBILITY_ERROR")

            elif path.startswith("/api/v1/assembly/orders/") and path.endswith("/qc"):
                parts = path.split("/")
                oid = int(parts[5])
                user = self.get_auth_user()
                tech_id = user["id"] if user else int(body.get("technician_id", 3))
                res = record_assembly_qc(oid, body, tech_id)
                return self.send_json(res, 200)

            # 5. Modification & Dynamic Upgrade Pricing (RULE 6 & 8)
            elif path == "/api/v1/products/calculate-price":
                base_pid = int(body.get("base_product_id"))
                upg_ids = [int(x) for x in body.get("upgrade_ids", [])]
                res = calculate_configured_price(base_pid, upg_ids)
                return self.send_json(res)

            # 6. Sales Orders & Checkout (RULE 3, 7, 8)
            elif path == "/api/v1/orders":
                user = self.get_auth_user()
                cid = user["id"] if user else int(body.get("customer_id", 1))
                res = create_order(body, cid)
                return self.send_json(res, 201)

            elif path == "/api/v1/quotations":
                user = self.get_auth_user()
                uid = user["id"] if user else 1
                res = create_quotation(body, uid)
                return self.send_json(res, 201)

            # 7. Repairs & RMA
            elif path == "/api/v1/repair/tickets":
                user = self.get_auth_user()
                tech_id = user["id"] if user else 6
                res = create_repair_ticket(body, tech_id)
                return self.send_json(res, 201)

            elif path.startswith("/api/v1/repair/tickets/") and path.endswith("/update"):
                parts = path.split("/")
                tid = int(parts[5])
                user = self.get_auth_user()
                tech_id = user["id"] if user else 6
                res = update_repair_ticket(tid, body, tech_id)
                return self.send_json(res, 200)

            # 8. Refurbishment Work Orders & Cost Capitalization
            elif path == "/api/v1/inquiries":
                st = params.get("status")
                return self.send_json(list_inquiries(st))

            elif path == "/api/v1/crm/reminders":
                st = params.get("status")
                return self.send_json(list_crm_reminders(st))

            elif path == "/api/v1/refurbishment/work-orders":
                user = self.get_auth_user()
                uid = user["id"] if user else 3
                res = create_refurb_work_order(body, uid)
                return self.send_json(res, 201)

            elif path.startswith("/api/v1/refurbishment/work-orders/") and path.endswith("/consume-part"):
                wo_id = int(path.split("/")[5])
                user = self.get_auth_user()
                uid = user["id"] if user else 3
                res = consume_work_order_part(wo_id, body, uid)
                return self.send_json(res, 200)

            elif path.startswith("/api/v1/refurbishment/work-orders/") and path.endswith("/log-labour"):
                wo_id = int(path.split("/")[5])
                user = self.get_auth_user()
                uid = user["id"] if user else 3
                res = log_work_order_labour(wo_id, body, uid)
                return self.send_json(res, 200)

            elif path.startswith("/api/v1/refurbishment/work-orders/") and path.endswith("/complete"):
                wo_id = int(path.split("/")[5])
                user = self.get_auth_user()
                uid = user["id"] if user else 3
                res = complete_refurb_work_order(wo_id, uid, body)
                return self.send_json(res, 200)

            # 10. Bulk Inventory & Inquiry Pipeline & CRM Reminders
            elif path == "/api/v1/inventory/bulk-upload":
                items = body.get("items", body)
                res = process_bulk_upload(items)
                return self.send_json(res, 200)

            elif path == "/api/v1/inquiries":
                res = create_inquiry(body)
                return self.send_json(res, 201)

            elif path.startswith("/api/v1/inquiries/") and path.endswith("/quotation"):
                inq_id = int(path.split("/")[4])
                res = generate_quotation_from_inquiry(inq_id)
                return self.send_json(res, 200)

            elif path.startswith("/api/v1/inquiries/") and path.endswith("/convert-to-bill"):
                inq_id = int(path.split("/")[4])
                res = convert_inquiry_to_bill(inq_id, body)
                return self.send_json(res, 200)

            elif path.startswith("/api/v1/inquiries/") and path.endswith("/lost"):
                inq_id = int(path.split("/")[4])
                reason = body.get("loss_reason", "")
                res = mark_inquiry_lost(inq_id, reason)
                return self.send_json(res, 200)

            elif path.startswith("/api/v1/crm/reminders/") and path.endswith("/complete"):
                rem_id = int(path.split("/")[4])
                res = complete_crm_reminder(rem_id, body)
                return self.send_json(res, 200)

            elif path.startswith("/api/v1/crm/reminders/") and path.endswith("/reschedule"):
                rem_id = int(path.split("/")[4])
                new_date = body.get("scheduled_date", "")
                res = reschedule_crm_reminder(rem_id, new_date)
                return self.send_json(res, 200)

            # 9. Manual Accounting Journal Entries
            elif path == "/api/v1/accounting/journals":
                user = self.get_auth_user()
                uid = user["id"] if user else 1
                with db.get_db() as conn:
                    cnt = conn.execute("SELECT COUNT(*) as cnt FROM journals").fetchone()
                    j_num = body.get("entry_number") or f"JRN-MANUAL-{datetime.now().strftime('%Y%m%d')}-{cnt['cnt']+1:04d}"
                    res = post_journal_entry(
                        conn=conn,
                        entry_number=j_num,
                        reference_type=body.get("reference_type", "MANUAL"),
                        reference_id=body.get("reference_id", "MANUAL-001"),
                        memo=body.get("memo", "Manual Ledger Adjustment"),
                        lines=body.get("lines", []),
                        user_id=uid
                    )
                return self.send_json(res, 201)

            else:
                return self.send_error_json(f"Endpoint {path} not found", 404, "NOT_FOUND")

        except ValueError as ve:
            return self.send_error_json(str(ve), 400, "VALIDATION_ERROR")
        except Exception as e:
            return self.send_error_json(str(e), 500, "SERVER_ERROR")

def run(port=8085):
    server_address = ("0.0.0.0", port)
    httpd = ThreadedHTTPServer(server_address, PCWareRequestHandler)
    print(f"============================================================")
    print(f"🚀 PC WARE ENTERPRISE WEBSITE + ERP SYSTEM ACTIVE")
    print(f"🌐 Running on http://localhost:{port}")
    print(f"🏢 Showroom: SF 47-49 Suvarnabhumi Complex, Mota Mava, Rajkot")
    print(f"============================================================")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer shutting down gracefully.")
        httpd.server_close()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8085))
    run(port)
