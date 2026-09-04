import json
import os

base_dir = os.path.dirname(os.path.abspath(__file__))
seed_file = os.path.join(base_dir, "static", "seed_data.json")
target_file = os.path.join(base_dir, "static", "app.js")

with open(seed_file, "r", encoding="utf-8") as f:
    seed_json = f.read().strip()

with open("static/app.js", "r", encoding="utf-8") as f:
    orig_js = f.read()

# Replace DEFAULT_SEED_DATA in app.js
seed_prefix = "const DEFAULT_SEED_DATA = "
seed_start = orig_js.find(seed_prefix)
if seed_start != -1:
    brace_start = orig_js.find("{", seed_start)
    # Find matching closing of DEFAULT_SEED_DATA
    # It ends before `function getLocalDB()`
    func_pos = orig_js.find("function getLocalDB()", brace_start)
    semicolon_pos = orig_js.rfind(";", brace_start, func_pos)
    orig_js = orig_js[:brace_start] + seed_json + orig_js[semicolon_pos:]

# Update LocalStorage key from pcware_db_v1 to pcware_db_v2 to ensure fresh seed data is loaded
orig_js = orig_js.replace('"pcware_db_v1"', '"pcware_db_v2"')

# In handleLocalMock, add staff, warehouses, warehouse-stock, stock-transfers, branches, whatsapp-booking, gemini/chat
mock_get_anchor = 'if (path === "products") {'
new_mock_gets = '''
    if (path === "staff") return db.staff || DEFAULT_SEED_DATA.staff || [];
    if (path === "warehouses") return db.warehouses || DEFAULT_SEED_DATA.warehouses || [];
    if (path === "warehouse-stock") {
      const whId = params.get("warehouse_id");
      let stocks = db.warehouse_stocks || DEFAULT_SEED_DATA.warehouse_stocks || [];
      if (whId) stocks = stocks.filter(s => s.warehouse_id == whId);
      return stocks.map(s => {
        const wh = (db.warehouses || []).find(w => w.id == s.warehouse_id) || {};
        const p = (db.products || []).find(pr => pr.id == s.product_id) || {};
        return {
          ...s,
          warehouse_name: wh.name || "Main Showroom",
          warehouse_code: wh.code || "WH-SHOWROOM",
          product_name: p.name || "",
          category: p.category || "",
          brand: p.brand || "",
          selling_price: p.selling_price || 0,
          sku: p.sku || ""
        };
      });
    }
    if (path === "stock-transfers") {
      const trfs = db.stock_transfers || DEFAULT_SEED_DATA.stock_transfers || [];
      return trfs.map(t => {
        const wf = (db.warehouses || []).find(w => w.id == t.from_warehouse_id) || {};
        const wt = (db.warehouses || []).find(w => w.id == t.to_warehouse_id) || {};
        const p = (db.products || []).find(pr => pr.id == t.product_id) || {};
        return {
          ...t,
          from_warehouse_name: wf.name || "From Godown",
          to_warehouse_name: wt.name || "To Godown",
          product_name: p.name || "",
          product_sku: p.sku || ""
        };
      });
    }
    if (path === "branches") return db.branches || DEFAULT_SEED_DATA.branches || [];
'''

if mock_get_anchor in orig_js and 'if (path === "staff")' not in orig_js:
    orig_js = orig_js.replace(mock_get_anchor, new_mock_gets + "\n    " + mock_get_anchor)

