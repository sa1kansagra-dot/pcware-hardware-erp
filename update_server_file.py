import sys
import re

with open("server.py", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Add Gemini Helper Function before ERPRequestHandler
gemini_helper = '''
def handle_gemini_interaction(user_msg, prods, api_key, gemini_model, history=None):
    user_lower = user_msg.lower()

    # If real Gemini API key is provided, attempt live API call
    if api_key and api_key.strip():
        try:
            import urllib.request
            import json

            # Compact catalog summary for grounding
            catalog_summary = []
            for p in prods[:40]:
                catalog_summary.append(f"- {p['name']} ({p['category']}): ₹{p['selling_price']:,.0f} [Stock: {p['stock_quantity']}]")
            catalog_str = "\\n".join(catalog_summary)

            system_instruction = (
                "You are the official AI Hardware & IT Consultant for PCWARE (Rajkot, Gujarat). "
                "PCWARE specializes in Laptops (Business, Gaming, Refurbished), Custom PC Builds, Workstations, Servers, "
                "Sophos/Fortinet Firewalls, Antivirus, and Expert Repair & AMC Services.\\n"
                "Address: Shop No. SF, 47, 48, 49, Suvarnabhumi Complex, opp. Speedwell Party Plot, Ambika Twp, Mota Mava, Rajkot, Gujarat 360005.\\n"
                "Contacts: CEO +91 94261 83934, Service +91 80007 80704, Inquiry +91 70167 37271.\\n"
                "Always respond politely in the language used by the customer (Gujarati or English).\\n"
                "Ground your answers strictly on the following in-stock PCWARE products whenever recommending hardware:\\n"
                f"{catalog_str}\\n"
                "Encourage customers to click 'Book on WhatsApp' or visit the Rajkot showroom for live demos."
            )

            url = f"https://generativelanguage.googleapis.com/v1beta/models/{gemini_model}:generateContent?key={api_key}"
            payload = {
                "contents": [
                    {
                        "role": "user",
                        "parts": [{"text": f"{system_instruction}\\n\\nCustomer Query: {user_msg}"}]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.7,
                    "maxOutputTokens": 600
                }
            }
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=8) as response:
                resp_data = json.loads(response.read().decode("utf-8"))
                candidates = resp_data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        text_reply = parts[0].get("text", "")
                        return {
                            "reply": text_reply,
                            "source": "google_gemini_live",
                            "recommendations": find_recommendations(user_lower, prods)
                        }
        except Exception as e:
            # Fall back to smart built-in engine if network/API fails
            pass

    # Built-in High-Quality Smart AI Engine (Grounded on PCWARE Inventory)
    is_gujarati = any(ord(char) >= 0x0A80 and ord(char) <= 0x0AFF for char in user_msg)
    recommendations = find_recommendations(user_lower, prods)

    # 1. Greetings
    if any(w in user_lower for w in ["hi", "hello", "kem cho", "કેમ છો", "નમસ્તે", "namaste", "hey"]):
        if is_gujarati:
            reply = "નમસ્તે! PCWARE રાજકોટમાં આપનું હાર્દિક સ્વાગત છે! 🖥️✨\\n\\nહું તમારો AI હાર્ડવેર આસિસ્ટન્ટ છું. હું તમને શ્રેષ્ઠ **લેપટોપ, વર્કસ્ટેશન, કસ્ટમ પીસી, સર્વર, ફાયરવોલ અને રિપેરિંગ સર્વિસ** પસંદ કરવામાં મદદ કરી શકું છું.\\n\\nઆજે હું તમને શું સહાય કરી શકું?"
        else:
            reply = "Hello! Welcome to **PCWARE Rajkot**! 🖥️✨\\n\\nI am your AI Hardware & IT Consultant. I can help you with **Laptops, Desktop Workstations, Custom PC Builds, Servers, Network Firewalls, and Laptop Repair/AMC Services**.\\n\\nHow can I help you today?"

    # 2. Contact & Address
    elif any(w in user_lower for w in ["address", "location", "ક્યાં છે", "સરનામું", "phone", "number", "mobile", "ક્યાં આવેલી", "શોરૂમ", "showroom"]):
        if is_gujarati:
            reply = "📍 **PCWARE શોરૂમ સરનામું:**\\nShop No. SF, 47, 48, 49, સુવર્ણભૂમિ કોમ્પ્લેક્સ, સ્પીડવેલ પાર્ટી પ્લોટ સામે, અંબિકા ટાઉનશીપ, મોટા મવા, રાજકોટ - 360005.\\n\\n📞 **સંપર્ક નંબરો:**\\n• CEO: +91 94261 83934\\n• સર્વિસ લેબ: +91 80007 80704\\n• સેલ્સ & પૂછપરછ: +91 70167 37271\\n\\nતમે રૂબરૂ શોરૂમ પર આવીને કોઈપણ મશીનનું લાઈવ ડેમો જોઈ શકો છો!"
        else:
            reply = "📍 **PCWARE Rajkot Showroom Address:**\\nShop No. SF, 47, 48, 49, Suvarnabhumi Complex, opp. Speedwell Party Plot, Ambika Twp, Mota Mava, Rajkot, Gujarat 360005.\\n\\n📞 **Direct Helplines:**\\n• CEO: +91 94261 83934\\n• Service / Lab: +91 80007 80704\\n• Sales / Inquiry: +91 70167 37271\\n\\nYou are welcome to visit our showroom for live product demonstrations!"

    # 3. Laptop / Laptops
    elif any(w in user_lower for w in ["laptop", "લેપટોપ", "tally", "ટેલી", "dell", "lenovo", "thinkpad", "latitude"]):
        matched = [p for p in prods if p["category"] == "laptop"][:3]
        if is_gujarati:
            items_txt = "\\n".join([f"• **{p['name']}** — ₹{p['selling_price']:,.0f} (સ્ટોક: {p['stock_quantity']})" for p in matched])
            reply = f"અમારી પાસે બિઝનેસ, ઓફિસ અને સ્ટુડન્ટ્સ માટે શ્રેષ્ઠ લેપટોપ્સ સ્ટોકમાં ઉપલબ્ધ છે! તમે RAM અને SSD આપણી વેબસાઇટ પરથી જ લાઈવ અપગ્રેડ પણ કરી શકો છો:\\n\\n{items_txt}\\n\\nકોઈપણ લેપટોપ બુક કરવા માટે નીચે **'Book on WhatsApp'** પર ક્લિક કરો."
        else:
            items_txt = "\\n".join([f"• **{p['name']}** — ₹{p['selling_price']:,.0f} (Stock: {p['stock_quantity']})" for p in matched])
            reply = f"We have excellent Commercial, Business & Refurbished laptops in stock! You can customize & upgrade RAM and SSD with live pricing right on our store:\\n\\n{items_txt}\\n\\nClick **'Book on WhatsApp'** below to instantly reserve your configuration!"

    # 4. Workstations & Video Editing / CAD
    elif any(w in user_lower for w in ["workstation", "વર્કસ્ટેશન", "cad", "solidworks", "video editing", "3d", "rendering", "ai"]):
        matched = [p for p in prods if p["category"] == "workstation"][:3]
        if is_gujarati:
            items_txt = "\\n".join([f"• **{p['name']}** — ₹{p['selling_price']:,.0f}" for p in matched])
            reply = f"AutoCAD, 3D Rendering, Premier Pro અને AI Deep Learning માટે અમારી સુપરફાસ્ટ વર્કસ્ટેશન્સ ઉપલબ્ધ છે:\\n\\n{items_txt}\\n\\nઆ મશીન્સમાં ECC મેમરી અને ક્વાડ્રો/RTX ગ્રાફિક્સ કાર્ડ આવે છે. સેલ્સ એક્ઝિક્યુટિવ સાથે વાત કરવા WhatsApp બટન દબાવો."
        else:
            items_txt = "\\n".join([f"• **{p['name']}** — ₹{p['selling_price']:,.0f}" for p in matched])
            reply = f"For AutoCAD, SolidWorks, 4K Video Editing and AI modeling, here are our specialized high-performance workstations:\\n\\n{items_txt}\\n\\nEquipped with Xeon/Ryzen processors and RTX graphics. Click below to discuss corporate configurations!"

    # 5. Servers & TrueNAS
    elif any(w in user_lower for w in ["server", "સર્વર", "truenas", "nas", "raid", "poweredge"]):
        matched = [p for p in prods if p["category"] == "server"][:3]
        if is_gujarati:
            items_txt = "\\n".join([f"• **{p['name']}** — ₹{p['selling_price']:,.0f}" for p in matched])
            reply = f"ઓફિસ ડેટાબેઝ, ટેલી ક્લાઉડ અને ઓટોમેટિક બેકઅપ માટે અમારી પાસે Tower & Rack Servers સ્ટોકમાં છે:\\n\\n{items_txt}\\n\\nઆમાં RAID-1/RAID-Z2 સાથે ડેટા સુરક્ષિત રહે છે. સંપૂર્ણ ડેમો માટે અમારો સંપર્ક કરો."
        else:
            items_txt = "\\n".join([f"• **{p['name']}** — ₹{p['selling_price']:,.0f}" for p in matched])
            reply = f"For central office ERP databases, Tally multi-user, and enterprise backups, we offer certified servers:\\n\\n{items_txt}\\n\\nIncludes hot-plug drives and redundant power supplies. Let us know your requirements!"

    # 6. Firewalls & Networking
    elif any(w in user_lower for w in ["firewall", "ફાયરવોલ", "sophos", "fortinet", "network", "સ્વિચ", "switch", "vpn"]):
        matched = [p for p in prods if p["category"] == "firewall_networking"][:3]
        if is_gujarati:
            items_txt = "\\n".join([f"• **{p['name']}** — ₹{p['selling_price']:,.0f}" for p in matched])
            reply = f"તમારી કંપની કે હોસ્પિટલના નેટવર્કને હેકિંગ અને રેન્સમવેરથી બચાવવા માટે અમે Sophos અને Fortinet ફાયરવોલ સેટઅપ અને મેન્ટેનન્સ આપીએ છીએ:\\n\\n{items_txt}\\n\\nઅમારા નેટવર્ક એન્જિનિયર તમારી ઓફિસે વિઝિટ કરીને સંપૂર્ણ સેટઅપ કરી આપશે."
        else:
            items_txt = "\\n".join([f"• **{p['name']}** — ₹{p['selling_price']:,.0f}" for p in matched])
            reply = f"To protect your corporate network from ransomware, intrusion and data leaks, we provide hardware firewall solutions:\\n\\n{items_txt}\\n\\nIncludes VPN configuration, web filtering and bandwidth management."

    # 7. Antivirus & Security
    elif any(w in user_lower for w in ["antivirus", "એન્ટિવાયરસ", "quick heal", "kaspersky", "seqrite", "વાયરસ", "virus"]):
        matched = [p for p in prods if p["category"] == "antivirus_software"][:3]
        if is_gujarati:
            items_txt = "\\n".join([f"• **{p['name']}** — ₹{p['selling_price']:,.0f}" for p in matched])
            reply = f"અમે અધિકૃત Quick Heal, Kaspersky અને Seqrite Endpoint Security લાઇસન્સ પ્રોવાઇડ કરીએ છીએ:\\n\\n{items_txt}\\n\\n૧ વર્ષ અને ૩ વર્ષના ઓરિજિનલ સીરીયલ બોક્સ તાત્કાલિક ઉપલબ્ધ છે."
        else:
            items_txt = "\\n".join([f"• **{p['name']}** — ₹{p['selling_price']:,.0f}" for p in matched])
            reply = f"We are authorized partners for Quick Heal, Kaspersky, and Seqrite Endpoint Cloud Security:\\n\\n{items_txt}\\n\\nGenuine retail packs with instant license activation."

    # 8. Repair & Service
    elif any(w in user_lower for w in ["repair", "service", "રિપેર", "સર્વિસ", "ખરાબ", "બ્લુ સ્ક્રીન", "blue screen", "heating", "display", "slow", "સ્લો"]):
        if is_gujarati:
            reply = "🔧 **PCWARE એક્સપર્ટ સર્વિસ લેબ:**\\nઅમે લેપટોપ મધરબોર્ડ ચિપલેવલ રિપેરિંગ, સ્ક્રિન/કીબોર્ડ બદલવા, થર્મલ પેસ્ટ અને હીટિંગ સોલ્યુશન, તેમજ વિન્ડોઝ ફોર્મેટિંગની સર્વોત્તમ સેવા આપીએ છીએ.\\n\\n• **વોરંટી સર્વિસ:** ફ્રી\\n• **પેઇડ સર્વિસ:** વ્યાજબી દરો\\n• **AMC સપોર્ટ:** વાર્ષિક કોન્ટ્રેક્ટ\\n\\nતમારો જોબશીટ ટોકન બુક કરવા માટે વેબસાઇટમાં **'Book Service'** ટેબ પર જાઓ અથવા સીધો 8000780704 પર કોલ કરો!"
        else:
            reply = "🔧 **PCWARE Advanced Hardware Repair Lab:**\\nWe provide chip-level laptop motherboard repair, screen & keyboard replacements, thermal servicing, and Windows troubleshooting.\\n\\n• **Warranty Support:** Free under warranty\\n• **Paid Service:** Affordable rates\\n• **Corporate AMC:** Available for offices\\n\\nClick the **'Book Service'** tab above to reserve a repair token, or call our service lab at +91 80007 80704!"

    # 9. Generic Fallback
    else:
        if is_gujarati:
            reply = f"હું તમારી પૂછપરછ સમજી રહ્યો છું. PCWARE માં અમારી પાસે તમામ કમ્પ્યુટર પાર્ટ્સ, કસ્ટમ પીસી, બિઝનેસ લેપટોપ્સ, સર્વર્સ અને આઈટી સર્વિસ ઉપલબ્ધ છે!\\n\\nવિશેષ ટેકનિકલ સહાય અથવા લાઈવ સ્ટોક ક્વોટેશન માટે તમે સીધું WhatsApp પર અમારા સેલ્સ એક્ઝિક્યુટિવ સાથે વાત કરી શકો છો."
        else:
            reply = f"I understand your query regarding computer hardware & IT solutions. At **PCWARE**, we have complete stocks of processors, motherboards, laptops, workstations, network firewalls, and expert repair services!\\n\\nFor custom configurations and instant quotes, feel free to chat directly with our team on WhatsApp."

    return {
        "reply": reply,
        "source": "pcware_grounded_ai",
        "recommendations": recommendations,
        "suggested_chips": [
            "Best Laptop under ₹50,000",
            "AutoCAD Workstation Suggestion",
            "Sophos Firewall Details",
            "Book Laptop Repair Service"
        ]
    }

def find_recommendations(query_lower, prods):
    recs = []
    if any(k in query_lower for k in ["laptop", "લેપટોપ"]):
        recs = [p for p in prods if p["category"] == "laptop"][:3]
    elif any(k in query_lower for k in ["workstation", "વર્કસ્ટેશન", "cad", "editing"]):
        recs = [p for p in prods if p["category"] == "workstation"][:3]
    elif any(k in query_lower for k in ["server", "સર્વર", "nas"]):
        recs = [p for p in prods if p["category"] == "server"][:3]
    elif any(k in query_lower for k in ["firewall", "ફાયરવોલ", "network"]):
        recs = [p for p in prods if p["category"] == "firewall_networking"][:3]
    elif any(k in query_lower for k in ["antivirus", "એન્ટિવાયરસ", "quick heal"]):
        recs = [p for p in prods if p["category"] == "antivirus_software"][:3]
    elif any(k in query_lower for k in ["cpu", "processor", "પ્રોસેસર"]):
        recs = [p for p in prods if p["category"] == "processor"][:3]
    else:
        recs = prods[:3]
    return recs
'''

# Check if handle_gemini_interaction already in content
if "def handle_gemini_interaction" not in content:
    content = gemini_helper + "\n" + content

# 2. Add GET endpoints
get_routes_code = '''
            # 17. Staff Members (8 Team Members)
            if path == "/api/staff":
                rows = cursor.execute("SELECT * FROM staff_members ORDER BY id ASC").fetchall()
                return self.send_json([dict(r) for r in rows])

            # 18. Warehouses (3 Godowns)
            if path == "/api/warehouses":
                rows = cursor.execute("SELECT * FROM warehouses ORDER BY is_primary DESC, id ASC").fetchall()
                return self.send_json([dict(r) for r in rows])

            # 19. Warehouse Stock
            if path == "/api/warehouse-stock":
                wh_id = query.get("warehouse_id", [None])[0]
                prod_id = query.get("product_id", [None])[0]
                sql = """
                SELECT ws.*, w.name as warehouse_name, w.code as warehouse_code,
                       p.name as product_name, p.category, p.brand, p.selling_price, p.sku
                FROM warehouse_stocks ws
                JOIN warehouses w ON ws.warehouse_id = w.id
                JOIN products p ON ws.product_id = p.id
                WHERE 1=1
                """
                params = []
                if wh_id:
                    sql += " AND ws.warehouse_id = ?"
                    params.append(wh_id)
                if prod_id:
                    sql += " AND ws.product_id = ?"
                    params.append(prod_id)
                sql += " ORDER BY w.id ASC, p.id ASC"
                rows = cursor.execute(sql, params).fetchall()
                return self.send_json([dict(r) for r in rows])

            # 20. Stock Transfers
            if path == "/api/stock-transfers":
                sql = """
                SELECT st.*,
                       wf.name as from_warehouse_name,
                       wt.name as to_warehouse_name,
                       p.name as product_name, p.sku as product_sku
                FROM stock_transfers st
                JOIN warehouses wf ON st.from_warehouse_id = wf.id
                JOIN warehouses wt ON st.to_warehouse_id = wt.id
                JOIN products p ON st.product_id = p.id
                ORDER BY st.id DESC
                """
                rows = cursor.execute(sql).fetchall()
                return self.send_json([dict(r) for r in rows])

            # 21. Branches (Franchise-Ready Architecture)
            if path == "/api/branches":
                rows = cursor.execute("SELECT * FROM branches ORDER BY is_hq DESC, id ASC").fetchall()
                return self.send_json([dict(r) for r in rows])
'''

get_anchor = 'return self.send_json({"error": "API route not found"}, 404)'
# Insert before the last return in handle_api_get
pos_get_anchor = content.find(get_anchor)
if pos_get_anchor != -1 and "/api/staff" not in content:
    content = content[:pos_get_anchor] + get_routes_code + "\n            " + content[pos_get_anchor:]

# 3. Add POST endpoints
post_routes_code = '''
            # 14. Add Staff Member
            if path == "/api/staff":
                cursor.execute("""
                INSERT INTO staff_members (name, role, department, phone, email, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    body.get("name"), body.get("role"), body.get("department"),
                    body.get("phone"), body.get("email"), body.get("status", "ACTIVE"), now_str
                ))
                conn.commit()
                return self.send_json({"success": True, "id": cursor.lastrowid})

            # 15. Stock Transfer between Godowns
            if path == "/api/stock-transfers":
                from_wh = int(body.get("from_warehouse_id"))
                to_wh = int(body.get("to_warehouse_id"))
                prod_id = int(body.get("product_id"))
                qty = int(body.get("quantity", 1))
                transferred_by = body.get("transferred_by", "Staff")
                notes = body.get("notes", "")

                if from_wh == to_wh:
                    return self.send_json({"error": "Source and destination warehouse cannot be the same"}, 400)
                if qty <= 0:
                    return self.send_json({"error": "Quantity must be greater than zero"}, 400)

                curr_source = cursor.execute(
                    "SELECT quantity FROM warehouse_stocks WHERE warehouse_id = ? AND product_id = ?",
                    (from_wh, prod_id)
                ).fetchone()
                source_stock = curr_source[0] if curr_source else 0

                if source_stock < qty:
                    return self.send_json({"error": f"Insufficient stock in source warehouse (Available: {source_stock})"}, 400)

                cursor.execute("""
                UPDATE warehouse_stocks SET quantity = quantity - ?, updated_at = ?
                WHERE warehouse_id = ? AND product_id = ?
                """, (qty, now_str, from_wh, prod_id))

                curr_dest = cursor.execute(
                    "SELECT id FROM warehouse_stocks WHERE warehouse_id = ? AND product_id = ?",
                    (to_wh, prod_id)
                ).fetchone()
                if curr_dest:
                    cursor.execute("""
                    UPDATE warehouse_stocks SET quantity = quantity + ?, updated_at = ?
                    WHERE warehouse_id = ? AND product_id = ?
                    """, (qty, now_str, to_wh, prod_id))
                else:
                    cursor.execute("""
                    INSERT INTO warehouse_stocks (warehouse_id, product_id, quantity, updated_at)
                    VALUES (?, ?, ?, ?)
                    """, (to_wh, prod_id, qty, now_str))

                count_trf = cursor.execute("SELECT COUNT(*) FROM stock_transfers").fetchone()[0]
                trf_no = f"TRF-{datetime.now().year}-{str(count_trf + 1).zfill(3)}"
                cursor.execute("""
                INSERT INTO stock_transfers (transfer_no, from_warehouse_id, to_warehouse_id, product_id, quantity, transferred_by, notes, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'COMPLETED', ?)
                """, (trf_no, from_wh, to_wh, prod_id, qty, transferred_by, notes, now_str))

                conn.commit()
                return self.send_json({"success": True, "transfer_no": trf_no})

            # 16. WhatsApp Booking with Auto-Lead Creation
            if path == "/api/whatsapp-booking":
                cust_name = body.get("customer_name", "Valued Customer")
                cust_phone = body.get("customer_phone", "")
                cust_email = body.get("customer_email", "")
                cust_address = body.get("customer_address", "")
                req_type = body.get("requirement_type", "LAPTOP")
                items_requested = body.get("items_requested", "")
                custom_specs = body.get("custom_specs", "")
                if isinstance(custom_specs, dict):
                    import json
                    custom_specs = json.dumps(custom_specs)
                budget = float(body.get("estimated_budget", 0))
                fulfillment = body.get("fulfillment_mode", "SHOWROOM_VISIT")
                notes = body.get("notes", "")

                # Assign staff
                assigned_staff_id = 2  # Hardik Patel (Sales)
                assigned_staff_name = "Hardik Patel"
                if req_type in ("WORKSTATION", "SERVER"):
                    assigned_staff_id = 3
                    assigned_staff_name = "Pratik Dave"
                elif req_type in ("FIREWALL_NETWORKING", "ANTIVIRUS_SOFTWARE"):
                    assigned_staff_id = 6
                    assigned_staff_name = "Ravi Kothari"

                count_inq = cursor.execute("SELECT COUNT(*) FROM inquiries").fetchone()[0]
                inq_no = f"INQ-{datetime.now().year}-{str(count_inq + 101)}"

                cursor.execute("""
                INSERT INTO inquiries (inquiry_number, customer_name, customer_phone, customer_email, customer_address, requirement_type, items_requested, custom_specs, estimated_budget, status, source, fulfillment_mode, assigned_staff_id, assigned_staff_name, notes, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'NEW', 'WhatsApp Store', ?, ?, ?, ?, ?)
                """, (inq_no, cust_name, cust_phone, cust_email, cust_address, req_type, items_requested, custom_specs, budget, fulfillment, assigned_staff_id, assigned_staff_name, notes, now_str))

                cursor.execute("UPDATE staff_members SET active_leads_count = active_leads_count + 1 WHERE id = ?", (assigned_staff_id,))
                conn.commit()

                mode_str = "🏪 Showroom Visit & Live Demo" if fulfillment == "SHOWROOM_VISIT" else "📦 Courier Parcel Dispatch"
                wa_text = f"Hello PCWARE! I would like to book/inquire:\\n\\n" \\
                          f"📋 *Inquiry No:* {inq_no}\\n" \\
                          f"💻 *Item:* {items_requested}\\n" \\
                          f"💰 *Budget/Price:* ₹{budget:,.2f}\\n" \\
                          f"🚚 *Fulfillment:* {mode_str}\\n" \\
                          f"👤 *Customer:* {cust_name}\\n" \\
                          f"📞 *Mobile:* {cust_phone}\\n" \\
                          f"📍 *City/Address:* {cust_address or 'Rajkot'}\\n"
                if custom_specs:
                    wa_text += f"⚙️ *Specs/Upgrades:* {custom_specs}\\n"
                wa_text += "\\nPlease confirm availability and share next steps. Thank you!"

                ceo_phone = "9426183934"
                encoded_msg = urllib.parse.quote(wa_text)
                whatsapp_url = f"https://wa.me/91{ceo_phone}?text={encoded_msg}"

                return self.send_json({
                    "success": True,
                    "inquiry_number": inq_no,
                    "assigned_staff": assigned_staff_name,
                    "whatsapp_url": whatsapp_url,
                    "message": wa_text
                })

            # 17. Google Gemini AI Assistant
            if path == "/api/gemini/chat":
                user_msg = body.get("message", "").strip()
                history = body.get("history", [])

                api_key_row = cursor.execute("SELECT value FROM store_settings WHERE key = 'gemini_api_key'").fetchone()
                model_row = cursor.execute("SELECT value FROM store_settings WHERE key = 'gemini_model'").fetchone()
                api_key = (api_key_row[0] if api_key_row else "") or os.environ.get("GEMINI_API_KEY", "")
                gemini_model = (model_row[0] if model_row else "gemini-1.5-flash")

                prods = [dict(r) for r in cursor.execute(
                    "SELECT id, name, category, brand, selling_price, specs, stock_quantity FROM products WHERE stock_quantity > 0 ORDER BY selling_price ASC"
                ).fetchall()]

                ai_response = handle_gemini_interaction(user_msg, prods, api_key, gemini_model, history)
                return self.send_json(ai_response)
'''

# Find end of handle_api_post
# Look for the last `return self.send_json({"error": "API route not found"}, 404)` in handle_api_post
post_anchor_pattern = re.compile(r'def handle_api_post\(self, path\):.*?return self\.send_json\(\{"error": "API route not found"\}, 404\)', re.DOTALL)
m = post_anchor_pattern.search(content)
if m and "/api/whatsapp-booking" not in content:
    match_str = m.group(0)
    idx = match_str.rfind('return self.send_json({"error": "API route not found"}, 404)')
    new_match_str = match_str[:idx] + post_routes_code + "\n            " + match_str[idx:]
    content = content[:m.start()] + new_match_str + content[m.end():]

# 4. Add PUT endpoints
put_routes_code = '''
            # Assign Staff to Inquiry
            if path.startswith("/api/inquiries/") and path.endswith("/assign"):
                inq_id = path.split("/")[-2]
                staff_id = body.get("staff_id")
                staff = cursor.execute("SELECT name FROM staff_members WHERE id = ?", (staff_id,)).fetchone()
                staff_name = staff[0] if staff else ""
                cursor.execute("UPDATE inquiries SET assigned_staff_id = ?, assigned_staff_name = ? WHERE id = ?", (staff_id, staff_name, inq_id))
                cursor.execute("UPDATE staff_members SET active_leads_count = active_leads_count + 1 WHERE id = ?", (staff_id,))
                conn.commit()
                return self.send_json({"success": True, "assigned_staff_name": staff_name})

            # Update Fulfillment Mode & Tracking
            if path.startswith("/api/inquiries/") and path.endswith("/fulfillment"):
                inq_id = path.split("/")[-2]
                mode = body.get("fulfillment_mode", "SHOWROOM_VISIT")
                trk = body.get("delivery_tracking_no", "")
                cursor.execute("UPDATE inquiries SET fulfillment_mode = ?, delivery_tracking_no = ? WHERE id = ?", (mode, trk, inq_id))
                conn.commit()
                return self.send_json({"success": True})

            # Update Staff Member
            if path.startswith("/api/staff/"):
                st_id = path.split("/")[-1]
                cursor.execute("""
                UPDATE staff_members SET name = ?, role = ?, department = ?, phone = ?, email = ?, status = ?
                WHERE id = ?
                """, (body.get("name"), body.get("role"), body.get("department"), body.get("phone"), body.get("email"), body.get("status", "ACTIVE"), st_id))
                conn.commit()
                return self.send_json({"success": True})
'''

put_anchor_pattern = re.compile(r'def handle_api_put\(self, path\):.*?return self\.send_json\(\{"error": "API route not found"\}, 404\)', re.DOTALL)
m2 = put_anchor_pattern.search(content)
if m2 and "/fulfillment" not in content:
    match_str2 = m2.group(0)
    idx2 = match_str2.rfind('return self.send_json({"error": "API route not found"}, 404)')
    new_match_str2 = match_str2[:idx2] + put_routes_code + "\n            " + match_str2[idx2:]
    content = content[:m2.start()] + new_match_str2 + content[m2.end():]

with open("server.py", "w", encoding="utf-8") as f:
    f.write(content)

print("server.py updated with all new enterprise routes and Gemini AI assistant!")
