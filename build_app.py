import json
import os

base_dir = os.path.dirname(os.path.abspath(__file__))
seed_file = os.path.join(base_dir, "static", "seed_data.json")
target_file = os.path.join(base_dir, "static", "app.js")

with open(seed_file, "r") as f:
    seed_json = f.read().strip()

js_code = f"""// PCWARE Hardware E-Commerce & Service ERP Engine
// Auto-generated production script with direct window bindings and dual engine

const DEFAULT_SEED_DATA = {seed_json};

function getLocalDB() {{
  try {{
    const existing = localStorage.getItem("pcware_db_v1");
    if (!existing) {{
      localStorage.setItem("pcware_db_v1", JSON.stringify(DEFAULT_SEED_DATA));
      return JSON.parse(JSON.stringify(DEFAULT_SEED_DATA));
    }}
    return JSON.parse(existing);
  }} catch(e) {{
    return JSON.parse(JSON.stringify(DEFAULT_SEED_DATA));
  }}
}}

function saveLocalDB(db) {{
  try {{
    localStorage.setItem("pcware_db_v1", JSON.stringify(db));
  }} catch(e) {{
    console.error("LocalStorage save error:", e);
  }}
}}

function handleLocalMock(endpoint, method, data) {{
  const db = getLocalDB();
  const path = endpoint.split("?")[0];
  const queryStr = endpoint.includes("?") ? endpoint.split("?")[1] : "";
  const params = new URLSearchParams(queryStr);

  if (method === "GET") {{
    if (path === "store-settings") return db.settings || DEFAULT_SEED_DATA.settings;
    if (path === "stats") {{
      const activeRepairs = db.jobsheets.filter(j => j.status !== "DELIVERED" && j.status !== "CANCELLED").length;
      const repairsReady = db.jobsheets.filter(j => j.status === "REPAIRED").length;
      const lowStock = db.products.filter(p => p.stock_quantity <= p.low_stock_threshold).length;
      const revenue = db.invoices.reduce((sum, inv) => sum + (inv.grand_total || 0), 0);
      return {{
        total_products: db.products.length,
        low_stock_count: lowStock,
        active_repairs: activeRepairs,
        repairs_ready: repairsReady,
        total_revenue: revenue,
        recent_jobs: db.jobsheets.slice(-5).reverse(),
        low_stock_items: db.products.filter(p => p.stock_quantity <= p.low_stock_threshold).slice(0, 5)
      }};
    }}
    if (path === "products") {{
      const cat = params.get("category");
      const search = (params.get("search") || "").toLowerCase().trim();
      return db.products.filter(p => {{
        const matchCat = (!cat || cat === "all" || p.category === cat);
        const matchSearch = (!search || p.name.toLowerCase().includes(search) || p.brand.toLowerCase().includes(search) || (p.model && p.model.toLowerCase().includes(search)));
        return matchCat && matchSearch;
      }});
    }}
    if (path === "jobsheets") {{
      const status = params.get("status");
      const search = (params.get("search") || "").toLowerCase().trim();
      return db.jobsheets.filter(j => {{
        const matchStatus = (!status || status === "all" || j.status === status);
        const matchSearch = (!search || j.job_sheet_number.toLowerCase().includes(search) || j.customer_name.toLowerCase().includes(search) || j.customer_phone.includes(search));
        return matchStatus && matchSearch;
      }}).slice().reverse();
    }}
    if (path.startsWith("jobsheets/")) {{
      const id = parseInt(path.split("/")[1]);
      return db.jobsheets.find(j => j.id === id);
    }}
    if (path === "track") {{
      const q = (params.get("q") || "").toLowerCase().trim();
      return db.jobsheets.filter(j => j.job_sheet_number.toLowerCase().includes(q) || j.customer_phone.includes(q));
    }}
    if (path === "serials") {{
      const q = (params.get("q") || "").toLowerCase().trim();
      return db.serials.filter(s => !q || s.serial_number.toLowerCase().includes(q) || (s.product_name && s.product_name.toLowerCase().includes(q)));
    }}
    if (path === "invoices") {{
      return db.invoices ? db.invoices.slice().reverse() : [];
    }}
    if (path.startsWith("invoices/")) {{
      const id = parseInt(path.split("/")[1]);
      return (db.invoices || []).find(inv => inv.id === id);
    }}
    if (path === "amc") {{
      return db.amc ? db.amc.slice().reverse() : [];
    }}
    if (path === "orders") {{
      return db.orders ? db.orders.slice().reverse() : [];
    }}
    if (path === "inquiries") {{
      return db.inquiries ? db.inquiries.slice().reverse() : [];
    }}
    if (path === "quotations") {{
      return db.quotations ? db.quotations.slice().reverse() : [];
    }}
    if (path.startsWith("quotations/")) {{
      const id = parseInt(path.split("/")[1]);
      return (db.quotations || []).find(q => q.id === id);
    }}
    if (path === "purchase-orders") {{
      return db.purchase_orders ? db.purchase_orders.slice().reverse() : [];
    }}
    if (path === "shortage-items") {{
      return (db.products || []).filter(p => p.stock_quantity <= p.low_stock_threshold);
    }}
    if (path === "parties") {{
      const type = params.get("type");
      return (db.parties || []).filter(p => !type || p.party_type === type);
    }}
    if (path === "ledger") {{
      const partyId = parseInt(params.get("party_id"));
      const party = (db.parties || []).find(p => p.id === partyId);
      if (!party) return {{ error: "Party not found" }};
      const entries = (db.ledger_entries || []).filter(e => e.party_id === partyId);
      return {{ ...party, entries }};
    }}
  }}

  if (method === "POST") {{
    const now = new Date().toISOString().replace("T", " ").split(".")[0];
    if (path === "jobsheets" || path === "service-booking") {{
      const nextNum = 1001 + db.jobsheets.length;
      const jobNum = "JS-2026-" + nextNum;
      const newJob = {{
        id: db.jobsheets.length + 1,
        job_sheet_number: jobNum,
        created_at: now,
        status: "RECEIVED",
        estimated_cost: parseFloat(data.estimated_cost || 0),
        final_cost: parseFloat(data.final_cost || 0),
        advance_paid: parseFloat(data.advance_paid || 0),
        assigned_technician: data.assigned_technician || "Lab Queue",
        customer_name: data.customer_name || data.name,
        customer_phone: data.customer_phone || data.phone,
        customer_address: data.customer_address || data.address || "",
        device_type: data.device_type || "Laptop",
        device_brand: data.device_brand || data.brand || "Generic",
        device_model: data.device_model || data.model || "N/A",
        device_serial: data.device_serial || "",
        accessories_received: data.accessories_received || "None",
        physical_condition: data.physical_condition || "Checked",
        reported_problem: data.reported_problem || data.problem || "",
        technician_notes: data.technician_notes || ""
      }};
      db.jobsheets.push(newJob);
      saveLocalDB(db);
      return {{ success: true, id: newJob.id, job_sheet_number: jobNum }};
    }}

    if (path === "products") {{
      const newP = {{
        id: db.products.length + 1,
        sku: data.sku || ("SKU-" + Date.now()),
        name: data.name,
        category: data.category,
        brand: data.brand,
        cost_price: parseFloat(data.cost_price || 0),
        selling_price: parseFloat(data.selling_price || 0),
        stock_quantity: parseInt(data.stock_quantity || 0),
        low_stock_threshold: 2,
        wattage: parseInt(data.wattage || 0),
        hsn_code: data.hsn_code || "8471",
        specs: data.specs || "",
        image_url: data.image_url || "https://images.unsplash.com/photo-1591799264318-7e6ef8ddb7ea?w=400"
      }};
      db.products.push(newP);
      saveLocalDB(db);
      return {{ success: true, id: newP.id }};
    }}

    if (path === "serials") {{
      const product = db.products.find(p => p.id == data.product_id);
      const newS = {{
        id: db.serials.length + 1,
        product_id: parseInt(data.product_id),
        serial_number: data.serial_number,
        supplier_name: data.supplier_name,
        warranty_months: parseInt(data.warranty_months || 36),
        status: "IN_STOCK",
        purchase_date: new Date().toISOString().split("T")[0],
        product_name: product ? product.name : "Hardware",
        product_brand: product ? product.brand : ""
      }};
      db.serials.push(newS);
      if (product) product.stock_quantity += 1;
      saveLocalDB(db);
      return {{ success: true, id: newS.id }};
    }}

    if (path === "invoices") {{
      const nextInvNum = "INV-2026-" + (1001 + db.invoices.length);
      const newInv = {{
        id: db.invoices.length + 1,
        invoice_number: nextInvNum,
        invoice_date: new Date().toISOString().split("T")[0],
        customer_name: data.customer_name,
        customer_phone: data.customer_phone,
        customer_address: data.customer_address,
        customer_gstin: data.customer_gstin,
        payment_method: data.payment_method,
        notes: data.notes,
        subtotal: parseFloat(data.subtotal),
        cgst: parseFloat(data.cgst),
        sgst: parseFloat(data.sgst),
        grand_total: parseFloat(data.grand_total),
        items: data.items
      }};
      (data.items || []).forEach(it => {{
        const prod = db.products.find(p => p.id === it.product_id);
        if (prod) prod.stock_quantity = Math.max(0, prod.stock_quantity - (it.quantity || 1));
        if (it.serial_number) {{
          const ser = db.serials.find(s => s.serial_number === it.serial_number);
          if (ser) ser.status = "SOLD";
        }}
      }});
      db.invoices.push(newInv);
      saveLocalDB(db);
      return {{ success: true, id: newInv.id, invoice_number: nextInvNum }};
    }}

    if (path === "amc") {{
      const newAMC = {{
        id: db.amc.length + 1,
        contract_number: "AMC-2026-" + (101 + db.amc.length),
        client_name: data.client_name,
        contact_person: data.contact_person,
        phone: data.phone,
        total_systems: parseInt(data.total_systems || 1),
        contract_value: parseFloat(data.contract_value || 0),
        start_date: data.start_date,
        end_date: data.end_date,
        visit_frequency: data.visit_frequency,
        status: "ACTIVE",
        address: data.address || ""
      }};
      db.amc.push(newAMC);
      saveLocalDB(db);
      return {{ success: true, id: newAMC.id }};
    }}

    if (path === "orders") {{
      db.orders = db.orders || [];
      const ordNum = "ORD-2026-" + (1001 + db.orders.length);
      const items = data.items || [];
      items.forEach(it => {{
        const prod = (db.products || []).find(p => p.id === it.id);
        if (prod) prod.stock_quantity = Math.max(0, prod.stock_quantity - (it.qty || 1));
      }});
      const newOrd = {{
        id: db.orders.length + 1,
        order_number: ordNum,
        customer_name: data.customer_name || data.name || "Customer",
        customer_phone: data.customer_phone || data.phone || "",
        customer_email: data.customer_email || data.email || "",
        customer_address: data.customer_address || data.address || "",
        order_type: "HARDWARE",
        items_json: JSON.stringify(items),
        total_amount: parseFloat(data.total_amount || 0),
        status: "CONFIRMED",
        payment_method: data.payment_method || "COD",
        created_at: now
      }};
      db.orders.push(newOrd);
      saveLocalDB(db);
      return {{ success: true, order_number: ordNum, id: newOrd.id }};
    }}

    if (path === "inquiries") {{
      db.inquiries = db.inquiries || [];
      const inqNum = "INQ-2026-" + (101 + db.inquiries.length);
      const newInq = {{
        id: db.inquiries.length + 1,
        inquiry_number: inqNum,
        customer_name: data.customer_name,
        customer_phone: data.customer_phone,
        customer_email: data.customer_email || "",
        customer_address: data.customer_address || "",
        requirement_type: data.requirement_type || "Hardware",
        items_requested: data.items_requested || "",
        estimated_budget: parseFloat(data.estimated_budget || 0),
        status: "NEW",
        source: data.source || "Walk-in",
        notes: data.notes || "",
        created_at: now
      }};
      db.inquiries.push(newInq);
      saveLocalDB(db);
      return {{ success: true, id: newInq.id, inquiry_number: inqNum }};
    }}

    if (path === "quotations") {{
      db.quotations = db.quotations || [];
      const qtNum = "QT-2026-" + (501 + db.quotations.length);
      const newQt = {{
        id: db.quotations.length + 1,
        quotation_number: qtNum,
        inquiry_id: data.inquiry_id ? parseInt(data.inquiry_id) : null,
        customer_name: data.customer_name,
        customer_phone: data.customer_phone,
        customer_email: data.customer_email || "",
        customer_address: data.customer_address || "",
        customer_gstin: data.customer_gstin || "",
        items_json: typeof data.items === "string" ? data.items : JSON.stringify(data.items || []),
        subtotal: parseFloat(data.subtotal || 0),
        gst_amount: parseFloat(data.gst_amount || 0),
        grand_total: parseFloat(data.grand_total || 0),
        valid_until: data.valid_until || "",
        status: "SENT",
        notes: data.notes || "",
        created_at: now
      }};
      db.quotations.push(newQt);
      if (newQt.inquiry_id && db.inquiries) {{
        const inq = db.inquiries.find(i => i.id === newQt.inquiry_id);
        if (inq) inq.status = "QUOTED";
      }}
      saveLocalDB(db);
      return {{ success: true, id: newQt.id, quotation_number: qtNum }};
    }}

    if (path.startsWith("quotations/") && path.endsWith("/convert-order")) {{
      const qtId = parseInt(path.split("/")[1]);
      db.orders = db.orders || [];
      const qt = (db.quotations || []).find(q => q.id === qtId);
      if (!qt) return {{ error: "Quotation not found" }};
      const ordNum = "ORD-2026-" + (1001 + db.orders.length);
      const newOrd = {{
        id: db.orders.length + 1,
        order_number: ordNum,
        customer_name: qt.customer_name,
        customer_phone: qt.customer_phone,
        customer_email: qt.customer_email,
        customer_address: qt.customer_address,
        order_type: "HARDWARE",
        items_json: qt.items_json,
        total_amount: qt.grand_total,
        status: "CONFIRMED",
        payment_method: data.payment_method || "COD",
        created_at: now
      }};
      db.orders.push(newOrd);
      qt.status = "CONVERTED";
      if (qt.inquiry_id && db.inquiries) {{
        const inq = db.inquiries.find(i => i.id === qt.inquiry_id);
        if (inq) inq.status = "ORDER_CONFIRMED";
      }}
      saveLocalDB(db);
      return {{ success: true, order_id: newOrd.id, order_number: ordNum }};
    }}

    if (path.startsWith("orders/") && path.endsWith("/fulfill")) {{
      const ordId = parseInt(path.split("/")[1]);
      const ord = (db.orders || []).find(o => o.id === ordId);
      if (!ord) return {{ error: "Order not found" }};
      db.invoices = db.invoices || [];
      const invNum = "INV-2026-0" + (101 + db.invoices.length);
      const items = typeof ord.items_json === "string" ? JSON.parse(ord.items_json || "[]") : (ord.items_json || []);
      
      let subtotal = 0;
      items.forEach(it => {{
        const pId = it.product_id || it.id;
        const qty = it.qty || it.quantity || 1;
        const unitP = it.unit_price || it.price || 0;
        subtotal += unitP * qty;
        const p = (db.products || []).find(prod => prod.id === pId);
        if (p) p.stock_quantity = Math.max(0, p.stock_quantity - qty);
      }});

      const cgst = Math.round(subtotal * 0.09 * 100) / 100;
      const sgst = Math.round(subtotal * 0.09 * 100) / 100;
      const grandTotal = Math.round((subtotal + cgst + sgst) * 100) / 100;

      const newInv = {{
        id: db.invoices.length + 1,
        invoice_number: invNum,
        invoice_date: now.split(" ")[0],
        customer_name: ord.customer_name,
        customer_phone: ord.customer_phone,
        customer_email: ord.customer_email || "",
        customer_address: ord.customer_address || "",
        customer_gstin: "",
        subtotal: subtotal,
        cgst: cgst,
        sgst: sgst,
        igst: 0,
        discount: 0,
        grand_total: grandTotal,
        payment_method: ord.payment_method || "COD",
        payment_status: ord.payment_method === "COD" ? "UNPAID" : "PAID",
        notes: "Generated from Order " + ord.order_number,
        created_at: now,
        items: items.map((it, idx) => ({{
          id: idx + 1,
          product_id: it.product_id || it.id,
          item_name: it.name || "Hardware Item",
          hsn_code: "8471",
          quantity: it.qty || it.quantity || 1,
          unit_price: it.unit_price || it.price || 0,
          gst_rate: 18.0,
          total: (it.unit_price || it.price || 0) * (it.qty || it.quantity || 1)
        }}))
      }};
      db.invoices.push(newInv);
      ord.status = "DELIVERED";

      const party = (db.parties || []).find(p => p.party_type === "CUSTOMER" && (p.phone === ord.customer_phone || p.name === ord.customer_name));
      if (party) {{
        party.current_balance = (party.current_balance || 0) + grandTotal;
        db.ledger_entries = db.ledger_entries || [];
        db.ledger_entries.push({{
          id: db.ledger_entries.length + 1,
          party_id: party.id,
          party_type: "CUSTOMER",
          entry_date: now.split(" ")[0],
          voucher_type: "SALES_INVOICE",
          voucher_no: invNum,
          narration: "Sales Invoice generated for Order " + ord.order_number,
          debit: grandTotal,
          credit: 0,
          running_balance: party.current_balance,
          created_at: now
        }});
      }}

      saveLocalDB(db);
      return {{ success: true, invoice_id: newInv.id, invoice_number: invNum }};
    }}

    if (path === "purchase-orders") {{
      db.purchase_orders = db.purchase_orders || [];
      const poNum = "PO-2026-" + (801 + db.purchase_orders.length);
      const itemsJson = typeof data.items === "string" ? data.items : JSON.stringify(data.items || []);
      const newPO = {{
        id: db.purchase_orders.length + 1,
        po_number: poNum,
        supplier_id: data.supplier_id ? parseInt(data.supplier_id) : null,
        supplier_name: data.supplier_name,
        supplier_phone: data.supplier_phone || "",
        supplier_gstin: data.supplier_gstin || "",
        order_date: data.order_date || now.split(" ")[0],
        expected_date: data.expected_date || "",
        items_json: itemsJson,
        subtotal: parseFloat(data.subtotal || 0),
        gst_amount: parseFloat(data.gst_amount || 0),
        total_amount: parseFloat(data.total_amount || 0),
        status: "ORDERED",
        payment_status: "UNPAID",
        notes: data.notes || "",
        created_at: now
      }};
      db.purchase_orders.push(newPO);
      saveLocalDB(db);
      return {{ success: true, id: newPO.id, po_number: poNum }};
    }}

    if (path.startsWith("purchase-orders/") && path.endsWith("/inward")) {{
      const poId = parseInt(path.split("/")[1]);
      const po = (db.purchase_orders || []).find(p => p.id === poId);
      if (!po) return {{ error: "Purchase order not found" }};
      const items = typeof po.items_json === "string" ? JSON.parse(po.items_json || "[]") : (po.items_json || []);
      items.forEach(it => {{
        const pId = it.product_id || it.id;
        const qty = it.qty || it.quantity || 1;
        const prod = (db.products || []).find(p => p.id === pId);
        if (prod) prod.stock_quantity = (prod.stock_quantity || 0) + qty;
      }});

      po.status = "RECEIVED";

      let supplier = null;
      if (po.supplier_id) supplier = (db.parties || []).find(p => p.id === po.supplier_id);
      if (!supplier && po.supplier_name) supplier = (db.parties || []).find(p => p.party_type === "SUPPLIER" && p.name === po.supplier_name);

      if (supplier) {{
        supplier.current_balance = (supplier.current_balance || 0) + po.total_amount;
        db.ledger_entries = db.ledger_entries || [];
        db.ledger_entries.push({{
          id: db.ledger_entries.length + 1,
          party_id: supplier.id,
          party_type: "SUPPLIER",
          entry_date: now.split(" ")[0],
          voucher_type: "PURCHASE_BILL",
          voucher_no: po.po_number,
          narration: "Inward GRN received against PO " + po.po_number,
          debit: 0,
          credit: po.total_amount,
          running_balance: supplier.current_balance,
          created_at: now
        }});
      }}

      saveLocalDB(db);
      return {{ success: true, status: "RECEIVED" }};
    }}

    if (path === "parties") {{
      db.parties = db.parties || [];
      const newParty = {{
        id: db.parties.length + 1,
        party_type: data.party_type || "CUSTOMER",
        name: data.name,
        contact_person: data.contact_person || "",
        phone: data.phone,
        email: data.email || "",
        address: data.address || "",
        gstin: data.gstin || "",
        opening_balance: parseFloat(data.opening_balance || 0),
        current_balance: parseFloat(data.opening_balance || 0),
        created_at: now
      }};
      db.parties.push(newParty);
      saveLocalDB(db);
      return {{ success: true, id: newParty.id }};
    }}

    if (path === "ledger-transactions") {{
      const partyId = parseInt(data.party_id);
      const party = (db.parties || []).find(p => p.id === partyId);
      if (!party) return {{ error: "Party not found" }};
      const amount = parseFloat(data.amount || 0);
      const isCust = party.party_type === "CUSTOMER";
      const vType = isCust ? "PAYMENT_RECEIVED" : "PAYMENT_MADE";
      const prefix = isCust ? "PAY-REC" : "PAY-SUP";
      db.ledger_entries = db.ledger_entries || [];
      const vNo = prefix + "-" + (101 + db.ledger_entries.filter(e => e.voucher_type === vType).length);
      const narration = data.narration || ("Payment of ₹" + amount.toLocaleString('en-IN') + " via " + (data.payment_mode || "UPI"));

      party.current_balance = (party.current_balance || 0) - amount;

      db.ledger_entries.push({{
        id: db.ledger_entries.length + 1,
        party_id: partyId,
        party_type: party.party_type,
        entry_date: data.date || now.split(" ")[0],
        voucher_type: vType,
        voucher_no: vNo,
        narration: narration,
        debit: isCust ? 0 : amount,
        credit: isCust ? amount : 0,
        running_balance: party.current_balance,
        created_at: now
      }});

      saveLocalDB(db);
      return {{ success: true, voucher_no: vNo, new_balance: party.current_balance }};
    }}
  }}

  if (method === "PUT") {{
    if (path.startsWith("jobsheets/")) {{
      const id = parseInt(path.split("/")[1]);
      const job = db.jobsheets.find(j => j.id === id);
      if (job) {{
        if (data.status) job.status = data.status;
        if (data.technician_notes) job.technician_notes = data.technician_notes;
        if (data.final_cost !== undefined) job.final_cost = parseFloat(data.final_cost);
        if (data.advance_paid !== undefined) job.advance_paid = parseFloat(data.advance_paid);
        saveLocalDB(db);
        return {{ success: true }};
      }}
    }}
    if (path.startsWith("inquiries/")) {{
      const id = parseInt(path.split("/")[1]);
      const inq = (db.inquiries || []).find(i => i.id === id);
      if (inq) {{
        if (data.status) inq.status = data.status;
        if (data.notes) inq.notes = data.notes;
        saveLocalDB(db);
        return {{ success: true }};
      }}
    }}
    if (path.startsWith("purchase-orders/")) {{
      const id = parseInt(path.split("/")[1]);
      const po = (db.purchase_orders || []).find(p => p.id === id);
      if (po) {{
        if (data.status) po.status = data.status;
        if (data.payment_status) po.payment_status = data.payment_status;
        if (data.notes) po.notes = data.notes;
        saveLocalDB(db);
        return {{ success: true }};
      }}
    }}
    if (path.startsWith("orders/")) {{
      const id = parseInt(path.split("/")[1]);
      const ord = (db.orders || []).find(o => o.id === id);
      if (ord) {{
        if (data.status) ord.status = data.status;
        saveLocalDB(db);
        return {{ success: true }};
      }}
    }}
  }}

  return null;
}}

async function apiGet(endpoint) {{
  if (window.location.protocol !== "file:") {{
    try {{
      const res = await fetch("/api/" + endpoint);
      if (res.ok) return await res.json();
    }} catch (e) {{}}
  }}
  return handleLocalMock(endpoint, "GET");
}}

async function apiPost(endpoint, data) {{
  if (window.location.protocol !== "file:") {{
    try {{
      const res = await fetch("/api/" + endpoint, {{
        method: "POST",
        headers: {{ "Content-Type": "application/json" }},
        body: JSON.stringify(data)
      }});
      if (res.ok) return await res.json();
    }} catch (e) {{}}
  }}
  return handleLocalMock(endpoint, "POST", data);
}}

async function apiPut(endpoint, data) {{
  if (window.location.protocol !== "file:") {{
    try {{
      const res = await fetch("/api/" + endpoint, {{
        method: "PUT",
        headers: {{ "Content-Type": "application/json" }},
        body: JSON.stringify(data)
      }});
      if (res.ok) return await res.json();
    }} catch (e) {{}}
  }}
  return handleLocalMock(endpoint, "PUT", data);
}}

const TRANSLATIONS = {{
  gu: {{
    tagline: "કમ્પ્યુટર હાર્ડવેર, કસ્ટમ પીસી અને સર્વિસ હબ",
    nav_shop: "હાર્ડવેર શોપ (Shop)",
    nav_builder: "કસ્ટમ PC Builder",
    nav_track: "જોબ-શીટ ટ્રેકર (Track Repair)",
    nav_book: "સર્વિસ બુકિંગ (Book Service)",
    nav_erp: "ERP પોર્ટલ",
    nav_shop_m: "🛍️ શોપ",
    nav_builder_m: "⚙️ PC Builder",
    nav_track_m: "🔍 ટ્રેકર",
    nav_book_m: "📅 સર્વિસ",
    nav_erp_m: "📊 ERP",
    hero_badge: "⚡ ઓરિજિનલ હાર્ડવેર અને સીરીયલ વોરંટી",
    hero_title: "કમ્પ્યુટર પાર્ટ્સ, લેપટોપ અને કસ્ટમ પીસી સોલ્યુશન્સ",
    hero_desc: "Intel 14th Gen, AMD Ryzen 7000, RTX 4000 Series, Gen4 NVMe SSDs અને લેપટોપ રિપેરિંગની સર્વોત્તમ સેવા એક જ સ્થળે.",
    hero_btn_builder: "કસ્ટમ PC કન્ફિગર કરો",
    hero_btn_track: "રિપેરિંગ સ્ટેટસ જુઓ",
    search_placeholder: "કમ્પોનન્ટ, બ્રાન્ડ, મોડલ સર્ચ કરો...",
    gst_notice: "તમામ કિંમતોમાં GST શામેલ છે • લોકલ રિપેરિંગ માટે ફ્રી પિકઅપ ઉપલબ્ધ છે",
    cat_all: "બધા પ્રોડક્ટ્સ",
    cat_processor: "પ્રોસેસર્સ (CPU)",
    cat_motherboard: "મધરબોર્ડ્સ",
    cat_ram: "રેમ (Memory)",
    cat_storage: "સ્ટોરેજ (SSD/HDD)",
    cat_gpu: "ગ્રાફિક કાર્ડ્સ",
    cat_psu: "પાવર સપ્લાય",
    cat_cabinet: "કેબિનેટ્સ",
    cat_cooler: "કૂલર્સ અને ફેન્સ",
    cat_laptop: "લેપટોપ્સ",
    cat_peripheral: "પેરિફેરલ્સ અને પ્રિન્ટર્સ",
    cat_service_parts: "સર્વિસ પાર્ટ્સ",
    incl_gst: "GST સહિત:",
    add_to_cart: "કાર્ટમાં ઉમેરો",
    stock_prefix: "સ્ટોક: ",
    out_of_stock: "સ્ટોક ખાલી",
    no_products: "કોઈ પ્રોડક્ટ મળ્યો નથી",
    no_products_desc: "કૃપા કરીને અન્ય સર્ચ શબ્દ અથવા કેટેગરી પસંદ કરો.",
    builder_badge: "ઇન્ટરેક્ટિવ ટૂલ",
    builder_title: "કસ્ટમ PC બિલ્ડર (Custom PC Configurator)",
    builder_desc: "પાર્ટ્સ પસંદ કરો, પાવર અને બજેટની લાઈવ ગણતરી કરો, અને એક ક્લિકમાં ઓર્ડર કરો.",
    builder_reset: "રીસેટ કરો",
    builder_whatsapp: "WhatsApp શેર",
    builder_add_cart: "આખો PC કાર્ટમાં ઉમેરો",
    builder_summary_title: "બિલ્ડ સારાંશ (Build Summary)",
    builder_wattage_label: "⚡ અંદાજિત પાવર ખપત (TDP):",
    builder_psu_rec: "ભલામણ કરેલ SMPS ક્ષમતા:",
    builder_total_price: "કુલ રકમ (GST સહિત):",
    builder_selected: "પસંદ કર્યું",
    builder_remove: "✕ હટાવો",
    builder_pending: "પસંદગી બાકી",
    track_badge: "24x7 Live Service Portal",
    track_title: "રિપેરિંગ / સર્વિસ સ્ટેટસ ટ્રેકર",
    track_desc: "તમારો જોબ-શીટ નંબર (દા.ત. JS-2026-1001) અથવા નોંધાયેલ મોબાઇલ નંબર દાખલ કરીને લાઈવ રિપેરિંગ સ્ટેટસ જુઓ.",
    track_input_ph: "દાખલ કરો: JS-2026-1001 અથવા 9825011223",
    track_btn: "ટ્રેક કરો (Track)",
    track_quick: "નમૂના માટે ટ્રાય કરો:",
    track_enter_prompt: "કૃપા કરીને જોબ-શીટ નંબર અથવા મોબાઇલ નંબર નાખો.",
    track_not_found: "કોઈ સર્વિસ રેકોર્ડ મળ્યો નથી. કૃપા કરીને નંબર ફરી ચકાસો.",
    stage_received: "સ્વીકારેલ (Received)",
    stage_diagnosing: "તપાસ ચાલુ (Diagnosing)",
    stage_waiting: "મંજૂરી બાકી (Quote Approval)",
    stage_repaired: "રિપેર થયેલ (Repaired & QC)",
    stage_delivered: "ડિલિવરી (Delivered)",
    book_badge: "Doorstep / Store Care",
    book_title: "ઓનલાઇન કમ્પ્યુટર સર્વિસ રિક્વેસ્ટ",
    book_desc: "લેપટોપ, ડેસ્કટોપ કે પ્રિન્ટર રિપેરિંગ માટે રિક્વેસ્ટ બુક કરો. અમારો એન્જિનિયર તરત જ સંપર્ક કરશે.",
    book_name_lbl: "તમારું નામ (Full Name) *",
    book_phone_lbl: "મોબાઇલ નંબર (Mobile) *",
    book_type_lbl: "ડિવાઇસનો પ્રકાર (Device Type)",
    book_brand_lbl: "બ્રાન્ડ / કંપની (Brand)",
    book_model_lbl: "મોડેલ નંબર (Model)",
    book_prob_lbl: "સમસ્યાની વિગત (Reported Fault) *",
    book_addr_lbl: "પિકઅપ સરનામું (વૈકલ્પિક)",
    book_submit_btn: "સર્વિસ રિક્વેસ્ટ સબમિટ કરો (Book Token)",
    cart_title: "શોપિંગ કાર્ટ",
    cart_empty: "તમારું કાર્ટ ખાલી છે",
    cart_empty_sub: "પ્રોડક્ટ ઉમેરવા માટે શોપ પર જાઓ.",
    cart_subtotal_lbl: "સબ-ટોટલ:",
    cart_gst_lbl: "GST (18% સમાવિષ્ટ):",
    cart_gst_val: "Included",
    cart_total_lbl: "કુલ રકમ (GST સહિત):",
    cart_checkout_btn: "ઓર્ડર કન્ફર્મ કરો (Cash / UPI)",
    order_name_ph: "તમારું નામ (Full Name) *",
    order_phone_ph: "મોબાઇલ નંબર (Phone) *",
    order_address_ph: "ડિલિવરી સરનામું (Address) *",
    opt_cod: "Cash on Delivery (દુકાન પર અથવા ડિલિવરી વખતે રોકડા)",
    opt_upi: "UPI / QR Code પેમેન્ટ",
    opt_bank: "Bank NEFT/RTGS",
    tab_overview: "📊 ઓવરવ્યૂ (Overview)",
    tab_jobsheets: "🛠️ જોબ શીટ્સ / લેબ (Job Sheets)",
    tab_inventory: "📦 સ્ટોક ઇન્વેન્ટરી (Inventory)",
    tab_serials: "🏷️ સીરીયલ ટ્રેકિંગ (Serial Registry)",
    tab_billing: "🧾 GST બિલિંગ (Invoicing)",
    tab_amc: "🏢 AMC કોન્ટ્રેક્ટ્સ (AMC)",
    tab_inquiries: "📋 ઇન્ક્વાયરી & ઓર્ડર્સ",
    tab_purchase: "🛒 ઘટતો માલ & ખરીદી",
    tab_ledger: "📑 પાર્ટી ખાતાવહી",
    inq_title: "ગ્રાહક ઇન્ક્વાયરી & લીડ્સ",
    inq_btn_new: "+ નવી ઇન્ક્વાયરી",
    inq_qt_title: "ક્વોટેશન્સ & અંદાજપત્ર",
    inq_orders_title: "કન્ફર્મ સેલ્સ ઓર્ડર્સ",
    shortage_title: "સ્ટોકમાં ઘટતી વસ્તુઓ (Low Stock Requisition)",
    po_title: "સપ્લાયર ખરીદ ઓર્ડર્સ (Purchase Orders)",
    po_btn_new: "+ નવો ખરીદ ઓર્ડર (PO)",
    ledger_title: "પાર્ટી ખાતાવહી (Customer & Supplier Ledgers)",
    ledger_cust_btn: "ગ્રાહક ખાતાઓ (Customers)",
    ledger_sup_btn: "સપ્લાયર ખાતાઓ (Suppliers)",
    party_btn_new: "+ નવું એકાઉન્ટ / પાર્ટી"
  }},
  en: {{
    tagline: "Computer Hardware Sales, Custom PC Builds & Service Hub",
    nav_shop: "Hardware Shop",
    nav_builder: "Custom PC Builder",
    nav_track: "Track Repair",
    nav_book: "Book Service",
    nav_erp: "ERP Portal",
    nav_shop_m: "🛍️ Shop",
    nav_builder_m: "⚙️ PC Builder",
    nav_track_m: "🔍 Track",
    nav_book_m: "📅 Service",
    nav_erp_m: "📊 ERP",
    hero_badge: "⚡ Genuine Hardware with Serial Warranty",
    hero_title: "Computer Parts, Laptops & Custom PC Solutions",
    hero_desc: "One-stop destination for Intel 14th Gen, AMD Ryzen 7000, RTX 4000 Series, Gen4 NVMe SSDs and expert laptop repair services.",
    hero_btn_builder: "Configure Custom PC",
    hero_btn_track: "View Repair Status",
    search_placeholder: "Search components, brands, models, SKUs...",
    gst_notice: "GST Included in all prices • Free pickup available for local repairs",
    cat_all: "All Products",
    cat_processor: "Processors (CPU)",
    cat_motherboard: "Motherboards",
    cat_ram: "RAM (Memory)",
    cat_storage: "Storage (SSD/HDD)",
    cat_gpu: "Graphic Cards",
    cat_psu: "Power Supplies",
    cat_cabinet: "Cabinets",
    cat_cooler: "Coolers & Fans",
    cat_laptop: "Laptops",
    cat_peripheral: "Peripherals & Printers",
    cat_service_parts: "Service & Spares",
    incl_gst: "Incl. GST:",
    add_to_cart: "Add to Cart",
    stock_prefix: "Stock: ",
    out_of_stock: "Out of Stock",
    no_products: "No products found",
    no_products_desc: "Please try another search keyword or category.",
    builder_badge: "Interactive Tool",
    builder_title: "Custom PC Builder (Configurator)",
    builder_desc: "Select parts, calculate live TDP wattage and budget, and order in one click.",
    builder_reset: "Reset Build",
    builder_whatsapp: "Share on WhatsApp",
    builder_add_cart: "Add Full PC to Cart",
    builder_summary_title: "Build Summary",
    builder_wattage_label: "⚡ Estimated Power Draw (TDP):",
    builder_psu_rec: "Recommended PSU Capacity:",
    builder_total_price: "Total Amount (Incl. GST):",
    builder_selected: "Selected",
    builder_remove: "✕ Remove",
    builder_pending: "Selection Pending",
    track_badge: "24x7 Live Service Portal",
    track_title: "Repair & Service Status Tracker",
    track_desc: "Enter your Job Sheet Number (e.g. JS-2026-1001) or registered mobile number to track live status.",
    track_input_ph: "Enter: JS-2026-1001 or 9825011223",
    track_btn: "Track Status",
    track_quick: "Try Sample Numbers:",
    track_enter_prompt: "Please enter a Job Sheet number or mobile number.",
    track_not_found: "No service records found. Please recheck the number.",
    stage_received: "1. Received",
    stage_diagnosing: "2. Diagnosing",
    stage_waiting: "3. Waiting Approval",
    stage_repaired: "4. Repaired & QC",
    stage_delivered: "5. Delivered",
    book_badge: "Doorstep / Store Care",
    book_title: "Online Computer Service Request",
    book_desc: "Book a service request for laptop, desktop, or printer repair. Our engineer will contact you promptly.",
    book_name_lbl: "Full Customer Name *",
    book_phone_lbl: "Mobile Number *",
    book_type_lbl: "Device Type",
    book_brand_lbl: "Brand / Make",
    book_model_lbl: "Model Number",
    book_prob_lbl: "Reported Fault / Problem *",
    book_addr_lbl: "Pickup Address (Optional)",
    book_submit_btn: "Submit Service Request (Book Token)",
    cart_title: "Shopping Cart",
    cart_empty: "Your cart is empty",
    cart_empty_sub: "Go to the shop to add products.",
    cart_subtotal_lbl: "Subtotal:",
    cart_gst_lbl: "GST (18% Included):",
    cart_gst_val: "Included",
    cart_total_lbl: "Total Amount (Incl. GST):",
    cart_checkout_btn: "Confirm Order (Cash / UPI)",
    order_name_ph: "Full Customer Name *",
    order_phone_ph: "Mobile Number (Phone) *",
    order_address_ph: "Delivery Address *",
    opt_cod: "Cash on Delivery / Pay at Store",
    opt_upi: "UPI / QR Code Payment",
    opt_bank: "Bank NEFT / RTGS Transfer",
    tab_overview: "📊 Overview",
    tab_jobsheets: "🛠️ Job Sheets / Lab",
    tab_inventory: "📦 Stock Inventory",
    tab_serials: "🏷️ Serial Tracking",
    tab_billing: "🧾 GST Billing",
    tab_amc: "🏢 AMC Contracts",
    tab_inquiries: "📋 Inquiries & Orders",
    tab_purchase: "🛒 Shortage & Purchase",
    tab_ledger: "📑 Party Accounts & Ledger",
    inq_title: "Customer Inquiries & Leads",
    inq_btn_new: "+ New Inquiry",
    inq_qt_title: "Quotations & Estimates",
    inq_orders_title: "Confirmed Sales Orders",
    shortage_title: "Low Stock & Shortage Requisition",
    po_title: "Supplier Purchase Orders (PO)",
    po_btn_new: "+ New Purchase Order (PO)",
    ledger_title: "Party Accounts & Ledgers (Ledger)",
    ledger_cust_btn: "Customer Accounts",
    ledger_sup_btn: "Supplier Accounts",
    party_btn_new: "+ Add Party / Account"
  }}
}};

function t(key) {{
  const l = (state && state.lang) || "en";
  return (TRANSLATIONS[l] && TRANSLATIONS[l][key]) || (TRANSLATIONS.en && TRANSLATIONS.en[key]) || (TRANSLATIONS.gu && TRANSLATIONS.gu[key]) || key;
}}

function setLanguage(lang) {{
  if (!state) return;
  state.lang = lang;
  try {{
    localStorage.setItem("pcware_lang", lang);
  }} catch(e) {{}}

  const btnEn = document.getElementById("btn-lang-en");
  const btnGu = document.getElementById("btn-lang-gu");
  if (btnEn && btnGu) {{
    if (lang === "en") {{
      btnEn.className = "px-2 py-1 text-xs font-bold rounded-lg transition cursor-pointer bg-white text-brand-600 shadow-sm";
      btnGu.className = "px-2 py-1 text-xs font-bold rounded-lg transition cursor-pointer text-slate-600 hover:text-slate-900";
    }} else {{
      btnGu.className = "px-2 py-1 text-xs font-bold rounded-lg transition cursor-pointer bg-white text-brand-600 shadow-sm";
      btnEn.className = "px-2 py-1 text-xs font-bold rounded-lg transition cursor-pointer text-slate-600 hover:text-slate-900";
    }}
  }}

  const dict = TRANSLATIONS[lang] || TRANSLATIONS.gu;
  document.querySelectorAll("[data-i18n]").forEach(el => {{
    const key = el.getAttribute("data-i18n");
    if (dict[key]) el.textContent = dict[key];
  }});

  document.querySelectorAll("[data-i18n-placeholder]").forEach(el => {{
    const key = el.getAttribute("data-i18n-placeholder");
    if (dict[key]) el.placeholder = dict[key];
  }});

  renderProductsGrid();
  renderPCBuilder();
  updateCartUI();
}}

const state = {{
  lang: (function() {{ try {{ return localStorage.getItem("pcware_lang") || "en"; }} catch(e) {{ return "en"; }} }})(),
  products: (DEFAULT_SEED_DATA && DEFAULT_SEED_DATA.products) ? [...DEFAULT_SEED_DATA.products] : [],
  filteredProducts: (DEFAULT_SEED_DATA && DEFAULT_SEED_DATA.products) ? [...DEFAULT_SEED_DATA.products] : [],
  cart: JSON.parse(localStorage.getItem("pcware_cart") || "[]"),
  currentView: "catalog",
  adminTab: "overview",
  pcBuilder: {{
    processor: null,
    motherboard: null,
    ram: null,
    storage: null,
    gpu: null,
    psu: null,
    cabinet: null
  }},
  jobsheets: (DEFAULT_SEED_DATA && DEFAULT_SEED_DATA.jobsheets) ? [...DEFAULT_SEED_DATA.jobsheets] : [],
  invoices: (DEFAULT_SEED_DATA && DEFAULT_SEED_DATA.invoices) ? [...DEFAULT_SEED_DATA.invoices] : [],
  serials: (DEFAULT_SEED_DATA && DEFAULT_SEED_DATA.serials) ? [...DEFAULT_SEED_DATA.serials] : [],
  amcList: (DEFAULT_SEED_DATA && DEFAULT_SEED_DATA.amc) ? [...DEFAULT_SEED_DATA.amc] : [],
  storeSettings: (DEFAULT_SEED_DATA && DEFAULT_SEED_DATA.settings) ? {{...DEFAULT_SEED_DATA.settings}} : {{}}
}};

function initApp() {{
  setLanguage(state.lang);
  loadStoreSettings();
  loadProducts();
  updateCartUI();
  setupInvoiceLineRowDefault();

  const today = new Date().toISOString().split("T")[0];
  const nextYear = new Date(Date.now() + 365 * 24 * 60 * 60 * 1000).toISOString().split("T")[0];
  const amcStart = document.getElementById("amc-start");
  const amcEnd = document.getElementById("amc-end");
  if (amcStart) amcStart.value = today;
  if (amcEnd) amcEnd.value = nextYear;
}}

if (document.readyState === "loading") {{
  document.addEventListener("DOMContentLoaded", initApp);
}} else {{
  initApp();
}}

async function loadStoreSettings() {{
  const data = await apiGet("store-settings");
  if (data) state.storeSettings = data;
}}

function switchView(viewName) {{
  state.currentView = viewName;
  const views = ["catalog", "builder", "track", "book", "admin"];
  views.forEach(v => {{
    const el = document.getElementById("view-" + v);
    if (el) {{
      if (v === viewName) {{
        el.classList.remove("hidden");
      }} else {{
        el.classList.add("hidden");
      }}
    }}
    
    // Desktop navigation tabs
    const navBtn = document.getElementById("nav-" + v);
    if (navBtn) {{
      if (v === "admin") {{
        if (v === viewName) {{
          navBtn.classList.add("ring-2", "ring-brand-400", "bg-slate-800");
        }} else {{
          navBtn.classList.remove("ring-2", "ring-brand-400", "bg-slate-800");
        }}
      }} else {{
        if (v === viewName) {{
          navBtn.classList.add("text-brand-600", "bg-brand-50", "font-bold");
          navBtn.classList.remove("text-slate-700");
        }} else {{
          navBtn.classList.remove("text-brand-600", "bg-brand-50", "font-bold");
          navBtn.classList.add("text-slate-700");
        }}
      }}
    }}

    // Mobile & Tablet sub-nav buttons
    document.querySelectorAll(`.nav-mobile-btn[data-nav="${{v}}"]`).forEach(btn => {{
      if (v === "admin") {{
        if (v === viewName) {{
          btn.className = "nav-mobile-btn px-3 py-1.5 rounded-lg bg-slate-900 text-brand-300 font-bold shadow-sm whitespace-nowrap cursor-pointer transition flex items-center gap-1";
        }} else {{
          btn.className = "nav-mobile-btn px-3 py-1.5 rounded-lg bg-slate-800 text-slate-200 hover:bg-slate-700 whitespace-nowrap cursor-pointer transition flex items-center gap-1";
        }}
      }} else {{
        if (v === viewName) {{
          btn.className = "nav-mobile-btn px-3 py-1.5 rounded-lg bg-brand-600 text-white font-bold shadow-sm whitespace-nowrap cursor-pointer transition flex items-center gap-1";
        }} else {{
          btn.className = "nav-mobile-btn px-3 py-1.5 rounded-lg bg-slate-100 text-slate-700 hover:bg-brand-50 hover:text-brand-600 whitespace-nowrap cursor-pointer transition flex items-center gap-1";
        }}
      }}
    }});
  }});

  window.scrollTo({{ top: 0, behavior: "smooth" }});

  if (viewName === "catalog") loadProducts();
  if (viewName === "builder") renderPCBuilder();
  if (viewName === "admin") {{
    loadAdminStats();
    switchAdminTab(state.adminTab || "overview");
  }}
}}

function switchAdminTab(tabName) {{
  state.adminTab = tabName;
  const tabs = ["overview", "inquiries_orders", "purchase_shortage", "accounts_ledger", "jobsheets", "inventory", "serials", "billing", "amc"];
  tabs.forEach(t => {{
    const panel = document.getElementById("admin-tab-" + t);
    const btn = document.getElementById("tab-btn-" + t);
    if (panel) {{
      if (t === tabName) {{
        panel.classList.remove("hidden");
      }} else {{
        panel.classList.add("hidden");
      }}
    }}
    if (btn) {{
      if (t === tabName) {{
        btn.classList.add("bg-brand-600", "text-white");
        btn.classList.remove("bg-slate-800", "text-slate-300");
      }} else {{
        btn.classList.remove("bg-brand-600", "text-white");
        btn.classList.add("bg-slate-800", "text-slate-300");
      }}
    }}
  }});

  if (tabName === "overview") loadAdminStats();
  if (tabName === "inquiries_orders") loadInquiriesAndOrders();
  if (tabName === "purchase_shortage") loadPurchaseAndShortage();
  if (tabName === "accounts_ledger") loadAccountsAndLedger();
  if (tabName === "jobsheets") loadJobSheets();
  if (tabName === "inventory") loadInventoryTable();
  if (tabName === "serials") loadSerialsTable();
  if (tabName === "billing") loadInvoicesTable();
  if (tabName === "amc") loadAMCTable();
}}

async function loadProducts() {{
  const data = await apiGet("products");
  if (data) {{
    state.products = data;
    state.filteredProducts = [...data];
    renderProductsGrid();
  }}
}}

function filterCategory(cat, btn) {{
  document.querySelectorAll(".cat-pill").forEach(pill => {{
    pill.classList.remove("bg-brand-600", "text-white", "shadow-sm");
    pill.classList.add("bg-slate-100", "text-slate-700");
  }});
  if (btn) {{
    btn.classList.add("bg-brand-600", "text-white", "shadow-sm");
    btn.classList.remove("bg-slate-100", "text-slate-700");
  }}

  const searchVal = (document.getElementById("catalog-search")?.value || "").toLowerCase().trim();

  state.filteredProducts = state.products.filter(p => {{
    const matchCat = (cat === "all" || p.category === cat);
    const matchSearch = (!searchVal || 
      p.name.toLowerCase().includes(searchVal) ||
      p.brand.toLowerCase().includes(searchVal) ||
      (p.model && p.model.toLowerCase().includes(searchVal)) ||
      p.sku.toLowerCase().includes(searchVal)
    );
    return matchCat && matchSearch;
  }});

  renderProductsGrid();
}}

let searchDebounceTimer = null;
function debounceProductSearch() {{
  clearTimeout(searchDebounceTimer);
  searchDebounceTimer = setTimeout(() => {{
    const searchVal = (document.getElementById("catalog-search")?.value || "").toLowerCase().trim();
    state.filteredProducts = state.products.filter(p => {{
      return (
        p.name.toLowerCase().includes(searchVal) ||
        p.brand.toLowerCase().includes(searchVal) ||
        (p.model && p.model.toLowerCase().includes(searchVal)) ||
        p.sku.toLowerCase().includes(searchVal)
      );
    }});
    renderProductsGrid();
  }}, 200);
}}

function renderProductsGrid() {{
  const container = document.getElementById("products-grid");
  if (!container) return;

  if (state.filteredProducts.length === 0) {{
    container.innerHTML = `
      <div class="col-span-full py-12 text-center text-slate-500">
        <p class="font-semibold text-slate-700">${{t('no_products')}}</p>
        <p class="text-xs text-slate-400">${{t('no_products_desc')}}</p>
      </div>
    `;
    return;
  }}

  container.innerHTML = state.filteredProducts.map(p => {{
    const isLowStock = p.stock_quantity <= p.low_stock_threshold;
    const isOutOfStock = p.stock_quantity <= 0;

    return `
      <div class="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-sm hover:shadow-md transition group flex flex-col justify-between">
        <div class="relative h-44 bg-slate-100 overflow-hidden flex items-center justify-center p-3">
          <img src="${{p.image_url || 'https://images.unsplash.com/photo-1591799264318-7e6ef8ddb7ea?w=400'}}" alt="${{p.name}}" loading="lazy" class="max-h-full max-w-full object-contain group-hover:scale-105 transition duration-300">
          <span class="absolute top-2 left-2 bg-slate-900/80 backdrop-blur text-white text-[10px] font-bold px-2 py-0.5 rounded uppercase">
            ${{p.brand}}
          </span>
          <span class="absolute top-2 right-2 text-[10px] font-bold px-2 py-0.5 rounded ${{
            isOutOfStock ? 'bg-rose-100 text-rose-700 border border-rose-200' :
            isLowStock ? 'bg-amber-100 text-amber-700 border border-amber-200' :
            'bg-emerald-100 text-emerald-700 border border-emerald-200'
          }}">
            ${{isOutOfStock ? t('out_of_stock') : t('stock_prefix') + p.stock_quantity}}
          </span>
        </div>

        <div class="p-4 flex-1 flex flex-col justify-between space-y-3">
          <div class="space-y-1">
            <span class="text-[11px] font-semibold text-brand-600 uppercase tracking-wider">${{p.category}}</span>
            <h3 class="font-bold text-slate-900 text-sm leading-snug line-clamp-2" title="${{p.name}}">${{p.name}}</h3>
            ${{p.specs ? `<p class="text-xs text-slate-500 line-clamp-2">${{p.specs}}</p>` : ''}}
          </div>

          <div class="pt-2 border-t border-slate-100 flex items-center justify-between">
            <div>
              <span class="text-xs text-slate-400 block font-medium leading-tight">${{t('incl_gst')}}</span>
              <span class="text-lg font-black text-slate-900">₹${{p.selling_price.toLocaleString('en-IN')}}</span>
            </div>
            <button type="button" onclick="addToCart(${{p.id}})" ${{isOutOfStock ? 'disabled' : ''}} class="bg-brand-600 hover:bg-brand-700 disabled:bg-slate-300 text-white font-semibold text-xs px-3.5 py-2 rounded-xl shadow-sm transition flex items-center gap-1.5 cursor-pointer">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"/></svg>
              <span>${{t('add_to_cart')}}</span>
            </button>
          </div>
        </div>
      </div>
    `;
  }}).join("");
}}

function toggleCartDrawer(open) {{
  const drawer = document.getElementById("cart-drawer");
  if (drawer) {{
    if (open) drawer.classList.remove("hidden");
    else drawer.classList.add("hidden");
  }}
}}

function addToCart(productId) {{
  const product = state.products.find(p => p.id === productId);
  if (!product) return;

  const existing = state.cart.find(item => item.id === productId);
  if (existing) {{
    if (existing.qty < product.stock_quantity) {{
      existing.qty += 1;
      showToast(product.name + " નો જથ્થો વધાર્યો (+1)");
    }} else {{
      showToast("માફ કરશો, ઉપલબ્ધ સ્ટોક માત્ર " + product.stock_quantity + " છે.", "error");
      return;
    }}
  }} else {{
    state.cart.push({{
      id: product.id,
      sku: product.sku,
      name: product.name,
      price: product.selling_price,
      image_url: product.image_url,
      category: product.category,
      qty: 1
    }});
    showToast("કાર્ટમાં ઉમેર્યું: " + product.name);
  }}

  saveCart();
  updateCartUI();
}}

function updateCartQty(productId, delta) {{
  const item = state.cart.find(i => i.id === productId);
  if (!item) return;

  item.qty += delta;
  if (item.qty <= 0) {{
    state.cart = state.cart.filter(i => i.id !== productId);
  }}
  saveCart();
  updateCartUI();
}}

function saveCart() {{
  localStorage.setItem("pcware_cart", JSON.stringify(state.cart));
}}

function updateCartUI() {{
  const badge = document.getElementById("cart-badge");
  const totalCount = state.cart.reduce((sum, i) => sum + i.qty, 0);
  if (badge) badge.textContent = totalCount;

  const container = document.getElementById("cart-items-container");
  const subtotalEl = document.getElementById("cart-subtotal");
  const grandTotalEl = document.getElementById("cart-grand-total");

  const totalAmount = state.cart.reduce((sum, i) => sum + (i.price * i.qty), 0);

  if (subtotalEl) subtotalEl.textContent = "₹" + totalAmount.toLocaleString('en-IN');
  if (grandTotalEl) grandTotalEl.textContent = "₹" + totalAmount.toLocaleString('en-IN');

  if (!container) return;

  if (state.cart.length === 0) {{
    container.innerHTML = `
      <div class="text-center py-12 text-slate-400">
        <p class="font-medium">${{t('cart_empty')}}</p>
        <p class="text-xs">${{t('cart_empty_sub')}}</p>
      </div>
    `;
    return;
  }}

  container.innerHTML = state.cart.map(item => `
    <div class="py-3 flex items-center justify-between gap-3">
      <div class="flex items-center gap-3">
        <img src="${{item.image_url || 'https://images.unsplash.com/photo-1591799264318-7e6ef8ddb7ea?w=400'}}" class="w-12 h-12 object-contain bg-slate-100 rounded-lg p-1">
        <div>
          <h4 class="font-semibold text-xs text-slate-900 line-clamp-1">${{item.name}}</h4>
          <span class="text-xs text-brand-600 font-bold">₹${{item.price.toLocaleString('en-IN')}}</span>
        </div>
      </div>
      <div class="flex items-center gap-2">
        <button type="button" onclick="updateCartQty(${{item.id}}, -1)" class="w-6 h-6 rounded bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold text-xs flex items-center justify-center cursor-pointer">-</button>
        <span class="text-xs font-bold text-slate-800">${{item.qty}}</span>
        <button type="button" onclick="updateCartQty(${{item.id}}, 1)" class="w-6 h-6 rounded bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold text-xs flex items-center justify-center cursor-pointer">+</button>
      </div>
    </div>
  `).join("");
}}

async function placeOrder() {{
  if (state.cart.length === 0) {{
    showToast("કાર્ટ ખાલી છે!", "error");
    return;
  }}

  const name = document.getElementById("order-name")?.value.trim();
  const phone = document.getElementById("order-phone")?.value.trim();
  const address = document.getElementById("order-address")?.value.trim();
  const paymentMethod = document.getElementById("order-payment")?.value;

  if (!name || !phone || !address) {{
    showToast("કૃપા કરીને નામ, મોબાઇલ અને સરનામું ભરો.", "error");
    return;
  }}

  const totalAmount = state.cart.reduce((sum, i) => sum + (i.price * i.qty), 0);

  const payload = {{
    customer_name: name,
    customer_phone: phone,
    customer_address: address,
    payment_method: paymentMethod,
    total_amount: totalAmount,
    items: state.cart
  }};

  const res = await apiPost("orders", payload);
  if (res && res.success) {{
    showToast("ઓર્ડર સફળ થયો! ઓર્ડર નં: " + res.order_number);
    state.cart = [];
    saveCart();
    updateCartUI();
    toggleCartDrawer(false);
    loadProducts();
  }}
}}

const BUILDER_CATEGORIES = [
  {{ key: "processor", title_gu: "1. Processor (CPU / પ્રોસેસર)", title_en: "1. Processor (CPU)", icon: "⚡" }},
  {{ key: "motherboard", title_gu: "2. Motherboard (મધરબોર્ડ)", title_en: "2. Motherboard", icon: "🧩" }},
  {{ key: "ram", title_gu: "3. RAM (મેમરી)", title_en: "3. RAM (Memory)", icon: "💾" }},
  {{ key: "storage", title_gu: "4. Storage (NVMe SSD/HDD)", title_en: "4. Storage (NVMe SSD/HDD)", icon: "💽" }},
  {{ key: "gpu", title_gu: "5. Graphic Card (ગ્રાફિક કાર્ડ)", title_en: "5. Graphic Card (GPU)", icon: "🎮" }},
  {{ key: "psu", title_gu: "6. Power Supply (SMPS પાવર)", title_en: "6. Power Supply (PSU)", icon: "🔌" }},
  {{ key: "cabinet", title_gu: "7. Cabinet / Case (કેબિનેટ)", title_en: "7. Cabinet / Case", icon: "🖥️" }}
];

function getActiveCompatibility() {{
  const cpu = state.pcBuilder.processor;
  const mobo = state.pcBuilder.motherboard;
  const ram = state.pcBuilder.ram;

  const socket = (cpu && cpu.socket) || (mobo && mobo.socket) || null;
  const memoryType = (mobo && mobo.memory_type) || (ram && ram.memory_type) || null;

  return {{ cpu, mobo, ram, socket, memoryType }};
}}

function resetCompatibilityFilters() {{
  state.pcBuilder.processor = null;
  state.pcBuilder.motherboard = null;
  state.pcBuilder.ram = null;
  renderPCBuilder();
  showToast(state.lang === 'en' ? "Compatibility filters cleared." : "કમ્પોનન્ટ ફિલ્ટર્સ રીસેટ કરવામાં આવ્યા.");
}}

async function renderPCBuilder() {{
  const container = document.getElementById("builder-steps-container");
  if (!container) return;

  if (!state.products || state.products.length === 0) {{
    await loadProducts();
  }}

  const {{ cpu, mobo, ram, socket, memoryType }} = getActiveCompatibility();

  let bannerHtml = "";
  if (socket || memoryType) {{
    const filterTitle = state.lang === 'en' ? 'Smart Compatibility Active' : 'કમ્પોનન્ટ સુસંગતતા સક્રિય';
    const filterDesc = state.lang === 'en' ? 'Incompatible parts are automatically hidden.' : 'અસંગત પાર્ટ્સ આપમેળે છુપાવવામાં આવ્યા છે.';
    const resetBtnTxt = state.lang === 'en' ? 'Clear Filters' : 'ફિલ્ટર્સ હટાવો';

    bannerHtml = `
      <div class="mb-4 p-3.5 bg-gradient-to-r from-emerald-50 via-teal-50 to-sky-50 border border-emerald-200 rounded-2xl flex flex-wrap items-center justify-between gap-2 shadow-sm">
        <div class="flex items-center gap-2.5">
          <span class="text-xl">🛡️</span>
          <div>
            <div class="flex items-center gap-1.5 flex-wrap">
              <strong class="font-bold text-slate-900 text-xs">${{filterTitle}}:</strong>
              ${{socket ? `<span class="px-2 py-0.5 bg-emerald-100 text-emerald-800 text-[11px] font-bold rounded-md border border-emerald-200">Socket: ${{socket}}</span>` : ''}}
              ${{memoryType ? `<span class="px-2 py-0.5 bg-teal-100 text-teal-800 text-[11px] font-bold rounded-md border border-teal-200">RAM: ${{memoryType}}</span>` : ''}}
            </div>
            <p class="text-[11px] text-emerald-700 mt-0.5">${{filterDesc}}</p>
          </div>
        </div>
        <button type="button" onclick="resetCompatibilityFilters()" class="text-xs font-bold text-rose-600 hover:text-rose-800 underline flex items-center gap-1 cursor-pointer">
          ✕ ${{resetBtnTxt}}
        </button>
      </div>
    `;
  }}

  const stepsHtml = BUILDER_CATEGORIES.map(cat => {{
    const selected = state.pcBuilder[cat.key];
    let availableItems = state.products.filter(p => p.category === cat.key);
    const catTitle = state.lang === 'en' ? cat.title_en : cat.title_gu;

    let filterBadge = "";
    if (cat.key === "processor") {{
      if (socket) {{
        availableItems = availableItems.filter(p => p.socket === socket);
        filterBadge = `<span class="text-[10px] px-1.5 py-0.5 bg-emerald-50 text-emerald-700 rounded border border-emerald-200 font-semibold">${{socket}} Only</span>`;
      }}
    }} else if (cat.key === "motherboard") {{
      if (socket) {{
        availableItems = availableItems.filter(p => p.socket === socket);
        filterBadge = `<span class="text-[10px] px-1.5 py-0.5 bg-emerald-50 text-emerald-700 rounded border border-emerald-200 font-semibold">${{socket}}</span>`;
      }}
      if (memoryType) {{
        availableItems = availableItems.filter(p => p.memory_type === memoryType);
        filterBadge += ` <span class="text-[10px] px-1.5 py-0.5 bg-teal-50 text-teal-700 rounded border border-teal-200 font-semibold">${{memoryType}}</span>`;
      }}
    }} else if (cat.key === "ram") {{
      if (memoryType) {{
        availableItems = availableItems.filter(p => p.memory_type === memoryType);
        filterBadge = `<span class="text-[10px] px-1.5 py-0.5 bg-teal-50 text-teal-700 rounded border border-teal-200 font-semibold">${{memoryType}} Only</span>`;
      }}
    }}

    return `
      <div class="bg-white rounded-2xl border ${{selected ? 'border-brand-300 ring-1 ring-brand-100' : 'border-slate-200'}} p-5 shadow-sm space-y-3 transition">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2">
            <span class="text-xl">${{cat.icon}}</span>
            <h3 class="font-bold text-slate-900 text-sm">${{catTitle}}</h3>
            ${{filterBadge}}
          </div>
          ${{selected ? `
            <button type="button" onclick="selectPCComponent('${{cat.key}}', null)" class="text-xs font-semibold text-rose-500 hover:text-rose-700 flex items-center gap-1 cursor-pointer">
              ${{t('builder_remove')}}
            </button>
          ` : `
            <span class="text-[11px] font-medium text-slate-400">${{t('builder_pending')}}</span>
          `}}
        </div>

        ${{selected ? `
          <div class="p-3 bg-brand-50/50 rounded-xl border border-brand-100 flex items-center justify-between gap-3">
            <div class="flex items-center gap-3">
              <img src="${{selected.image_url}}" class="w-12 h-12 object-contain bg-white rounded-lg p-1 border border-brand-200">
              <div>
                <h4 class="font-bold text-xs text-slate-900">${{selected.name}}</h4>
                <div class="flex items-center gap-1.5 mt-0.5 flex-wrap">
                  ${{selected.socket ? `<span class="text-[9px] px-1.5 py-0.5 bg-emerald-100 text-emerald-800 rounded font-semibold">Socket: ${{selected.socket}}</span>` : ''}}
                  ${{selected.memory_type ? `<span class="text-[9px] px-1.5 py-0.5 bg-teal-100 text-teal-800 rounded font-semibold">${{selected.memory_type}}</span>` : ''}}
                  <span class="text-[11px] text-slate-500">${{selected.specs || ''}} ${{selected.wattage ? '• ⚡ ' + selected.wattage + 'W TDP' : ''}}</span>
                </div>
              </div>
            </div>
            <div class="text-right">
              <span class="font-black text-sm text-brand-600">₹${{selected.selling_price.toLocaleString('en-IN')}}</span>
            </div>
          </div>
        ` : `
          ${{availableItems.length === 0 ? `
            <div class="p-4 bg-slate-50 rounded-xl text-center text-xs text-slate-500 border border-dashed border-slate-300">
              ${{state.lang === 'en' ? 'No matching components found for the selected socket/memory.' : 'પસંદ કરેલા સોકેટ/મેમરી માટે કોઈ સુસંગત પાર્ટ્સ મળ્યા નથી.'}}
              <br><button type="button" onclick="resetCompatibilityFilters()" class="mt-2 text-brand-600 font-bold underline cursor-pointer">${{state.lang === 'en' ? 'Clear Compatibility Filter' : 'ફિલ્ટર હટાવો'}}</button>
            </div>
          ` : `
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-1">
              ${{availableItems.map(item => `
                <div onclick="selectPCComponent('${{cat.key}}', ${{item.id}})" class="cursor-pointer p-2.5 rounded-xl border border-slate-200 hover:border-brand-500 hover:bg-brand-50/30 transition flex items-center justify-between gap-2">
                  <div class="flex items-center gap-2 overflow-hidden">
                    <img src="${{item.image_url}}" class="w-8 h-8 object-contain rounded bg-slate-50 p-0.5">
                    <div class="truncate">
                      <p class="font-semibold text-xs text-slate-800 truncate">${{item.name}}</p>
                      <div class="flex items-center gap-1 mt-0.5">
                        <span class="text-[10px] text-slate-400">${{item.brand}}</span>
                        ${{item.socket ? `<span class="text-[9px] px-1 bg-emerald-50 text-emerald-700 rounded font-mono font-bold">${{item.socket}}</span>` : ''}}
                        ${{item.memory_type ? `<span class="text-[9px] px-1 bg-teal-50 text-teal-700 rounded font-mono font-bold">${{item.memory_type}}</span>` : ''}}
                      </div>
                    </div>
                  </div>
                  <span class="text-xs font-bold text-slate-900 whitespace-nowrap">₹${{item.selling_price.toLocaleString('en-IN')}}</span>
                </div>
              `).join("")}}
            </div>
          `}}
        `}}
      </div>
    `;
  }}).join("");

  container.innerHTML = bannerHtml + stepsHtml;
  updatePCBuilderSummary();
}}

function selectPCComponent(catKey, productId) {{
  if (!productId) {{
    state.pcBuilder[catKey] = null;
  }} else {{
    const item = state.products.find(p => p.id === productId);
    if (!item) return;

    if (catKey === "processor") {{
      if (state.pcBuilder.motherboard && state.pcBuilder.motherboard.socket !== item.socket) {{
        state.pcBuilder.motherboard = null;
        const note = state.lang === 'en' ? `Socket changed to ${{item.socket}}. Incompatible motherboard cleared.` : `સોકેટ બદલાઈને ${{item.socket}} થયું. અસંગત મધરબોર્ડ દૂર કરાયું.`;
        showToast(note, "info");
      }}
      state.pcBuilder.processor = item;
    }} else if (catKey === "motherboard") {{
      if (state.pcBuilder.processor && state.pcBuilder.processor.socket !== item.socket) {{
        state.pcBuilder.processor = null;
        const note = state.lang === 'en' ? `Motherboard socket is ${{item.socket}}. Incompatible CPU cleared.` : `મધરબોર્ડ સોકેટ ${{item.socket}} છે. અસંગત સીપીયુ દૂર કરાયું.`;
        showToast(note, "info");
      }}
      if (state.pcBuilder.ram && state.pcBuilder.ram.memory_type !== item.memory_type) {{
        state.pcBuilder.ram = null;
        const note = state.lang === 'en' ? `Motherboard requires ${{item.memory_type}} RAM. Incompatible RAM cleared.` : `મધરબોર્ડ ${{item.memory_type}} રેમ માંગે છે. અસંગત રેમ દૂર કરાઈ.`;
        showToast(note, "info");
      }}
      state.pcBuilder.motherboard = item;
    }} else if (catKey === "ram") {{
      if (state.pcBuilder.motherboard && state.pcBuilder.motherboard.memory_type !== item.memory_type) {{
        state.pcBuilder.motherboard = null;
        const note = state.lang === 'en' ? `RAM type is ${{item.memory_type}}. Incompatible motherboard cleared.` : `રેમ પ્રકાર ${{item.memory_type}} છે. અસંગત મધરબોર્ડ દૂર કરાયું.`;
        showToast(note, "info");
      }}
      state.pcBuilder.ram = item;
    }} else {{
      state.pcBuilder[catKey] = item;
    }}

    const msg = state.lang === 'en' ? `Selected: ${{item.name}}` : `પસંદ કર્યું: ${{item.name}}`;
    showToast(msg);
  }}
  renderPCBuilder();
}}

function resetPCBuilder() {{
  Object.keys(state.pcBuilder).forEach(k => state.pcBuilder[k] = null);
  renderPCBuilder();
  showToast(state.lang === 'en' ? "PC configuration reset." : "PC બિલ્ડ રીસેટ કરવામાં આવ્યો.");
}}

function updatePCBuilderSummary() {{
  const chosenListEl = document.getElementById("builder-chosen-list");
  const wattageEl = document.getElementById("builder-wattage");
  const wattBarEl = document.getElementById("builder-watt-bar");
  const psuRecEl = document.getElementById("builder-psu-rec");
  const subtotalEl = document.getElementById("builder-subtotal");
  const grandTotalEl = document.getElementById("builder-grand-total");

  let totalWatt = 60;
  let totalPrice = 0;
  const chosenItems = [];

  Object.entries(state.pcBuilder).forEach(([cat, item]) => {{
    if (item) {{
      chosenItems.push(item);
      totalPrice += item.selling_price;
      if (item.wattage) totalWatt += item.wattage;
    }}
  }});

  if (wattageEl) wattageEl.textContent = totalWatt + " Watts";
  if (wattBarEl) {{
    const percent = Math.min(100, Math.round((totalWatt / 850) * 100));
    wattBarEl.style.width = percent + "%";
    wattBarEl.className = totalWatt > 450 ? "bg-rose-500 h-full transition-all duration-300" : "bg-brand-500 h-full transition-all duration-300";
  }}

  const recPSU = totalWatt < 250 ? "450W" : totalWatt < 400 ? "550W - 650W" : "750W - 850W Gold";
  if (psuRecEl) {{
    const label = state.lang === 'en' ? 'Recommended PSU Rating:' : 'ભલામણ કરેલ SMPS પાવર:';
    psuRecEl.innerHTML = `${{label}} <strong class="text-slate-800">${{recPSU}}</strong>`;
  }}

  if (subtotalEl) subtotalEl.textContent = "₹" + totalPrice.toLocaleString('en-IN');
  if (grandTotalEl) grandTotalEl.textContent = "₹" + totalPrice.toLocaleString('en-IN');

  if (chosenListEl) {{
    if (chosenItems.length === 0) {{
      const emptyTxt = state.lang === 'en' ? 'No components selected yet.' : 'હજુ સુધી કોઈ પાર્ટ્સ પસંદ કરેલ નથી.';
      chosenListEl.innerHTML = `<p class="text-slate-400 italic py-2">${{emptyTxt}}</p>`;
    }} else {{
      chosenListEl.innerHTML = chosenItems.map(item => `
        <div class="py-1.5 flex justify-between items-center text-xs">
          <span class="font-medium text-slate-700 truncate pr-2">${{item.name}}</span>
          <span class="font-bold text-slate-900 whitespace-nowrap">₹${{item.selling_price.toLocaleString('en-IN')}}</span>
        </div>
      `).join("");
    }}
  }}
}}

function addPCBuildToCart() {{
  const chosen = Object.values(state.pcBuilder).filter(Boolean);
  if (chosen.length === 0) {{
    showToast("કૃપા કરીને પહેલા PC પાર્ટ્સ પસંદ કરો!", "error");
    return;
  }}
  chosen.forEach(item => {{
    addToCart(item.id);
  }});
  showToast("સંપૂર્ણ PC કન્ફિગરેશન કાર્ટમાં ઉમેરવામાં આવ્યું!");
  toggleCartDrawer(true);
}}

function shareBuildWhatsApp() {{
  const chosen = Object.values(state.pcBuilder).filter(Boolean);
  if (chosen.length === 0) {{
    showToast("શેર કરવા માટે કોઈ પાર્ટ્સ પસંદ કરેલા નથી.", "error");
    return;
  }}
  let msg = "Hello PCWARE! I want to order this Custom PC Build:\\n\\n";
  let total = 0;
  chosen.forEach(i => {{
    msg += "• " + i.name + ": ₹" + i.selling_price.toLocaleString('en-IN') + "\\n";
    total += i.selling_price;
  }});
  msg += "\\nTotal Estimated Price: ₹" + total.toLocaleString('en-IN') + " (incl. GST)\\nPlease check component stock and delivery!";

  const url = "https://wa.me/917016737271?text=" + encodeURIComponent(msg);
  window.open(url, "_blank");
}}

async function performJobTracking() {{
  const query = document.getElementById("track-input")?.value.trim();
  if (!query) {{
    showToast(t('track_enter_prompt'), "error");
    return;
  }}

  const container = document.getElementById("track-results-container");
  if (!container) return;

  container.innerHTML = `<div class="p-8 text-center text-slate-500 font-semibold">${{state.lang === 'en' ? 'Searching repair records...' : 'સ્ટેટસ શોધી રહ્યું છે...'}}</div>`;

  const results = await apiGet("track?q=" + encodeURIComponent(query));
  if (!results || results.length === 0) {{
    container.innerHTML = `
      <div class="bg-white p-8 rounded-2xl border border-slate-200 text-center space-y-2">
        <h4 class="font-bold text-slate-800 text-base">${{t('track_not_found')}}</h4>
        <p class="text-xs text-slate-500">${{state.lang === 'en' ? 'No job sheets found matching (' + query + '). Please verify the number.' : 'દાખલ કરેલ નંબર (' + query + ') માટે કોઈ જોબ-શીટ નથી મળી. કૃપા કરીને નંબર ફરી ચકાસો.'}}</p>
      </div>
    `;
    return;
  }}

  container.innerHTML = results.map(job => renderTrackJobCard(job)).join("");
}}

function setTrackTest(val) {{
  const input = document.getElementById("track-input");
  if (input) {{
    input.value = val;
    performJobTracking();
  }}
}}

function renderTrackJobCard(job) {{
  const stages = [
    {{ key: "RECEIVED", label: t('stage_received') }},
    {{ key: "DIAGNOSING", label: t('stage_diagnosing') }},
    {{ key: "WAITING_APPROVAL", label: t('stage_waiting') }},
    {{ key: "REPAIRED", label: t('stage_repaired') }},
    {{ key: "DELIVERED", label: t('stage_delivered') }}
  ];

  const statusIdx = stages.findIndex(s => s.key === job.status);
  const currentStep = statusIdx >= 0 ? statusIdx : 0;
  const balance = (job.final_cost || job.estimated_cost || 0) - (job.advance_paid || 0);

  return `
    <div class="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 space-y-6">
      <div class="flex flex-wrap justify-between items-start gap-4 border-b border-slate-100 pb-4">
        <div>
          <span class="text-xs font-bold text-brand-600 bg-brand-50 px-2.5 py-1 rounded-md border border-brand-200">
            ${{job.job_sheet_number}}
          </span>
          <h3 class="text-xl font-black text-slate-900 mt-2">${{job.device_brand}} ${{job.device_model}}</h3>
          <p class="text-xs text-slate-500">${{state.lang === 'en' ? 'Customer' : 'ગ્રાહક'}}: <strong class="text-slate-700">${{job.customer_name}}</strong> • ${{job.customer_phone}}</p>
        </div>
        <div class="text-right">
          <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-extrabold ${{getStatusBadgeClass(job.status)}}">
            ● ${{job.status}}
          </span>
          <p class="text-[11px] text-slate-400 mt-1">${{state.lang === 'en' ? 'Date' : 'દાખલ તારીખ'}}: ${{job.created_at}}</p>
        </div>
      </div>

      <div class="space-y-2">
        <div class="flex items-center justify-between text-xs font-bold text-slate-700">
          <span>${{state.lang === 'en' ? 'Service Progress Timeline:' : 'સર્વિસ પ્રોગ્રેસ (Progress Timeline):'}}</span>
          <span class="text-brand-600">${{stages[currentStep]?.label || job.status}}</span>
        </div>
        <div class="grid grid-cols-5 gap-2 pt-2">
          ${{stages.map((s, idx) => `
            <div class="space-y-1.5 text-center">
              <div class="h-2 rounded-full ${{idx <= currentStep ? 'bg-emerald-500' : 'bg-slate-200'}}"></div>
              <span class="text-[10px] font-semibold block ${{idx <= currentStep ? 'text-emerald-700' : 'text-slate-400'}}">${{s.label.split(' ')[0]}}</span>
            </div>
          `).join("")}}
        </div>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-4 bg-slate-50 p-4 rounded-xl text-xs">
        <div class="space-y-1">
          <span class="font-bold text-slate-700">ફરિયાદ / સમસ્યા (Reported Issue):</span>
          <p class="text-slate-600">${{job.reported_problem}}</p>
          ${{job.accessories_received ? `<p class="text-[11px] text-slate-500 mt-1">સાથે આવેલ એક્સેસરીઝ: <strong>${{job.accessories_received}}</strong></p>` : ''}}
        </div>
        <div class="space-y-1 border-t md:border-t-0 md:border-l border-slate-200 pt-2 md:pt-0 md:pl-4">
          <span class="font-bold text-brand-700">લેબ ડાયગ્નોસ્ટિક અને ટેકનિશિયન નોંધ:</span>
          <p class="text-slate-600 italic">${{job.technician_notes || 'ટેકનિશિયન હાલ તપાસ કરી રહ્યો છે.'}}</p>
          ${{job.assigned_technician ? `<p class="text-[11px] text-slate-500 mt-1">ઇજનેર: <strong>${{job.assigned_technician}}</strong></p>` : ''}}
        </div>
      </div>

      <div class="flex flex-wrap items-center justify-between gap-4 p-4 rounded-xl border border-slate-200 bg-white">
        <div class="flex items-center space-x-6 text-xs">
          <div>
            <span class="text-slate-400 block">કુલ / અંદાજિત ખર્ચ:</span>
            <span class="text-base font-black text-slate-900">₹${{(job.final_cost || job.estimated_cost || 0).toLocaleString('en-IN')}}</span>
          </div>
          <div>
            <span class="text-slate-400 block">એડવાન્સ જમા:</span>
            <span class="text-base font-bold text-emerald-600">₹${{(job.advance_paid || 0).toLocaleString('en-IN')}}</span>
          </div>
          <div>
            <span class="text-slate-400 block">બાકી રકમ (Balance Due):</span>
            <span class="text-base font-black text-rose-600">₹${{Math.max(0, balance).toLocaleString('en-IN')}}</span>
          </div>
        </div>

        <div class="flex items-center gap-2">
          <button type="button" onclick="printJobSheet(${{job.id}})" class="text-xs font-semibold text-slate-700 hover:text-brand-600 border border-slate-300 hover:border-brand-300 py-2 px-3 rounded-lg flex items-center gap-1.5 cursor-pointer">
            જોબ સ્લિપ પ્રિન્ટ
          </button>
          <a href="tel:+919825012345" class="bg-brand-600 hover:bg-brand-700 text-white font-semibold text-xs py-2 px-3.5 rounded-lg shadow flex items-center gap-1.5">
            📞 હેલ્પલાઇન કોલ
          </a>
        </div>
      </div>
    </div>
  `;
}}

function getStatusBadgeClass(status) {{
  switch (status) {{
    case "RECEIVED": return "bg-blue-100 text-blue-800 border border-blue-200";
    case "DIAGNOSING": return "bg-amber-100 text-amber-800 border border-amber-200";
    case "WAITING_APPROVAL": return "bg-purple-100 text-purple-800 border border-purple-200";
    case "REPAIRED": return "bg-emerald-100 text-emerald-800 border border-emerald-200";
    case "DELIVERED": return "bg-slate-100 text-slate-700 border border-slate-300";
    default: return "bg-slate-100 text-slate-600";
  }}
}}

async function submitServiceBooking(e) {{
  e.preventDefault();
  const name = document.getElementById("book-name")?.value.trim();
  const phone = document.getElementById("book-phone")?.value.trim();
  const deviceType = document.getElementById("book-device-type")?.value;
  const brand = document.getElementById("book-brand")?.value.trim();
  const model = document.getElementById("book-model")?.value.trim();
  const address = document.getElementById("book-address")?.value.trim();
  const problem = document.getElementById("book-problem")?.value.trim();

  const payload = {{
    name, phone, device_type: deviceType, brand, model, address, problem
  }};

  const res = await apiPost("service-booking", payload);
  if (res && res.success) {{
    showToast("સર્વિસ રિક્વેસ્ટ બુક થઈ ગઈ! ટોકન #: " + res.job_sheet_number);
    document.getElementById("service-booking-form")?.reset();
    switchView("track");
    setTrackTest(res.job_sheet_number);
  }}
}}

async function loadAdminStats() {{
  const stats = await apiGet("stats");
  if (!stats) return;

  const prodEl = document.getElementById("stat-products");
  const repairsEl = document.getElementById("stat-active-repairs");
  const readyEl = document.getElementById("stat-repairs-ready");
  const lowStockEl = document.getElementById("stat-low-stock");
  const revEl = document.getElementById("stat-revenue");

  if (prodEl) prodEl.textContent = stats.total_products;
  if (repairsEl) repairsEl.textContent = stats.active_repairs;
  if (readyEl) readyEl.textContent = stats.repairs_ready;
  if (lowStockEl) lowStockEl.textContent = stats.low_stock_count;
  if (revEl) revEl.textContent = "₹" + Math.round(stats.total_revenue).toLocaleString('en-IN');

  const jobsTbody = document.getElementById("overview-jobs-tbody");
  if (jobsTbody && stats.recent_jobs) {{
    jobsTbody.innerHTML = stats.recent_jobs.map(j => `
      <tr class="hover:bg-slate-50">
        <td class="py-2.5 font-bold text-brand-600">${{j.job_sheet_number}}</td>
        <td class="py-2.5 font-medium text-slate-800">${{j.customer_name}}</td>
        <td class="py-2.5 text-slate-600">${{j.device_brand}} ${{j.device_model}}</td>
        <td class="py-2.5"><span class="px-2 py-0.5 rounded text-[10px] font-bold ${{getStatusBadgeClass(j.status)}}">${{j.status}}</span></td>
      </tr>
    `).join("");
  }}

  const lowStockTbody = document.getElementById("overview-lowstock-tbody");
  if (lowStockTbody && stats.low_stock_items) {{
    lowStockTbody.innerHTML = stats.low_stock_items.map(p => `
      <tr class="hover:bg-slate-50">
        <td class="py-2.5 font-medium text-slate-800">${{p.name}}</td>
        <td class="py-2.5 font-black text-rose-600">${{p.stock_quantity}} બાકી</td>
        <td class="py-2.5 font-bold text-slate-700">₹${{p.selling_price.toLocaleString('en-IN')}}</td>
      </tr>
    `).join("");
  }}
}}

async function loadJobSheets() {{
  const search = document.getElementById("jobsheet-filter-search")?.value || "";
  const status = document.getElementById("jobsheet-filter-status")?.value || "all";

  const data = await apiGet("jobsheets?status=" + status + "&search=" + encodeURIComponent(search));
  if (!data) return;

  state.jobsheets = data;
  const tbody = document.getElementById("jobsheets-table-body");
  if (!tbody) return;

  if (data.length === 0) {{
    tbody.innerHTML = `<tr><td colspan="7" class="py-8 text-center text-slate-400">કોઈ જોબ શીટ મળી નથી.</td></tr>`;
    return;
  }}

  tbody.innerHTML = data.map(j => `
    <tr class="hover:bg-slate-50/80 transition">
      <td class="py-3 px-4">
        <span class="font-bold text-brand-600">${{j.job_sheet_number}}</span>
        <span class="block text-[10px] text-slate-400">${{(j.created_at || '').split(' ')[0]}}</span>
      </td>
      <td class="py-3 px-4">
        <span class="font-semibold text-slate-900">${{j.customer_name}}</span>
        <span class="block text-[11px] text-slate-500">${{j.customer_phone}}</span>
      </td>
      <td class="py-3 px-4">
        <span class="font-medium text-slate-800">${{j.device_type}}: ${{j.device_brand}} ${{j.device_model}}</span>
        <span class="block text-[10px] text-slate-400 font-mono">SN: ${{j.device_serial || 'N/A'}}</span>
      </td>
      <td class="py-3 px-4 max-w-xs">
        <span class="line-clamp-2 text-slate-600">${{j.reported_problem}}</span>
      </td>
      <td class="py-3 px-4">
        <span class="px-2.5 py-1 rounded-md text-[11px] font-bold ${{getStatusBadgeClass(j.status)}}">
          ${{j.status}}
        </span>
      </td>
      <td class="py-3 px-4">
        <span class="font-bold text-slate-900">₹${{(j.final_cost || j.estimated_cost || 0).toLocaleString('en-IN')}}</span>
        <span class="block text-[10px] text-emerald-600">જમા: ₹${{(j.advance_paid || 0).toLocaleString('en-IN')}}</span>
      </td>
      <td class="py-3 px-4 text-right space-x-1 whitespace-nowrap">
        <button type="button" onclick="openUpdateJobSheetModal(${{j.id}})" class="px-2.5 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-800 font-semibold rounded-md text-[11px] transition cursor-pointer">
          અપડેટ
        </button>
        <button type="button" onclick="printJobSheet(${{j.id}})" class="px-2.5 py-1.5 bg-brand-50 hover:bg-brand-100 text-brand-700 font-semibold rounded-md text-[11px] transition cursor-pointer">
          પ્રિન્ટ
        </button>
      </td>
    </tr>
  `).join("");
}}

async function loadInventoryTable() {{
  const search = document.getElementById("inv-search")?.value || "";
  const cat = document.getElementById("inv-category-select")?.value || "all";

  const data = await apiGet("products?category=" + cat + "&search=" + encodeURIComponent(search));
  if (!data) return;

  const tbody = document.getElementById("inventory-table-body");
  if (!tbody) return;

  tbody.innerHTML = data.map(p => `
    <tr class="hover:bg-slate-50 transition">
      <td class="py-3 px-4">
        <span class="font-bold text-slate-900">${{p.sku}}</span>
        <span class="block text-[10px] text-slate-400">HSN: ${{p.hsn_code}}</span>
      </td>
      <td class="py-3 px-4 font-semibold text-slate-800">${{p.name}}</td>
      <td class="py-3 px-4">
        <span class="capitalize text-slate-600">${{p.category}}</span>
        <span class="block text-[11px] text-slate-400 font-semibold">${{p.brand}}</span>
      </td>
      <td class="py-3 px-4 text-slate-600">₹${{p.cost_price.toLocaleString('en-IN')}}</td>
      <td class="py-3 px-4 font-bold text-slate-900">₹${{p.selling_price.toLocaleString('en-IN')}}</td>
      <td class="py-3 px-4">
        <span class="px-2 py-0.5 rounded text-xs font-bold ${{
          p.stock_quantity <= p.low_stock_threshold ? 'bg-rose-100 text-rose-700 border border-rose-200' : 'bg-emerald-100 text-emerald-800'
        }}">
          ${{p.stock_quantity}}
        </span>
      </td>
      <td class="py-3 px-4 text-right">
        <button type="button" onclick="deleteProduct(${{p.id}})" class="text-slate-400 hover:text-rose-600 p-1 cursor-pointer">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
        </button>
      </td>
    </tr>
  `).join("");
}}

async function deleteProduct(id) {{
  if (!confirm("શું તમે ખરેખર આ પ્રોડક્ટ ડિલીટ કરવા માંગો છો?")) return;
  const db = getLocalDB();
  db.products = db.products.filter(p => p.id !== id);
  saveLocalDB(db);
  showToast("પ્રોડક્ટ સફળતાપૂર્વક ડિલીટ કર્યો.");
  loadInventoryTable();
  loadProducts();
}}

async function loadSerialsTable() {{
  const q = document.getElementById("serial-search")?.value || "";
  const data = await apiGet("serials?q=" + encodeURIComponent(q));
  if (!data) return;

  const tbody = document.getElementById("serials-table-body");
  if (!tbody) return;

  tbody.innerHTML = data.map(s => `
    <tr class="hover:bg-slate-50 transition">
      <td class="py-3 px-4 font-mono font-bold text-slate-900">${{s.serial_number}}</td>
      <td class="py-3 px-4">
        <span class="font-semibold text-slate-800">${{s.product_name || 'Generic Item'}}</span>
        <span class="block text-[11px] text-slate-400">${{s.product_brand || ''}}</span>
      </td>
      <td class="py-3 px-4 text-slate-600">
        <span>${{s.supplier_name || 'N/A'}}</span>
        <span class="block text-[10px] text-slate-400">${{s.purchase_date}}</span>
      </td>
      <td class="py-3 px-4 font-semibold text-slate-700">${{s.warranty_months}} મહિના</td>
      <td class="py-3 px-4">
        <span class="px-2 py-0.5 rounded text-[10px] font-bold ${{
          s.status === 'IN_STOCK' ? 'bg-emerald-100 text-emerald-800' :
          s.status === 'SOLD' ? 'bg-blue-100 text-blue-800' :
          'bg-amber-100 text-amber-800'
        }}">${{s.status}}</span>
      </td>
      <td class="py-3 px-4 text-xs">
        ${{s.customer_name ? `
          <span class="font-semibold text-slate-900">${{s.customer_name}}</span>
          <span class="block text-[10px] text-slate-400">બિલ: ${{s.invoice_number || '-'}} (${{s.sold_date}})</span>
        ` : `
          <span class="text-slate-400 italic">ગોડાઉનમાં ઉપલબ્ધ</span>
        `}}
      </td>
    </tr>
  `).join("");
}}

async function loadInvoicesTable() {{
  const data = await apiGet("invoices");
  if (!data) return;

  state.invoices = data;
  const tbody = document.getElementById("invoices-table-body");
  if (!tbody) return;

  tbody.innerHTML = data.map(inv => `
    <tr class="hover:bg-slate-50 transition">
      <td class="py-3 px-4">
        <span class="font-bold text-emerald-700">${{inv.invoice_number}}</span>
        <span class="block text-[10px] text-slate-400">${{inv.invoice_date}}</span>
      </td>
      <td class="py-3 px-4">
        <span class="font-semibold text-slate-900">${{inv.customer_name}}</span>
        <span class="block text-[11px] text-slate-500">${{inv.customer_phone}}</span>
      </td>
      <td class="py-3 px-4 font-mono text-xs text-slate-700">${{inv.customer_gstin || 'B2C Retail'}}</td>
      <td class="py-3 px-4 text-slate-600">₹${{(inv.cgst + inv.sgst + (inv.igst || 0)).toLocaleString('en-IN')}}</td>
      <td class="py-3 px-4 font-black text-slate-900">₹${{inv.grand_total.toLocaleString('en-IN')}}</td>
      <td class="py-3 px-4">
        <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-100 text-slate-700">${{inv.payment_method}}</span>
      </td>
      <td class="py-3 px-4 text-right">
        <button type="button" onclick="printGSTInvoice(${{inv.id}})" class="px-3 py-1 bg-emerald-50 hover:bg-emerald-100 text-emerald-700 font-semibold rounded-md text-xs transition flex items-center gap-1 ml-auto cursor-pointer">
          <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z"/></svg>
          બિલ પ્રિન્ટ
        </button>
      </td>
    </tr>
  `).join("");
}}

async function loadAMCTable() {{
  const data = await apiGet("amc");
  if (!data) return;

  const tbody = document.getElementById("amc-table-body");
  if (!tbody) return;

  tbody.innerHTML = data.map(a => `
    <tr class="hover:bg-slate-50 transition">
      <td class="py-3 px-4 font-bold text-brand-600">${{a.contract_number}}</td>
      <td class="py-3 px-4">
        <span class="font-bold text-slate-900">${{a.client_name}}</span>
        <span class="block text-[11px] text-slate-500">${{a.address}}</span>
      </td>
      <td class="py-3 px-4">
        <span class="text-slate-800 font-medium">${{a.contact_person || '-'}}</span>
        <span class="block text-[11px] text-slate-500">${{a.phone}}</span>
      </td>
      <td class="py-3 px-4 font-bold text-slate-700">${{a.total_systems}} સિસ્ટમ્સ</td>
      <td class="py-3 px-4 text-xs text-slate-600">${{a.start_date}} થી ${{a.end_date}}</td>
      <td class="py-3 px-4 font-black text-slate-900">₹${{a.contract_value.toLocaleString('en-IN')}}</td>
      <td class="py-3 px-4">
        <span class="px-2 py-0.5 rounded text-[10px] font-bold ${{
          a.status === 'ACTIVE' ? 'bg-emerald-100 text-emerald-800' :
          a.status === 'EXPIRING_SOON' ? 'bg-amber-100 text-amber-800 font-black animate-pulse' :
          'bg-slate-100 text-slate-700'
        }}">${{a.status}}</span>
      </td>
    </tr>
  `).join("");
}}

// ==========================================
// ERP WORKFLOW 1: INQUIRIES, QUOTATIONS & ORDERS
// ==========================================
async function loadInquiriesAndOrders() {{
  const [inquiries, quotations, orders, parties] = await Promise.all([
    apiGet("inquiries"),
    apiGet("quotations"),
    apiGet("orders"),
    apiGet("parties")
  ]);

  if (inquiries) state.inquiries = inquiries;
  if (quotations) state.quotations = quotations;
  if (orders) state.orders = orders;
  if (parties) state.parties = parties;

  renderInquiriesList();
  renderQuotationsList();
  renderERPOrdersList();
}}

function renderInquiriesList() {{
  const tbody = document.getElementById("inquiries-table-body");
  if (!tbody) return;
  const list = state.inquiries || [];

  const statTotal = document.getElementById("stat-inq-total");
  const statPending = document.getElementById("stat-inq-pending");
  if (statTotal) statTotal.textContent = list.length;
  if (statPending) statPending.textContent = list.filter(i => i.status === 'NEW' || i.status === 'IN_PROGRESS').length;

  if (list.length === 0) {{
    tbody.innerHTML = `<tr><td colspan="6" class="text-center py-6 text-slate-400">કોઈ ઇન્ક્વાયરી નોંધાયેલ નથી.</td></tr>`;
    return;
  }}

  tbody.innerHTML = list.map(inq => `
    <tr class="hover:bg-slate-50 transition border-b border-slate-100">
      <td class="py-3 px-4 font-mono font-bold text-slate-800 text-xs">
        ${{inq.inquiry_number}}
        <span class="block text-[10px] text-slate-400">${{inq.source || 'Walk-in'}} • ${{inq.created_at || ''}}</span>
      </td>
      <td class="py-3 px-4">
        <span class="font-bold text-slate-900">${{inq.customer_name}}</span>
        ${{inq.company_name ? `<span class="block text-[11px] text-slate-500 font-medium">${{inq.company_name}}</span>` : ''}}
        <span class="block text-[11px] text-slate-500">📞 ${{inq.customer_phone || inq.phone || '-'}}</span>
      </td>
      <td class="py-3 px-4 max-w-xs">
        <span class="font-semibold text-slate-800">${{inq.subject || inq.requirement_type || 'Hardware Inquiry'}}</span>
        <p class="text-[11px] text-slate-500 line-clamp-2 mt-0.5">${{inq.requirements || inq.items_requested || inq.notes || '-'}}</p>
      </td>
      <td class="py-3 px-4 font-bold text-slate-900">
        ₹${{Number(inq.estimated_budget || 0).toLocaleString('en-IN')}}
      </td>
      <td class="py-3 px-4">
        <span class="px-2 py-0.5 rounded-full text-[10px] font-bold ${{
          inq.status === 'NEW' ? 'bg-blue-100 text-blue-800' :
          inq.status === 'QUOTED' ? 'bg-purple-100 text-purple-800' :
          inq.status === 'WON' || inq.status === 'ORDER_CONFIRMED' ? 'bg-emerald-100 text-emerald-800' :
          'bg-slate-100 text-slate-600'
        }}">${{inq.status}}</span>
      </td>
      <td class="py-3 px-4 text-right whitespace-nowrap">
        <button type="button" onclick="openQuotationModal(${{inq.id}})" class="px-2.5 py-1 bg-brand-50 hover:bg-brand-100 text-brand-700 font-semibold rounded text-xs transition cursor-pointer">
          📝 Quotation બનાવો
        </button>
      </td>
    </tr>
  `).join("");
}}

function renderQuotationsList() {{
  const tbody = document.getElementById("quotations-table-body");
  if (!tbody) return;
  const list = state.quotations || [];

  if (list.length === 0) {{
    tbody.innerHTML = `<tr><td colspan="7" class="text-center py-6 text-slate-400">કોઈ ક્વોટેશન તૈયાર નથી.</td></tr>`;
    return;
  }}

  tbody.innerHTML = list.map(q => `
    <tr class="hover:bg-slate-50 transition border-b border-slate-100">
      <td class="py-3 px-4 font-mono font-bold text-brand-700 text-xs">
        ${{q.quotation_number}}
        <span class="block text-[10px] text-slate-400">${{q.created_at || ''}}</span>
      </td>
      <td class="py-3 px-4">
        <span class="font-bold text-slate-900">${{q.customer_name}}</span>
        <span class="block text-[11px] text-slate-500">📞 ${{q.customer_phone || q.phone || '-'}}</span>
      </td>
      <td class="py-3 px-4 text-xs text-slate-700">
        ${{(() => {{
          const it = q.items_json ? (typeof q.items_json === 'string' ? JSON.parse(q.items_json) : q.items_json) : (q.items ? (typeof q.items === 'string' ? JSON.parse(q.items) : q.items) : []);
          return (it && it.length) ? it.length : 0;
        }})()}} આઇટમ્સ
      </td>
      <td class="py-3 px-4 text-xs text-slate-600">
        ₹${{Number(q.subtotal || 0).toLocaleString('en-IN')}}
      </td>
      <td class="py-3 px-4 font-black text-slate-900 text-xs">
        ₹${{Number(q.grand_total || 0).toLocaleString('en-IN')}}
      </td>
      <td class="py-3 px-4">
        <span class="px-2 py-0.5 rounded-full text-[10px] font-bold ${{
          q.status === 'CONVERTED' ? 'bg-emerald-100 text-emerald-800' :
          q.status === 'ACCEPTED' ? 'bg-blue-100 text-blue-800' :
          q.status === 'SENT' ? 'bg-amber-100 text-amber-800' :
          'bg-slate-100 text-slate-700'
        }}">${{q.status}}</span>
      </td>
      <td class="py-3 px-4 text-right whitespace-nowrap space-x-1">
        <button type="button" onclick="printQuotation(${{q.id}})" class="px-2 py-1 bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold rounded text-xs transition cursor-pointer">
          🖨️ પ્રિન્ટ
        </button>
        ${{q.status !== 'CONVERTED' ? `
          <button type="button" onclick="convertQuotationToOrder(${{q.id}})" class="px-2.5 py-1 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold rounded text-xs transition cursor-pointer shadow-sm">
            ✓ ઓર્ડરમાં ફેરવો
          </button>
        ` : `
          <span class="text-xs text-emerald-600 font-semibold">ઓર્ડર કન્ફર્મ</span>
        `}}
      </td>
    </tr>
  `).join("");
}}

function renderERPOrdersList() {{
  const tbody = document.getElementById("erp-orders-table-body");
  if (!tbody) return;
  const list = state.orders || [];

  const statOrders = document.getElementById("stat-orders-total");
  if (statOrders) statOrders.textContent = list.length;

  if (list.length === 0) {{
    tbody.innerHTML = `<tr><td colspan="7" class="text-center py-6 text-slate-400">કોઈ સેલ્સ ઓર્ડર મળ્યા નથી.</td></tr>`;
    return;
  }}

  tbody.innerHTML = list.map(o => `
    <tr class="hover:bg-slate-50 transition border-b border-slate-100">
      <td class="py-3 px-4 font-mono font-bold text-slate-800 text-xs">
        ${{o.order_number}}
        <span class="block text-[10px] text-slate-400">${{o.created_at || ''}}</span>
      </td>
      <td class="py-3 px-4">
        <span class="font-bold text-slate-900">${{o.customer_name}}</span>
        <span class="block text-[11px] text-slate-500">📞 ${{o.customer_phone}}</span>
      </td>
      <td class="py-3 px-4 text-xs text-slate-700">
        ${{o.items ? (typeof o.items === 'string' ? JSON.parse(o.items).length : o.items.length) : 0}} આઇટમ્સ
      </td>
      <td class="py-3 px-4 font-black text-slate-900 text-xs">
        ₹${{Number(o.total_amount || 0).toLocaleString('en-IN')}}
      </td>
      <td class="py-3 px-4">
        <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-100 text-slate-700">${{o.payment_method || 'COD'}}</span>
      </td>
      <td class="py-3 px-4">
        <span class="px-2 py-0.5 rounded-full text-[10px] font-bold ${{
          o.status === 'DELIVERED' ? 'bg-emerald-100 text-emerald-800' :
          o.status === 'CONFIRMED' ? 'bg-blue-100 text-blue-800' :
          'bg-amber-100 text-amber-800'
        }}">${{o.status}}</span>
      </td>
      <td class="py-3 px-4 text-right whitespace-nowrap">
        ${{o.status !== 'DELIVERED' ? `
          <button type="button" onclick="fulfillOrder(${{o.id}})" class="px-2.5 py-1 bg-brand-600 hover:bg-brand-700 text-white font-semibold rounded text-xs transition cursor-pointer shadow-sm">
            📦 ડિલિવર & GST બિલ બનાવો
          </button>
        ` : `
          <span class="text-xs text-emerald-600 font-semibold flex items-center justify-end gap-1">
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>
            બિલ & સ્ટોક પૂર્ણ
          </span>
        `}}
      </td>
    </tr>
  `).join("");
}}

function openNewInquiryModal() {{
  const form = document.getElementById("form-new-inquiry");
  if (form) form.reset();
  document.getElementById("modal-new-inquiry")?.classList.remove("hidden");
}}

async function handleCreateInquirySubmit(e) {{
  e.preventDefault();
  const payload = {{
    customer_name: document.getElementById("inq-cust-name")?.value,
    phone: document.getElementById("inq-cust-phone")?.value,
    email: document.getElementById("inq-cust-email")?.value,
    company_name: document.getElementById("inq-company")?.value,
    subject: document.getElementById("inq-subject")?.value,
    requirements: document.getElementById("inq-req")?.value,
    estimated_budget: parseFloat(document.getElementById("inq-budget")?.value || 0),
    source: document.getElementById("inq-source")?.value || "Walk-in"
  }};

  const res = await apiPost("inquiries", payload);
  if (res && res.success) {{
    showToast("નવી ઇન્ક્વાયરી નોંધાઈ ગઈ: " + res.inquiry_number);
    closeModal("modal-new-inquiry");
    loadInquiriesAndOrders();
  }} else {{
    showToast("ઇન્ક્વાયરી સેવ કરવામાં ભૂલ આવી", "error");
  }}
}}

function openQuotationModal(inquiryId = null) {{
  const form = document.getElementById("form-create-quotation");
  if (form) form.reset();

  const partySelect = document.getElementById("quote-party-id");
  if (partySelect) {{
    const parties = (state.parties || []).filter(p => p.party_type === 'CUSTOMER');
    partySelect.innerHTML = `<option value="">-- નવો / અન્ય ગ્રાહક --</option>` +
      parties.map(p => `<option value="${{p.id}}" data-phone="${{p.phone || ''}}" data-name="${{p.name}}">${{p.name}} (${{p.phone || 'No phone'}})</option>`).join("");
  }}

  const today = new Date();
  const nextMonth = new Date(today.getTime() + 15 * 24 * 60 * 60 * 1000);
  const validUntilInput = document.getElementById("quote-valid-until");
  if (validUntilInput) validUntilInput.value = nextMonth.toISOString().split("T")[0];

  const inqInput = document.getElementById("quote-inquiry-id");
  if (inqInput) inqInput.value = inquiryId || "";

  if (inquiryId && state.inquiries) {{
    const inq = state.inquiries.find(i => i.id == inquiryId);
    if (inq) {{
      const nameInput = document.getElementById("quote-cust-name");
      const phoneInput = document.getElementById("quote-cust-phone");
      const emailInput = document.getElementById("quote-cust-email");
      const notesInput = document.getElementById("quote-notes");
      if (nameInput) nameInput.value = inq.customer_name || inq.company_name || "";
      if (phoneInput) phoneInput.value = inq.phone || "";
      if (emailInput) emailInput.value = inq.email || "";
      if (notesInput) notesInput.value = "ઇન્ક્વાયરી સંદર્ભ: " + inq.inquiry_number + " - " + inq.subject;
    }}
  }}

  const tbody = document.getElementById("quote-items-tbody");
  if (tbody) {{
    tbody.innerHTML = "";
    addQuotationLineRow();
  }}

  calculateQuotationTotals();
  document.getElementById("modal-create-quotation")?.classList.remove("hidden");
}}

function onQuotationPartySelect(select) {{
  const opt = select.options[select.selectedIndex];
  if (opt && opt.value) {{
    const nameInput = document.getElementById("quote-cust-name");
    const phoneInput = document.getElementById("quote-cust-phone");
    if (nameInput) nameInput.value = opt.getAttribute("data-name") || "";
    if (phoneInput) phoneInput.value = opt.getAttribute("data-phone") || "";
  }}
}}

function addQuotationLineRow(productId = null, qty = 1, rate = null) {{
  const tbody = document.getElementById("quote-items-tbody");
  if (!tbody) return;

  const rowId = "quote-row-" + Date.now() + "-" + Math.floor(Math.random() * 1000);
  const products = state.products || [];

  const tr = document.createElement("tr");
  tr.id = rowId;
  tr.className = "border-b border-slate-100 quote-line-row";
  tr.innerHTML = `
    <td class="py-2 px-2">
      <select class="w-full text-xs p-1.5 border border-slate-300 rounded outline-none quote-product-select" onchange="onQuoteProductChange('${{rowId}}')">
        <option value="">-- આઇટમ પસંદ કરો --</option>
        ${{products.map(p => `<option value="${{p.id}}" data-price="${{p.price}}" data-tax="${{p.tax_rate || 18}}" ${{productId == p.id ? 'selected' : ''}}>${{p.name}} (₹${{p.price}})</option>`).join("")}}
      </select>
    </td>
    <td class="py-2 px-2 w-20">
      <input type="number" min="1" value="${{qty}}" class="w-full text-xs p-1.5 border border-slate-300 rounded outline-none quote-qty" oninput="calculateQuotationTotals()">
    </td>
    <td class="py-2 px-2 w-28">
      <input type="number" step="0.01" value="${{rate !== null ? rate : 0}}" class="w-full text-xs p-1.5 border border-slate-300 rounded outline-none quote-rate" oninput="calculateQuotationTotals()">
    </td>
    <td class="py-2 px-2 w-20 text-center text-xs text-slate-600 quote-tax-rate">18%</td>
    <td class="py-2 px-2 w-28 text-right font-bold text-xs text-slate-800 quote-line-total">₹0</td>
    <td class="py-2 px-2 w-10 text-center">
      <button type="button" onclick="document.getElementById('${{rowId}}').remove(); calculateQuotationTotals();" class="text-rose-500 hover:text-rose-700 font-bold text-sm cursor-pointer">✕</button>
    </td>
  `;

  tbody.appendChild(tr);
  if (productId) onQuoteProductChange(rowId);
  calculateQuotationTotals();
}}

function onQuoteProductChange(rowId) {{
  const row = document.getElementById(rowId);
  if (!row) return;
  const select = row.querySelector(".quote-product-select");
  const opt = select.options[select.selectedIndex];
  if (opt && opt.value) {{
    const price = parseFloat(opt.getAttribute("data-price") || 0);
    const tax = opt.getAttribute("data-tax") || "18";
    const rateInput = row.querySelector(".quote-rate");
    const taxSpan = row.querySelector(".quote-tax-rate");
    if (rateInput) rateInput.value = price;
    if (taxSpan) taxSpan.textContent = tax + "%";
  }}
  calculateQuotationTotals();
}}

function calculateQuotationTotals() {{
  let subtotal = 0;
  let taxTotal = 0;

  const rows = document.querySelectorAll(".quote-line-row");
  rows.forEach(row => {{
    const qty = parseFloat(row.querySelector(".quote-qty")?.value || 0);
    const rate = parseFloat(row.querySelector(".quote-rate")?.value || 0);
    const taxText = row.querySelector(".quote-tax-rate")?.textContent || "18%";
    const taxRate = parseFloat(taxText.replace("%", "")) || 18;

    const lineBase = qty * rate;
    const lineTax = (lineBase * taxRate) / 100;
    const lineTotal = lineBase + lineTax;

    subtotal += lineBase;
    taxTotal += lineTax;

    const totalCell = row.querySelector(".quote-line-total");
    if (totalCell) totalCell.textContent = "₹" + Math.round(lineTotal).toLocaleString('en-IN');
  }});

  const cgst = taxTotal / 2;
  const sgst = taxTotal / 2;
  const grandTotal = subtotal + taxTotal;

  const elSubtotal = document.getElementById("quote-subtotal");
  const elCgst = document.getElementById("quote-cgst");
  const elSgst = document.getElementById("quote-sgst");
  const elGrand = document.getElementById("quote-grand-total");

  if (elSubtotal) elSubtotal.textContent = "₹" + subtotal.toLocaleString('en-IN', {{ minimumFractionDigits: 2, maximumFractionDigits: 2 }});
  if (elCgst) elCgst.textContent = "₹" + cgst.toLocaleString('en-IN', {{ minimumFractionDigits: 2, maximumFractionDigits: 2 }});
  if (elSgst) elSgst.textContent = "₹" + sgst.toLocaleString('en-IN', {{ minimumFractionDigits: 2, maximumFractionDigits: 2 }});
  if (elGrand) elGrand.textContent = "₹" + Math.round(grandTotal).toLocaleString('en-IN');
}}

async function handleCreateQuotationSubmit(e) {{
  e.preventDefault();
  const rows = document.querySelectorAll(".quote-line-row");
  const items = [];
  rows.forEach(row => {{
    const select = row.querySelector(".quote-product-select");
    const opt = select.options[select.selectedIndex];
    if (opt && opt.value) {{
      const qty = parseInt(row.querySelector(".quote-qty")?.value || 1);
      const rate = parseFloat(row.querySelector(".quote-rate")?.value || 0);
      const taxRate = parseFloat((row.querySelector(".quote-tax-rate")?.textContent || "18").replace("%", ""));
      const amount = qty * rate * (1 + taxRate / 100);
      items.push({{
        product_id: parseInt(opt.value),
        name: opt.text.split(" (")[0],
        quantity: qty,
        unit_price: rate,
        tax_rate: taxRate,
        amount: Math.round(amount)
      }});
    }}
  }});

  if (items.length === 0) {{
    showToast("ઓછામાં ઓછી એક પ્રોડક્ટ ઉમેરો", "error");
    return;
  }}

  const payload = {{
    inquiry_id: document.getElementById("quote-inquiry-id")?.value ? parseInt(document.getElementById("quote-inquiry-id").value) : null,
    party_id: document.getElementById("quote-party-id")?.value ? parseInt(document.getElementById("quote-party-id").value) : null,
    customer_name: document.getElementById("quote-cust-name")?.value,
    customer_phone: document.getElementById("quote-cust-phone")?.value,
    customer_email: document.getElementById("quote-cust-email")?.value,
    items: items,
    valid_until: document.getElementById("quote-valid-until")?.value,
    notes: document.getElementById("quote-notes")?.value
  }};

  const res = await apiPost("quotations", payload);
  if (res && res.success) {{
    showToast("GST ક્વોટેશન તૈયાર થઈ ગયું: " + res.quotation_number);
    closeModal("modal-create-quotation");
    loadInquiriesAndOrders();
    printQuotation(res.id);
  }} else {{
    showToast("ક્વોટેશન સેવ કરવામાં ભૂલ આવી", "error");
  }}
}}

async function convertQuotationToOrder(quoteId) {{
  if (!confirm("શું તમે આ ક્વોટેશનને કન્ફર્મ સેલ્સ ઓર્ડરમાં ફેરવવા માંગો છો?")) return;
  const res = await apiPost(`quotations/${{quoteId}}/convert-order`, {{}});
  if (res && res.success) {{
    showToast("ઓર્ડર બની ગયો: " + res.order_number);
    loadInquiriesAndOrders();
  }} else {{
    showToast("ઓર્ડરમાં ફેરવવામાં નિષ્ફળતા", "error");
  }}
}}

async function fulfillOrder(orderId) {{
  if (!confirm("ઓર્ડર ડિલિવરી કન્ફર્મ કરો છો? તેનાથી આપમેળે GST ટેક્સ ઇન્વોઇસ બનશે, સ્ટોકમાંથી માલ કપાશે અને ગ્રાહકના લેજરમાં ઉધાર (Debit) થશે.")) return;
  const res = await apiPost(`orders/${{orderId}}/fulfill`, {{ payment_method: "CASH" }});
  if (res && res.success) {{
    showToast("ઓર્ડર પૂર્ણ થયો! ઇન્વોઇસ: " + res.invoice_number);
    loadInquiriesAndOrders();
    loadInventoryTable();
    if (res.invoice_id) printGSTInvoice(res.invoice_id);
  }} else {{
    showToast(res?.error || "ઓર્ડર પૂર્ણ કરવામાં ભૂલ આવી", "error");
  }}
}}

async function printQuotation(quoteId) {{
  let quote = null;
  if (state.quotations) quote = state.quotations.find(q => q.id == quoteId);
  if (!quote) quote = await apiGet("quotations/" + quoteId);
  if (!quote) return;

  const items = typeof quote.items === 'string' ? JSON.parse(quote.items) : (quote.items || []);
  const printArea = document.getElementById("print-area");
  if (!printArea) return;

  printArea.className = "block bg-white text-black p-8 font-sans";
  printArea.innerHTML = `
    <div style="max-width: 800px; margin: 0 auto; border: 2px solid #1e293b; padding: 24px; font-size: 13px; font-family: system-ui, -apple-system, sans-serif;">
      <table style="width: 100%; border-bottom: 2px solid #1e293b; padding-bottom: 12px;">
        <tr>
          <td style="width: 60%;">
            <h1 style="font-size: 24px; font-weight: 900; margin: 0; color: #1e3a8a;">PCWARE</h1>
            <p style="margin: 3px 0 0 0; font-size: 12px; color: #475569;">
              સેલ્સ, કસ્ટમ PC બિલ્ડિંગ, લેપટોપ ચિપ-લેવલ રિપેરિંગ & AMC સર્વિસિસ<br>
              Shop No. SF, 47, 48, 49, Suvarnabhumi Complex, Mota Mava, Rajkot - 360005<br>
              GSTIN: <strong>24AABCP1234F1Z5</strong> | ફોન: <strong>+91 98250 11223</strong>
            </p>
          </td>
          <td style="width: 40%; text-align: right; vertical-align: top;">
            <div style="background: #1e3a8a; color: #fff; display: inline-block; padding: 6px 14px; font-size: 16px; font-weight: bold; border-radius: 4px;">
              GST QUOTATION / અંદાજપત્ર
            </div>
            <p style="margin: 8px 0 0 0; font-size: 12px;">
              <strong>કોટેશન નં:</strong> ${{quote.quotation_number}}<br>
              <strong>તારીખ:</strong> ${{quote.created_at || new Date().toISOString().split("T")[0]}}<br>
              <strong>માન્ય મુદત:</strong> ${{quote.valid_until || '15 Days'}}
            </p>
          </td>
        </tr>
      </table>

      <table style="width: 100%; margin-top: 14px; border-bottom: 1px solid #cbd5e1; padding-bottom: 10px;">
        <tr>
          <td>
            <strong style="color: #64748b; font-size: 11px; text-transform: uppercase;">ગ્રાહકની વિગત (Customer Details):</strong><br>
            <strong style="font-size: 15px; color: #0f172a;">${{quote.customer_name}}</strong><br>
            <span>સંપર્ક: ${{quote.customer_phone}} | ${{quote.customer_email || ''}}</span>
          </td>
        </tr>
      </table>

      <table style="width: 100%; border-collapse: collapse; margin-top: 16px; font-size: 12px;">
        <thead>
          <tr style="background: #f1f5f9; border-bottom: 2px solid #94a3b8; text-align: left;">
            <th style="padding: 8px; border: 1px solid #cbd5e1; width: 40px; text-align: center;">#</th>
            <th style="padding: 8px; border: 1px solid #cbd5e1;">આઇટમ અને વર્ણન (Description)</th>
            <th style="padding: 8px; border: 1px solid #cbd5e1; width: 60px; text-align: center;">જથ્થો</th>
            <th style="padding: 8px; border: 1px solid #cbd5e1; width: 90px; text-align: right;">દર (Rate)</th>
            <th style="padding: 8px; border: 1px solid #cbd5e1; width: 60px; text-align: center;">GST %</th>
            <th style="padding: 8px; border: 1px solid #cbd5e1; width: 110px; text-align: right;">રકમ (Total)</th>
          </tr>
        </thead>
        <tbody>
          ${{items.map((item, idx) => `
            <tr>
              <td style="padding: 8px; border: 1px solid #cbd5e1; text-align: center;">${{idx + 1}}</td>
              <td style="padding: 8px; border: 1px solid #cbd5e1; font-weight: 600;">${{item.name || item.product_name}}</td>
              <td style="padding: 8px; border: 1px solid #cbd5e1; text-align: center;">${{item.quantity}}</td>
              <td style="padding: 8px; border: 1px solid #cbd5e1; text-align: right;">₹${{Number(item.unit_price).toFixed(2)}}</td>
              <td style="padding: 8px; border: 1px solid #cbd5e1; text-align: center;">${{item.tax_rate || 18}}%</td>
              <td style="padding: 8px; border: 1px solid #cbd5e1; text-align: right; font-weight: bold;">₹${{Number(item.amount).toFixed(2)}}</td>
            </tr>
          `).join("")}}
        </tbody>
      </table>

      <table style="width: 100%; border: none; margin-top: 16px;">
        <tr>
          <td style="width: 60%; vertical-align: top; font-size: 11px;">
            <strong>બેંક ખાતાની વિગતો (Bank Details for Payment):</strong><br>
            બેંક: <strong>State Bank of India (SBI)</strong><br>
            ખાતાનું નામ: <strong>PCWARE</strong><br>
            ખાતા નંબર: <strong>402983719283</strong> | IFSC Code: <strong>SBIN0004128</strong><br>
            UPI ID: <strong>9426183934@upi</strong><br><br>
            <strong>નિયમો અને શરતો:</strong><br>
            1. ઉપર આપેલ દરો 15 દિવસ માટે માન્ય રહેશે.<br>
            2. ઓર્ડર કન્ફર્મ કરવા 50% એડવાન્સ જરૂરી છે.<br>
            3. બધી પ્રોડક્ટ્સ પર કંપની વોરંટી લાગુ પડશે.
          </td>
          <td style="width: 40%; vertical-align: top;">
            <table style="width: 100%; font-size: 12px;">
              <tr>
                <td>સબ-ટોટલ:</td>
                <td style="text-align: right; font-weight: 600;">₹${{Number(quote.subtotal || 0).toFixed(2)}}</td>
              </tr>
              <tr>
                <td>CGST (9%):</td>
                <td style="text-align: right;">₹${{Number(quote.cgst || 0).toFixed(2)}}</td>
              </tr>
              <tr>
                <td>SGST (9%):</td>
                <td style="text-align: right;">₹${{Number(quote.sgst || 0).toFixed(2)}}</td>
              </tr>
              <tr style="border-top: 2px solid #000; font-size: 15px;">
                <td><strong>કુલ રકમ (Total):</strong></td>
                <td style="text-align: right; font-weight: bold; color: #1e3a8a;">₹${{Number(quote.grand_total || 0).toFixed(2)}}</td>
              </tr>
            </table>
          </td>
        </tr>
      </table>

      <table style="width: 100%; margin-top: 30px; font-size: 11px;">
        <tr>
          <td style="width: 50%;">ગ્રાહકની સહી / સ્વીકૃતિ: ______________</td>
          <td style="width: 50%; text-align: right;">
            For, <strong>PCWARE</strong><br><br><br>
            <strong>ઓથોરાઇઝ્ડ સિગ્નેટરી</strong>
          </td>
        </tr>
      </table>
    </div>
  `;

  window.print();
}}

// ==========================================
// ERP WORKFLOW 2: SHORTAGE REORDER & PURCHASE MANAGEMENT
// ==========================================
async function loadPurchaseAndShortage() {{
  const [shortage, pos, parties] = await Promise.all([
    apiGet("shortage-items"),
    apiGet("purchase-orders"),
    apiGet("parties")
  ]);

  state.shortageItems = shortage || [];
  state.purchaseOrders = pos || [];
  if (parties) state.parties = parties;

  renderShortageList();
  renderPurchaseOrdersList();
}}

function renderShortageList() {{
  const tbody = document.getElementById("shortage-table-body");
  if (!tbody) return;
  const list = state.shortageItems || [];

  const statShortage = document.getElementById("stat-shortage-count");
  if (statShortage) statShortage.textContent = list.length;

  if (list.length === 0) {{
    tbody.innerHTML = `<tr><td colspan="7" class="text-center py-6 text-emerald-600 font-semibold">✓ તમામ આઇટમ્સ પર્યાપ્ત સ્ટોકમાં છે! કોઈ ઘટતી વસ્તુ નથી.</td></tr>`;
    return;
  }}

  tbody.innerHTML = list.map(item => {{
    const reorderLvl = item.reorder_level || item.low_stock_threshold || 5;
    const shortageQty = item.shortage_qty || Math.max(1, (reorderLvl * 2) - (item.stock_quantity || 0));
    return `
    <tr class="hover:bg-rose-50/50 transition border-b border-slate-100">
      <td class="py-3 px-4 font-bold text-slate-900 text-xs">
        ${{item.name}}
        <span class="block text-[10px] text-slate-400 font-mono">${{item.sku || ''}}</span>
      </td>
      <td class="py-3 px-4 text-xs text-slate-600">
        <span class="px-2 py-0.5 rounded text-[10px] font-semibold bg-slate-100">${{item.category || 'Hardware'}}</span>
      </td>
      <td class="py-3 px-4">
        <span class="font-black ${{item.stock_quantity === 0 ? 'text-rose-600' : 'text-amber-600'}} text-sm">
          ${{item.stock_quantity}}
        </span>
        ${{item.stock_quantity === 0 ? '<span class="text-[10px] text-rose-500 font-bold block">સ્ટોક ખાલી!</span>' : ''}}
      </td>
      <td class="py-3 px-4 text-xs font-semibold text-slate-600">
        ${{reorderLvl}}
      </td>
      <td class="py-3 px-4">
        <span class="font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded text-xs">
          +${{shortageQty}} નંગ
        </span>
      </td>
      <td class="py-3 px-4 text-xs text-slate-700 font-medium">
        ${{item.preferred_supplier || 'Redington / Supertron'}}
      </td>
      <td class="py-3 px-4 text-right">
        <button type="button" onclick="openCreatePOModal(${{item.id}})" class="px-3 py-1 bg-amber-500 hover:bg-amber-600 text-white font-bold rounded text-xs transition cursor-pointer shadow-sm">
          🛒 PO બનાવો
        </button>
      </td>
    </tr>
    `;
  }}).join("");
}}

function renderPurchaseOrdersList() {{
  const tbody = document.getElementById("po-table-body");
  if (!tbody) return;
  const list = state.purchaseOrders || [];

  const statPO = document.getElementById("stat-po-count");
  const statVal = document.getElementById("stat-po-value");
  if (statPO) statPO.textContent = list.length;
  if (statVal) {{
    const totalVal = list.reduce((sum, p) => sum + (parseFloat(p.grand_total || p.total_amount) || 0), 0);
    statVal.textContent = "₹" + Math.round(totalVal).toLocaleString('en-IN');
  }}

  if (list.length === 0) {{
    tbody.innerHTML = `<tr><td colspan="7" class="text-center py-6 text-slate-400">કોઈ Purchase Order નોંધાયેલ નથી.</td></tr>`;
    return;
  }}

  tbody.innerHTML = list.map(po => `
    <tr class="hover:bg-slate-50 transition border-b border-slate-100">
      <td class="py-3 px-4 font-mono font-bold text-slate-800 text-xs">
        ${{po.po_number}}
        <span class="block text-[10px] text-slate-400">${{po.order_date || ''}}</span>
      </td>
      <td class="py-3 px-4">
        <span class="font-bold text-slate-900">${{po.supplier_name}}</span>
      </td>
      <td class="py-3 px-4 text-xs text-slate-700">
        ${{(() => {{
          const it = po.items_json ? (typeof po.items_json === 'string' ? JSON.parse(po.items_json) : po.items_json) : (po.items ? (typeof po.items === 'string' ? JSON.parse(po.items) : po.items) : []);
          return (it && it.length) ? it.length : 0;
        }})()}} આઇટમ્સ
      </td>
      <td class="py-3 px-4 font-black text-slate-900 text-xs">
        ₹${{Number(po.grand_total || po.total_amount || 0).toLocaleString('en-IN')}}
      </td>
      <td class="py-3 px-4">
        <span class="px-2 py-0.5 rounded-full text-[10px] font-bold ${{
          po.status === 'RECEIVED' ? 'bg-emerald-100 text-emerald-800' :
          po.status === 'ORDERED' ? 'bg-blue-100 text-blue-800' :
          'bg-slate-100 text-slate-700'
        }}">${{po.status}}</span>
      </td>
      <td class="py-3 px-4 text-right whitespace-nowrap space-x-1">
        <button type="button" onclick="printPurchaseOrder(${{po.id}})" class="px-2 py-1 bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold rounded text-xs transition cursor-pointer">
          🖨️ પ્રિન્ટ PO
        </button>
        ${{po.status !== 'RECEIVED' ? `
          <button type="button" onclick="inwardPurchaseOrder(${{po.id}})" class="px-2.5 py-1 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold rounded text-xs transition cursor-pointer shadow-sm">
            📥 માલ જમા (GRN)
          </button>
        ` : `
          <span class="text-xs text-emerald-600 font-semibold">સ્ટોક જમા પૂર્ણ</span>
        `}}
      </td>
    </tr>
  `).join("");
}}

function openCreatePOModal(productId = null) {{
  const form = document.getElementById("form-create-po");
  if (form) form.reset();

  const supSelect = document.getElementById("po-supplier-id");
  if (supSelect) {{
    const suppliers = (state.parties || []).filter(p => p.party_type === 'SUPPLIER');
    supSelect.innerHTML = suppliers.map(s => `<option value="${{s.id}}">${{s.name}} (${{s.city || 'Gujarat'}})</option>`).join("");
  }}

  const today = new Date().toISOString().split("T")[0];
  const dateInput = document.getElementById("po-order-date");
  if (dateInput) dateInput.value = today;

  const tbody = document.getElementById("po-items-tbody");
  if (tbody) {{
    tbody.innerHTML = "";
    if (productId) {{
      const p = (state.products || []).find(x => x.id == productId);
      const shortage = (state.shortageItems || []).find(x => x.id == productId);
      const qty = shortage ? shortage.shortage_qty : 5;
      const rate = p ? Math.round(p.price * 0.82) : 0;
      addPOLineRow(productId, qty, rate);
    }} else {{
      addPOLineRow();
    }}
  }}

  calculatePOTotals();
  document.getElementById("modal-create-po")?.classList.remove("hidden");
}}

function addPOLineRow(productId = null, qty = 1, rate = 0) {{
  const tbody = document.getElementById("po-items-tbody");
  if (!tbody) return;

  const rowId = "po-row-" + Date.now() + "-" + Math.floor(Math.random() * 1000);
  const products = state.products || [];

  const tr = document.createElement("tr");
  tr.id = rowId;
  tr.className = "border-b border-slate-100 po-line-row";
  tr.innerHTML = `
    <td class="py-2 px-2">
      <select class="w-full text-xs p-1.5 border border-slate-300 rounded outline-none po-product-select" onchange="onPOProductChange('${{rowId}}')">
        <option value="">-- પ્રોડક્ટ પસંદ કરો --</option>
        ${{products.map(p => `<option value="${{p.id}}" data-cost="${{Math.round(p.price * 0.82)}}" ${{productId == p.id ? 'selected' : ''}}>${{p.name}} (વર્તમાન સ્ટોક: ${{p.stock_quantity}})</option>`).join("")}}
      </select>
    </td>
    <td class="py-2 px-2 w-24">
      <input type="number" min="1" value="${{qty}}" class="w-full text-xs p-1.5 border border-slate-300 rounded outline-none po-qty" oninput="calculatePOTotals()">
    </td>
    <td class="py-2 px-2 w-28">
      <input type="number" step="0.01" value="${{rate}}" class="w-full text-xs p-1.5 border border-slate-300 rounded outline-none po-rate" oninput="calculatePOTotals()">
    </td>
    <td class="py-2 px-2 w-28 text-right font-bold text-xs text-slate-800 po-line-total">₹0</td>
    <td class="py-2 px-2 w-10 text-center">
      <button type="button" onclick="document.getElementById('${{rowId}}').remove(); calculatePOTotals();" class="text-rose-500 hover:text-rose-700 font-bold text-sm cursor-pointer">✕</button>
    </td>
  `;

  tbody.appendChild(tr);
  if (productId && rate === 0) onPOProductChange(rowId);
  calculatePOTotals();
}}

function onPOProductChange(rowId) {{
  const row = document.getElementById(rowId);
  if (!row) return;
  const select = row.querySelector(".po-product-select");
  const opt = select.options[select.selectedIndex];
  if (opt && opt.value) {{
    const cost = parseFloat(opt.getAttribute("data-cost") || 0);
    const rateInput = row.querySelector(".po-rate");
    if (rateInput) rateInput.value = cost;
  }}
  calculatePOTotals();
}}

function calculatePOTotals() {{
  let subtotal = 0;
  const rows = document.querySelectorAll(".po-line-row");
  rows.forEach(row => {{
    const qty = parseFloat(row.querySelector(".po-qty")?.value || 0);
    const rate = parseFloat(row.querySelector(".po-rate")?.value || 0);
    const total = qty * rate;
    subtotal += total;
    const totalCell = row.querySelector(".po-line-total");
    if (totalCell) totalCell.textContent = "₹" + Math.round(total).toLocaleString('en-IN');
  }});

  const tax = subtotal * 0.18;
  const grandTotal = subtotal + tax;

  const elSub = document.getElementById("po-subtotal");
  const elTax = document.getElementById("po-tax");
  const elGrand = document.getElementById("po-grand-total");

  if (elSub) elSub.textContent = "₹" + subtotal.toLocaleString('en-IN', {{ minimumFractionDigits: 2, maximumFractionDigits: 2 }});
  if (elTax) elTax.textContent = "₹" + tax.toLocaleString('en-IN', {{ minimumFractionDigits: 2, maximumFractionDigits: 2 }});
  if (elGrand) elGrand.textContent = "₹" + Math.round(grandTotal).toLocaleString('en-IN');
}}

async function handleCreatePOSubmit(e) {{
  e.preventDefault();
  const rows = document.querySelectorAll(".po-line-row");
  const items = [];
  rows.forEach(row => {{
    const select = row.querySelector(".po-product-select");
    const opt = select.options[select.selectedIndex];
    if (opt && opt.value) {{
      const qty = parseInt(row.querySelector(".po-qty")?.value || 1);
      const rate = parseFloat(row.querySelector(".po-rate")?.value || 0);
      items.push({{
        product_id: parseInt(opt.value),
        name: opt.text.split(" (")[0],
        quantity: qty,
        unit_price: rate,
        amount: Math.round(qty * rate)
      }});
    }}
  }});

  if (items.length === 0) {{
    showToast("ઓછામાં ઓછી એક પ્રોડક્ટ ઉમેરો", "error");
    return;
  }}

  const payload = {{
    supplier_id: parseInt(document.getElementById("po-supplier-id")?.value),
    order_date: document.getElementById("po-order-date")?.value,
    expected_delivery_date: document.getElementById("po-expected-date")?.value,
    notes: document.getElementById("po-notes")?.value,
    items: items
  }};

  const res = await apiPost("purchase-orders", payload);
  if (res && res.success) {{
    showToast("નવો Purchase Order બન્યો: " + res.po_number);
    closeModal("modal-create-po");
    loadPurchaseAndShortage();
    printPurchaseOrder(res.id);
  }} else {{
    showToast("PO સેવ કરવામાં ભૂલ આવી", "error");
  }}
}}

async function inwardPurchaseOrder(poId) {{
  if (!confirm("માલ ઇનવર્ડ (GRN સ્વીકાર) કરવો છે? આનાથી પ્રોડક્ટ્સનો સ્ટોક વધશે અને સપ્લાયરના ખાતામાં રકમ જમા (Credit) થશે.")) return;
  const res = await apiPost(`purchase-orders/${{poId}}/inward`, {{ invoice_ref: "SUP-INV-" + Date.now().toString().slice(-4) }});
  if (res && res.success) {{
    showToast("માલ સ્ટોકમાં જમા થયો અને સપ્લાયર લેજર અપડેટ થયું!");
    loadPurchaseAndShortage();
    loadInventoryTable();
  }} else {{
    showToast(res?.error || "ઇનવર્ડ કરવામાં ભૂલ આવી", "error");
  }}
}}

async function printPurchaseOrder(poId) {{
  let po = null;
  if (state.purchaseOrders) po = state.purchaseOrders.find(p => p.id == poId);
  if (!po) return;

  const items = typeof po.items === 'string' ? JSON.parse(po.items) : (po.items || []);
  const printArea = document.getElementById("print-area");
  if (!printArea) return;

  printArea.className = "block bg-white text-black p-8 font-sans";
  printArea.innerHTML = `
    <div style="max-width: 800px; margin: 0 auto; border: 2px solid #334155; padding: 24px; font-size: 13px; font-family: system-ui, sans-serif;">
      <table style="width: 100%; border-bottom: 2px solid #334155; padding-bottom: 12px;">
        <tr>
          <td style="width: 60%;">
            <h1 style="font-size: 22px; font-weight: 900; margin: 0; color: #0f172a;">PCWARE</h1>
            <p style="margin: 3px 0 0 0; font-size: 12px; color: #475569;">
              સત્તાવાર ખરીદી ઓર્ડર (Official Purchase Order)<br>
              Shop No. SF, 47, 48, 49, Suvarnabhumi Complex, Mota Mava, Rajkot - 360005<br>
              GSTIN: <strong>24AABCP1234F1Z5</strong>
            </p>
          </td>
          <td style="width: 40%; text-align: right; vertical-align: top;">
            <div style="background: #0f172a; color: #fff; display: inline-block; padding: 6px 14px; font-size: 15px; font-weight: bold; border-radius: 4px;">
              PURCHASE ORDER (PO)
            </div>
            <p style="margin: 8px 0 0 0; font-size: 12px;">
              <strong>PO નંબર:</strong> ${{po.po_number}}<br>
              <strong>તારીખ:</strong> ${{po.order_date || ''}}<br>
              <strong>સ્ટેટસ:</strong> ${{po.status}}
            </p>
          </td>
        </tr>
      </table>

      <table style="width: 100%; margin-top: 14px; border-bottom: 1px solid #cbd5e1; padding-bottom: 10px;">
        <tr>
          <td style="width: 50%;">
            <strong style="color: #64748b; font-size: 11px; text-transform: uppercase;">સપ્લાયર વિગત (Vendor / Supplier):</strong><br>
            <strong style="font-size: 15px; color: #0f172a;">${{po.supplier_name}}</strong>
          </td>
          <td style="width: 50%; text-align: right;">
            <strong style="color: #64748b; font-size: 11px; text-transform: uppercase;">ડિલિવરી સ્થળ (Ship To):</strong><br>
            PCWARE Central Warehouse / Lab, Suvarnabhumi Complex, Rajkot<br>
            Rajkot, Gujarat - 360005
          </td>
        </tr>
      </table>

      <table style="width: 100%; border-collapse: collapse; margin-top: 16px; font-size: 12px;">
        <thead>
          <tr style="background: #f8fafc; border-bottom: 2px solid #94a3b8; text-align: left;">
            <th style="padding: 8px; border: 1px solid #cbd5e1; width: 40px; text-align: center;">#</th>
            <th style="padding: 8px; border: 1px solid #cbd5e1;">પ્રોડક્ટનું નામ (Product Description)</th>
            <th style="padding: 8px; border: 1px solid #cbd5e1; width: 60px; text-align: center;">જથ્થો (Qty)</th>
            <th style="padding: 8px; border: 1px solid #cbd5e1; width: 100px; text-align: right;">ખરીદી દર (Rate)</th>
            <th style="padding: 8px; border: 1px solid #cbd5e1; width: 110px; text-align: right;">કુલ રકમ</th>
          </tr>
        </thead>
        <tbody>
          ${{items.map((item, idx) => `
            <tr>
              <td style="padding: 8px; border: 1px solid #cbd5e1; text-align: center;">${{idx + 1}}</td>
              <td style="padding: 8px; border: 1px solid #cbd5e1; font-weight: 600;">${{item.name || item.product_name}}</td>
              <td style="padding: 8px; border: 1px solid #cbd5e1; text-align: center;">${{item.quantity}}</td>
              <td style="padding: 8px; border: 1px solid #cbd5e1; text-align: right;">₹${{Number(item.unit_price).toFixed(2)}}</td>
              <td style="padding: 8px; border: 1px solid #cbd5e1; text-align: right; font-weight: bold;">₹${{Number(item.amount).toFixed(2)}}</td>
            </tr>
          `).join("")}}
        </tbody>
      </table>

      <table style="width: 100%; border: none; margin-top: 16px;">
        <tr>
          <td style="width: 60%; vertical-align: top; font-size: 11px;">
            <strong>ખરીદી શરતો:</strong><br>
            1. માલ સાથે ટેક્સ ઇન્વોઇસ અને વોરંટી સીરીયલ શીટ મોકલવી અનિવાર્ય છે.<br>
            2. ક્ષતિગ્રસ્ત અથવા તૂટેલો માલ સ્વીકારવામાં આવશે નહીં.
          </td>
          <td style="width: 40%; vertical-align: top;">
            <table style="width: 100%; font-size: 12px;">
              <tr>
                <td>કુલ ખરીદી રકમ:</td>
                <td style="text-align: right; font-weight: bold; font-size: 15px;">₹${{Number(po.grand_total || 0).toFixed(2)}}</td>
              </tr>
            </table>
          </td>
        </tr>
      </table>

      <table style="width: 100%; margin-top: 40px; font-size: 11px;">
        <tr>
          <td style="width: 50%;">સપ્લાયર સ્વીકૃતિ: ______________</td>
          <td style="width: 50%; text-align: right;">
            For, <strong>PCWARE</strong><br><br><br>
            <strong>પરચેઝ મેનેજર (Purchase Signatory)</strong>
          </td>
        </tr>
      </table>
    </div>
  `;

  window.print();
}}

// ==========================================
// ERP WORKFLOW 3: CUSTOMER & SUPPLIER ACCOUNTS & PARTY LEDGERS
// ==========================================
async function loadAccountsAndLedger(filterType = "ALL") {{
  const parties = await apiGet("parties");
  if (!parties) return;
  state.parties = parties;

  let filtered = parties;
  if (filterType === "CUSTOMER") filtered = parties.filter(p => p.party_type === "CUSTOMER");
  if (filterType === "SUPPLIER") filtered = parties.filter(p => p.party_type === "SUPPLIER");

  // Calculate overall metrics
  const receivables = parties.filter(p => p.party_type === 'CUSTOMER' && p.current_balance > 0)
                             .reduce((acc, p) => acc + parseFloat(p.current_balance), 0);
  const payables = parties.filter(p => p.party_type === 'SUPPLIER' && p.current_balance > 0)
                          .reduce((acc, p) => acc + parseFloat(p.current_balance), 0);

  const elRec = document.getElementById("stat-receivables-total");
  const elPay = document.getElementById("stat-payables-total");
  const elCount = document.getElementById("stat-parties-count");

  if (elRec) elRec.textContent = "₹" + Math.round(receivables).toLocaleString('en-IN');
  if (elPay) elPay.textContent = "₹" + Math.round(payables).toLocaleString('en-IN');
  if (elCount) elCount.textContent = parties.length;

  renderPartiesList(filtered);
}}

function renderPartiesList(list) {{
  const tbody = document.getElementById("parties-table-body");
  if (!tbody) return;

  if (list.length === 0) {{
    tbody.innerHTML = `<tr><td colspan="6" class="text-center py-6 text-slate-400">કોઈ પાર્ટી રેકોર્ડ મળ્યો નથી.</td></tr>`;
    return;
  }}

  tbody.innerHTML = list.map(p => `
    <tr class="hover:bg-slate-50 transition border-b border-slate-100">
      <td class="py-3 px-4">
        <span class="font-bold text-slate-900">${{p.name}}</span>
        ${{p.city ? `<span class="block text-[11px] text-slate-500">${{p.city}}</span>` : ''}}
      </td>
      <td class="py-3 px-4">
        <span class="px-2 py-0.5 rounded-full text-[10px] font-bold ${{
          p.party_type === 'CUSTOMER' ? 'bg-blue-100 text-blue-800' : 'bg-purple-100 text-purple-800'
        }}">
          ${{p.party_type === 'CUSTOMER' ? '👤 ગ્રાહક (Customer)' : '🏢 સપ્લાયર (Supplier)'}}
        </span>
      </td>
      <td class="py-3 px-4 text-xs text-slate-700">
        📞 ${{p.phone || '-'}}<br>
        <span class="text-[11px] text-slate-400">${{p.email || ''}}</span>
      </td>
      <td class="py-3 px-4 font-mono text-xs text-slate-600">
        ${{p.gstin || '-'}}
      </td>
      <td class="py-3 px-4">
        <span class="font-black text-sm ${{
          p.party_type === 'CUSTOMER' ? (p.current_balance > 0 ? 'text-amber-600' : 'text-emerald-600') :
          (p.current_balance > 0 ? 'text-rose-600' : 'text-emerald-600')
        }}">
          ₹${{Number(p.current_balance || 0).toLocaleString('en-IN')}}
        </span>
        <span class="block text-[10px] text-slate-400">
          ${{p.party_type === 'CUSTOMER' ? (p.current_balance > 0 ? 'બાકી લેવાના (Receivable)' : 'ચુકતે') : (p.current_balance > 0 ? 'ચૂકવવાના (Payable)' : 'ચુકતે')}}
        </span>
      </td>
      <td class="py-3 px-4 text-right whitespace-nowrap space-x-1">
        <button type="button" onclick="openPartyLedgerModal(${{p.id}})" class="px-2.5 py-1 bg-brand-50 hover:bg-brand-100 text-brand-700 font-semibold rounded text-xs transition cursor-pointer">
          📒 ખાતાવહી (Ledger)
        </button>
        <button type="button" onclick="openRecordPaymentModal(${{p.id}})" class="px-2.5 py-1 bg-emerald-50 hover:bg-emerald-100 text-emerald-700 font-semibold rounded text-xs transition cursor-pointer">
          💰 રકમ નોંધો
        </button>
      </td>
    </tr>
  `).join("");
}}

async function openPartyLedgerModal(partyId) {{
  const res = await apiGet("ledger?party_id=" + partyId);
  if (!res) return;

  const party = res.party || res;
  const entries = res.entries || res.ledger || [];

  window.currentLedgerParty = party;
  window.currentLedgerEntries = entries;

  const elName = document.getElementById("ledger-party-name");
  const elBadge = document.getElementById("ledger-party-badge");
  const elContact = document.getElementById("ledger-party-contact");
  const elBal = document.getElementById("ledger-party-balance");

  if (elName) elName.textContent = party.name;
  if (elBadge) {{
    elBadge.textContent = party.party_type === 'CUSTOMER' ? '👤 ગ્રાહક ખાતું' : '🏢 સપ્લાયર ખાતું';
    elBadge.className = party.party_type === 'CUSTOMER' ? 'px-2 py-0.5 rounded-full text-xs font-bold bg-blue-100 text-blue-800' : 'px-2 py-0.5 rounded-full text-xs font-bold bg-purple-100 text-purple-800';
  }}
  if (elContact) {{
    elContact.innerHTML = `📞 ${{party.phone || '-'}} | GSTIN: ${{party.gstin || 'Unregistered'}} | સરનામું: ${{party.address || '-'}}, ${{party.city || ''}}`;
  }}
  if (elBal) {{
    const bal = parseFloat(party.current_balance || 0);
    elBal.textContent = "₹" + bal.toLocaleString('en-IN');
    elBal.className = "text-xl font-black " + (party.party_type === 'CUSTOMER' ? (bal > 0 ? "text-amber-600" : "text-emerald-600") : (bal > 0 ? "text-rose-600" : "text-emerald-600"));
  }}

  const tbody = document.getElementById("ledger-entries-tbody");
  let totalDebit = 0;
  let totalCredit = 0;

  if (tbody) {{
    if (entries.length === 0) {{
      tbody.innerHTML = `<tr><td colspan="6" class="text-center py-6 text-slate-400">કોઈ લેજર એન્ટ્રી નોંધાયેલ નથી.</td></tr>`;
    }} else {{
      tbody.innerHTML = entries.map(e => {{
        const debit = parseFloat(e.debit || 0);
        const credit = parseFloat(e.credit || 0);
        totalDebit += debit;
        totalCredit += credit;
        const vType = e.voucher_type || e.type || 'TXN';
        const vNo = e.voucher_no || e.reference_number || '';
        const vDesc = e.narration || e.description || '-';
        const vDate = e.entry_date || e.date || '';
        return `
          <tr class="hover:bg-slate-50 transition border-b border-slate-100 text-xs">
            <td class="py-2.5 px-3 font-mono text-slate-600">${{vDate}}</td>
            <td class="py-2.5 px-3">
              <span class="px-1.5 py-0.5 rounded text-[10px] font-bold ${{
                vType.includes('INVOICE') || vType.includes('BILL') ? 'bg-indigo-100 text-indigo-800' :
                vType.includes('PAYMENT') ? 'bg-emerald-100 text-emerald-800' : 'bg-slate-100 text-slate-700'
              }}">${{vType}}</span>
              <span class="block text-[10px] text-slate-400 font-mono mt-0.5">${{vNo || '-'}}</span>
            </td>
            <td class="py-2.5 px-3 text-slate-800">${{vDesc}}</td>
            <td class="py-2.5 px-3 text-right font-semibold text-slate-900">${{debit > 0 ? '₹' + debit.toLocaleString('en-IN') : '-'}}</td>
            <td class="py-2.5 px-3 text-right font-semibold text-emerald-700">${{credit > 0 ? '₹' + credit.toLocaleString('en-IN') : '-'}}</td>
            <td class="py-2.5 px-3 text-right font-black text-slate-900">₹${{Number(e.running_balance || 0).toLocaleString('en-IN')}}</td>
          </tr>
        `;
      }}).join("");
    }}
  }}

  const elTotDeb = document.getElementById("ledger-total-debit");
  const elTotCred = document.getElementById("ledger-total-credit");
  const elCloseBal = document.getElementById("ledger-closing-bal");

  if (elTotDeb) elTotDeb.textContent = "₹" + totalDebit.toLocaleString('en-IN');
  if (elTotCred) elTotCred.textContent = "₹" + totalCredit.toLocaleString('en-IN');
  if (elCloseBal) elCloseBal.textContent = "₹" + Number(party.current_balance || 0).toLocaleString('en-IN');

  document.getElementById("modal-party-ledger")?.classList.remove("hidden");
}}

function printPartyLedger(partyId = null) {{
  const party = window.currentLedgerParty || (state.parties || []).find(p => p.id == partyId);
  const entries = window.currentLedgerEntries || [];
  if (!party) return;

  const printArea = document.getElementById("print-area");
  if (!printArea) return;

  printArea.className = "block bg-white text-black p-8 font-sans";
  printArea.innerHTML = `
    <div style="max-width: 850px; margin: 0 auto; border: 2px solid #1e293b; padding: 24px; font-size: 12px; font-family: system-ui, sans-serif;">
      <table style="width: 100%; border-bottom: 2px solid #1e293b; padding-bottom: 12px;">
        <tr>
          <td style="width: 60%;">
            <h1 style="font-size: 22px; font-weight: 900; margin: 0; color: #1e3a8a;">PCWARE</h1>
            <p style="margin: 3px 0 0 0; font-size: 11px; color: #475569;">
              સત્તાવાર ખાતાવહી સ્ટેટમેન્ટ (Official Party Statement of Account)<br>
              Shop No. SF, 47, 48, 49, Suvarnabhumi Complex, Mota Mava, Rajkot - 360005<br>
              GSTIN: 24AABCP1234F1Z5 | ફોન: +91 98250 11223
            </p>
          </td>
          <td style="width: 40%; text-align: right; vertical-align: top;">
            <div style="background: #1e3a8a; color: #fff; display: inline-block; padding: 5px 12px; font-size: 14px; font-weight: bold; border-radius: 4px;">
              ${{party.party_type === 'CUSTOMER' ? 'CUSTOMER LEDGER / ગ્રાહક ખાતાવહી' : 'SUPPLIER LEDGER / સપ્લાયર ખાતાવહી'}}
            </div>
            <p style="margin: 6px 0 0 0; font-size: 11px;">
              <strong>સ્ટેટમેન્ટ તારીખ:</strong> ${{new Date().toLocaleDateString('en-GB')}}<br>
              <strong>ખાતાનું પ્રકાર:</strong> ${{party.party_type}}
            </p>
          </td>
        </tr>
      </table>

      <table style="width: 100%; margin-top: 12px; border-bottom: 1px solid #cbd5e1; padding-bottom: 8px;">
        <tr>
          <td>
            <strong style="font-size: 15px; color: #0f172a;">${{party.name}}</strong><br>
            <span>સંપર્ક: ${{party.phone || '-'}} | ${{party.email || ''}}</span><br>
            <span>સરનામું: ${{party.address || '-'}}, ${{party.city || ''}} | GSTIN: ${{party.gstin || 'Unregistered'}}</span>
          </td>
          <td style="text-align: right; vertical-align: bottom;">
            <span style="font-size: 11px; color: #64748b;">વર્તમાન આખર બાકી (Closing Balance):</span><br>
            <span style="font-size: 18px; font-weight: 900; color: #1e3a8a;">₹${{Number(party.current_balance || 0).toLocaleString('en-IN')}}</span>
          </td>
        </tr>
      </table>

      <table style="width: 100%; border-collapse: collapse; margin-top: 14px; font-size: 11px;">
        <thead>
          <tr style="background: #f1f5f9; border-bottom: 2px solid #94a3b8; text-align: left;">
            <th style="padding: 6px; border: 1px solid #cbd5e1; width: 75px;">તારીખ</th>
            <th style="padding: 6px; border: 1px solid #cbd5e1; width: 110px;">વ્યવહાર પ્રકાર</th>
            <th style="padding: 6px; border: 1px solid #cbd5e1;">વિગત / વર્ણન (Particulars)</th>
            <th style="padding: 6px; border: 1px solid #cbd5e1; width: 90px; text-align: right;">ઉધાર / Debit (₹)</th>
            <th style="padding: 6px; border: 1px solid #cbd5e1; width: 90px; text-align: right;">જમા / Credit (₹)</th>
            <th style="padding: 6px; border: 1px solid #cbd5e1; width: 100px; text-align: right;">બાકી / Balance (₹)</th>
          </tr>
        </thead>
        <tbody>
          ${{entries.map(e => `
            <tr>
              <td style="padding: 6px; border: 1px solid #cbd5e1;">${{e.entry_date || e.date}}</td>
              <td style="padding: 6px; border: 1px solid #cbd5e1; font-weight: 600;">
                ${{e.voucher_type || e.type}}<br>
                <span style="font-size: 9px; color: #64748b;">${{e.voucher_no || e.reference_number || ''}}</span>
              </td>
              <td style="padding: 6px; border: 1px solid #cbd5e1;">${{e.narration || e.description || '-'}}</td>
              <td style="padding: 6px; border: 1px solid #cbd5e1; text-align: right;">${{e.debit > 0 ? '₹' + Number(e.debit).toLocaleString('en-IN') : '-'}}</td>
              <td style="padding: 6px; border: 1px solid #cbd5e1; text-align: right; color: #15803d;">${{e.credit > 0 ? '₹' + Number(e.credit).toLocaleString('en-IN') : '-'}}</td>
              <td style="padding: 6px; border: 1px solid #cbd5e1; text-align: right; font-weight: bold;">₹${{Number(e.running_balance).toLocaleString('en-IN')}}</td>
            </tr>
          `).join("")}}
        </tbody>
      </table>

      <table style="width: 100%; margin-top: 40px; font-size: 11px;">
        <tr>
          <td style="width: 50%;">પાર્ટીની સહી / સ્વીકૃતિ: ______________</td>
          <td style="width: 50%; text-align: right;">
            For, <strong>PCWARE</strong><br><br><br>
            <strong>ઓથોરાઇઝ્ડ એકાઉન્ટન્ટ</strong>
          </td>
        </tr>
      </table>
    </div>
  `;

  window.print();
}}

function openRecordPaymentModal(partyId = null) {{
  const form = document.getElementById("form-record-payment");
  if (form) form.reset();

  const parties = state.parties || [];
  const select = document.getElementById("pay-party-id");
  if (select) {{
    select.innerHTML = parties.map(p => `<option value="${{p.id}}" data-type="${{p.party_type}}" ${{partyId == p.id ? 'selected' : ''}}>${{p.name}} (${{p.party_type === 'CUSTOMER' ? 'ગ્રાહક' : 'સપ્લાયર'}})</option>`).join("");
  }}

  const today = new Date().toISOString().split("T")[0];
  const dateInput = document.getElementById("pay-date");
  if (dateInput) dateInput.value = today;

  onPaymentPartyChange();
  document.getElementById("modal-record-payment")?.classList.remove("hidden");
}}

function onPaymentPartyChange() {{
  const select = document.getElementById("pay-party-id");
  if (!select) return;
  const opt = select.options[select.selectedIndex];
  const pType = opt ? opt.getAttribute("data-type") : "CUSTOMER";
  const txnTypeSelect = document.getElementById("pay-txn-type");
  if (txnTypeSelect) {{
    if (pType === "CUSTOMER") {{
      txnTypeSelect.innerHTML = `
        <option value="PAYMENT_RECEIVED" selected>PAYMENT_RECEIVED - ગ્રાહક પાસેથી રકમ મળી (Credit)</option>
        <option value="DEBIT_NOTE">DEBIT_NOTE - ડેબિટ નોટ / ચાર્જ (Debit)</option>
      `;
    }} else {{
      txnTypeSelect.innerHTML = `
        <option value="PAYMENT_MADE" selected>PAYMENT_MADE - સપ્લાયરને રકમ ચૂકવી (Debit)</option>
        <option value="CREDIT_NOTE">CREDIT_NOTE - ક્રેડિટ નોટ / ડિસ્કાઉન્ટ (Credit)</option>
      `;
    }}
  }}
}}

async function handleRecordPaymentSubmit(e) {{
  e.preventDefault();
  const partyId = parseInt(document.getElementById("pay-party-id")?.value);
  const amount = parseFloat(document.getElementById("pay-amount")?.value || 0);

  if (amount <= 0) {{
    showToast("માન્ય રકમ દાખલ કરો", "error");
    return;
  }}

  const payload = {{
    party_id: partyId,
    type: document.getElementById("pay-txn-type")?.value,
    payment_mode: document.getElementById("pay-payment-mode")?.value,
    amount: amount,
    reference_number: document.getElementById("pay-ref-number")?.value,
    date: document.getElementById("pay-date")?.value,
    notes: document.getElementById("pay-notes")?.value
  }};

  const res = await apiPost("ledger-transactions", payload);
  if (res && res.success) {{
    showToast("ચૂકવણી સફળતાપૂર્વક નોંધાઈ ગઈ!");
    closeModal("modal-record-payment");
    loadAccountsAndLedger();
    if (!document.getElementById("modal-party-ledger")?.classList.contains("hidden")) {{
      openPartyLedgerModal(partyId);
    }}
  }} else {{
    showToast("ચૂકવણી નોંધવામાં ભૂલ આવી", "error");
  }}
}}

function openNewPartyModal() {{
  const form = document.getElementById("form-new-party");
  if (form) form.reset();
  document.getElementById("modal-new-party")?.classList.remove("hidden");
}}

async function handleCreatePartySubmit(e) {{
  e.preventDefault();
  const payload = {{
    name: document.getElementById("newparty-name")?.value,
    party_type: document.getElementById("newparty-type")?.value,
    phone: document.getElementById("newparty-phone")?.value,
    email: document.getElementById("newparty-email")?.value,
    address: document.getElementById("newparty-address")?.value,
    city: document.getElementById("newparty-city")?.value,
    gstin: document.getElementById("newparty-gstin")?.value,
    opening_balance: parseFloat(document.getElementById("newparty-opening-bal")?.value || 0)
  }};

  const res = await apiPost("parties", payload);
  if (res && res.success) {{
    showToast("નવું ખાતું ઉમેરાઈ ગયું: " + payload.name);
    closeModal("modal-new-party");
    loadAccountsAndLedger();
  }} else {{
    showToast("પાર્ટી સેવ કરવામાં ભૂલ આવી", "error");
  }}
}}

function closeModal(id) {{
  const modal = document.getElementById(id);
  if (modal) modal.classList.add("hidden");
}}

function openNewJobSheetModal() {{
  document.getElementById("modal-new-jobsheet")?.classList.remove("hidden");
}}

async function handleCreateJobSheet(e) {{
  e.preventDefault();
  const payload = {{
    customer_name: document.getElementById("js-cust-name")?.value,
    customer_phone: document.getElementById("js-cust-phone")?.value,
    customer_address: document.getElementById("js-cust-address")?.value,
    device_type: document.getElementById("js-dev-type")?.value,
    device_brand: document.getElementById("js-dev-brand")?.value,
    device_model: document.getElementById("js-dev-model")?.value,
    device_serial: document.getElementById("js-dev-serial")?.value,
    accessories_received: document.getElementById("js-accessories")?.value,
    physical_condition: document.getElementById("js-condition")?.value,
    reported_problem: document.getElementById("js-problem")?.value,
    estimated_cost: document.getElementById("js-est-cost")?.value,
    advance_paid: document.getElementById("js-advance")?.value,
    assigned_technician: document.getElementById("js-technician")?.value
  }};

  const res = await apiPost("jobsheets", payload);
  if (res && res.success) {{
    showToast("જોબ શીટ બની ગઈ: " + res.job_sheet_number);
    closeModal("modal-new-jobsheet");
    loadJobSheets();
    loadAdminStats();
    printJobSheet(res.id);
  }}
}}

async function openUpdateJobSheetModal(jobId) {{
  const job = await apiGet("jobsheets/" + jobId);
  if (!job) return;

  document.getElementById("update-js-id").value = job.id;
  document.getElementById("update-js-title").textContent = job.job_sheet_number + " - સ્ટેટસ અપડેટ";
  document.getElementById("update-js-subtitle").textContent = job.customer_name + " (" + job.device_brand + " " + job.device_model + ")";
  document.getElementById("update-js-status").value = job.status;
  document.getElementById("update-js-tech-notes").value = job.technician_notes || "";
  document.getElementById("update-js-final-cost").value = job.final_cost || job.estimated_cost || 0;
  document.getElementById("update-js-advance").value = job.advance_paid || 0;
  document.getElementById("update-js-log-note").value = "";

  document.getElementById("modal-update-jobsheet")?.classList.remove("hidden");
}}

async function handleUpdateJobSheetSubmit(e) {{
  e.preventDefault();
  const id = document.getElementById("update-js-id")?.value;
  const payload = {{
    status: document.getElementById("update-js-status")?.value,
    technician_notes: document.getElementById("update-js-tech-notes")?.value,
    final_cost: document.getElementById("update-js-final-cost")?.value,
    advance_paid: document.getElementById("update-js-advance")?.value,
    log_note: document.getElementById("update-js-log-note")?.value
  }};

  const res = await apiPut("jobsheets/" + id, payload);
  if (res && res.success) {{
    showToast("જોબ શીટ અપડેટ થઈ ગઈ!");
    closeModal("modal-update-jobsheet");
    loadJobSheets();
    loadAdminStats();
  }}
}}

function openNewProductModal() {{
  document.getElementById("modal-new-product")?.classList.remove("hidden");
}}

async function handleCreateProductSubmit(e) {{
  e.preventDefault();
  const payload = {{
    name: document.getElementById("p-name")?.value,
    category: document.getElementById("p-category")?.value,
    brand: document.getElementById("p-brand")?.value,
    cost_price: document.getElementById("p-cost")?.value,
    selling_price: document.getElementById("p-sell")?.value,
    stock_quantity: document.getElementById("p-qty")?.value,
    wattage: document.getElementById("p-wattage")?.value,
    hsn_code: document.getElementById("p-hsn")?.value,
    specs: document.getElementById("p-specs")?.value
  }};

  const res = await apiPost("products", payload);
  if (res && res.success) {{
    showToast("પ્રોડક્ટ ઉમેરાઈ ગયો!");
    closeModal("modal-new-product");
    loadProducts();
    loadInventoryTable();
    loadAdminStats();
  }}
}}

async function openNewSerialModal() {{
  const select = document.getElementById("s-product-id");
  if (select) {{
    select.innerHTML = state.products.map(p => `
      <option value="${{p.id}}">${{p.name}} (${{p.brand}})</option>
    `).join("");
  }}
  document.getElementById("modal-new-serial")?.classList.remove("hidden");
}}

async function handleCreateSerialSubmit(e) {{
  e.preventDefault();
  const payload = {{
    product_id: document.getElementById("s-product-id")?.value,
    serial_number: document.getElementById("s-serial-no")?.value,
    supplier_name: document.getElementById("s-supplier")?.value,
    warranty_months: document.getElementById("s-warranty")?.value,
    notes: document.getElementById("s-notes")?.value
  }};

  const res = await apiPost("serials", payload);
  if (res && res.success) {{
    showToast("સીરીયલ નંબર સફળતાપૂર્વક રજીસ્ટર થયો!");
    closeModal("modal-new-serial");
    loadSerialsTable();
    loadInventoryTable();
  }}
}}

function openNewAMCModal() {{
  document.getElementById("modal-new-amc")?.classList.remove("hidden");
}}

async function handleCreateAMCSubmit(e) {{
  e.preventDefault();
  const payload = {{
    client_name: document.getElementById("amc-name")?.value,
    contact_person: document.getElementById("amc-contact")?.value,
    phone: document.getElementById("amc-phone")?.value,
    total_systems: document.getElementById("amc-systems")?.value,
    contract_value: document.getElementById("amc-value")?.value,
    start_date: document.getElementById("amc-start")?.value,
    end_date: document.getElementById("amc-end")?.value,
    visit_frequency: document.getElementById("amc-freq")?.value,
    notes: document.getElementById("amc-notes")?.value
  }};

  const res = await apiPost("amc", payload);
  if (res && res.success) {{
    showToast("AMC કોન્ટ્રેક્ટ ઉમેરાઈ ગયો!");
    closeModal("modal-new-amc");
    loadAMCTable();
    loadAdminStats();
  }}
}}

function openNewInvoiceModal() {{
  document.getElementById("modal-new-invoice")?.classList.remove("hidden");
  const container = document.getElementById("invoice-items-container");
  if (!container || container.children.length === 0 || !container.querySelector(".inv-prod-select option[value]:not([value=''])")) {{
    if (container) container.innerHTML = "";
    addInvoiceLineRow();
  }}
}}

function setupInvoiceLineRowDefault() {{
  const container = document.getElementById("invoice-items-container");
  if (container && container.children.length === 0) {{
    addInvoiceLineRow();
  }}
}}

function addInvoiceLineRow() {{
  const container = document.getElementById("invoice-items-container");
  if (!container) return;

  const rowId = "inv-row-" + Date.now();
  const div = document.createElement("div");
  div.id = rowId;
  div.className = "grid grid-cols-12 gap-2 items-center bg-white p-2 rounded-lg border border-slate-200 text-xs";

  div.innerHTML = `
    <div class="col-span-4">
      <select onchange="onInvoiceProductSelect('${{rowId}}', this)" class="w-full px-2 py-1.5 border border-slate-300 rounded outline-none bg-white inv-prod-select">
        <option value="">-- આઇટમ પસંદ કરો --</option>
        ${{state.products.map(p => `<option value="${{p.id}}" data-name="${{p.name}}" data-price="${{p.selling_price}}" data-hsn="${{p.hsn_code}}">${{p.name}} (₹${{p.selling_price}})</option>`).join("")}}
      </select>
    </div>
    <div class="col-span-3">
      <input type="text" placeholder="સીરીયલ નંબર (વૈકલ્પિક)" class="w-full px-2 py-1.5 border border-slate-300 rounded outline-none inv-serial">
    </div>
    <div class="col-span-1">
      <input type="number" min="1" value="1" oninput="calculateInvoiceTotals()" class="w-full px-2 py-1.5 border border-slate-300 rounded outline-none text-center inv-qty">
    </div>
    <div class="col-span-2">
      <input type="number" value="0" oninput="calculateInvoiceTotals()" placeholder="કિંમત" class="w-full px-2 py-1.5 border border-slate-300 rounded outline-none inv-price font-bold text-slate-800">
    </div>
    <div class="col-span-1 text-right font-bold text-slate-900 inv-row-total">₹0</div>
    <div class="col-span-1 text-right">
      <button type="button" onclick="document.getElementById('${{rowId}}').remove(); calculateInvoiceTotals();" class="text-rose-500 hover:text-rose-700 font-bold p-1 cursor-pointer">✕</button>
    </div>
  `;

  container.appendChild(div);
  calculateInvoiceTotals();
}}

function onInvoiceProductSelect(rowId, selectEl) {{
  const row = document.getElementById(rowId);
  if (!row) return;

  const selectedOpt = selectEl.options[selectEl.selectedIndex];
  const price = selectedOpt.getAttribute("data-price") || 0;
  const priceInput = row.querySelector(".inv-price");
  if (priceInput) priceInput.value = price;

  calculateInvoiceTotals();
}}

function calculateInvoiceTotals() {{
  const rows = document.querySelectorAll("#invoice-items-container > div");
  let grandTotal = 0;

  rows.forEach(r => {{
    const qty = parseFloat(r.querySelector(".inv-qty")?.value || 0);
    const price = parseFloat(r.querySelector(".inv-price")?.value || 0);
    const lineTot = qty * price;
    grandTotal += lineTot;
    const totEl = r.querySelector(".inv-row-total");
    if (totEl) totEl.textContent = "₹" + lineTot.toLocaleString('en-IN');
  }});

  const baseSubtotal = grandTotal / 1.18;
  const tax = grandTotal - baseSubtotal;
  const cgst = tax / 2;
  const sgst = tax / 2;

  const subEl = document.getElementById("inv-calc-subtotal");
  const cgstEl = document.getElementById("inv-calc-cgst");
  const sgstEl = document.getElementById("inv-calc-sgst");
  const grandEl = document.getElementById("inv-calc-grand");

  if (subEl) subEl.textContent = "₹" + baseSubtotal.toFixed(2);
  if (cgstEl) cgstEl.textContent = "₹" + cgst.toFixed(2);
  if (sgstEl) sgstEl.textContent = "₹" + sgst.toFixed(2);
  if (grandEl) grandEl.textContent = "₹" + grandTotal.toFixed(2);
}}

async function handleCreateInvoiceSubmit(e) {{
  e.preventDefault();
  const rows = document.querySelectorAll("#invoice-items-container > div");
  if (rows.length === 0) {{
    showToast("ઓછામાં ઓછી એક આઇટમ ઉમેરો!", "error");
    return;
  }}

  const items = [];
  let grandTotal = 0;

  rows.forEach(r => {{
    const selectEl = r.querySelector(".inv-prod-select");
    const opt = selectEl.options[selectEl.selectedIndex];
    const pId = selectEl.value ? parseInt(selectEl.value) : null;
    const pName = opt?.getAttribute("data-name") || "Computer Hardware";
    const hsn = opt?.getAttribute("data-hsn") || "8471";
    const serial = r.querySelector(".inv-serial")?.value.trim();
    const qty = parseInt(r.querySelector(".inv-qty")?.value || 1);
    const unitPrice = parseFloat(r.querySelector(".inv-price")?.value || 0);
    const total = qty * unitPrice;
    grandTotal += total;

    items.push({{
      product_id: pId,
      item_name: pName,
      hsn_code: hsn,
      serial_number: serial,
      quantity: qty,
      unit_price: unitPrice,
      gst_rate: 18.0,
      total: total
    }});
  }});

  const baseSubtotal = grandTotal / 1.18;
  const tax = grandTotal - baseSubtotal;
  const cgst = tax / 2;
  const sgst = tax / 2;

  const payload = {{
    customer_name: document.getElementById("inv-cust-name")?.value,
    customer_phone: document.getElementById("inv-cust-phone")?.value,
    customer_address: document.getElementById("inv-cust-address")?.value,
    customer_gstin: document.getElementById("inv-cust-gstin")?.value,
    payment_method: document.getElementById("inv-payment-method")?.value,
    notes: document.getElementById("inv-notes")?.value,
    subtotal: baseSubtotal,
    cgst: cgst,
    sgst: sgst,
    grand_total: grandTotal,
    items: items
  }};

  const res = await apiPost("invoices", payload);
  if (res && res.success) {{
    showToast("GST બિલ બની ગયું: " + res.invoice_number);
    closeModal("modal-new-invoice");
    loadInvoicesTable();
    loadInventoryTable();
    loadAdminStats();
    printGSTInvoice(res.id);
  }}
}}

async function printJobSheet(id) {{
  const job = await apiGet("jobsheets/" + id);
  if (!job) return;

  const printArea = document.getElementById("print-area");
  if (!printArea) return;

  const store = state.storeSettings || DEFAULT_SEED_DATA.settings;
  const balance = (job.final_cost || job.estimated_cost || 0) - (job.advance_paid || 0);

  printArea.innerHTML = `
    <div style="font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; border: 2px solid #333; line-height: 1.4;">
      <div style="text-align: center; border-bottom: 2px solid #333; padding-bottom: 10px; margin-bottom: 15px;">
        <h1 style="margin: 0; font-size: 24px; font-weight: bold; text-transform: uppercase;">${{store.store_name || 'PCWARE'}}</h1>
        <p style="margin: 3px 0; font-size: 13px;">${{store.tagline || 'Hardware Sales, Custom PC Builds & Service Hub'}}</p>
        <p style="margin: 3px 0; font-size: 12px;">${{store.address || 'Suvarnabhumi Complex, Mota Mava, Rajkot, Gujarat'}}</p>
        <p style="margin: 3px 0; font-size: 12px; font-weight: bold;">Phone: ${{store.phone || '+91 98250 12345'}} | GSTIN: ${{store.gstin || '24AABCP1234F1Z5'}}</p>
        <div style="background: #000; color: #fff; display: inline-block; padding: 4px 15px; font-weight: bold; font-size: 14px; margin-top: 5px; border-radius: 4px;">
          SERVICE REPAIR JOB CARD / RECEIPT
        </div>
      </div>

      <table style="width: 100%; border-collapse: collapse; margin-bottom: 15px; font-size: 13px;">
        <tr>
          <td style="width: 50%; padding: 6px; border: 1px solid #ccc; vertical-align: top;">
            <strong>Job Sheet No:</strong> <span style="font-size: 16px; font-weight: bold; color: #000;">${{job.job_sheet_number}}</span><br>
            <strong>Date In:</strong> ${{job.created_at}}<br>
            <strong>Status:</strong> ${{job.status}}<br>
            <strong>Assigned Tech:</strong> ${{job.assigned_technician || 'Hardware Lab'}}
          </td>
          <td style="width: 50%; padding: 6px; border: 1px solid #ccc; vertical-align: top;">
            <strong>Customer:</strong> <span style="font-size: 15px; font-weight: bold;">${{job.customer_name}}</span><br>
            <strong>Mobile:</strong> ${{job.customer_phone}}<br>
            <strong>Address:</strong> ${{job.customer_address || 'Walk-in Customer'}}
          </td>
        </tr>
      </table>

      <div style="margin-bottom: 15px;">
        <h4 style="margin: 0 0 5px 0; font-size: 14px; border-bottom: 1px solid #000; padding-bottom: 2px;">EQUIPMENT DETAILS</h4>
        <table style="width: 100%; border-collapse: collapse; font-size: 12px;">
          <tr>
            <td style="padding: 5px; border: 1px solid #ddd; width: 25%;"><strong>Device Type:</strong> ${{job.device_type}}</td>
            <td style="padding: 5px; border: 1px solid #ddd; width: 25%;"><strong>Brand:</strong> ${{job.device_brand}}</td>
            <td style="padding: 5px; border: 1px solid #ddd; width: 25%;"><strong>Model:</strong> ${{job.device_model}}</td>
            <td style="padding: 5px; border: 1px solid #ddd; width: 25%;"><strong>Serial No:</strong> ${{job.device_serial || 'N/A'}}</td>
          </tr>
          <tr>
            <td colspan="2" style="padding: 5px; border: 1px solid #ddd;"><strong>Accessories Handed In:</strong> ${{job.accessories_received || 'Unit Only'}}</td>
            <td colspan="2" style="padding: 5px; border: 1px solid #ddd;"><strong>Physical Condition:</strong> ${{job.physical_condition || 'Normal wear'}}</td>
          </tr>
        </table>
      </div>

      <div style="margin-bottom: 15px;">
        <h4 style="margin: 0 0 5px 0; font-size: 14px; border-bottom: 1px solid #000; padding-bottom: 2px;">REPORTED FAULT & DIAGNOSIS</h4>
        <div style="border: 1px solid #ddd; padding: 8px; font-size: 13px; margin-bottom: 5px;">
          <strong>Problem Reported:</strong> ${{job.reported_problem}}
        </div>
        ${{job.technician_notes ? `
          <div style="border: 1px solid #ddd; padding: 8px; font-size: 13px; background: #f9f9f9;">
            <strong>Diagnosis / Work Done:</strong> ${{job.technician_notes}}
          </div>
        ` : ''}}
      </div>

      <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px; font-size: 13px;">
        <tr style="background: #f0f0f0;">
          <th style="padding: 6px; border: 1px solid #ccc; text-align: left;">Estimated / Final Cost</th>
          <th style="padding: 6px; border: 1px solid #ccc; text-align: center;">Advance Paid</th>
          <th style="padding: 6px; border: 1px solid #ccc; text-align: right;">Balance Payable</th>
        </tr>
        <tr>
          <td style="padding: 8px; border: 1px solid #ccc; font-weight: bold; font-size: 15px;">₹${{(job.final_cost || job.estimated_cost || 0).toLocaleString('en-IN')}}</td>
          <td style="padding: 8px; border: 1px solid #ccc; text-align: center; color: green; font-weight: bold;">₹${{(job.advance_paid || 0).toLocaleString('en-IN')}}</td>
          <td style="padding: 8px; border: 1px solid #ccc; text-align: right; color: red; font-weight: bold; font-size: 16px;">₹${{Math.max(0, balance).toLocaleString('en-IN')}}</td>
        </tr>
      </table>

      <div style="font-size: 10px; color: #555; border-top: 1px solid #ccc; padding-top: 8px; margin-bottom: 25px;">
        <strong>TERMS & CONDITIONS:</strong><br>
        1. Data backup is customer responsibility. We are not liable for any data loss during repair.<br>
        2. Devices must be collected within 30 days of repair completion.<br>
        3. 30-day warranty on specific hardware parts replaced.<br>
        4. Please produce this original receipt while collecting equipment.
      </div>

      <table style="width: 100%; border: none; font-size: 12px; margin-top: 30px;">
        <tr>
          <td style="width: 50%; text-align: left;">
            ___________________________<br>
            <strong>Customer Signature</strong>
          </td>
          <td style="width: 50%; text-align: right;">
            ___________________________<br>
            <strong>Authorized Signatory / Tech</strong>
          </td>
        </tr>
      </table>
    </div>
  `;

  window.print();
}}

async function printGSTInvoice(id) {{
  let inv = null;
  if (state.invoices) inv = state.invoices.find(i => i.id == id);
  if (!inv) inv = await apiGet("invoices/" + id);
  if (!inv) return;

  const printArea = document.getElementById("print-area");
  if (!printArea) return;

  const items = inv.items || [];
  const totalTax = (Number(inv.cgst || 0) + Number(inv.sgst || 0) + Number(inv.igst || 0));

  printArea.className = "block bg-white text-slate-900 p-6 font-sans";
  printArea.innerHTML = `
    <div style="font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 820px; margin: 0 auto; background: #ffffff; color: #1e293b; line-height: 1.4;">
      
      <!-- Top Header Row -->
      <table style="width: 100%; border-collapse: collapse; margin-bottom: 22px;">
        <tr>
          <td style="vertical-align: top; width: 62%;">
            <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 8px;">
              <img src="/static/logo.svg" alt="PCWARE" style="height: 52px; width: auto; max-width: 200px; object-fit: contain;">
            </div>
            <div style="font-size: 11px; color: #475569; line-height: 1.5;">
              <strong style="color: #0C2340; font-size: 13px;">PCWARE</strong><br>
              Shop No. SF, 47, 48, 49, Suvarnabhumi Complex,<br>
              opp. Speedwell Party Plot, Ambika Twp, Mota Mava,<br>
              Rajkot, Gujarat - 360005<br>
              <span><strong>CEO:</strong> +91 94261 83934 &nbsp;|&nbsp; <strong>Service:</strong> +91 80007 80704 &nbsp;|&nbsp; <strong>Inquiry:</strong> +91 70167 37271</span><br>
              <span><strong>GSTIN:</strong> 24AABCP1234F1Z5 &nbsp;|&nbsp; <strong>Email:</strong> info@pcware.in</span>
            </div>
          </td>
          <td style="vertical-align: top; width: 38%; text-align: right;">
            <h1 style="font-size: 36px; font-weight: 900; letter-spacing: 2px; color: #1e293b; margin: 0 0 4px 0; text-transform: uppercase;">INVOICE</h1>
            <p style="font-size: 13px; font-weight: 700; color: #64748b; margin: 0;">#${{inv.invoice_number}}</p>
          </td>
        </tr>
      </table>

      <!-- Client & Invoice Info Row -->
      <table style="width: 100%; border-collapse: collapse; margin-bottom: 22px;">
        <tr>
          <!-- Bill To Left Box -->
          <td style="vertical-align: top; width: 50%; padding-right: 15px;">
            <div style="text-transform: uppercase; font-size: 11px; font-weight: 800; color: #0f172a; letter-spacing: 0.5px; margin-bottom: 4px;">INVOICE TO:</div>
            <div style="font-size: 14px; font-weight: 800; color: #0f172a;">${{inv.customer_name}}</div>
            <div style="font-size: 11.5px; color: #475569; margin-top: 2px; line-height: 1.45;">
              ${{inv.customer_address || 'Rajkot, Gujarat'}}<br>
              Phone: <strong>${{inv.customer_phone}}</strong>
              ${{inv.customer_email ? `<br>Email: ${{inv.customer_email}}` : ''}}
              ${{inv.customer_gstin ? `<br>GSTIN: <strong>${{inv.customer_gstin}}</strong>` : ''}}
            </div>
          </td>

          <!-- Invoice Details Right Gray Card with Coral Border -->
          <td style="vertical-align: top; width: 50%; padding-left: 15px;">
            <div style="background: #f1f5f9; border-radius: 6px; border-left: 5px solid #F26522; padding: 12px 18px;">
              <table style="width: 100%; border-collapse: collapse;">
                <tr>
                  <td style="width: 50%; vertical-align: top;">
                    <span style="font-size: 10.5px; font-weight: 700; color: #64748b; text-transform: uppercase; display: block;">Invoice Number</span>
                    <strong style="font-size: 13px; color: #0f172a; display: block; margin-top: 3px;">${{inv.invoice_number}}</strong>
                  </td>
                  <td style="width: 50%; vertical-align: top;">
                    <span style="font-size: 10.5px; font-weight: 700; color: #64748b; text-transform: uppercase; display: block;">Date Information</span>
                    <strong style="font-size: 13px; color: #0f172a; display: block; margin-top: 3px;">${{inv.invoice_date}}</strong>
                  </td>
                </tr>
              </table>
            </div>
          </td>
        </tr>
      </table>

      <!-- Main Item Table -->
      <table style="width: 100%; border-collapse: collapse; margin-bottom: 22px; font-size: 12px;">
        <thead>
          <tr style="background: #F26522; color: #ffffff;">
            <th style="padding: 10px 12px; text-align: center; width: 6%; font-weight: 800; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px;">NO</th>
            <th style="padding: 10px 12px; text-align: left; font-weight: 800; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px;">ITEM DESCRIPTION</th>
            <th style="padding: 10px 12px; text-align: right; width: 16%; font-weight: 800; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px;">PRICE</th>
            <th style="padding: 10px 12px; text-align: center; width: 8%; font-weight: 800; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px;">QTY</th>
            <th style="padding: 10px 12px; text-align: right; width: 18%; font-weight: 800; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px;">TOTAL</th>
          </tr>
        </thead>
        <tbody>
          ${{items.map((item, idx) => `
            <tr style="background: ${{idx % 2 === 0 ? '#ffffff' : '#f8fafc'}}; border-bottom: 1px solid #e2e8f0;">
              <td style="padding: 12px 10px; text-align: center; color: #64748b; font-weight: 700;">${{String(idx + 1).padStart(2, '0')}}.</td>
              <td style="padding: 12px 10px;">
                <div style="font-weight: 700; color: #0f172a; font-size: 12.5px;">${{item.item_name}}</div>
                <div style="font-size: 10.5px; color: #64748b; margin-top: 2px;">
                  ${{item.serial_number ? `<span style="font-family: monospace; font-weight: 600; color: #334155; margin-right: 8px;">SN: ${{item.serial_number}}</span>` : ''}}
                  <span>HSN: ${{item.hsn_code || '8471'}}</span>
                </div>
              </td>
              <td style="padding: 12px 10px; text-align: right; color: #334155; font-weight: 600;">₹${{Number(item.unit_price).toLocaleString('en-IN', {{minimumFractionDigits: 2}})}}</td>
              <td style="padding: 12px 10px; text-align: center; color: #334155; font-weight: 700;">${{item.quantity}}</td>
              <td style="padding: 12px 10px; text-align: right; font-weight: 800; color: #0f172a;">₹${{Number(item.total).toLocaleString('en-IN', {{minimumFractionDigits: 2}})}}</td>
            </tr>
          `).join("")}}
        </tbody>
      </table>

      <!-- Bottom Split Section -->
      <table style="width: 100%; border-collapse: collapse; margin-bottom: 22px;">
        <tr>
          <!-- Left Details: Payment Method & Terms -->
          <td style="vertical-align: top; width: 55%; padding-right: 20px;">
            <table style="width: 100%; border-collapse: collapse; margin-bottom: 12px;">
              <tr>
                <td style="vertical-align: top; width: 50%;">
                  <strong style="font-size: 12px; color: #0f172a; display: block; margin-bottom: 4px;">Payment Method</strong>
                  <div style="font-size: 11px; color: #475569; line-height: 1.5;">
                    Bank: <strong>HDFC / SBI</strong><br>
                    A/C: <strong>50200094261839</strong><br>
                    IFSC: <strong>HDFC0001234</strong><br>
                    UPI / GPay: <strong>9426183934@upi</strong>
                  </div>
                </td>
                <td style="vertical-align: top; width: 50%;">
                  <strong style="font-size: 12px; color: #0f172a; display: block; margin-bottom: 4px;">Terms & Condition</strong>
                  <div style="font-size: 10.5px; color: #475569; line-height: 1.4;">
                    • Warranty as per OEM terms.<br>
                    • Physical damage / burn voids warranty.<br>
                    • Goods once sold not returnable without serial box.
                  </div>
                </td>
              </tr>
            </table>

            <p style="font-size: 10.5px; color: #94a3b8; line-height: 1.4; margin: 6px 0 14px 0;">
              Certified that all particulars given above are true and correct. Subject to Rajkot jurisdiction.
            </p>

            <!-- Signatory Block -->
            <div style="margin-top: 10px;">
              <div style="font-family: 'Brush Script MT', cursive, sans-serif; font-size: 26px; color: #334155;">Authorized Signatory</div>
              <div style="font-size: 11px; font-weight: 800; color: #0f172a; margin-top: 2px;">PCWARE / CEO</div>
              <div style="font-size: 10px; color: #64748b;">Authorized Signatory</div>
            </div>
          </td>

          <!-- Right Details: Subtotal, Tax, Grand Total Banner & Thank You -->
          <td style="vertical-align: top; width: 45%;">
            <table style="width: 100%; border-collapse: collapse; font-size: 12px; margin-bottom: 8px;">
              <tr>
                <td style="padding: 4px 0; color: #475569; font-weight: 600;">Sub Total:</td>
                <td style="padding: 4px 0; text-align: right; font-weight: 700; color: #0f172a;">₹${{Number(inv.subtotal).toLocaleString('en-IN', {{minimumFractionDigits: 2}})}}</td>
              </tr>
              <tr>
                <td style="padding: 4px 0; color: #475569; font-weight: 600;">Tax (GST 18%):</td>
                <td style="padding: 4px 0; text-align: right; font-weight: 700; color: #0f172a;">₹${{Number(totalTax).toLocaleString('en-IN', {{minimumFractionDigits: 2}})}}</td>
              </tr>
              <tr>
                <td style="padding: 4px 0; color: #475569; font-weight: 600;">Discount:</td>
                <td style="padding: 4px 0; text-align: right; font-weight: 700; color: #0f172a;">₹${{Number(inv.discount || 0).toLocaleString('en-IN', {{minimumFractionDigits: 2}})}}</td>
              </tr>
            </table>

            <!-- Grand Total Coral Banner -->
            <div style="background: #F26522; color: #ffffff; padding: 12px 18px; border-radius: 6px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 2px 4px rgba(242, 101, 34, 0.2);">
              <span style="font-size: 13px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.5px;">Grand Total:</span>
              <strong style="font-size: 18px; font-weight: 900;">₹${{Number(inv.grand_total).toLocaleString('en-IN', {{minimumFractionDigits: 2}})}}</strong>
            </div>

            <!-- Bottom Right Thank You Note -->
            <div style="margin-top: 22px; text-align: right;">
              <h3 style="font-size: 16px; font-weight: 900; color: #F26522; margin: 0 0 4px 0;">Thank you for your business!</h3>
              <p style="font-size: 11px; color: #64748b; margin: 0;">
                📞 +91 94261 83934 / 70167 37271 &nbsp;|&nbsp; ✉️ info@pcware.in
              </p>
            </div>
          </td>
        </tr>
      </table>

    </div>
  `;

  window.print();
}}

function showToast(message, type = "success") {{
  const container = document.getElementById("toast-container");
  if (!container) return;

  const toast = document.createElement("div");
  const bgClass = type === "error" ? "bg-rose-600" : type === "info" ? "bg-brand-600" : "bg-emerald-600";
  toast.className = bgClass + " text-white text-xs font-semibold px-4 py-2.5 rounded-xl shadow-xl flex items-center gap-2 transform transition-all duration-300 translate-y-2 opacity-0";
  toast.innerHTML = `
    <span>${{type === 'error' ? '⚠️' : '✓'}}</span>
    <span>${{message}}</span>
  `;

  container.appendChild(toast);

  setTimeout(() => {{
    toast.classList.remove("translate-y-2", "opacity-0");
  }}, 10);

  setTimeout(() => {{
    toast.classList.add("opacity-0", "translate-y-2");
    setTimeout(() => toast.remove(), 300);
  }}, 3500);
}}

// Global window bindings
window.switchView = switchView;
window.switchAdminTab = switchAdminTab;
window.filterCategory = filterCategory;
window.debounceProductSearch = debounceProductSearch;
window.addToCart = addToCart;
window.updateCartQty = updateCartQty;
window.toggleCartDrawer = toggleCartDrawer;
window.placeOrder = placeOrder;
window.selectPCComponent = selectPCComponent;
window.resetPCBuilder = resetPCBuilder;
window.resetCompatibilityFilters = resetCompatibilityFilters;
window.addPCBuildToCart = addPCBuildToCart;
window.shareBuildWhatsApp = shareBuildWhatsApp;
window.performJobTracking = performJobTracking;
window.setTrackTest = setTrackTest;
window.submitServiceBooking = submitServiceBooking;
window.closeModal = closeModal;
window.openNewJobSheetModal = openNewJobSheetModal;
window.handleCreateJobSheet = handleCreateJobSheet;
window.openUpdateJobSheetModal = openUpdateJobSheetModal;
window.handleUpdateJobSheetSubmit = handleUpdateJobSheetSubmit;
window.openNewProductModal = openNewProductModal;
window.handleCreateProductSubmit = handleCreateProductSubmit;
window.openNewSerialModal = openNewSerialModal;
window.handleCreateSerialSubmit = handleCreateSerialSubmit;
window.openNewAMCModal = openNewAMCModal;
window.handleCreateAMCSubmit = handleCreateAMCSubmit;
window.openNewInvoiceModal = openNewInvoiceModal;
window.addInvoiceLineRow = addInvoiceLineRow;
window.onInvoiceProductSelect = onInvoiceProductSelect;
window.calculateInvoiceTotals = calculateInvoiceTotals;
window.handleCreateInvoiceSubmit = handleCreateInvoiceSubmit;
window.printJobSheet = printJobSheet;
window.printGSTInvoice = printGSTInvoice;
window.deleteProduct = deleteProduct;
window.loadJobSheets = loadJobSheets;
window.loadInventoryTable = loadInventoryTable;
window.loadSerialsTable = loadSerialsTable;
window.setLanguage = setLanguage;
window.t = t;

// ERP Workflow 1: Inquiries & Orders
window.loadInquiriesAndOrders = loadInquiriesAndOrders;
window.openNewInquiryModal = openNewInquiryModal;
window.handleCreateInquirySubmit = handleCreateInquirySubmit;
window.openQuotationModal = openQuotationModal;
window.onQuotationPartySelect = onQuotationPartySelect;
window.addQuotationLineRow = addQuotationLineRow;
window.onQuoteProductChange = onQuoteProductChange;
window.calculateQuotationTotals = calculateQuotationTotals;
window.handleCreateQuotationSubmit = handleCreateQuotationSubmit;
window.convertQuotationToOrder = convertQuotationToOrder;
window.fulfillOrder = fulfillOrder;
window.printQuotation = printQuotation;

// ERP Workflow 2: Shortage & Purchase Orders
window.loadPurchaseAndShortage = loadPurchaseAndShortage;
window.openCreatePOModal = openCreatePOModal;
window.addPOLineRow = addPOLineRow;
window.onPOProductChange = onPOProductChange;
window.calculatePOTotals = calculatePOTotals;
window.handleCreatePOSubmit = handleCreatePOSubmit;
window.inwardPurchaseOrder = inwardPurchaseOrder;
window.printPurchaseOrder = printPurchaseOrder;

// ERP Workflow 3: Accounts & Ledgers
window.loadAccountsAndLedger = loadAccountsAndLedger;
window.openPartyLedgerModal = openPartyLedgerModal;
window.printPartyLedger = printPartyLedger;
window.openRecordPaymentModal = openRecordPaymentModal;
window.onPaymentPartyChange = onPaymentPartyChange;
window.handleRecordPaymentSubmit = handleRecordPaymentSubmit;
window.openNewPartyModal = openNewPartyModal;
window.handleCreatePartySubmit = handleCreatePartySubmit;

console.log("PCWARE App engine loaded with full window bindings.");
"""

with open(target_file, "w") as f:
    f.write(js_code)

print("Successfully compiled app.js with 40+ products and window functions.")