# Add POST handlers to handleLocalMock
mock_post_anchor = 'if (path === "jobsheets") {'
new_mock_posts = '''
    if (path === "whatsapp-booking") {
      const nowStr = new Date().toISOString().replace("T", " ").substring(0, 19);
      if (!db.inquiries) db.inquiries = DEFAULT_SEED_DATA.inquiries ? [...DEFAULT_SEED_DATA.inquiries] : [];
      const inqNo = "INQ-" + new Date().getFullYear() + "-" + String(db.inquiries.length + 101).padStart(4, "0");
      const inq = {
        id: db.inquiries.length + 1,
        inquiry_number: inqNo,
        customer_name: data.customer_name || "Customer",
        customer_phone: data.customer_phone || "",
        customer_email: data.customer_email || "",
        customer_address: data.customer_address || "",
        requirement_type: data.requirement_type || "LAPTOP",
        items_requested: data.items_requested || "",
        custom_specs: typeof data.custom_specs === "object" ? JSON.stringify(data.custom_specs) : data.custom_specs,
        estimated_budget: Number(data.estimated_budget || 0),
        status: "NEW",
        source: "WhatsApp Store",
        fulfillment_mode: data.fulfillment_mode || "SHOWROOM_VISIT",
        assigned_staff_id: 2,
        assigned_staff_name: "Hardik Patel",
        delivery_tracking_no: "",
        notes: data.notes || "",
        created_at: nowStr
      };
      db.inquiries.unshift(inq);
      saveLocalDB(db);

      const modeStr = inq.fulfillment_mode === "SHOWROOM_VISIT" ? "🏪 Showroom Visit & Live Demo" : "📦 Courier Parcel Dispatch";
      const waText = `Hello PCWARE! I want to book/inquire:\\n\\n` +
                     `📋 *Inquiry No:* ${inqNo}\\n` +
                     `💻 *Item:* ${inq.items_requested}\\n` +
                     `💰 *Budget/Price:* ₹${inq.estimated_budget.toLocaleString('en-IN')}\\n` +
                     `🚚 *Fulfillment:* ${modeStr}\\n` +
                     `👤 *Customer:* ${inq.customer_name}\\n` +
                     `📞 *Mobile:* ${inq.customer_phone}\\n` +
                     `📍 *City/Address:* ${inq.customer_address || 'Rajkot'}\\n` +
                     (inq.custom_specs ? `⚙️ *Specs:* ${inq.custom_specs}\\n` : '') +
                     `\\nPlease confirm availability and share next steps. Thank you!`;
      const waUrl = `https://wa.me/919426183934?text=${encodeURIComponent(waText)}`;
      return { success: true, inquiry_number: inqNo, assigned_staff: "Hardik Patel", whatsapp_url: waUrl, message: waText };
    }

    if (path === "stock-transfers") {
      const nowStr = new Date().toISOString().replace("T", " ").substring(0, 19);
      if (!db.stock_transfers) db.stock_transfers = DEFAULT_SEED_DATA.stock_transfers ? [...DEFAULT_SEED_DATA.stock_transfers] : [];
      if (!db.warehouse_stocks) db.warehouse_stocks = DEFAULT_SEED_DATA.warehouse_stocks ? [...DEFAULT_SEED_DATA.warehouse_stocks] : [];
      
      const fromWh = Number(data.from_warehouse_id);
      const toWh = Number(data.to_warehouse_id);
      const prodId = Number(data.product_id);
      const qty = Number(data.quantity || 1);

      // Decrement source
      let src = db.warehouse_stocks.find(s => s.warehouse_id === fromWh && s.product_id === prodId);
      if (src) src.quantity = Math.max(0, src.quantity - qty);

      // Increment destination
      let dest = db.warehouse_stocks.find(s => s.warehouse_id === toWh && s.product_id === prodId);
      if (dest) dest.quantity += qty;
      else db.warehouse_stocks.push({ id: db.warehouse_stocks.length + 1, warehouse_id: toWh, product_id: prodId, quantity: qty, updated_at: nowStr });

      const trfNo = "TRF-" + new Date().getFullYear() + "-" + String(db.stock_transfers.length + 1).padStart(3, "0");
      db.stock_transfers.unshift({
        id: db.stock_transfers.length + 1,
        transfer_no: trfNo,
        from_warehouse_id: fromWh,
        to_warehouse_id: toWh,
        product_id: prodId,
        quantity: qty,
        transferred_by: data.transferred_by || "Sanjay Rathod",
        notes: data.notes || "",
        status: "COMPLETED",
        created_at: nowStr
      });
      saveLocalDB(db);
      return { success: true, transfer_no: trfNo };
    }

    if (path === "gemini/chat") {
      const msg = (data.message || "").toLowerCase();
      const isGu = /[\\u0A80-\\u0AFF]/.test(data.message || "");
      let reply = "";
      if (msg.includes("laptop") || msg.includes("લેપટોપ")) {
        reply = isGu ? "અમારી પાસે Dell Latitude, Lenovo ThinkPad અને Asus ROG ગેમિંગ લેપટોપ્સ સ્ટોકમાં ઉપલબ્ધ છે! તમે વેબસાઇટ પરથી RAM અને SSD અપગ્રેડ પણ પસંદ કરી શકો છો." : "We have Dell Latitude, Lenovo ThinkPad, and Asus ROG Gaming laptops in stock! You can customize RAM & SSD directly on our store with live pricing.";
      } else if (msg.includes("workstation") || msg.includes("વર્કસ્ટેશન") || msg.includes("cad") || msg.includes("editing")) {
        reply = isGu ? "AutoCAD, SolidWorks અને 4K Video Editing માટે HP Z4 G4 અને Dell Precision 3660 વર્કસ્ટેશન્સ તૈયાર છે. આમાં Quadro/RTX GPU અને ECC મેમરી આવે છે." : "For AutoCAD, 3D Rendering and 4K Video Editing, we offer HP Z4 G4 and Dell Precision 3660 workstations with Quadro/RTX GPUs.";
      } else if (msg.includes("firewall") || msg.includes("ફાયરવોલ") || msg.includes("sophos") || msg.includes("network")) {
        reply = isGu ? "કંપની નેટવર્કને સુરક્ષિત કરવા માટે Sophos XGS 116 અને Fortinet FortiGate 40F હાર્ડવેર ફાયરવોલ ઉપલબ્ધ છે. અમારા નેટવર્ક એન્જિનિયર સંપૂર્ણ ઇન્સ્ટોલેશન કરી આપશે." : "To secure your corporate network from threats, we provide Sophos XGS 116 and Fortinet FortiGate 40F Next-Gen Firewalls with on-site setup.";
      } else if (msg.includes("repair") || msg.includes("સર્વિસ") || msg.includes("service") || msg.includes("blue screen") || msg.includes("display")) {
        reply = isGu ? "અમારી સર્વિસ લેબમાં લેપટોપ મધરબોર્ડ ચિપલેવલ રિપેરિંગ, ડિસ્પ્લે રિપ્લેસમેન્ટ અને થર્મલ સર્વિસ થાય છે. વેબસાઇટ પર 'Book Service' ટેબથી ટોકન બુક કરો!" : "Our advanced hardware lab offers chip-level laptop repair, screen replacement, and thermal servicing. Book a service token under 'Book Service'!";
      } else {
        reply = isGu ? "નમસ્તે! PCWARE માં આપનું સ્વાગત છે. હું તમારો સ્માર્ટ AI હાર્ડવેર આસિસ્ટન્ટ છું. લેપટોપ, કસ્ટમ પીસી, સર્વર કે સર્વિસ વિશે કંઈપણ પૂછી શકો છો!" : "Hello! Welcome to PCWARE. I am your smart AI Hardware Consultant. Feel free to ask about any laptop, workstation, server, firewall, or repair service!";
      }
      return {
        reply: reply,
        source: "pcware_client_ai",
        recommendations: (db.products || []).slice(0, 3)
      };
    }
'''

