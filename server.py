import http.server
import socketserver
import json
import urllib.parse
import os
import sqlite3
import base64
import uuid
import re
import shutil
from datetime import datetime, timedelta

PORT = int(os.environ.get("PORT", 8080))
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
DB_PATH = os.path.join(BASE_DIR, "hardware_erp.db")
BACKUPS_DIR = os.path.join(BASE_DIR, "backups")
os.makedirs(BACKUPS_DIR, exist_ok=True)

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def ensure_daily_backup():
    try:
        if not os.path.exists(DB_PATH):
            return
        os.makedirs(BACKUPS_DIR, exist_ok=True)
        today_str = datetime.now().strftime("%Y-%m-%d")
        daily_filename = f"daily_backup_{today_str}.db"
        daily_path = os.path.join(BACKUPS_DIR, daily_filename)
        if not os.path.exists(daily_path):
            src_conn = sqlite3.connect(DB_PATH)
            dst_conn = sqlite3.connect(daily_path)
            src_conn.backup(dst_conn)
            dst_conn.close()
            src_conn.close()
            print(f"[Backup] Daily automated backup saved: {daily_filename}")
    except Exception as e:
        print(f"[Backup Error] Daily backup failed: {e}")

def create_backup_snapshot(prefix="manual"):
    try:
        if not os.path.exists(DB_PATH):
            return None, "Database file not found"
        os.makedirs(BACKUPS_DIR, exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"{prefix}_backup_{timestamp}.db"
        target_path = os.path.join(BACKUPS_DIR, filename)
        src_conn = sqlite3.connect(DB_PATH)
        dst_conn = sqlite3.connect(target_path)
        src_conn.backup(dst_conn)
        dst_conn.close()
        src_conn.close()
        return filename, None
    except Exception as e:
        return None, str(e)

def get_backups_metadata():
    ensure_daily_backup()
    os.makedirs(BACKUPS_DIR, exist_ok=True)
    files = [f for f in os.listdir(BACKUPS_DIR) if f.endswith(".db")]
    backups = []
    
    for f in files:
        f_path = os.path.join(BACKUPS_DIR, f)
        try:
            stat = os.stat(f_path)
            size_bytes = stat.st_size
            size_kb = size_bytes / 1024
            size_str = f"{size_kb:.1f} KB" if size_kb < 1024 else f"{size_kb/1024:.2f} MB"
            
            mtime = datetime.fromtimestamp(stat.st_mtime)
            created_iso = mtime.isoformat()
            date_formatted = mtime.strftime("%d %b %Y")
            time_formatted = mtime.strftime("%I:%M %p")
            
            if f.startswith("daily_backup_"):
                b_type = "daily"
                b_type_label = "Daily Auto-Backup"
                badge_class = "bg-emerald-100 text-emerald-800 border-emerald-300"
            elif f.startswith("manual_backup_"):
                b_type = "manual"
                b_type_label = "Manual Snapshot"
                badge_class = "bg-blue-100 text-blue-800 border-blue-300"
            elif f.startswith("pre_restore_safety_backup_"):
                b_type = "safety"
                b_type_label = "Safety Checkpoint"
                badge_class = "bg-amber-100 text-amber-800 border-amber-300"
            elif f.startswith("uploaded_backup_"):
                b_type = "uploaded"
                b_type_label = "Uploaded Backup"
                badge_class = "bg-purple-100 text-purple-800 border-purple-300"
            else:
                b_type = "other"
                b_type_label = "Database Backup"
                badge_class = "bg-slate-100 text-slate-800 border-slate-300"
                
            backups.append({
                "filename": f,
                "size_bytes": size_bytes,
                "size_formatted": size_str,
                "created_at": created_iso,
                "date_formatted": date_formatted,
                "time_formatted": time_formatted,
                "timestamp": stat.st_mtime,
                "type": b_type,
                "type_label": b_type_label,
                "badge_class": badge_class
            })
        except Exception:
            continue
            
    backups.sort(key=lambda x: x["timestamp"], reverse=True)
    
    live_size_bytes = os.path.getsize(DB_PATH) if os.path.exists(DB_PATH) else 0
    live_kb = live_size_bytes / 1024
    live_size_formatted = f"{live_kb:.1f} KB" if live_kb < 1024 else f"{live_kb/1024:.2f} MB"
    
    p_count, inv_count, cust_count, ord_count = 0, 0, 0, 0
    try:
        conn = get_db()
        c = conn.cursor()
        p_count = c.execute("SELECT COUNT(*) FROM products").fetchone()[0]
        inv_count = c.execute("SELECT COUNT(*) FROM invoices").fetchone()[0]
        cust_count = c.execute("SELECT COUNT(*) FROM parties WHERE type='CUSTOMER'").fetchone()[0]
        ord_count = c.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
        conn.close()
    except Exception:
        pass
        
    today_str = datetime.now().strftime("%Y-%m-%d")
    today_file = f"daily_backup_{today_str}.db"
    today_exists = os.path.exists(os.path.join(BACKUPS_DIR, today_file))
    
    return {
        "backups": backups,
        "total_backups": len(backups),
        "live_db_size_bytes": live_size_bytes,
        "live_db_size_formatted": live_size_formatted,
        "today_backup_status": "Active (Saved)" if today_exists else "Pending",
        "today_backup_file": today_file if today_exists else None,
        "stats": {
            "products": p_count,
            "invoices": inv_count,
            "customers": cust_count,
            "orders": ord_count
        }
    }


def is_gujlish_or_gujarati(msg, lower_words):
    if any(ord(char) >= 0x0A80 and ord(char) <= 0x0AFF for char in msg):
        return True
    gujlish_markers = {
        "kem", "cho", "kyan", "su", "shu", "nathi", "aavti", "chale", "che", "levu",
        "joi", "bhav", "ketlo", "ketla", "mate", "karvu", "banavvu", "batao", "aapo",
        "karo", "ma", "chalu", "bandh", "tuti", "kharab", "tamare", "amare", "saru",
        "bhai", "kone", "kyare", "rakhyo", "aavse", "bataavo", "madad"
    }
    return bool(lower_words.intersection(gujlish_markers))

def extract_budget(text):
    m_k = re.search(r'(\d+)\s*k\b', text, re.IGNORECASE)
    if m_k:
        return int(m_k.group(1)) * 1000
    m_num = re.search(r'\b(\d{4,6})\b', text)
    if m_num:
        return int(m_num.group(1))
    return None

def run_builtin_pcware_ai(user_msg, prods):
    user_lower = user_msg.lower().strip()
    words = set(re.findall(r'\b\w+\b', user_lower))
    is_gu = is_gujlish_or_gujarati(user_msg, words)
    budget = extract_budget(user_lower)

    # Priority 1: Repair & Service issues
    repair_words = {"repair", "service", "રિપેર", "સર્વિસ", "display", "screen", "keyboard", "broken", "tuti", "heating", "slow", "hang", "format", "kharab", "chalu"}
    if words.intersection(repair_words) or any(k in user_lower for k in ["display nathi", "chalu nathi", "screen damage", "blue screen", "હાર્ડવેર રિપેર"]):
        recs = [p for p in prods if p.get("category") in ("laptop", "ram", "storage")][:3]
        if is_gu:
            reply = (
                "🔧 **PCWARE એડવાન્સ ચિપલેવલ રિપેરિંગ લેબ (રાજકોટ):**\n\n"
                "અમારી પાસે અદ્યતન BGA મશીન અને કુશળ હાર્ડવેર એન્જિનિયર્સ છે જે નીચેની સેવાઓ આપે છે:\n"
                "• મધરબોર્ડ ચિપલેવલ રિપેરિંગ & શોર્ટિંગ સોલ્યુશન\n"
                "• ઓરિજિનલ લેપટોપ ડિસ્પ્લે & કીબોર્ડ રિપ્લેસમેન્ટ\n"
                "• થર્મલ પેસ્ટ સર્વિસિંગ (હીટિંગ & ફેન અવાજ)\n"
                "• વિન્ડોઝ ફોર્મેટિંગ & ડેટા રિકવરી\n\n"
                "🏷️ **વોરંટી સપોર્ટ:** વોરંટી વાળા ગ્રાહકો માટે ફ્રી ડાયગ્નોસ્ટિક્સ!\n"
                "📞 સર્વિસ હેલ્પલાઇન: **+91 80007 80704**\n"
                "તમારી જોબશીટ બુક કરવા માટે વેબસાઇટ ઉપર **'Book Service'** ટેબ પર ક્લિક કરો!"
            )
        else:
            reply = (
                "🔧 **PCWARE Advanced Chip-Level Hardware Lab (Rajkot):**\n\n"
                "Equipped with BGA rework stations and skilled chip-level engineers:\n"
                "• Motherboard short-circuit & IC replacement\n"
                "• Original FHD/4K laptop screen & keyboard replacement\n"
                "• Deep thermal cleaning & liquid cooling service\n"
                "• High-recovery data retrieval & OS repair\n\n"
                "🏷️ **Warranty Support:** Free inspection for machines under PCWARE warranty!\n"
                "📞 Direct Service Lab: **+91 80007 80704**\n"
                "Click the **'Book Service'** tab above to reserve your service token immediately!"
            )

    # Priority 2: Server & TrueNAS
    elif any(k in user_lower for k in ["server", "સર્વર", "truenas", "nas", "raid", "poweredge"]):
        recs = [p for p in prods if p.get("category") == "server"][:3]
        if is_gu:
            items_txt = "\n".join([f"• **{p['name']}** — ₹{p['selling_price']:,.0f}" for p in recs])
            reply = (
                "સેન્ટ્રલ ઓફિસ ERP, Tally Multi-User અને ઓટોમેટિક ડેટા બેકઅપ માટે PCWARE સર્ટીફાઇડ સર્વર્સ પ્રોવાઇડ કરે છે! 🗄️\n\n"
                f"{items_txt}\n\n"
                "• હાર્ડવેર RAID-1 / RAID-Z2 પ્રોટેક્શન\n"
                "• Hot-Plug Enterprise HDDs & Redundant SMPS\n"
                "તમારી કંપનીની જરૂરિયાત મુજબ સર્વર ડિઝાઇન કરાવવા નીચે 'Book on WhatsApp' પર ક્લિક કરો."
            )
        else:
            items_txt = "\n".join([f"• **{p['name']}** — ₹{p['selling_price']:,.0f}" for p in recs])
            reply = (
                "For central office ERP databases, Multi-User Tally, and bulletproof backups, we deploy enterprise servers: 🗄️\n\n"
                f"{items_txt}\n\n"
                "• Hardware RAID-1 / ZFS Redundancy\n"
                "• Hot-Swap Enterprise SAS/SATA drives\n"
                "• Dual Redundant Power Supplies\n"
                "Reach out via WhatsApp to architect your server deployment!"
            )

    # Priority 3: Workstation / CAD / 3D / Video Editing / AI
    elif any(k in user_lower for k in ["workstation", "વર્કસ્ટેશન", "cad", "solidworks", "video editing", "3d", "rendering", "ai studio", "quadro"]):
        recs = [p for p in prods if p.get("category") == "workstation"][:3]
        if is_gu:
            items_txt = "\n".join([f"• **{p['name']}** — ₹{p['selling_price']:,.0f}" for p in recs])
            reply = (
                "AutoCAD, SolidWorks, 4K Premiere Pro, 3ds Max અને AI Deep Learning માટે સુપર કમ્પ્યુટિંગ વર્કસ્ટેશન્સ સ્ટોકમાં ઉપલબ્ધ છે! 🚀\n\n"
                f"{items_txt}\n\n"
                "આ મશીન્સમાં Intel Xeon / AMD Ryzen પ્રોસેસર્સ, ECC Error-Correction મેમરી અને Dedicated RTX Graphics આવે છે.\n"
                "કસ્ટમ વર્કસ્ટેશન ક્વોટેશન માટે નીચે **'Book on WhatsApp'** પર ક્લિક કરો."
            )
        else:
            items_txt = "\n".join([f"• **{p['name']}** — ₹{p['selling_price']:,.0f}" for p in recs])
            reply = (
                "For heavy workloads like AutoCAD, SolidWorks, 4K Video Editing, 3D Rendering, and AI/ML Training: 🚀\n\n"
                f"{items_txt}\n\n"
                "Equipped with Xeon/Ryzen CPUs, ECC server-grade RAM, and Nvidia RTX GPUs for 24/7 stability.\n"
                "Click below to get a specialized technical quotation via WhatsApp!"
            )

    # Priority 4: Firewall & Networking
    elif any(k in user_lower for k in ["firewall", "ફાયરવોલ", "sophos", "fortinet", "switch", "router", "vpn"]):
        recs = [p for p in prods if p.get("category") == "firewall_networking"][:3]
        if is_gu:
            items_txt = "\n".join([f"• **{p['name']}** — ₹{p['selling_price']:,.0f}" for p in recs])
            reply = (
                "તમારી કંપની, હોસ્પિટલ કે ફેક્ટરીના ડેટાને રેન્સમવેર અને સાયબર હુમલાઓથી સુરક્ષિત કરવા માટે Sophos અને Fortinet હાર્ડવેર ફાયરવોલ શ્રેષ્ઠ ઉપાય છે! 🛡️\n\n"
                f"{items_txt}\n\n"
                "અમારા સર્ટીફાઈડ નેટવર્ક એન્જિનિયર તમારી સાઈટ પર આવીને Site-to-Site VPN, બેન્ડવિડ્થ કંટ્રોલ અને કન્ટેન્ટ ફિલ્ટરિંગ સેટઅપ કરી આપે છે."
            )
        else:
            items_txt = "\n".join([f"• **{p['name']}** — ₹{p['selling_price']:,.0f}" for p in recs])
            reply = (
                "To shield your corporate network from ransomware, unauthorized intrusions, and data leakage: 🛡️\n\n"
                f"{items_txt}\n\n"
                "Includes complete deployment of IPsec VPN, multi-WAN failover, bandwidth management, and intrusion prevention."
            )

    # Priority 5: Antivirus & Security Software
    elif any(k in user_lower for k in ["antivirus", "એન્ટિવાયરસ", "quick heal", "kaspersky", "seqrite", "virus"]):
        recs = [p for p in prods if p.get("category") == "antivirus_software"][:3]
        if is_gu:
            items_txt = "\n".join([f"• **{p['name']}** — ₹{p['selling_price']:,.0f}" for p in recs])
            reply = (
                "અમે Quick Heal, Kaspersky અને Seqrite Endpoint Security ના અધિકૃત પાર્ટનર છીએ! 🔒\n\n"
                f"{items_txt}\n\n"
                "૧ વર્ષ અને ૩ વર્ષના ઓરિજિનલ બોક્સ પેક અને ઈન્સ્ટન્ટ લાયસન્સ એકટીવેશન ઉપલબ્ધ છે."
            )
        else:
            items_txt = "\n".join([f"• **{p['name']}** — ₹{p['selling_price']:,.0f}" for p in recs])
            reply = (
                "Authorized sales & cloud deployment partner for Quick Heal, Kaspersky, and Seqrite Endpoint Security: 🔒\n\n"
                f"{items_txt}\n\n"
                "Genuine retail licenses with on-spot activation and cloud management console."
            )

    # Priority 6: PC Build / Custom PC / Gaming Rig
    elif any(k in user_lower for k in ["pc build", "custom pc", "પીસી બનાવવું", "gaming pc", "ગેમિંગ", "assemble"]) or (("pc" in words or "computer" in words) and ("gaming" in words or "build" in words or "banavvu" in words)):
        recs = [p for p in prods if p.get("category") in ("gpu", "processor", "motherboard", "cabinet_power")][:3]
        if is_gu:
            reply = (
                "🖥️ **PCWARE કસ્ટમ પીસી બિલ્ડિંગ & એસેમ્બલિંગ:**\n\n"
                "અમે ગેમિંગ, 4K એડિટિંગ અને ઓફિસ યુઝ માટે બેસ્ટ કસ્ટમ પીસી તૈયાર કરીએ છીએ:\n"
                "• Intel 13th/14th Gen Core i5 / i7 / i9 અથવા AMD Ryzen 5 / 7 / 9\n"
                "• Nvidia GeForce RTX 3060 / 4060 / 4070 Ti Graphics Cards\n"
                "• Kingston / Crucial High-Speed DDR4/DDR5 RGB RAM & NVMe SSD\n"
                "• Corsair 80 Plus Bronze/Gold SMPS & RGB Tempered Glass Cabinets\n\n"
                "તમારા ચોક્કસ બજેટમાં પીસી એસેમ્બલિંગ ક્વોટેશન માટે WhatsApp બટન દબાવો!"
            )
        else:
            reply = (
                "🖥️ **PCWARE Custom PC Build & Rig Studio:**\n\n"
                "Custom built to precision for Esports Gaming, Content Creation, and Everyday Productivity:\n"
                "• Intel Core i5/i7/i9 (14th Gen) & AMD Ryzen 5000/7000/9000 series\n"
                "• Dedicated Nvidia GeForce RTX series graphic cards\n"
                "• High frequency DDR4/DDR5 RAM and Gen4 NVMe SSDs\n"
                "• Certified 80-Plus Power Supplies & Airflow Optimized Cases\n\n"
                "Chat on WhatsApp with our PC build master to customize your machine!"
            )

    # Priority 7: Budget Query
    elif budget:
        under = [p for p in prods if p.get("selling_price", 0) <= budget + 5000]
        recs = sorted(under, key=lambda x: abs(x.get("selling_price", 0) - budget))[:3] if under else prods[:3]
        matched_txt = "\n".join([f"• **{p['name']}** — ₹{p['selling_price']:,.0f} [સ્ટોક: {p['stock_quantity']}]" for p in recs])
        if is_gu:
            reply = (
                f"તમારા **₹{budget:,.0f}** ના બજેટ માટે PCWARE પાસે શ્રેષ્ઠ વિકલ્પો ઉપલબ્ધ છે! 🎯\n\n"
                f"{matched_txt}\n\n"
                "💡 **વિશેષતા:** તમે આપણી વેબસાઇટ પરથી જ તમારી જરૂરિયાત મુજબ **RAM (16GB/32GB)** અને **SSD (512GB/1TB/2TB)** લાઈવ અપગ્રેડ કરી શકો છો!\n"
                "બુકિંગ માટે નીચે આપેલા પ્રોડક્ટ કાર્ડમાંથી સીધું **'Book'** અથવા **'Book on WhatsApp'** દબાવો."
            )
        else:
            matched_txt_en = "\n".join([f"• **{p['name']}** — ₹{p['selling_price']:,.0f} [In Stock: {p['stock_quantity']}]" for p in recs])
            reply = (
                f"Here are top-performing hardware options around your budget of **₹{budget:,.0f}**: 🎯\n\n"
                f"{matched_txt_en}\n\n"
                "💡 **Custom Upgrades:** You can customize RAM & SSD capacity directly on our website with instant live price calculation!\n"
                "Click **'Book'** or **'Book on WhatsApp'** to reserve your device instantly."
            )

    # Priority 8: Laptop Query
    elif any(k in user_lower for k in ["laptop", "લેપટોપ", "latitude", "thinkpad", "tally", "refurbished", "notebook"]):
        recs = [p for p in prods if p.get("category") == "laptop"][:3]
        if is_gu:
            items_txt = "\n".join([f"• **{p['name']}** — ₹{p['selling_price']:,.0f} (સ્ટોક: {p['stock_quantity']})" for p in recs])
            reply = (
                "અમારી પાસે બિઝનેસ, એકાઉન્ટિંગ (Tally Prime), ઓફિસ અને સ્ટુડન્ટ્સ માટે પ્રીમિયમ લેપટોપ્સ સ્ટોકમાં ઉપલબ્ધ છે! 💻\n\n"
                f"{items_txt}\n\n"
                "🔥 **લાઈવ અપગ્રેડ ઉપલબ્ધ:**\n"
                "વેબસાઇટ પર 'Customize & Book' ક્લિક કરીને તમે 8GB થી 64GB RAM અને 512GB થી 2TB NVMe SSD તેમજ Quick Heal Antivirus સીધું પસંદ કરી શકો છો!\n"
                "તત્કાલ બુક કરવા માટે નીચે **'Book'** પર ક્લિક કરો."
            )
        else:
            items_txt = "\n".join([f"• **{p['name']}** — ₹{p['selling_price']:,.0f} (Stock: {p['stock_quantity']})" for p in recs])
            reply = (
                "We have a high-grade collection of Commercial, Business & Refurbished laptops in stock! 💻\n\n"
                f"{items_txt}\n\n"
                "🔥 **Dynamic Custom Upgrades Available:**\n"
                "You can configure RAM (up to 64GB) and ultra-fast NVMe SSD (up to 2TB) directly from our online store!\n"
                "Click **'Book'** below to instantly connect with our sales desk on WhatsApp."
            )

    # Priority 9: Hardware Components
    elif words.intersection({"ram", "ssd", "nvme", "gpu", "processor", "motherboard", "smps"}):
        recs = [p for p in prods if p.get("category") in ("ram", "storage", "processor", "motherboard", "gpu")][:3]
        if is_gu:
            reply = (
                "⚡ **હાર્ડવેર કમ્પોનન્ટ્સ & ઓન-સ્પોટ અપગ્રેડ:**\n\n"
                "અમારી પાસે તમામ અસલ કમ્પોનન્ટ્સ સીધા કંપની વોરંટી સાથે સ્ટોકમાં છે:\n"
                "• **RAM:** Crucial / Kingston DDR4 & DDR5 (8GB, 16GB, 32GB)\n"
                "• **SSD:** Kingston NV2 / Samsung 980 NVMe Gen4 (512GB, 1TB, 2TB)\n"
                "• **ગ્રાફિક્સ કાર્ડ:** Zotac / Gigabyte Nvidia GeForce RTX Series\n"
                "• **મધરબોર્ડ્સ:** Asus Prime, Gigabyte Ultra Durable, MSI Pro Series\n\n"
                "અમારા શોરૂમ પર માત્ર 15 મિનિટમાં તમારા લેપટોપ કે પીસીમાં ઇન્સ્ટોલેશન થઈ જશે!"
            )
        else:
            reply = (
                "⚡ **Genuine Hardware Components & Instant Upgrades:**\n\n"
                "All items backed by authentic brand manufacturer warranty:\n"
                "• **RAM:** DDR4 & DDR5 3200MHz / 5600MHz (Crucial / Kingston)\n"
                "• **SSD:** PCIe NVMe Gen4 M.2 SSDs (512GB to 2TB)\n"
                "• **GPUs:** Nvidia GeForce RTX 3050, 4060, 3060 12GB\n"
                "• **Motherboards:** Intel LGA1700 & AMD AM4/AM5 chipsets\n\n"
                "Get your upgrade installed in just 15 minutes at our Rajkot showroom!"
            )

    # Priority 10: Address & Contact & Location
    elif words.intersection({"address", "location", "kyan", "સરનામું", "showroom", "શોરૂમ", "phone", "contact", "ceo", "kahan"}):
        recs = prods[:3]
        if is_gu:
            reply = (
                "📍 **PCWARE શોરૂમ સરનામું (રાજકોટ):**\n"
                "શોપ નં. SF 47, 48, 49, સુવર્ણભૂમિ કોમ્પ્લેક્સ, સ્પીડવેલ પાર્ટી પ્લોટ સામે, અંબિકા ટાઉનશીપ, મોટા મવા, રાજકોટ, ગુજરાત - 360005.\n\n"
                "📞 **ડાયરેક્ટ સંપર્ક નંબરો:**\n"
                "• **CEO (સેલ્સ & ક્વોટેશન):** +91 94261 83934\n"
                "• **સર્વિસ & રિપેરિંગ લેબ:** +91 80007 80704\n"
                "• **જનરલ પૂછપરછ:** +91 70167 37271\n\n"
                "🕒 **શોરૂમ સમય:** સોમવાર થી શનિવાર, સવારે 10:00 થી રાત્રે 8:30 સુધી.\n"
                "તમે રૂબરૂ પધારીને તમામ મશીનનું લાઈવ ડેમો પણ જોઈ શકો છો!"
            )
        else:
            reply = (
                "📍 **PCWARE Rajkot Flagship Showroom:**\n"
                "Shop No. SF 47, 48, 49, Suvarnabhumi Complex, opp. Speedwell Party Plot, Ambika Twp, Mota Mava, Rajkot, Gujarat 360005.\n\n"
                "📞 **Official Helplines:**\n"
                "• **CEO (Direct Sales & Bulk Deals):** +91 94261 83934\n"
                "• **Hardware Service Lab:** +91 80007 80704\n"
                "• **Inquiries & Quotes:** +91 70167 37271\n\n"
                "🕒 **Timings:** Monday - Saturday, 10:00 AM - 8:30 PM.\n"
                "Visit us anytime for a hands-on live demo of laptops, workstations & servers!"
            )

    # Priority 11: Greetings
    elif words.intersection({"hi", "hello", "hey", "namaste", "kem", "cho", "pranam", "sup", "kemcho"}):
        recs = [p for p in prods if p.get("category") == "laptop"][:3]
        if is_gu:
            reply = (
                "નમસ્તે! **PCWARE રાજકોટ** માં આપનું હાર્દિક સ્વાગત છે! 🖥️✨\n\n"
                "હું તમારો 24/7 AI IT & હાર્ડવેર કન્સલ્ટન્ટ છું. હું તમને નીચેની બાબતોમાં સહાય કરી શકું છું:\n"
                "• **લેપટોપ્સ:** બિઝનેસ, સ્ટુડન્ટ, ગેમિંગ & રિફર્બિશ્ડ (લાઇવ RAM/SSD અપગ્રેડ સાથે)\n"
                "• **ડેસ્કટોપ & વર્કસ્ટેશન્સ:** AutoCAD, 3D Rendering & AI Studio\n"
                "• **સર્વર્સ & TrueNAS:** એન્ટરપ્રાઇઝ ડેટાબેઝ & ઓટો-બેકઅપ\n"
                "• **ફાયરવોલ & એન્ટિવાયરસ:** Sophos, Fortinet, Quick Heal, Seqrite\n"
                "• **ચિપલેવલ રિપેરિંગ:** ડિસ્પ્લે, મધરબોર્ડ & થર્મલ સર્વિસ\n\n"
                "તમને આજે કયા ઉત્પાદન અથવા સર્વિસ માટે માહિતી જોઈએ છે?"
            )
        else:
            reply = (
                "Hello! Welcome to **PCWARE Rajkot**! 🖥️✨\n\n"
                "I am your official AI IT & Hardware Consultant. How can I assist you today?\n"
                "• **Laptops:** Commercial, ThinkPad, Latitude, Gaming (with live RAM/SSD customization)\n"
                "• **Workstations & Custom PCs:** AutoCAD, 4K Video Editing & AI Studio\n"
                "• **Servers & TrueNAS:** Centralized ERP databases & Automated Storage\n"
                "• **Firewall & Security:** Sophos, Fortinet Next-Gen Firewalls & Seqrite EPS\n"
                "• **Chip-Level Repair Lab:** Motherboard, Screen, Keyboard & Windows troubleshooting\n\n"
                "Feel free to ask about any configuration or budget!"
            )

    # Fallback with Live Products
    else:
        recs = prods[:3]
        sample_names = ", ".join([p.get("name", "") for p in recs[:2]])
        if is_gu:
            reply = (
                f"હું તમારી પૂછપરછ સમજી ગયો છું! **PCWARE રાજકોટ** માં તમામ પ્રકારના લેપટોપ્સ, વર્કસ્ટેશન્સ, સર્વર્સ, ફાયરવોલ અને એક્સપર્ટ રિપેરિંગ ઉપલબ્ધ છે.\n\n"
                f"અત્યારે અમારા સ્ટોકમાં **{sample_names}** સહિત 65+ થી વધુ પ્રોડક્ટ્સ રેડી સ્ટોકમાં છે!\n\n"
                "વધુ માહિતી કે ચોક્કસ ડિસ્કાઉન્ટ ભાવ માટે તમે સીધું નીચે **'Book on WhatsApp'** અથવા CEO (+91 94261 83934) સાથે ચેટ કરી શકો છો."
            )
        else:
            reply = (
                f"I understand your query! At **PCWARE Rajkot**, we specialize in business laptops, custom desktop PCs, servers, firewalls, and hardware care.\n\n"
                f"We currently have top systems in stock including **{sample_names}** and many more!\n\n"
                "For customized quotes or technical recommendations, please click **'Book on WhatsApp'** or chat with our CEO at +91 94261 83934."
            )

    return {
        "reply": reply,
        "source": "pcware_grounded_ai",
        "recommendations": recs,
        "suggested_chips": [
            "Best Laptop under ₹50,000",
            "AutoCAD Workstation Suggestion",
            "Sophos Firewall Details",
            "Book Laptop Repair Service"
        ]
    }

def handle_gemini_interaction(user_msg, prods, api_key, gemini_model, history=None):
    if api_key and api_key.strip():
        try:
            import urllib.request
            import json

            catalog_summary = []
            for p in prods[:35]:
                catalog_summary.append(f"- {p['name']} ({p['category']}): ₹{p['selling_price']:,.0f} [Stock: {p['stock_quantity']}]")
            catalog_str = "\n".join(catalog_summary)

            system_instruction = (
                "You are the official Senior AI IT & Hardware Consultant for PCWARE (Rajkot, Gujarat). "
                "PCWARE specializes in Laptops (Business, Gaming, Refurbished), Custom PC Builds, Workstations, Servers, "
                "Sophos/Fortinet Firewalls, Antivirus, and Expert Chip-Level Laptop Repair & AMC Services.\n"
                "Address: Shop No. SF, 47, 48, 49, Suvarnabhumi Complex, opp. Speedwell Party Plot, Ambika Twp, Mota Mava, Rajkot, Gujarat 360005.\n"
                "Contacts: CEO +91 94261 83934, Service +91 80007 80704, Inquiry +91 70167 37271.\n"
                "Always respond politely in the language used by the customer (Gujarati or English or Gujlish).\n"
                "Ground your answers strictly on the following in-stock PCWARE products whenever recommending hardware:\n"
                f"{catalog_str}\n"
                "Encourage customers to click 'Book on WhatsApp' or visit the Rajkot showroom for live demos."
            )

            url = f"https://generativelanguage.googleapis.com/v1beta/models/{gemini_model}:generateContent?key={api_key}"
            payload = {
                "contents": [
                    {
                        "role": "user",
                        "parts": [{"text": f"{system_instruction}\n\nCustomer Query: {user_msg}"}]
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
                            "recommendations": [p for p in prods if p.get("category") == "laptop"][:3]
                        }
        except Exception as e:
            pass

    return run_builtin_pcware_ai(user_msg, prods)

class ERPRequestHandler(http.server.BaseHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps(data, default=str).encode("utf-8"))

    def read_json_body(self):
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length == 0:
            return {}
        body = self.rfile.read(content_length)
        return json.loads(body.decode("utf-8"))

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        if path.startswith("/api/"):
            return self.handle_api_get(path, query)

        # Serve static files explicitly
        if path in ("/", "", "/index.html"):
            target = os.path.join(STATIC_DIR, "index.html")
        elif path in ("/app.js", "/static/app.js"):
            target = os.path.join(STATIC_DIR, "app.js")
        else:
            rel = path.lstrip("/")
            if rel.startswith("static/"):
                rel = rel[7:]
            target = os.path.join(STATIC_DIR, rel)

        if os.path.exists(target) and os.path.isfile(target):
            self.send_response(200)
            if target.endswith(".html"):
                self.send_header("Content-Type", "text/html; charset=utf-8")
            elif target.endswith(".js"):
                self.send_header("Content-Type", "application/javascript; charset=utf-8")
            elif target.endswith(".css"):
                self.send_header("Content-Type", "text/css; charset=utf-8")
            elif target.endswith(".svg"):
                self.send_header("Content-Type", "image/svg+xml")
            elif target.endswith(".png"):
                self.send_header("Content-Type", "image/png")
            elif target.endswith(".jpg") or target.endswith(".jpeg"):
                self.send_header("Content-Type", "image/jpeg")
            elif target.endswith(".json"):
                self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            with open(target, "rb") as f:
                self.wfile.write(f.read())
            return

        self.send_response(404)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"404 Not Found")

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        if path.startswith("/api/"):
            return self.handle_api_post(path)
        self.send_json({"error": "Not Found"}, 404)

    def do_PUT(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        if path.startswith("/api/"):
            return self.handle_api_put(path)
        self.send_json({"error": "Not Found"}, 404)

    def do_DELETE(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        if path.startswith("/api/"):
            return self.handle_api_delete(path)
        self.send_json({"error": "Not Found"}, 404)

    def handle_api_get(self, path, query):
        conn = get_db()
        cursor = conn.cursor()

        try:
            # 1. Dashboard Stats
            if path == "/api/stats":
                total_products = cursor.execute("SELECT COUNT(*) FROM products").fetchone()[0]
                low_stock = cursor.execute("SELECT COUNT(*) FROM products WHERE stock_quantity <= low_stock_threshold").fetchone()[0]
                active_repairs = cursor.execute("SELECT COUNT(*) FROM job_sheets WHERE status NOT IN ('DELIVERED', 'CANCELLED')").fetchone()[0]
                repairs_ready = cursor.execute("SELECT COUNT(*) FROM job_sheets WHERE status = 'REPAIRED'").fetchone()[0]
                active_amc = cursor.execute("SELECT COUNT(*) FROM amc_contracts WHERE status = 'ACTIVE'").fetchone()[0]
                amc_expiring = cursor.execute("SELECT COUNT(*) FROM amc_contracts WHERE status = 'EXPIRING_SOON'").fetchone()[0]
                revenue_row = cursor.execute("SELECT SUM(grand_total) FROM invoices").fetchone()[0]
                total_revenue = revenue_row if revenue_row else 0.0

                pending_inquiries = cursor.execute("SELECT COUNT(*) FROM inquiries WHERE status = 'PENDING'").fetchone()[0]
                total_orders = cursor.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
                total_parties = cursor.execute("SELECT COUNT(*) FROM parties").fetchone()[0]
                total_staff = cursor.execute("SELECT COUNT(*) FROM staff_members WHERE status = 'ACTIVE'").fetchone()[0]
                total_serials = cursor.execute("SELECT COUNT(*) FROM serial_numbers").fetchone()[0]
                total_invoices = cursor.execute("SELECT COUNT(*) FROM invoices").fetchone()[0]

                recent_jobs = [dict(row) for row in cursor.execute("SELECT * FROM job_sheets ORDER BY id DESC LIMIT 5").fetchall()]
                recent_orders = [dict(row) for row in cursor.execute("SELECT * FROM orders ORDER BY id DESC LIMIT 5").fetchall()]
                low_stock_items = [dict(row) for row in cursor.execute("SELECT * FROM products WHERE stock_quantity <= low_stock_threshold LIMIT 5").fetchall()]

                return self.send_json({
                    "total_products": total_products,
                    "low_stock_count": low_stock,
                    "active_repairs": active_repairs,
                    "repairs_ready": repairs_ready,
                    "active_amc": active_amc,
                    "amc_expiring": amc_expiring,
                    "total_revenue": total_revenue,
                    "pending_inquiries": pending_inquiries,
                    "total_orders": total_orders,
                    "total_parties": total_parties,
                    "total_staff": total_staff,
                    "total_serials": total_serials,
                    "total_invoices": total_invoices,
                    "recent_jobs": recent_jobs,
                    "recent_orders": recent_orders,
                    "low_stock_items": low_stock_items
                })

            # 2. Store Settings
            if path == "/api/store-settings":
                rows = cursor.execute("SELECT key, value FROM store_settings").fetchall()
                settings = {r["key"]: r["value"] for r in rows}
                return self.send_json(settings)

            # 3. Products
            if path == "/api/products":
                category = query.get("category", [None])[0]
                search = query.get("search", [None])[0]
                sql = "SELECT * FROM products WHERE 1=1"
                params = []
                if category and category != "all":
                    sql += " AND category = ?"
                    params.append(category)
                if search:
                    sql += " AND (name LIKE ? OR brand LIKE ? OR model LIKE ? OR sku LIKE ?)"
                    q = f"%{search}%"
                    params.extend([q, q, q, q])
                sql += " ORDER BY category ASC, id DESC"
                products = [dict(row) for row in cursor.execute(sql, params).fetchall()]
                return self.send_json(products)

            # 4. Job Sheets
            if path == "/api/jobsheets":
                status = query.get("status", [None])[0]
                search = query.get("search", [None])[0]
                sql = "SELECT * FROM job_sheets WHERE 1=1"
                params = []
                if status and status != "all":
                    sql += " AND status = ?"
                    params.append(status)
                if search:
                    sql += " AND (job_sheet_number LIKE ? OR customer_name LIKE ? OR customer_phone LIKE ? OR device_model LIKE ? OR device_serial LIKE ?)"
                    q = f"%{search}%"
                    params.extend([q, q, q, q, q])
                sql += " ORDER BY id DESC"
                jobs = [dict(row) for row in cursor.execute(sql, params).fetchall()]
                return self.send_json(jobs)

            # 5. Single Job Sheet + Logs
            if path.startswith("/api/jobsheets/"):
                job_id = path.split("/")[-1]
                job = cursor.execute("SELECT * FROM job_sheets WHERE id = ? OR job_sheet_number = ?", (job_id, job_id)).fetchone()
                if not job:
                    return self.send_json({"error": "Job Sheet not found"}, 404)
                logs = [dict(row) for row in cursor.execute("SELECT * FROM job_sheet_logs WHERE job_sheet_id = ? ORDER BY id ASC", (job["id"],)).fetchall()]
                res = dict(job)
                res["logs"] = logs
                return self.send_json(res)

            # 6. Customer Public Repair Tracker
            if path == "/api/track":
                q = query.get("q", [""])[0].strip()
                if not q:
                    return self.send_json([])
                jobs = cursor.execute("""
                SELECT * FROM job_sheets 
                WHERE job_sheet_number LIKE ? OR customer_phone LIKE ?
                ORDER BY id DESC LIMIT 5
                """, (f"%{q}%", f"%{q}%")).fetchall()
                results = []
                for j in jobs:
                    j_dict = dict(j)
                    logs = [dict(r) for r in cursor.execute("SELECT * FROM job_sheet_logs WHERE job_sheet_id = ? ORDER BY id ASC", (j["id"],)).fetchall()]
                    j_dict["logs"] = logs
                    results.append(j_dict)
                return self.send_json(results)

            # 7. Serial Numbers
            if path == "/api/serials":
                q = query.get("q", [""])[0].strip()
                sql = """
                SELECT s.*, p.name as product_name, p.brand as product_brand, p.category as product_category
                FROM serial_numbers s
                LEFT JOIN products p ON s.product_id = p.id
                WHERE 1=1
                """
                params = []
                if q:
                    sql += " AND (s.serial_number LIKE ? OR s.supplier_name LIKE ? OR s.customer_name LIKE ? OR s.customer_phone LIKE ? OR s.invoice_number LIKE ?)"
                    param_q = f"%{q}%"
                    params.extend([param_q, param_q, param_q, param_q, param_q])
                sql += " ORDER BY s.id DESC"
                serials = [dict(row) for row in cursor.execute(sql, params).fetchall()]
                return self.send_json(serials)

            # 8. Invoices
            if path == "/api/invoices":
                invoices = [dict(row) for row in cursor.execute("SELECT * FROM invoices ORDER BY id DESC").fetchall()]
                return self.send_json(invoices)

            if path.startswith("/api/invoices/"):
                inv_id = path.split("/")[-1]
                inv = cursor.execute("SELECT * FROM invoices WHERE id = ? OR invoice_number = ?", (inv_id, inv_id)).fetchone()
                if not inv:
                    return self.send_json({"error": "Invoice not found"}, 404)
                items = [dict(row) for row in cursor.execute("SELECT * FROM invoice_items WHERE invoice_id = ?", (inv["id"],)).fetchall()]
                res = dict(inv)
                res["items"] = items
                return self.send_json(res)

            # 9. AMC Contracts
            if path == "/api/amc":
                amcs = [dict(row) for row in cursor.execute("SELECT * FROM amc_contracts ORDER BY id DESC").fetchall()]
                return self.send_json(amcs)

            # 10.1 Referral & Loyalty Rules
            if path == "/api/referral/rules":
                rule = cursor.execute("SELECT * FROM referral_rules WHERE is_active = 1 ORDER BY id DESC LIMIT 1").fetchone()
                return self.send_json(dict(rule) if rule else {
                    "rule_name": "PCWARE Smart Refer & Earn",
                    "referrer_points": 200,
                    "referee_discount": 100.0,
                    "point_to_inr": 1.0,
                    "min_order_val": 500.0,
                    "max_discount_pct": 50.0,
                    "terms_text": "1. Refer friends and get 200 Reward Points on their first hardware purchase.\n2. Your friend gets instant discount on billing.\n3. 1 Reward Point = 1.00 INR.\n4. Only 1 referral code can be applied per order.\n5. Points are redeemed directly from net billing total."
                })

            # 10.2 All Referral Codes (Admin)
            if path == "/api/referral/codes":
                codes = [dict(row) for row in cursor.execute("SELECT * FROM referral_codes ORDER BY id DESC").fetchall()]
                return self.send_json(codes)

            # 10.3 Customer Rewards & Referral Profile
            if path == "/api/customer/rewards":
                phone = query.get("phone", [None])[0]
                if not phone:
                    return self.send_json({"error": "Phone number required"}, 400)

                # Total points balance
                points_row = cursor.execute("SELECT COALESCE(SUM(points), 0) FROM reward_transactions WHERE customer_phone = ?", (phone,)).fetchone()
                balance = points_row[0] if points_row else 0

                # Customer referral code
                code_row = cursor.execute("SELECT * FROM referral_codes WHERE owner_phone = ?", (phone,)).fetchone()
                if code_row:
                    cust_code = dict(code_row)
                else:
                    cust_name = "Customer"
                    party = cursor.execute("SELECT name FROM parties WHERE phone = ?", (phone,)).fetchone()
                    if party and party["name"]:
                        cust_name = party["name"]
                    
                    prefix = re.sub(r'[^A-Z]', '', cust_name.upper())[:4] or "PCW"
                    clean_phone = re.sub(r'[^0-9]', '', phone)[-4:]
                    generated_code = f"{prefix}{clean_phone}"

                    existing = cursor.execute("SELECT id FROM referral_codes WHERE code = ?", (generated_code,)).fetchone()
                    if existing:
                        generated_code = f"{generated_code}{uuid.uuid4().hex[:2].upper()}"

                    cursor.execute("""INSERT INTO referral_codes (code, owner_name, owner_phone, reward_points, discount_amount, usage_count, max_uses, status, notes) VALUES (?, ?, ?, 200, 100.0, 0, 0, 'ACTIVE', 'Auto-generated customer referral code')""", (generated_code, cust_name, phone))
                    conn.commit()
                    cust_code = {
                        "code": generated_code,
                        "owner_name": cust_name,
                        "owner_phone": phone,
                        "reward_points": 200,
                        "discount_amount": 100.0,
                        "usage_count": 0,
                        "status": "ACTIVE"
                    }

                stats_row = cursor.execute("""SELECT COUNT(*), COALESCE(SUM(points), 0) FROM reward_transactions WHERE customer_phone = ? AND transaction_type = 'REFERRAL_BONUS'""", (phone,)).fetchone()
                referral_count = stats_row[0] if stats_row else 0
                referral_points_earned = stats_row[1] if stats_row else 0

                ledger = [dict(row) for row in cursor.execute("""SELECT * FROM reward_transactions WHERE customer_phone = ? ORDER BY id DESC LIMIT 25""", (phone,)).fetchall()]

                rule = cursor.execute("SELECT * FROM referral_rules WHERE is_active = 1 ORDER BY id DESC LIMIT 1").fetchone()
                rule_dict = dict(rule) if rule else {
                    "referrer_points": 200,
                    "referee_discount": 100.0,
                    "point_to_inr": 1.0,
                    "min_order_val": 500.0
                }

                return self.send_json({
                    "balance": balance,
                    "referral_code": cust_code["code"],
                    "referral_stats": {
                        "total_referrals": referral_count,
                        "points_earned": referral_points_earned,
                        "usage_count": cust_code.get("usage_count", 0)
                    },
                    "transactions": ledger,
                    "rule": rule_dict
                })

            # 10. Orders
            if path == "/api/orders":
                orders = [dict(row) for row in cursor.execute("SELECT * FROM orders ORDER BY id DESC").fetchall()]
                return self.send_json(orders)

            # 11. Inquiries
            if path == "/api/inquiries":
                status = query.get("status", [None])[0]
                search = query.get("search", [None])[0]
                sql = "SELECT * FROM inquiries WHERE 1=1"
                params = []
                if status and status != "all":
                    sql += " AND status = ?"
                    params.append(status)
                if search:
                    sql += " AND (inquiry_number LIKE ? OR customer_name LIKE ? OR customer_phone LIKE ? OR requirement_type LIKE ?)"
                    q = f"%{search}%"
                    params.extend([q, q, q, q])
                sql += " ORDER BY id DESC"
                inquiries = [dict(row) for row in cursor.execute(sql, params).fetchall()]
                return self.send_json(inquiries)

            # 12. Quotations
            if path == "/api/quotations":
                search = query.get("search", [None])[0]
                sql = "SELECT * FROM quotations WHERE 1=1"
                params = []
                if search:
                    sql += " AND (quotation_number LIKE ? OR customer_name LIKE ? OR customer_phone LIKE ?)"
                    q = f"%{search}%"
                    params.extend([q, q, q])
                sql += " ORDER BY id DESC"
                quotations = [dict(row) for row in cursor.execute(sql, params).fetchall()]
                return self.send_json(quotations)

            if path.startswith("/api/quotations/"):
                qt_id = path.split("/")[-1]
                qt = cursor.execute("SELECT * FROM quotations WHERE id = ? OR quotation_number = ?", (qt_id, qt_id)).fetchone()
                if not qt:
                    return self.send_json({"error": "Quotation not found"}, 404)
                return self.send_json(dict(qt))

            # 13. Purchase Orders
            if path == "/api/purchase-orders":
                status = query.get("status", [None])[0]
                search = query.get("search", [None])[0]
                sql = "SELECT * FROM purchase_orders WHERE 1=1"
                params = []
                if status and status != "all":
                    sql += " AND status = ?"
                    params.append(status)
                if search:
                    sql += " AND (po_number LIKE ? OR supplier_name LIKE ? OR supplier_phone LIKE ?)"
                    q = f"%{search}%"
                    params.extend([q, q, q])
                sql += " ORDER BY id DESC"
                pos = [dict(row) for row in cursor.execute(sql, params).fetchall()]
                return self.send_json(pos)

            # 14. Shortage Requisition Items
            if path == "/api/shortage-items":
                sql = "SELECT * FROM products WHERE stock_quantity <= low_stock_threshold ORDER BY stock_quantity ASC"
                shortages = [dict(row) for row in cursor.execute(sql).fetchall()]
                return self.send_json(shortages)

            # 15. Parties (Customers & Suppliers)
            if path == "/api/parties":
                p_type = query.get("type", [None])[0]
                search = query.get("search", [None])[0]
                sql = "SELECT * FROM parties WHERE 1=1"
                params = []
                if p_type:
                    sql += " AND party_type = ?"
                    params.append(p_type)
                if search:
                    sql += " AND (name LIKE ? OR contact_person LIKE ? OR phone LIKE ? OR gstin LIKE ?)"
                    q = f"%{search}%"
                    params.extend([q, q, q, q])
                sql += " ORDER BY name ASC"
                parties = [dict(row) for row in cursor.execute(sql, params).fetchall()]
                return self.send_json(parties)

            # 16. Party Ledger
            if path == "/api/ledger":
                party_id = query.get("party_id", [None])[0]
                if not party_id:
                    return self.send_json({"error": "party_id required"}, 400)
                party = cursor.execute("SELECT * FROM parties WHERE id = ?", (party_id,)).fetchone()
                if not party:
                    return self.send_json({"error": "Party not found"}, 404)
                entries = [dict(row) for row in cursor.execute("SELECT * FROM ledger_entries WHERE party_id = ? ORDER BY entry_date ASC, id ASC", (party_id,)).fetchall()]
                res = dict(party)
                res["entries"] = entries
                return self.send_json(res)

            
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

            
            # 22. Customer Portal Dashboard API
            if path == "/api/customer/dashboard":
                phone = query.get("phone", [""])[0].strip()
                clean_phone = "".join(ch for ch in phone if ch.isdigit())
                if clean_phone:
                    phone = clean_phone[-10:]

                if not phone:
                    return self.send_json({"error": "Customer phone number required"}, 400)

                # Customer profile
                party = cursor.execute("SELECT * FROM parties WHERE phone LIKE ?", (f"%{phone}%",)).fetchone()
                cust_name = party["name"] if party else None

                if not cust_name:
                    inv_match = cursor.execute("SELECT customer_name, customer_email, customer_address FROM invoices WHERE customer_phone LIKE ? ORDER BY id DESC LIMIT 1", (f"%{phone}%",)).fetchone()
                    if inv_match:
                        cust_name = inv_match["customer_name"]

                if not cust_name:
                    sn_match = cursor.execute("SELECT customer_name FROM serial_numbers WHERE customer_phone LIKE ? ORDER BY id DESC LIMIT 1", (f"%{phone}%",)).fetchone()
                    if sn_match and sn_match["customer_name"]:
                        cust_name = sn_match["customer_name"]

                if not cust_name:
                    js_match = cursor.execute("SELECT customer_name FROM job_sheets WHERE customer_phone LIKE ? ORDER BY id DESC LIMIT 1", (f"%{phone}%",)).fetchone()
                    if js_match and js_match["customer_name"]:
                        cust_name = js_match["customer_name"]

                cust_profile = {
                    "name": cust_name or f"Customer ({phone})",
                    "phone": phone,
                    "email": (party["email"] if party and party["email"] else ""),
                    "address": (party["address"] if party and party["address"] else "Rajkot, Gujarat"),
                    "gstin": (party["gstin"] if party and party["gstin"] else "")
                }

                # Invoices
                invoices_rows = cursor.execute("SELECT * FROM invoices WHERE customer_phone LIKE ? ORDER BY id DESC", (f"%{phone}%",)).fetchall()
                invoices_list = []
                for inv in invoices_rows:
                    inv_dict = dict(inv)
                    items = [dict(r) for r in cursor.execute("SELECT * FROM invoice_items WHERE invoice_id = ?", (inv["id"],)).fetchall()]
                    inv_dict["items"] = items
                    invoices_list.append(inv_dict)

                # Registered Devices & Serial Numbers
                serials_rows = cursor.execute("""
                SELECT s.*, p.name as product_name, p.brand as product_brand, p.category as product_category, p.specs as product_specs
                FROM serial_numbers s
                LEFT JOIN products p ON s.product_id = p.id
                WHERE s.customer_phone LIKE ?
                ORDER BY s.id DESC
                """, (f"%{phone}%",)).fetchall()

                devices_list = []
                today_dt = datetime.now().date()

                for sn in serials_rows:
                    sn_dict = dict(sn)
                    model_name = sn_dict.get("device_model") or sn_dict.get("product_name") or "PCWARE Laptop"
                    
                    # Warranty calculation
                    days_remaining = 0
                    is_active = False
                    end_str = sn_dict.get("warranty_end_date") or ""
                    if end_str:
                        try:
                            end_dt = datetime.strptime(end_str.split(" ")[0], "%Y-%m-%d").date()
                            delta = (end_dt - today_dt).days
                            days_remaining = max(0, delta)
                            is_active = (delta > 0)
                        except Exception:
                            pass
                    elif sn_dict.get("sold_date") and sn_dict.get("warranty_months"):
                        try:
                            from datetime import timedelta
                            start_dt = datetime.strptime(sn_dict["sold_date"].split(" ")[0], "%Y-%m-%d").date()
                            end_dt = start_dt + timedelta(days=int(sn_dict["warranty_months"]) * 30)
                            end_str = end_dt.strftime("%Y-%m-%d")
                            delta = (end_dt - today_dt).days
                            days_remaining = max(0, delta)
                            is_active = (delta > 0)
                        except Exception:
                            pass

                    sn_dict["warranty_end_date"] = end_str
                    sn_dict["days_remaining"] = days_remaining
                    sn_dict["is_active_warranty"] = is_active
                    sn_dict["status_badge"] = f"🟢 સક્રિય વોરંટી ({days_remaining} દિવસ બાકી)" if is_active else "🔴 વોરંટી સમાપ્ત (Expired)"
                    
                    # Compatible upgrades tailored to device
                    sn_dict["compatible_upgrades"] = {
                        "ram": [
                            {"label": "+8GB DDR4 3200MHz High-Speed RAM", "price": 1750, "installed": "8GB Base"},
                            {"label": "+16GB DDR4 3200MHz Dual-Channel (Best for Multitasking)", "price": 3300},
                            {"label": "+32GB DDR4 High-Performance (Heavy Workload/Video)", "price": 5800}
                        ],
                        "ssd": [
                            {"label": "512GB NVMe Gen4 High-Speed M.2 SSD", "price": 3400},
                            {"label": "1TB NVMe Gen4 Ultra-Fast (Up to 3500MB/s)", "price": 5900},
                            {"label": "2TB NVMe Gen4 Enterprise Storage (Maximum Space)", "price": 10500}
                        ],
                        "antivirus": [
                            {"label": "Quick Heal Total Security 1 Year License Renewal", "price": 699},
                            {"label": "Quick Heal Total Security 3 Years Full Pack", "price": 1499},
                            {"label": "Seqrite Endpoint Cloud Security 1 Year", "price": 1850}
                        ],
                        "amc": [
                            {"label": "1-Year Comprehensive PCWARE Care & Priority AMC", "price": 2500}
                        ]
                    }
                    devices_list.append(sn_dict)

                # Service Tickets / Job Sheets
                tickets_rows = cursor.execute("""
                SELECT * FROM job_sheets 
                WHERE customer_phone LIKE ? 
                ORDER BY id DESC
                """, (f"%{phone}%",)).fetchall()

                tickets_list = []
                for t in tickets_rows:
                    t_dict = dict(t)
                    logs = [dict(r) for r in cursor.execute("SELECT * FROM job_sheet_logs WHERE job_sheet_id = ? ORDER BY id ASC", (t["id"],)).fetchall()]
                    t_dict["logs"] = logs
                    
                    st = t_dict.get("status", "RECEIVED")
                    if st == "RECEIVED":
                        progress = 25
                        step_label = "૧. સર્વિસ ટિકિટ નોંધાઈ (Received)"
                    elif st in ("DIAGNOSING", "ESTIMATED"):
                        progress = 50
                        step_label = "૨. લેબ ડાયગ્નોસ્ટિક્સ & ચેકિંગ (Diagnosing)"
                    elif st in ("IN_PROGRESS", "WAITING_PARTS"):
                        progress = 75
                        step_label = "૩. ચિપલેવલ રિપેરિંગ ચાલુ (Under Repair)"
                    elif st in ("REPAIRED", "READY"):
                        progress = 90
                        step_label = "૪. મશીન ટેસ્ટ થઈ ગયું (Ready for Pickup)"
                    elif st == "DELIVERED":
                        progress = 100
                        step_label = "૫. ગ્રાહકને સુપરત કરેલ (Delivered)"
                    else:
                        progress = 20
                        step_label = st

                    t_dict["progress"] = progress
                    t_dict["step_label"] = step_label
                    tickets_list.append(t_dict)

                return self.send_json({
                    "customer": cust_profile,
                    "invoices": invoices_list,
                    "devices": devices_list,
                    "tickets": tickets_list,
                    "stats": {
                        "total_invoices": len(invoices_list),
                        "total_devices": len(devices_list),
                        "active_warranties": len([d for d in devices_list if d["is_active_warranty"]]),
                        "total_tickets": len(tickets_list)
                    }
                })

            # Backup & Restore Endpoints
            if path == "/api/backups":
                return self.send_json(get_backups_metadata())

            if path == "/api/backups/download-latest":
                if not os.path.exists(DB_PATH):
                    return self.send_json({"error": "Database file not found"}, 404)
                now_str = datetime.now().strftime("%Y-%m-%d_%H%M%S")
                dl_name = f"hardware_erp_live_{now_str}.db"
                self.send_response(200)
                self.send_header("Content-Type", "application/octet-stream")
                self.send_header("Content-Disposition", f'attachment; filename="{dl_name}"')
                self.send_header("Content-Length", str(os.path.getsize(DB_PATH)))
                self.end_headers()
                with open(DB_PATH, "rb") as f:
                    self.wfile.write(f.read())
                return

            if path == "/api/backups/download":
                filename = query.get("file", [None])[0]
                if not filename or os.path.basename(filename) != filename or not filename.endswith(".db"):
                    return self.send_json({"error": "Invalid backup filename"}, 400)
                file_path = os.path.join(BACKUPS_DIR, filename)
                if not os.path.exists(file_path):
                    return self.send_json({"error": "Backup file not found"}, 404)
                self.send_response(200)
                self.send_header("Content-Type", "application/octet-stream")
                self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
                self.send_header("Content-Length", str(os.path.getsize(file_path)))
                self.end_headers()
                with open(file_path, "rb") as f:
                    self.wfile.write(f.read())
                return

            # Staff & Admin Auth Check
            if path == "/api/auth/me":
                auth_header = self.headers.get("Authorization", "")
                token = None
                if auth_header.startswith("Bearer "):
                    token = auth_header[7:].strip()
                if not token:
                    token = query.get("token", [None])[0]
                if not token:
                    return self.send_json({"authenticated": False, "error": "No session token"}, 401)
                
                sess = cursor.execute("""
                    SELECT s.*, m.name, m.role, m.department, m.phone, m.email, m.username, m.permissions, m.status
                    FROM staff_sessions s
                    JOIN staff_members m ON s.staff_id = m.id
                    WHERE s.token = ? AND m.status = 'ACTIVE'
                """, (token,)).fetchone()
                
                if not sess:
                    return self.send_json({"authenticated": False, "error": "Invalid or expired session"}, 401)
                
                perms = ["*"]
                if sess["permissions"]:
                    try:
                        perms = json.loads(sess["permissions"])
                    except Exception:
                        perms = ["*"]
                        
                return self.send_json({
                    "authenticated": True,
                    "user": {
                        "id": sess["staff_id"],
                        "name": sess["name"],
                        "role": sess["role"],
                        "department": sess["department"],
                        "phone": sess["phone"],
                        "email": sess["email"],
                        "username": sess["username"],
                        "permissions": perms
                    }
                })

            return self.send_json({"error": "API route not found"}, 404)

        finally:
            conn.close()

    def handle_api_post(self, path):
        conn = get_db()
        cursor = conn.cursor()
        body = self.read_json_body()

        try:
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # 1. Create Job Sheet
            if path == "/api/jobsheets":
                year = datetime.now().year
                count_row = cursor.execute("SELECT COUNT(*) FROM job_sheets").fetchone()[0]
                job_number = f"JS-{year}-{1001 + count_row}"

                cursor.execute("""
                INSERT INTO job_sheets (
                    job_sheet_number, customer_name, customer_phone, customer_email, customer_address,
                    device_type, device_brand, device_model, device_serial, accessories_received,
                    physical_condition, reported_problem, technician_notes, status,
                    estimated_cost, final_cost, advance_paid, assigned_technician, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    job_number,
                    body.get("customer_name", "").strip(),
                    body.get("customer_phone", "").strip(),
                    body.get("customer_email", "").strip(),
                    body.get("customer_address", "").strip(),
                    body.get("device_type", "Laptop"),
                    body.get("device_brand", ""),
                    body.get("device_model", ""),
                    body.get("device_serial", ""),
                    body.get("accessories_received", "None"),
                    body.get("physical_condition", "Good"),
                    body.get("reported_problem", ""),
                    body.get("technician_notes", ""),
                    body.get("status", "RECEIVED"),
                    float(body.get("estimated_cost", 0)),
                    float(body.get("final_cost", 0)),
                    float(body.get("advance_paid", 0)),
                    body.get("assigned_technician", "Unassigned"),
                    now_str,
                    now_str
                ))
                new_id = cursor.lastrowid

                cursor.execute("""
                INSERT INTO job_sheet_logs (job_sheet_id, status, note, created_at)
                VALUES (?, ?, ?, ?)
                """, (new_id, body.get("status", "RECEIVED"), f"Job Sheet created. Problem: {body.get('reported_problem', '')}", now_str))

                conn.commit()
                return self.send_json({"success": True, "id": new_id, "job_sheet_number": job_number}, 201)

            # 0. Multi-Image Upload API
            if path == "/api/upload":
                upload_dir = os.path.join(STATIC_DIR, "uploads")
                os.makedirs(upload_dir, exist_ok=True)
                urls = []

                images_payload = body.get("images", [])
                if not images_payload and body.get("image"):
                    images_payload = [{"name": body.get("filename", "upload.jpg"), "data": body.get("image")}]

                for item in images_payload:
                    data_uri = item.get("data", "")
                    raw_name = item.get("name", "photo.jpg")
                    safe_name = re.sub(r'[^a-zA-Z0-9_\.-]', '_', raw_name)
                    unique_filename = f"img_{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:6]}_{safe_name}"
                    file_path = os.path.join(upload_dir, unique_filename)

                    if "," in data_uri:
                        base64_data = data_uri.split(",", 1)[1]
                    else:
                        base64_data = data_uri

                    try:
                        with open(file_path, "wb") as f_img:
                            f_img.write(base64.b64decode(base64_data))
                        urls.append(f"/static/uploads/{unique_filename}")
                    except Exception as e:
                        print(f"Error saving uploaded image: {e}")

                return self.send_json({"success": True, "urls": urls}, 201)

            # 0.1 Validate Referral Code (Checkout)
            if path == "/api/referral/validate":
                code_input = (body.get("code") or "").strip().upper()
                cart_total = float(body.get("cart_total") or 0.0)
                cust_phone = (body.get("customer_phone") or "").strip()

                if not code_input:
                    return self.send_json({"valid": False, "error": "કૃપા કરીને રેફરલ કોડ દાખલ કરો (Please enter code)."}, 400)

                rule_row = cursor.execute("SELECT * FROM referral_rules WHERE is_active = 1 ORDER BY id DESC LIMIT 1").fetchone()
                min_order = rule_row["min_order_val"] if rule_row else 500.0

                if cart_total < min_order:
                    return self.send_json({
                        "valid": False, 
                        "error": f"રેફરલ કોડ વાપરવા માટે ન્યૂનતમ ઓર્ડર રકમ ₹{min_order:,.0f} હોવી જરૂરી છે (Min order ₹{min_order:,.0f})."
                    }, 400)

                ref = cursor.execute("SELECT * FROM referral_codes WHERE UPPER(code) = ?", (code_input,)).fetchone()
                if not ref:
                    return self.send_json({"valid": False, "error": "અમાન્ય રેફરલ કોડ (Invalid referral code)."}, 404)

                if ref["status"] != "ACTIVE":
                    return self.send_json({"valid": False, "error": "આ રેફરલ કોડ હાલમાં બંધ છે (Code is not active)."}, 400)

                if cust_phone and ref["owner_phone"] and cust_phone == ref["owner_phone"]:
                    return self.send_json({
                        "valid": False, 
                        "error": "તમે તમારો પોતાનો જ રેફરલ કોડ વાપરી શકતા નથી (You cannot use your own referral code)."
                    }, 400)

                if ref["max_uses"] > 0 and ref["usage_count"] >= ref["max_uses"]:
                    return self.send_json({"valid": False, "error": "આ રેફરલ કોડની મહત્તમ લિમિટ પૂરી થઈ ગઈ છે (Code limit reached)."}, 400)

                discount_val = float(ref["discount_amount"] or 100.0)
                return self.send_json({
                    "valid": True,
                    "code": ref["code"],
                    "discount_amount": discount_val,
                    "reward_points": ref["reward_points"],
                    "owner_name": ref["owner_name"],
                    "message": f"સફળ! ₹{discount_val:,.0f} ડિસ્કાઉન્ટ એપ્લાય થઈ ગયું છે."
                })

            # 0.2 Save Referral Rules (Admin)
            if path == "/api/referral/rules":
                cursor.execute("""INSERT INTO referral_rules (rule_name, referrer_points, referee_discount, point_to_inr, min_order_val, terms_text, is_active) VALUES (?, ?, ?, ?, ?, ?, 1)""", (
                    body.get("rule_name", "Custom Referral Program"),
                    int(body.get("referrer_points", 200)),
                    float(body.get("referee_discount", 100.0)),
                    float(body.get("point_to_inr", 1.0)),
                    float(body.get("min_order_val", 500.0)),
                    body.get("terms_text", "")
                ))
                conn.commit()
                return self.send_json({"success": True})

            # 0.3 Create New Referral Code (Admin)
            if path == "/api/referral/codes":
                new_code = (body.get("code") or f"PCW{int(datetime.now().timestamp())%100000}").strip().upper()
                cursor.execute("""INSERT INTO referral_codes (code, owner_name, owner_phone, reward_points, discount_amount, usage_count, max_uses, status, notes) VALUES (?, ?, ?, ?, ?, 0, ?, ?, ?)""", (
                    new_code,
                    body.get("owner_name", "PCWARE Partner").strip(),
                    body.get("owner_phone", "").strip(),
                    int(body.get("reward_points", 200)),
                    float(body.get("discount_amount", 100.0)),
                    int(body.get("max_uses", 0)),
                    body.get("status", "ACTIVE"),
                    body.get("notes", "Created via Admin Portal")
                ))
                conn.commit()
                return self.send_json({"success": True, "code": new_code}, 201)

            # 2. Create Product
            if path == "/api/products":
                cursor.execute("""
                INSERT INTO products (
                    sku, name, category, brand, model, hsn_code, cost_price,
                    selling_price, gst_rate, stock_quantity, low_stock_threshold, specs, wattage, image_url, gallery_images, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    body.get("sku", f"SKU-{int(datetime.now().timestamp())}"),
                    body.get("name", "").strip(),
                    body.get("category", "peripheral"),
                    body.get("brand", "").strip(),
                    body.get("model", "").strip(),
                    body.get("hsn_code", "8471"),
                    float(body.get("cost_price", 0)),
                    float(body.get("selling_price", 0)),
                    float(body.get("gst_rate", 18.0)),
                    int(body.get("stock_quantity", 0)),
                    int(body.get("low_stock_threshold", 2)),
                    body.get("specs", ""),
                    int(body.get("wattage", 0)),
                    body.get("image_url", "https://images.unsplash.com/photo-1591799264318-7e6ef8ddb7ea?w=400"),
                    now_str
                ))
                new_id = cursor.lastrowid
                conn.commit()
                return self.send_json({"success": True, "id": new_id}, 201)

            # 3. Create Serial Number
            if path == "/api/serials":
                cursor.execute("""
                INSERT INTO serial_numbers (
                    product_id, serial_number, supplier_name, purchase_date,
                    warranty_months, status, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    body.get("product_id"),
                    body.get("serial_number", "").strip(),
                    body.get("supplier_name", "").strip(),
                    body.get("purchase_date", datetime.now().strftime("%Y-%m-%d")),
                    int(body.get("warranty_months", 36)),
                    body.get("status", "IN_STOCK"),
                    body.get("notes", "")
                ))
                new_id = cursor.lastrowid
                if body.get("product_id"):
                    cursor.execute("UPDATE products SET stock_quantity = stock_quantity + 1 WHERE id = ?", (body.get("product_id"),))
                conn.commit()
                return self.send_json({"success": True, "id": new_id}, 201)

            # 4. Create GST Invoice
            if path == "/api/invoices":
                year = datetime.now().year
                count_inv = cursor.execute("SELECT COUNT(*) FROM invoices").fetchone()[0]
                invoice_number = f"INV-{year}-{1001 + count_inv}"

                subtotal = float(body.get("subtotal", 0))
                cgst = float(body.get("cgst", 0))
                sgst = float(body.get("sgst", 0))
                igst = float(body.get("igst", 0))
                discount = float(body.get("discount", 0))
                grand_total = float(body.get("grand_total", 0))

                cursor.execute("""
                INSERT INTO invoices (
                    invoice_number, customer_name, customer_phone, customer_email,
                    customer_address, customer_gstin, invoice_date, subtotal,
                    cgst, sgst, igst, discount, grand_total, payment_method,
                    payment_status, notes, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    invoice_number,
                    body.get("customer_name", "").strip(),
                    body.get("customer_phone", "").strip(),
                    body.get("customer_email", "").strip(),
                    body.get("customer_address", "").strip(),
                    body.get("customer_gstin", "").strip(),
                    body.get("invoice_date", datetime.now().strftime("%Y-%m-%d")),
                    subtotal, cgst, sgst, igst, discount, grand_total,
                    body.get("payment_method", "CASH"),
                    body.get("payment_status", "PAID"),
                    body.get("notes", ""),
                    now_str
                ))
                inv_id = cursor.lastrowid

                items = body.get("items", [])
                for item in items:
                    p_id = item.get("product_id")
                    qty = int(item.get("quantity", 1))
                    unit_p = float(item.get("unit_price", 0))
                    item_tot = float(item.get("total", qty * unit_p))
                    sn = item.get("serial_number", "").strip()

                    cursor.execute("""
                    INSERT INTO invoice_items (
                        invoice_id, product_id, item_name, hsn_code, serial_number, quantity, unit_price, gst_rate, total
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        inv_id, p_id, item.get("item_name", ""), item.get("hsn_code", "8471"),
                        sn, qty, unit_p, float(item.get("gst_rate", 18.0)), item_tot
                    ))

                    if p_id:
                        cursor.execute("UPDATE products SET stock_quantity = MAX(0, stock_quantity - ?) WHERE id = ?", (qty, p_id))

                    if sn:
                        cursor.execute("""
                        UPDATE serial_numbers SET
                            status = 'SOLD',
                            customer_name = ?,
                            customer_phone = ?,
                            invoice_number = ?,
                            sold_date = ?
                        WHERE serial_number = ?
                        """, (body.get("customer_name"), body.get("customer_phone"), invoice_number, datetime.now().strftime("%Y-%m-%d"), sn))

                conn.commit()
                return self.send_json({"success": True, "id": inv_id, "invoice_number": invoice_number}, 201)

            # 5. Create AMC Contract
            if path == "/api/amc":
                count_amc = cursor.execute("SELECT COUNT(*) FROM amc_contracts").fetchone()[0]
                contract_number = f"AMC-{datetime.now().year}-{101 + count_amc}"

                cursor.execute("""
                INSERT INTO amc_contracts (
                    contract_number, client_name, contact_person, phone, email,
                    address, total_systems, contract_value, start_date, end_date,
                    visit_frequency, status, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    contract_number,
                    body.get("client_name", "").strip(),
                    body.get("contact_person", "").strip(),
                    body.get("phone", "").strip(),
                    body.get("email", "").strip(),
                    body.get("address", "").strip(),
                    int(body.get("total_systems", 1)),
                    float(body.get("contract_value", 0)),
                    body.get("start_date", datetime.now().strftime("%Y-%m-%d")),
                    body.get("end_date", ""),
                    body.get("visit_frequency", "MONTHLY"),
                    body.get("status", "ACTIVE"),
                    body.get("notes", "")
                ))
                new_id = cursor.lastrowid
                conn.commit()
                return self.send_json({"success": True, "id": new_id, "contract_number": contract_number}, 201)

            # 6. Web Store Checkout (Orders)
            if path == "/api/orders":
                order_num = f"ORD-{int(datetime.now().timestamp())}"
                cursor.execute("""
                INSERT INTO orders (
                    order_number, customer_name, customer_phone, customer_email,
                    customer_address, order_type, items_json, total_amount, status, payment_method, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    order_num,
                    body.get("customer_name", "").strip(),
                    body.get("customer_phone", "").strip(),
                    body.get("customer_email", "").strip(),
                    body.get("customer_address", "").strip(),
                    body.get("order_type", "HARDWARE"),
                    json.dumps(body.get("items", [])),
                    float(body.get("total_amount", 0)),
                    "CONFIRMED",
                    body.get("payment_method", "COD"),
                    now_str
                ))
                new_id = cursor.lastrowid

                # REFERRAL REWARD & REDEMPTION ENGINE
                referral_code_used = (body.get("referral_code") or "").strip().upper()
                cust_phone = (body.get("customer_phone") or "").strip()
                cust_name = (body.get("customer_name") or "Valued Customer").strip()
                points_redeemed = int(body.get("points_redeemed") or 0)

                # A. Process Referral Code Bonus to Referrer
                if referral_code_used:
                    ref_match = cursor.execute("SELECT * FROM referral_codes WHERE UPPER(code) = ? AND status = 'ACTIVE'", (referral_code_used,)).fetchone()
                    if ref_match:
                        cursor.execute("UPDATE referral_codes SET usage_count = usage_count + 1 WHERE id = ?", (ref_match["id"],))
                        ref_phone = ref_match["owner_phone"]
                        if ref_phone and ref_phone != cust_phone:
                            reward_pts = int(ref_match["reward_points"] or 200)
                            cursor.execute("""INSERT INTO reward_transactions (customer_phone, customer_name, points, transaction_type, order_id, referral_code, referred_customer_phone, description) VALUES (?, ?, ?, 'REFERRAL_BONUS', ?, ?, ?, ?)""", (
                                ref_phone,
                                ref_match["owner_name"],
                                reward_pts,
                                new_id,
                                referral_code_used,
                                cust_phone,
                                f"Referral reward for order {order_num} by {cust_name}"
                            ))

                # B. Process Reward Points Redemption by Customer
                if points_redeemed > 0 and cust_phone:
                    cursor.execute("""INSERT INTO reward_transactions (customer_phone, customer_name, points, transaction_type, order_id, referral_code, description) VALUES (?, ?, ?, 'REDEEMED_DISCOUNT', ?, ?, ?)""", (
                        cust_phone,
                        cust_name,
                        -points_redeemed,
                        new_id,
                        referral_code_used,
                        f"Points redeemed for instant discount on order {order_num}"
                    ))

                for item in body.get("items", []):
                    if item.get("id"):
                        cursor.execute("UPDATE products SET stock_quantity = MAX(0, stock_quantity - ?) WHERE id = ?", (int(item.get("qty", 1)), item["id"]))

                conn.commit()
                return self.send_json({"success": True, "order_number": order_num, "id": new_id}, 201)

            # 7. Online Service / Repair Booking from Website
            if path == "/api/service-booking":
                year = datetime.now().year
                count_row = cursor.execute("SELECT COUNT(*) FROM job_sheets").fetchone()[0]
                job_number = f"JS-{year}-{1001 + count_row}"

                cursor.execute("""
                INSERT INTO job_sheets (
                    job_sheet_number, customer_name, customer_phone, customer_email, customer_address,
                    device_type, device_brand, device_model, device_serial, accessories_received,
                    physical_condition, reported_problem, status, estimated_cost, advance_paid,
                    assigned_technician, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    job_number,
                    body.get("name", "").strip(),
                    body.get("phone", "").strip(),
                    body.get("email", "").strip(),
                    body.get("address", "").strip(),
                    body.get("device_type", "Laptop"),
                    body.get("brand", "Unknown"),
                    body.get("model", "N/A"),
                    "",
                    "Store / Pickup Booking",
                    "Awaiting Physical Check",
                    body.get("problem", "").strip(),
                    "RECEIVED",
                    0,
                    0,
                    "Triage Queue",
                    now_str,
                    now_str
                ))
                new_id = cursor.lastrowid
                cursor.execute("""
                INSERT INTO job_sheet_logs (job_sheet_id, status, note, created_at)
                VALUES (?, ?, ?, ?)
                """, (new_id, "RECEIVED", f"Online Service Booking submitted by customer. Problem: {body.get('problem')}", now_str))

                conn.commit()
                return self.send_json({"success": True, "job_sheet_number": job_number, "id": new_id}, 201)

            # 8. Update Store Settings
            if path == "/api/store-settings":
                for k, v in body.items():
                    cursor.execute("INSERT OR REPLACE INTO store_settings (key, value) VALUES (?, ?)", (k, str(v)))
                conn.commit()
                return self.send_json({"success": True})

            # 9. Create Inquiry
            if path == "/api/inquiries":
                count = cursor.execute("SELECT COUNT(*) FROM inquiries").fetchone()[0]
                inq_num = f"INQ-2026-{101 + count}"
                cursor.execute("""
                INSERT INTO inquiries (inquiry_number, customer_name, customer_phone, customer_email, customer_address, requirement_type, items_requested, estimated_budget, status, source, notes, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    inq_num,
                    body.get("customer_name", "").strip(),
                    body.get("customer_phone", "").strip(),
                    body.get("customer_email", "").strip(),
                    body.get("customer_address", "").strip(),
                    body.get("requirement_type", "Hardware Sales"),
                    body.get("items_requested", ""),
                    float(body.get("estimated_budget", 0)),
                    body.get("status", "NEW"),
                    body.get("source", "Walk-in"),
                    body.get("notes", ""),
                    now_str
                ))
                new_id = cursor.lastrowid
                conn.commit()
                return self.send_json({"success": True, "id": new_id, "inquiry_number": inq_num}, 201)

            # 10. Create Quotation
            if path == "/api/quotations":
                count = cursor.execute("SELECT COUNT(*) FROM quotations").fetchone()[0]
                qt_num = f"QT-2026-{501 + count}"
                items_json = json.dumps(body.get("items", [])) if isinstance(body.get("items"), list) else body.get("items_json", "[]")
                subtotal = float(body.get("subtotal", 0))
                gst_amount = float(body.get("gst_amount", 0))
                grand_total = float(body.get("grand_total", subtotal + gst_amount))
                inq_id = body.get("inquiry_id")

                cursor.execute("""
                INSERT INTO quotations (quotation_number, inquiry_id, customer_name, customer_phone, customer_email, customer_address, customer_gstin, items_json, subtotal, gst_amount, grand_total, valid_until, status, notes, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    qt_num,
                    inq_id,
                    body.get("customer_name", "").strip(),
                    body.get("customer_phone", "").strip(),
                    body.get("customer_email", "").strip(),
                    body.get("customer_address", "").strip(),
                    body.get("customer_gstin", "").strip(),
                    items_json,
                    subtotal,
                    gst_amount,
                    grand_total,
                    body.get("valid_until", (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")),
                    "SENT",
                    body.get("notes", ""),
                    now_str
                ))
                new_id = cursor.lastrowid
                if inq_id:
                    cursor.execute("UPDATE inquiries SET status = 'QUOTED' WHERE id = ?", (inq_id,))
                conn.commit()
                return self.send_json({"success": True, "id": new_id, "quotation_number": qt_num}, 201)

            # 11. Convert Quotation to Order
            if path.startswith("/api/quotations/") and path.endswith("/convert-order"):
                qt_id = path.split("/")[3]
                qt = cursor.execute("SELECT * FROM quotations WHERE id = ?", (qt_id,)).fetchone()
                if not qt:
                    return self.send_json({"error": "Quotation not found"}, 404)

                order_count = cursor.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
                ord_num = f"ORD-2026-{1001 + order_count}"

                cursor.execute("""
                INSERT INTO orders (order_number, customer_name, customer_phone, customer_email, customer_address, order_type, items_json, total_amount, status, payment_method, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    ord_num,
                    qt["customer_name"],
                    qt["customer_phone"],
                    qt["customer_email"],
                    qt["customer_address"],
                    "HARDWARE",
                    qt["items_json"],
                    qt["grand_total"],
                    "CONFIRMED",
                    body.get("payment_method", "COD"),
                    now_str
                ))
                ord_id = cursor.lastrowid
                cursor.execute("UPDATE quotations SET status = 'CONVERTED' WHERE id = ?", (qt_id,))
                if qt["inquiry_id"]:
                    cursor.execute("UPDATE inquiries SET status = 'ORDER_CONFIRMED' WHERE id = ?", (qt["inquiry_id"],))
                conn.commit()
                return self.send_json({"success": True, "order_id": ord_id, "order_number": ord_num}, 201)

            # 12. Fulfill Order -> Generate Invoice + Deduct Stock + Debit Customer Ledger
            if path.startswith("/api/orders/") and path.endswith("/fulfill"):
                ord_id = path.split("/")[3]
                order = cursor.execute("SELECT * FROM orders WHERE id = ?", (ord_id,)).fetchone()
                if not order:
                    return self.send_json({"error": "Order not found"}, 404)

                inv_count = cursor.execute("SELECT COUNT(*) FROM invoices").fetchone()[0]
                inv_num = f"INV-2026-0{101 + inv_count}"
                items = json.loads(order["items_json"]) if order["items_json"] else []

                subtotal = 0.0
                for it in items:
                    p_id = it.get("product_id") or it.get("id")
                    qty = int(it.get("quantity") or it.get("qty") or 1)
                    unit_price = float(it.get("unit_price") or it.get("price") or 0)
                    subtotal += (unit_price * qty)
                    if p_id:
                        cursor.execute("UPDATE products SET stock_quantity = MAX(0, stock_quantity - ?) WHERE id = ?", (qty, p_id))

                cgst = round(subtotal * 0.09, 2)
                sgst = round(subtotal * 0.09, 2)
                grand_total = round(subtotal + cgst + sgst, 2)

                cursor.execute("""
                INSERT INTO invoices (invoice_number, customer_name, customer_phone, customer_email, customer_address, customer_gstin, invoice_date, subtotal, cgst, sgst, igst, discount, grand_total, payment_method, payment_status, notes, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    inv_num,
                    order["customer_name"],
                    order["customer_phone"],
                    order["customer_email"],
                    order["customer_address"],
                    "",
                    datetime.now().strftime("%Y-%m-%d"),
                    subtotal,
                    cgst,
                    sgst,
                    0,
                    0,
                    grand_total,
                    order["payment_method"],
                    "PAID" if order["payment_method"] != "COD" else "UNPAID",
                    f"Generated from Order {order['order_number']}",
                    now_str
                ))
                inv_id = cursor.lastrowid

                for it in items:
                    p_id = it.get("product_id") or it.get("id")
                    qty = int(it.get("quantity") or it.get("qty") or 1)
                    unit_price = float(it.get("unit_price") or it.get("price") or 0)
                    cursor.execute("""
                    INSERT INTO invoice_items (invoice_id, product_id, item_name, hsn_code, quantity, unit_price, gst_rate, total)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (inv_id, p_id, it.get("name", "Hardware Item"), "8471", qty, unit_price, 18.0, unit_price * qty))

                # Update party ledger (Debit customer)
                party = cursor.execute("SELECT * FROM parties WHERE party_type = 'CUSTOMER' AND (phone = ? OR name = ?)", (order["customer_phone"], order["customer_name"])).fetchone()
                if party:
                    new_bal = party["current_balance"] + grand_total
                    cursor.execute("UPDATE parties SET current_balance = ? WHERE id = ?", (new_bal, party["id"]))
                    cursor.execute("""
                    INSERT INTO ledger_entries (party_id, party_type, entry_date, voucher_type, voucher_no, narration, debit, credit, running_balance, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (party["id"], "CUSTOMER", datetime.now().strftime("%Y-%m-%d"), "SALES_INVOICE", inv_num, f"Sales Invoice generated for Order {order['order_number']}", grand_total, 0.0, new_bal, now_str))

                cursor.execute("UPDATE orders SET status = 'DELIVERED' WHERE id = ?", (ord_id,))
                conn.commit()
                return self.send_json({"success": True, "invoice_id": inv_id, "invoice_number": inv_num})

            # 13. Create Purchase Order
            if path == "/api/purchase-orders":
                po_count = cursor.execute("SELECT COUNT(*) FROM purchase_orders").fetchone()[0]
                po_num = f"PO-2026-{801 + po_count}"
                items_json = json.dumps(body.get("items", [])) if isinstance(body.get("items"), list) else body.get("items_json", "[]")
                subtotal = float(body.get("subtotal", 0))
                gst_amount = float(body.get("gst_amount", 0))
                total_amount = float(body.get("total_amount", subtotal + gst_amount))

                cursor.execute("""
                INSERT INTO purchase_orders (po_number, supplier_id, supplier_name, supplier_phone, supplier_gstin, order_date, expected_date, items_json, subtotal, gst_amount, total_amount, status, payment_status, notes, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    po_num,
                    body.get("supplier_id"),
                    body.get("supplier_name", "").strip(),
                    body.get("supplier_phone", "").strip(),
                    body.get("supplier_gstin", "").strip(),
                    body.get("order_date", datetime.now().strftime("%Y-%m-%d")),
                    body.get("expected_date", (datetime.now() + timedelta(days=4)).strftime("%Y-%m-%d")),
                    items_json,
                    subtotal,
                    gst_amount,
                    total_amount,
                    "ORDERED",
                    body.get("payment_status", "UNPAID"),
                    body.get("notes", ""),
                    now_str
                ))
                new_id = cursor.lastrowid
                conn.commit()
                return self.send_json({"success": True, "id": new_id, "po_number": po_num}, 201)

            # 14. Inward PO (Receive Goods -> Stock Increase + Credit Supplier Ledger)
            if path.startswith("/api/purchase-orders/") and path.endswith("/inward"):
                po_id = path.split("/")[3]
                po = cursor.execute("SELECT * FROM purchase_orders WHERE id = ?", (po_id,)).fetchone()
                if not po:
                    return self.send_json({"error": "Purchase Order not found"}, 404)

                items = json.loads(po["items_json"]) if po["items_json"] else []
                for it in items:
                    p_id = it.get("product_id") or it.get("id")
                    qty = int(it.get("quantity") or it.get("qty") or 1)
                    if p_id:
                        cursor.execute("UPDATE products SET stock_quantity = stock_quantity + ? WHERE id = ?", (qty, p_id))

                supplier = None
                if po["supplier_id"]:
                    supplier = cursor.execute("SELECT * FROM parties WHERE id = ?", (po["supplier_id"],)).fetchone()
                if not supplier and po["supplier_name"]:
                    supplier = cursor.execute("SELECT * FROM parties WHERE party_type = 'SUPPLIER' AND name = ?", (po["supplier_name"],)).fetchone()

                if supplier:
                    new_bal = supplier["current_balance"] + po["total_amount"]
                    cursor.execute("UPDATE parties SET current_balance = ? WHERE id = ?", (new_bal, supplier["id"]))
                    cursor.execute("""
                    INSERT INTO ledger_entries (party_id, party_type, entry_date, voucher_type, voucher_no, narration, debit, credit, running_balance, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (supplier["id"], "SUPPLIER", datetime.now().strftime("%Y-%m-%d"), "PURCHASE_BILL", po["po_number"], f"Inward GRN received against PO {po['po_number']}", 0.0, po["total_amount"], new_bal, now_str))

                cursor.execute("UPDATE purchase_orders SET status = 'RECEIVED' WHERE id = ?", (po_id,))
                conn.commit()
                return self.send_json({"success": True, "status": "RECEIVED"})

            # 15. Create Party (Customer or Supplier)
            if path == "/api/parties":
                cursor.execute("""
                INSERT INTO parties (party_type, name, contact_person, phone, email, address, gstin, opening_balance, current_balance, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    body.get("party_type", "CUSTOMER"),
                    body.get("name", "").strip(),
                    body.get("contact_person", "").strip(),
                    body.get("phone", "").strip(),
                    body.get("email", "").strip(),
                    body.get("address", "").strip(),
                    body.get("gstin", "").strip(),
                    float(body.get("opening_balance", 0)),
                    float(body.get("opening_balance", 0)),
                    now_str
                ))
                p_id = cursor.lastrowid
                conn.commit()
                return self.send_json({"success": True, "id": p_id}, 201)

            # 16. Record Payment Transaction (Customer Receipt or Supplier Payment)
            if path == "/api/ledger-transactions":
                party_id = body.get("party_id")
                party = cursor.execute("SELECT * FROM parties WHERE id = ?", (party_id,)).fetchone()
                if not party:
                    return self.send_json({"error": "Party not found"}, 404)

                amount = float(body.get("amount", 0))
                v_type = "PAYMENT_RECEIVED" if party["party_type"] == "CUSTOMER" else "PAYMENT_MADE"
                voucher_prefix = "PAY-REC" if party["party_type"] == "CUSTOMER" else "PAY-SUP"
                tx_count = cursor.execute("SELECT COUNT(*) FROM ledger_entries WHERE voucher_type = ?", (v_type,)).fetchone()[0]
                voucher_no = f"{voucher_prefix}-{101 + tx_count}"
                narration = body.get("narration") or f"Payment of ₹{amount:,.2f} via {body.get('payment_mode', 'UPI')}"

                if party["party_type"] == "CUSTOMER":
                    debit = 0.0
                    credit = amount
                    new_balance = party["current_balance"] - amount
                else:
                    debit = amount
                    credit = 0.0
                    new_balance = party["current_balance"] - amount

                cursor.execute("UPDATE parties SET current_balance = ? WHERE id = ?", (new_balance, party_id))
                cursor.execute("""
                INSERT INTO ledger_entries (party_id, party_type, entry_date, voucher_type, voucher_no, narration, debit, credit, running_balance, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    party_id,
                    party["party_type"],
                    body.get("date", datetime.now().strftime("%Y-%m-%d")),
                    v_type,
                    voucher_no,
                    narration,
                    debit,
                    credit,
                    new_balance,
                    now_str
                ))
                conn.commit()
                return self.send_json({"success": True, "voucher_no": voucher_no, "new_balance": new_balance}, 201)

            
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
                return self.send_json({"success": True, "id": cursor.lastrowid}, 201)

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
                return self.send_json({"success": True, "transfer_no": trf_no}, 201)

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
                wa_text = f"Hello PCWARE! I would like to book/inquire:\n\n" \
                          f"📋 *Inquiry No:* {inq_no}\n" \
                          f"💻 *Item:* {items_requested}\n" \
                          f"💰 *Budget/Price:* ₹{budget:,.2f}\n" \
                          f"🚚 *Fulfillment:* {mode_str}\n" \
                          f"👤 *Customer:* {cust_name}\n" \
                          f"📞 *Mobile:* {cust_phone}\n" \
                          f"📍 *City/Address:* {cust_address or 'Rajkot'}\n"
                if custom_specs:
                    wa_text += f"⚙️ *Specs/Upgrades:* {custom_specs}\n"
                wa_text += "\nPlease confirm availability and share next steps. Thank you!"

                ceo_phone = "9426183934"
                encoded_msg = urllib.parse.quote(wa_text)
                whatsapp_url = f"https://wa.me/91{ceo_phone}?text={encoded_msg}"

                return self.send_json({
                    "success": True,
                    "inquiry_number": inq_no,
                    "assigned_staff": assigned_staff_name,
                    "whatsapp_url": whatsapp_url,
                    "message": wa_text
                }, 201)

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

            
            # 18. Customer Portal Login
            if path == "/api/customer/login":
                phone = str(body.get("phone", "")).strip()
                clean_phone = "".join(ch for ch in phone if ch.isdigit())
                if len(clean_phone) < 10:
                    return self.send_json({"error": "માન્ય ૧૦ આંકડાનો મોબાઇલ નંબર દાખલ કરો"}, 400)
                phone = clean_phone[-10:]

                # Check name from DB
                party = cursor.execute("SELECT * FROM parties WHERE phone LIKE ?", (f"%{phone}%",)).fetchone()
                cust_name = party["name"] if party else None

                if not cust_name:
                    inv = cursor.execute("SELECT customer_name FROM invoices WHERE customer_phone LIKE ? LIMIT 1", (f"%{phone}%",)).fetchone()
                    if inv:
                        cust_name = inv["customer_name"]

                if not cust_name:
                    sn = cursor.execute("SELECT customer_name FROM serial_numbers WHERE customer_phone LIKE ? LIMIT 1", (f"%{phone}%",)).fetchone()
                    if sn and sn["customer_name"]:
                        cust_name = sn["customer_name"]

                if not cust_name:
                    cust_name = body.get("name") or f"Customer ({phone})"
                    cursor.execute("""
                    INSERT INTO parties (party_type, name, contact_person, phone, email, address, opening_balance, current_balance, created_at)
                    VALUES ('CUSTOMER', ?, ?, ?, '', 'Rajkot', 0, 0, ?)
                    """, (cust_name, cust_name, phone, now_str))
                    conn.commit()

                return self.send_json({
                    "success": True,
                    "customer": {
                        "name": cust_name,
                        "phone": phone,
                        "email": party["email"] if party else "",
                        "address": party["address"] if party else "Rajkot"
                    }
                })

            # 19. Customer Portal: Create Service Ticket
            if path == "/api/customer/tickets":
                cust_name = body.get("customer_name", "Customer")
                cust_phone = body.get("customer_phone", "").strip()
                dev_model = body.get("device_model", "Laptop")
                dev_serial = body.get("device_serial", "")
                category = body.get("problem_category", "Hardware Issue")
                problem_desc = body.get("reported_problem", "").strip()
                cust_address = body.get("customer_address", "Rajkot")

                if not cust_phone or not problem_desc:
                    return self.send_json({"error": "મોબાઇલ નંબર અને સમસ્યાની વિગત જરૂરી છે"}, 400)

                count_js = cursor.execute("SELECT COUNT(*) FROM job_sheets").fetchone()[0]
                ticket_num = f"JS-{datetime.now().year}-{str(count_js + 1001)}"

                cursor.execute("""
                INSERT INTO job_sheets (
                    job_sheet_number, customer_name, customer_phone, customer_address,
                    device_type, device_brand, device_model, device_serial,
                    reported_problem, status, service_tier, service_category,
                    estimated_cost, final_cost, advance_paid, assigned_technician, created_at
                )
                VALUES (?, ?, ?, ?, 'Laptop', 'Customer Device', ?, ?, ?, 'RECEIVED', 'CUSTOMER_PORTAL', 'HARDWARE', 0, 0, 0, 'Jignesh Mehta (Service Lab)', ?)
                """, (ticket_num, cust_name, cust_phone, cust_address, dev_model, dev_serial, f"[{category}] {problem_desc}", now_str))
                new_id = cursor.lastrowid

                cursor.execute("""
                INSERT INTO job_sheet_logs (job_sheet_id, status, note, created_at)
                VALUES (?, 'RECEIVED', 'ઓનલાઇન કસ્ટમર સેલ્ફ-સર્વિસ પોર્ટલ દ્વારા ટિકિટ નોંધાઈ.', ?)
                """, (new_id, now_str))
                conn.commit()

                return self.send_json({
                    "success": True,
                    "ticket_number": ticket_num,
                    "message": "તમારી સર્વિસ ટિકિટ સફળતાપૂર્વક નોંધાઈ ગઈ છે! PCWARE સર્વિસ ટીમ ટૂંક સમયમાં સંપર્ક કરશે."
                }, 201)

            # 20. Customer Portal: Book Laptop Upgrade
            if path == "/api/customer/upgrade-booking":
                cust_name = body.get("customer_name", "Customer")
                cust_phone = body.get("customer_phone", "")
                dev_model = body.get("device_model", "Laptop")
                dev_serial = body.get("device_serial", "")
                selected_ram = body.get("selected_ram", "")
                selected_ssd = body.get("selected_ssd", "")
                selected_av = body.get("selected_av", "")
                selected_amc = body.get("selected_amc", "")
                total_cost = float(body.get("total_cost", 0))

                upgrades_list = []
                if selected_ram: upgrades_list.append(f"• RAM: {selected_ram}")
                if selected_ssd: upgrades_list.append(f"• SSD: {selected_ssd}")
                if selected_av: upgrades_list.append(f"• Antivirus: {selected_av}")
                if selected_amc: upgrades_list.append(f"• Care/AMC: {selected_amc}")
                upgrades_str = "\n".join(upgrades_list)

                count_inq = cursor.execute("SELECT COUNT(*) FROM inquiries").fetchone()[0]
                inq_no = f"INQ-{datetime.now().year}-{str(count_inq + 101)}"

                cursor.execute("""
                INSERT INTO inquiries (
                    inquiry_number, customer_name, customer_phone, requirement_type,
                    items_requested, custom_specs, estimated_budget, status, source,
                    assigned_staff_id, assigned_staff_name, notes, created_at
                )
                VALUES (?, ?, ?, 'LAPTOP_UPGRADE', ?, ?, ?, 'NEW', 'Customer Portal Upgrade', 2, 'Hardik Patel', ?, ?)
                """, (inq_no, cust_name, cust_phone, f"Upgrade for {dev_model} (SN: {dev_serial})", upgrades_str, total_cost, f"Customer requested upgrades for registered device {dev_serial}", now_str))
                conn.commit()

                wa_text = f"Hello PCWARE! I am an existing customer and want to upgrade my laptop:\n\n" \
                          f"👤 *Customer:* {cust_name}\n" \
                          f"📞 *Mobile:* {cust_phone}\n" \
                          f"💻 *Device:* {dev_model}\n" \
                          f"🏷️ *Serial No:* {dev_serial or 'N/A'}\n\n" \
                          f"⚡ *Selected Upgrades:*\n{upgrades_str}\n\n" \
                          f"💰 *Total Upgrade Amount:* ₹{total_cost:,.2f}\n" \
                          f"📋 *Inquiry No:* {inq_no}\n\n" \
                          f"Please confirm availability and schedule my lab upgrade slot. Thank you!"
                ceo_phone = "9426183934"
                whatsapp_url = f"https://wa.me/91{ceo_phone}?text={urllib.parse.quote(wa_text)}"

                return self.send_json({
                    "success": True,
                    "inquiry_number": inq_no,
                    "whatsapp_url": whatsapp_url
                }, 201)

            # Backup & Restore POST Endpoints
            if path == "/api/backups/create":
                filename, err = create_backup_snapshot(prefix="manual")
                if err:
                    return self.send_json({"error": f"Failed to create backup: {err}"}, 500)
                return self.send_json({
                    "success": True,
                    "filename": filename,
                    "message": f"Manual backup {filename} created successfully"
                }, 201)

            if path == "/api/backups/restore":
                filename = body.get("filename")
                if not filename or os.path.basename(filename) != filename or not filename.endswith(".db"):
                    return self.send_json({"error": "Invalid backup filename"}, 400)
                backup_path = os.path.join(BACKUPS_DIR, filename)
                if not os.path.exists(backup_path):
                    return self.send_json({"error": "Target backup file does not exist"}, 404)
                
                # Step 1: Safety checkpoint of live database
                safety_file, err = create_backup_snapshot(prefix="pre_restore_safety")
                if err:
                    return self.send_json({"error": f"Could not create safety snapshot before restore: {err}"}, 500)
                
                # Step 2: Restore from target backup to DB_PATH
                try:
                    src_conn = sqlite3.connect(backup_path)
                    dst_conn = sqlite3.connect(DB_PATH)
                    src_conn.backup(dst_conn)
                    dst_conn.close()
                    src_conn.close()
                except Exception as e:
                    return self.send_json({"error": f"Restore failed: {str(e)}"}, 500)
                
                return self.send_json({
                    "success": True,
                    "filename": filename,
                    "safety_backup": safety_file,
                    "message": f"Database restored successfully from {filename}! Safety checkpoint saved as {safety_file}."
                })

            if path == "/api/backups/upload-restore":
                file_base64 = body.get("file_base64")
                orig_filename = body.get("filename", "uploaded.db")
                if not file_base64:
                    return self.send_json({"error": "No file content received"}, 400)
                
                try:
                    if "," in file_base64:
                        file_base64 = file_base64.split(",", 1)[1]
                    raw_bytes = base64.b64decode(file_base64)
                except Exception:
                    return self.send_json({"error": "Invalid base64 payload"}, 400)
                
                if not raw_bytes.startswith(b"SQLite format 3\x00"):
                    return self.send_json({"error": "Invalid file. The uploaded file is not a valid SQLite database."}, 400)
                
                timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                save_filename = f"uploaded_backup_{timestamp}.db"
                save_path = os.path.join(BACKUPS_DIR, save_filename)
                with open(save_path, "wb") as f:
                    f.write(raw_bytes)
                
                safety_file, err = create_backup_snapshot(prefix="pre_restore_safety")
                
                try:
                    src_conn = sqlite3.connect(save_path)
                    dst_conn = sqlite3.connect(DB_PATH)
                    src_conn.backup(dst_conn)
                    dst_conn.close()
                    src_conn.close()
                except Exception as e:
                    return self.send_json({"error": f"Restore failed: {str(e)}"}, 500)
                
                return self.send_json({
                    "success": True,
                    "filename": save_filename,
                    "safety_backup": safety_file,
                    "message": f"Uploaded database successfully restored! Safety checkpoint saved as {safety_file}."
                })

            # Staff & Admin Login Endpoint
            if path == "/api/auth/staff-login":
                ident = str(body.get("username_or_phone", "")).strip()
                secret = str(body.get("password", "")).strip()
                if not ident or not secret:
                    return self.send_json({"error": "કૃપા કરીને યુઝરનેમ/મોબાઇલ અને પાસવર્ડ/પિન દાખલ કરો."}, 400)
                
                clean_digits = "".join(ch for ch in ident if ch.isdigit())
                phone_query = clean_digits[-10:] if len(clean_digits) >= 10 else None
                
                if phone_query:
                    staff = cursor.execute("""
                        SELECT * FROM staff_members 
                        WHERE (username = ? OR phone LIKE ?) AND status = 'ACTIVE'
                    """, (ident, f"%{phone_query}%")).fetchone()
                else:
                    staff = cursor.execute("""
                        SELECT * FROM staff_members 
                        WHERE (username = ? OR email = ?) AND status = 'ACTIVE'
                    """, (ident, ident)).fetchone()
                    
                if not staff:
                    return self.send_json({"error": "કોઈ સક્રિય સ્ટાફ એકાઉન્ટ મળ્યું નથી. યુઝરનેમ કે મોબાઇલ તપાસો."}, 401)
                    
                db_pwd = staff["password"] or ""
                db_pin = staff["pin"] or "1234"
                
                if secret != db_pwd and secret != db_pin:
                    return self.send_json({"error": "ખોટો પાસવર્ડ અથવા પિન. ફરી પ્રયાસ કરો."}, 401)
                    
                token = "stf_" + uuid.uuid4().hex
                now = datetime.now()
                expires = (now + timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
                now_str = now.strftime("%Y-%m-%d %H:%M:%S")
                
                cursor.execute("""
                    INSERT INTO staff_sessions (token, staff_id, created_at, expires_at)
                    VALUES (?, ?, ?, ?)
                """, (token, staff["id"], now_str, expires))
                
                cursor.execute("UPDATE staff_members SET last_login = ? WHERE id = ?", (now_str, staff["id"]))
                conn.commit()
                
                perms = ["*"]
                if staff["permissions"]:
                    try:
                        perms = json.loads(staff["permissions"])
                    except Exception:
                        perms = ["*"]
                        
                user_data = {
                    "id": staff["id"],
                    "name": staff["name"],
                    "role": staff["role"],
                    "department": staff["department"],
                    "phone": staff["phone"],
                    "email": staff["email"],
                    "username": staff["username"],
                    "permissions": perms
                }
                return self.send_json({
                    "success": True,
                    "token": token,
                    "user": user_data,
                    "message": f"સ્વાગત છે, {staff['name']}!"
                })

            # Staff Logout Endpoint
            if path == "/api/auth/staff-logout":
                auth_header = self.headers.get("Authorization", "")
                token = body.get("token")
                if not token and auth_header.startswith("Bearer "):
                    token = auth_header[7:].strip()
                if token:
                    cursor.execute("DELETE FROM staff_sessions WHERE token = ?", (token,))
                    conn.commit()
                return self.send_json({"success": True})

            # Staff Credentials Update Endpoint
            if path == "/api/staff/update-credentials":
                staff_id = body.get("staff_id")
                new_password = body.get("password")
                new_pin = body.get("pin")
                new_username = body.get("username")
                
                if not staff_id:
                    return self.send_json({"error": "Staff ID required"}, 400)
                    
                updates = []
                params = []
                if new_password:
                    updates.append("password = ?")
                    params.append(new_password)
                if new_pin:
                    updates.append("pin = ?")
                    params.append(new_pin)
                if new_username:
                    updates.append("username = ?")
                    params.append(new_username)
                    
                if updates:
                    params.append(staff_id)
                    cursor.execute(f"UPDATE staff_members SET {', '.join(updates)} WHERE id = ?", params)
                    conn.commit()
                return self.send_json({"success": True, "message": "ક્રેડેન્શિયલ્સ સફળતાપૂર્વક અપડેટ થયા!"})

            return self.send_json({"error": "POST endpoint not recognized"}, 404)

        finally:
            conn.close()

    def handle_api_put(self, path):
        conn = get_db()
        cursor = conn.cursor()
        body = self.read_json_body()

        try:
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            if path.startswith("/api/jobsheets/"):
                job_id = path.split("/")[-1]
                job = cursor.execute("SELECT * FROM job_sheets WHERE id = ?", (job_id,)).fetchone()
                if not job:
                    return self.send_json({"error": "Job sheet not found"}, 404)

                old_status = job["status"]
                new_status = body.get("status", old_status)
                technician_notes = body.get("technician_notes", job["technician_notes"])
                final_cost = float(body.get("final_cost", job["final_cost"]))
                advance_paid = float(body.get("advance_paid", job["advance_paid"]))
                technician = body.get("assigned_technician", job["assigned_technician"])
                delivered_at = now_str if new_status == "DELIVERED" and not job["delivered_at"] else job["delivered_at"]

                cursor.execute("""
                UPDATE job_sheets SET
                    status = ?,
                    technician_notes = ?,
                    final_cost = ?,
                    advance_paid = ?,
                    assigned_technician = ?,
                    updated_at = ?,
                    delivered_at = ?
                WHERE id = ?
                """, (new_status, technician_notes, final_cost, advance_paid, technician, now_str, delivered_at, job_id))

                note_text = body.get("log_note", f"Status changed from {old_status} to {new_status}")
                cursor.execute("""
                INSERT INTO job_sheet_logs (job_sheet_id, status, note, created_at)
                VALUES (?, ?, ?, ?)
                """, (job_id, new_status, note_text, now_str))

                conn.commit()
                return self.send_json({"success": True, "status": new_status})

            if path.startswith("/api/products/"):
                p_id = path.split("/")[-1]
                cursor.execute("""
                UPDATE products SET
                    name = ?, category = ?, brand = ?, model = ?, hsn_code = ?,
                    cost_price = ?, selling_price = ?, gst_rate = ?,
                    stock_quantity = ?, low_stock_threshold = ?, specs = ?, wattage = ?
                WHERE id = ?
                """, (
                    body.get("name"), body.get("category"), body.get("brand"), body.get("model"),
                    body.get("hsn_code", "8471"), float(body.get("cost_price", 0)), float(body.get("selling_price", 0)),
                    float(body.get("gst_rate", 18.0)), int(body.get("stock_quantity", 0)),
                    int(body.get("low_stock_threshold", 2)), body.get("specs", ""), int(body.get("wattage", 0)),
                    p_id
                ))
                conn.commit()
                return self.send_json({"success": True})

            if path.startswith("/api/amc/"):
                amc_id = path.split("/")[-1]
                cursor.execute("""
                UPDATE amc_contracts SET
                    status = ?, notes = ?, total_systems = ?, contract_value = ?, end_date = ?
                WHERE id = ?
                """, (
                    body.get("status", "ACTIVE"), body.get("notes", ""), int(body.get("total_systems", 1)),
                    float(body.get("contract_value", 0)), body.get("end_date"), amc_id
                ))
                conn.commit()
                return self.send_json({"success": True})

            if path.startswith("/api/inquiries/"):
                inq_id = path.split("/")[-1]
                cursor.execute("""
                UPDATE inquiries SET status = ?, notes = ? WHERE id = ?
                """, (body.get("status", "NEW"), body.get("notes", ""), inq_id))
                conn.commit()
                return self.send_json({"success": True})

            if path.startswith("/api/purchase-orders/"):
                po_id = path.split("/")[-1]
                cursor.execute("""
                UPDATE purchase_orders SET status = ?, payment_status = ?, notes = ? WHERE id = ?
                """, (body.get("status", "ORDERED"), body.get("payment_status", "UNPAID"), body.get("notes", ""), po_id))
                conn.commit()
                return self.send_json({"success": True})

            if path.startswith("/api/orders/"):
                ord_id = path.split("/")[-1]
                cursor.execute("""
                UPDATE orders SET status = ? WHERE id = ?
                """, (body.get("status", "CONFIRMED"), ord_id))
                conn.commit()
                return self.send_json({"success": True})

            
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

            return self.send_json({"error": "PUT endpoint not found"}, 404)

        finally:
            conn.close()

    def handle_api_delete(self, path):
        conn = get_db()
        cursor = conn.cursor()
        try:
            if path.startswith("/api/products/"):
                p_id = path.split("/")[-1]
                cursor.execute("DELETE FROM products WHERE id = ?", (p_id,))
                conn.commit()
                return self.send_json({"success": True})

            if path.startswith("/api/jobsheets/"):
                j_id = path.split("/")[-1]
                cursor.execute("DELETE FROM job_sheet_logs WHERE job_sheet_id = ?", (j_id,))
                cursor.execute("DELETE FROM job_sheets WHERE id = ?", (j_id,))
                conn.commit()
                return self.send_json({"success": True})

            if path.startswith("/api/backups"):
                filename = path.replace("/api/backups/delete", "").replace("/api/backups/", "").lstrip("/")
                if not filename or filename == "delete":
                    parsed = urllib.parse.urlparse(self.path)
                    q = urllib.parse.parse_qs(parsed.query)
                    filename = q.get("file", [None])[0]
                if not filename or os.path.basename(filename) != filename or not filename.endswith(".db"):
                    return self.send_json({"error": "Invalid backup filename"}, 400)
                target_path = os.path.join(BACKUPS_DIR, filename)
                if os.path.exists(target_path):
                    os.remove(target_path)
                    return self.send_json({"success": True, "message": f"{filename} deleted successfully"})
                return self.send_json({"error": "Backup file not found"}, 404)

            return self.send_json({"error": "DELETE endpoint not found"}, 404)
        finally:
            conn.close()

def run_server():
    os.chdir(BASE_DIR)
    os.makedirs(STATIC_DIR, exist_ok=True)
    os.makedirs(BACKUPS_DIR, exist_ok=True)
    ensure_daily_backup()
    # Bind to all interfaces (0.0.0.0) so browser can connect via localhost
    with socketserver.ThreadingTCPServer(("0.0.0.0", PORT), ERPRequestHandler) as httpd:
        httpd.allow_reuse_address = True
        print(f"Server live at http://localhost:{PORT}")
        httpd.serve_forever()

if __name__ == "__main__":
    run_server()