if mock_post_anchor in orig_js and 'if (path === "whatsapp-booking")' not in orig_js:
    orig_js = orig_js.replace(mock_post_anchor, new_mock_posts + "\n    " + mock_post_anchor)

# In handleLocalMock PUT:
mock_put_anchor = 'if (path.startsWith("jobsheets/")) {'
new_mock_puts = '''
    if (path.startsWith("inquiries/") && path.endsWith("/assign")) {
      const inqId = path.split("/")[1];
      if (!db.inquiries) db.inquiries = [];
      const inq = db.inquiries.find(i => i.id == inqId);
      if (inq) {
        inq.assigned_staff_id = data.staff_id;
        const st = (db.staff || []).find(s => s.id == data.staff_id);
        inq.assigned_staff_name = st ? st.name : "";
      }
      saveLocalDB(db);
      return { success: true };
    }
    if (path.startsWith("inquiries/") && path.endsWith("/fulfillment")) {
      const inqId = path.split("/")[1];
      if (!db.inquiries) db.inquiries = [];
      const inq = db.inquiries.find(i => i.id == inqId);
      if (inq) {
        inq.fulfillment_mode = data.fulfillment_mode;
        inq.delivery_tracking_no = data.delivery_tracking_no || "";
      }
      saveLocalDB(db);
      return { success: true };
    }
'''

if mock_put_anchor in orig_js and 'inquiries/' not in orig_js:
    orig_js = orig_js.replace(mock_put_anchor, new_mock_puts + "\n    " + mock_put_anchor)

# Update state object to include staff, warehouses, etc.
state_anchor = 'invoices: (DEFAULT_SEED_DATA && DEFAULT_SEED_DATA.invoices) ? [...DEFAULT_SEED_DATA.invoices] : [],'
new_state_entries = '''invoices: (DEFAULT_SEED_DATA && DEFAULT_SEED_DATA.invoices) ? [...DEFAULT_SEED_DATA.invoices] : [],
  staff: (DEFAULT_SEED_DATA && DEFAULT_SEED_DATA.staff) ? [...DEFAULT_SEED_DATA.staff] : [],
  warehouses: (DEFAULT_SEED_DATA && DEFAULT_SEED_DATA.warehouses) ? [...DEFAULT_SEED_DATA.warehouses] : [],
  warehouseStocks: (DEFAULT_SEED_DATA && DEFAULT_SEED_DATA.warehouse_stocks) ? [...DEFAULT_SEED_DATA.warehouse_stocks] : [],
  stockTransfers: (DEFAULT_SEED_DATA && DEFAULT_SEED_DATA.stock_transfers) ? [...DEFAULT_SEED_DATA.stock_transfers] : [],
  branches: (DEFAULT_SEED_DATA && DEFAULT_SEED_DATA.branches) ? [...DEFAULT_SEED_DATA.branches] : [],
  currentCustomBuild: null,
'''
if state_anchor in orig_js and 'staff:' not in orig_js:
    orig_js = orig_js.replace(state_anchor, new_state_entries)

with open(target_file, "w", encoding="utf-8") as f:
    f.write(orig_js)

print("build_enterprise_app step 1 completed successfully!")
