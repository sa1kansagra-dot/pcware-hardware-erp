import sys

with open("static/index.html", "r", encoding="utf-8") as f:
    html = f.read()

# 1. Add new Category Pills to Store
cat_anchor = '<button type="button" onclick="filterCategory(\'service_parts\', this)" class="cat-pill px-3.5 py-1.5 rounded-full text-xs font-semibold bg-slate-100 text-slate-700 hover:bg-slate-200 transition cursor-pointer"><span data-i18n="cat_service_parts">Service & Spares</span></button>'

new_cats = '''
          <button type="button" onclick="filterCategory('workstation', this)" class="cat-pill px-3.5 py-1.5 rounded-full text-xs font-semibold bg-slate-100 text-slate-700 hover:bg-slate-200 transition cursor-pointer"><span>🖥️ Workstations (વર્કસ્ટેશન)</span></button>
          <button type="button" onclick="filterCategory('server', this)" class="cat-pill px-3.5 py-1.5 rounded-full text-xs font-semibold bg-slate-100 text-slate-700 hover:bg-slate-200 transition cursor-pointer"><span>🗄️ Servers (સર્વર્સ)</span></button>
          <button type="button" onclick="filterCategory('firewall_networking', this)" class="cat-pill px-3.5 py-1.5 rounded-full text-xs font-semibold bg-slate-100 text-slate-700 hover:bg-slate-200 transition cursor-pointer"><span>🛡️ Firewalls & Network (ફાયરવોલ)</span></button>
          <button type="button" onclick="filterCategory('antivirus_software', this)" class="cat-pill px-3.5 py-1.5 rounded-full text-xs font-semibold bg-slate-100 text-slate-700 hover:bg-slate-200 transition cursor-pointer"><span>🔒 Antivirus & Security (એન્ટિવાયરસ)</span></button>'''

if cat_anchor in html and "filterCategory('workstation'" not in html:
    html = html.replace(cat_anchor, cat_anchor + new_cats)

# 2. Add Staff and Warehouse Tabs to ERP Sub Navigation
erp_nav_anchor = '<button type="button" onclick="switchAdminTab(\'amc\')" id="tab-btn-amc"'
new_erp_tabs = '''<button type="button" onclick="switchAdminTab('staff')" id="tab-btn-staff" class="admin-tab px-3.5 py-1.5 rounded-lg text-xs font-semibold bg-slate-800 text-slate-300 hover:bg-slate-700 transition flex items-center gap-1.5 cursor-pointer whitespace-nowrap">
            <span>👥 ૮ સ્ટાફ ટીમ (Staff Team)</span>
          </button>
          <button type="button" onclick="switchAdminTab('warehouses')" id="tab-btn-warehouses" class="admin-tab px-3.5 py-1.5 rounded-lg text-xs font-semibold bg-slate-800 text-slate-300 hover:bg-slate-700 transition flex items-center gap-1.5 cursor-pointer whitespace-nowrap">
            <span>🏢 મલ્ટી-ગોડાઉન (Warehouses)</span>
          </button>
          '''

if erp_nav_anchor in html and "tab-btn-staff" not in html:
    html = html.replace(erp_nav_anchor, new_erp_tabs + erp_nav_anchor)

# 3. Add Staff Section and Warehouse Section before </section> (view-admin)
new_admin_sections = '''
      <!-- TAB: STAFF TEAM MANAGEMENT (8 EMPLOYEES) -->
      <div id="admin-tab-staff" class="hidden space-y-6">
        <div class="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
          <div class="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-slate-100">
            <div>
              <h3 class="text-base font-bold text-slate-900 flex items-center gap-2">
                <span>👥</span> ૮ સ્ટાફ ટીમ ડિરેક્ટરી અને રોલ મેનેજમેન્ટ (PCWARE Team)
              </h3>
              <p class="text-xs text-slate-500 mt-0.5">સેલ્સ એક્ઝિક્યુટિવ્સ, હાર્ડવેર લેબ એન્જિનિયર્સ, નેટવર્ક સ્પેશિયાલિસ્ટ અને એકાઉન્ટ્સ સ્ટાફની યાદી</p>
            </div>
            <button type="button" onclick="openNewStaffModal()" class="bg-brand-600 hover:bg-brand-700 text-white font-semibold text-xs py-2 px-3.5 rounded-lg shadow transition flex items-center gap-1.5 cursor-pointer">
              <span>+ નવો સ્ટાફ મેમ્બર ઉમેરો</span>
            </button>
          </div>

          <!-- Staff Cards Grid -->
          <div id="staff-cards-grid" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <!-- Dynamically populated via renderStaffTab() -->
          </div>
        </div>
      </div>

      <!-- TAB: MULTI-GODOWN & STOCK TRANSFERS -->
      <div id="admin-tab-warehouses" class="hidden space-y-6">
        <!-- Godown KPI Cards -->
        <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div class="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex items-center justify-between">
            <div>
              <span class="text-[11px] font-bold text-brand-600 uppercase">મુખ્ય શોરૂમ & કાઉન્ટર</span>
              <h4 class="text-base font-black text-slate-900 mt-1">સુવર્ણભૂમિ કોમ્પ્લેક્સ</h4>
              <p class="text-xs text-slate-500 mt-0.5" id="wh-showroom-units">લાઇવ ડિસ્પ્લે & કાઉન્ટર સ્ટોક</p>
            </div>
            <div class="w-10 h-10 rounded-xl bg-brand-50 text-brand-600 flex items-center justify-center font-bold text-lg">🏪</div>
          </div>

          <div class="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex items-center justify-between">
            <div>
              <span class="text-[11px] font-bold text-amber-600 uppercase">સેન્ટ્રલ ગોડાઉન ૧</span>
              <h4 class="text-base font-black text-slate-900 mt-1">કાલાવડ રોડ, રાજકોટ</h4>
              <p class="text-xs text-slate-500 mt-0.5" id="wh-godown1-units">બલ્ક લેપટોપ & સર્વર બોક્સ સ્ટોક</p>
            </div>
            <div class="w-10 h-10 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center font-bold text-lg">🏢</div>
          </div>

          <div class="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex items-center justify-between">
            <div>
              <span class="text-[11px] font-bold text-teal-600 uppercase">સર્વિસ & અપગ્રેડ લેબ</span>
              <h4 class="text-base font-black text-slate-900 mt-1">હાર્ડવેર લેબ (૨જો માળ)</h4>
              <p class="text-xs text-slate-500 mt-0.5" id="wh-lab-units">ટેસ્ટેડ RAM, SSD & સ્પેરપાર્ટ્સ</p>
            </div>
            <div class="w-10 h-10 rounded-xl bg-teal-50 text-teal-600 flex items-center justify-center font-bold text-lg">🔬</div>
          </div>
        </div>

        <!-- Stock Transfer Form -->
        <div class="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
          <div class="pb-3 border-b border-slate-100">
            <h3 class="text-base font-bold text-slate-900 flex items-center gap-2">
              <span>🚚</span> ગોડાઉન વચ્ચે સ્ટોક ટ્રાન્સફર (Inter-Godown Stock Movement)
            </h3>
            <p class="text-xs text-slate-500 mt-0.5">સેન્ટ્રલ ગોડાઉનમાંથી શોરૂમ કાઉન્ટર પર અથવા લેબમાં ટેસ્ટિંગ માટે માલ મોકલો</p>
          </div>

          <form id="form-stock-transfer" onsubmit="handleStockTransferSubmit(event)" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-6 gap-3 items-end">
            <div>
              <label class="block text-xs font-semibold text-slate-700 mb-1">ક્યાંથી (From Godown) *</label>
              <select id="transfer-from-wh" class="w-full text-xs p-2.5 rounded-lg border border-slate-300 bg-white" required>
                <option value="2">Godown 1 - Central Bulk (કાલાવડ રોડ)</option>
                <option value="1">Showroom & Store (સુવર્ણભૂમિ)</option>
                <option value="3">Service Lab (સર્વિસ લેબ)</option>
              </select>
            </div>

            <div>
              <label class="block text-xs font-semibold text-slate-700 mb-1">ક્યાં (To Godown) *</label>
              <select id="transfer-to-wh" class="w-full text-xs p-2.5 rounded-lg border border-slate-300 bg-white" required>
                <option value="1">Showroom & Store (સુવર્ણભૂમિ)</option>
                <option value="2">Godown 1 - Central Bulk (કાલાવડ રોડ)</option>
                <option value="3">Service Lab (સર્વિસ લેબ)</option>
              </select>
            </div>

            <div class="lg:col-span-2">
              <label class="block text-xs font-semibold text-slate-700 mb-1">પ્રોડક્ટ પસંદ કરો *</label>
              <select id="transfer-product-id" class="w-full text-xs p-2.5 rounded-lg border border-slate-300 bg-white" required>
                <!-- Populated dynamically -->
              </select>
            </div>

            <div>
              <label class="block text-xs font-semibold text-slate-700 mb-1">જથ્થો (Qty) *</label>
              <input type="number" id="transfer-qty" min="1" value="1" class="w-full text-xs p-2.5 rounded-lg border border-slate-300" required>
            </div>

            <div>
              <button type="submit" class="w-full bg-slate-900 hover:bg-slate-800 text-white font-semibold text-xs py-2.5 px-4 rounded-lg shadow transition cursor-pointer">
                🚚 ટ્રાન્સફર કરો
              </button>
            </div>
          </form>
        </div>

        <!-- Stock Transfer History Table -->
        <div class="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
          <div class="p-4 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
            <h4 class="font-bold text-xs text-slate-800 uppercase tracking-wider">તાજેતરના સ્ટોક ટ્રાન્સફર લોગ્સ (Movement History)</h4>
          </div>
          <div class="overflow-x-auto">
            <table class="w-full text-left text-xs border-collapse">
              <thead>
                <tr class="bg-slate-100 text-slate-600 font-bold border-b border-slate-200">
                  <th class="p-3">ટ્રાન્સફર No.</th>
                  <th class="p-3">ક્યાંથી (From)</th>
                  <th class="p-3">ક્યાં (To)</th>
                  <th class="p-3">પ્રોડક્ટ</th>
                  <th class="p-3 text-center">નંગ (Qty)</th>
                  <th class="p-3">જવાબદાર સ્ટાફ</th>
                  <th class="p-3">તારીખ</th>
                  <th class="p-3 text-center">સ્ટેટસ</th>
                </tr>
              </thead>
              <tbody id="stock-transfers-table-body" class="divide-y divide-slate-100">
                <!-- Dynamically populated -->
              </tbody>
            </table>
          </div>
        </div>
      </div>
'''

admin_section_close = '    </section>'
if admin_section_close in html and "admin-tab-staff" not in html:
    html = html.replace(admin_section_close, new_admin_sections + "\n" + admin_section_close)

# 4. Add Floating AI Chat Widget & Pop-up Window
floating_ai_widget = '''
  <!-- FLOATING GOOGLE GEMINI AI ASSISTANT WIDGET -->
  <div id="pcware-ai-widget" class="fixed bottom-6 right-6 z-40">
    <button type="button" onclick="toggleAIChatWindow()" class="relative group flex items-center gap-2.5 bg-gradient-to-r from-brand-600 to-indigo-600 hover:from-brand-700 hover:to-indigo-700 text-white font-bold text-xs py-3 px-4 rounded-full shadow-2xl hover:scale-105 transition-all duration-300 cursor-pointer border-2 border-white/20">
      <span class="text-xl animate-bounce">🤖</span>
      <span class="tracking-wide">PCWARE AI</span>
      <span class="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-ping"></span>
    </button>
  </div>

  <!-- AI CHAT WINDOW POPUP -->
  <div id="pcware-ai-chat-window" class="fixed bottom-20 right-6 z-50 w-[92vw] max-w-md bg-white rounded-3xl shadow-2xl border border-slate-200 overflow-hidden flex flex-col hidden transition-all duration-300" style="height: 540px;">
    <!-- Chat Header -->
    <div class="bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 text-white p-4 flex items-center justify-between shadow-md">
      <div class="flex items-center gap-2.5">
        <div class="w-9 h-9 rounded-xl bg-white/10 flex items-center justify-center text-xl">🤖</div>
        <div>
          <h3 class="text-sm font-black tracking-wide flex items-center gap-1.5">
            <span>PCWARE Smart AI</span>
            <span class="text-[9px] font-bold px-1.5 py-0.5 bg-indigo-500/30 text-indigo-200 rounded border border-indigo-400/30">Gemini Powered</span>
          </h3>
          <p class="text-[10px] text-slate-300">હાર્ડવેર સેલ્સ, સ્પેક્સ અને સર્વિસ આસિસ્ટન્ટ</p>
        </div>
      </div>
      <button type="button" onclick="toggleAIChatWindow()" class="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-white/10 cursor-pointer text-base">✕</button>
    </div>

    <!-- Chat Messages Scroll Container -->
    <div id="ai-chat-messages" class="flex-1 p-4 overflow-y-auto space-y-3.5 bg-slate-50 text-xs">
      <!-- Default welcome message -->
      <div class="flex gap-2.5">
        <div class="w-7 h-7 rounded-lg bg-indigo-100 text-indigo-700 flex items-center justify-center font-bold shrink-0 text-sm">🤖</div>
        <div class="bg-white p-3 rounded-2xl rounded-tl-none border border-slate-200 shadow-sm text-slate-800 space-y-2 max-w-[85%]">
          <p><strong>નમસ્તે! PCWARE માં આપનું સ્વાગત છે!</strong> 🖥️✨</p>
          <p class="text-slate-600">હું તમારો AI હાર્ડવેર કન્સલ્ટન્ટ છું. તમે મને ગુજરાતી કે અંગ્રેજીમાં કોઈપણ લેપટોપ, કસ્ટમ પીસી, વર્કસ્ટેશન, ફાયરવોલ કે રિપેરિંગ સર્વિસ વિશે પૂછી શકો છો!</p>
        </div>
      </div>
    </div>

    <!-- Suggested Quick Chips -->
    <div class="px-3 py-2 bg-slate-100/80 border-t border-slate-200 flex gap-1.5 overflow-x-auto text-[10px]">
      <button type="button" onclick="sendAIChip('Best Laptop under 50000')" class="px-2.5 py-1 bg-white border border-slate-200 rounded-full text-slate-700 hover:border-brand-500 hover:text-brand-600 whitespace-nowrap cursor-pointer">💼 Laptops under ₹50,000</button>
      <button type="button" onclick="sendAIChip('AutoCAD Workstation')" class="px-2.5 py-1 bg-white border border-slate-200 rounded-full text-slate-700 hover:border-brand-500 hover:text-brand-600 whitespace-nowrap cursor-pointer">🖥️ Workstation Suggestion</button>
      <button type="button" onclick="sendAIChip('Sophos Firewall Details')" class="px-2.5 py-1 bg-white border border-slate-200 rounded-full text-slate-700 hover:border-brand-500 hover:text-brand-600 whitespace-nowrap cursor-pointer">🛡️ Sophos Firewall</button>
      <button type="button" onclick="sendAIChip('Book Laptop Repair Service')" class="px-2.5 py-1 bg-white border border-slate-200 rounded-full text-slate-700 hover:border-brand-500 hover:text-brand-600 whitespace-nowrap cursor-pointer">🔧 Book Service</button>
    </div>

    <!-- Chat Input Area -->
    <form id="form-ai-chat" onsubmit="handleAIChatSubmit(event)" class="p-2.5 bg-white border-t border-slate-200 flex items-center gap-2">
      <input type="text" id="ai-user-input" placeholder="પ્રશ્ન પૂછો... Ask in Gujarati or English..." class="flex-1 text-xs p-2.5 rounded-xl border border-slate-200 focus:outline-none focus:border-indigo-500 bg-slate-50" required autocomplete="off">
      <button type="submit" class="bg-indigo-600 hover:bg-indigo-700 text-white p-2.5 rounded-xl shadow transition cursor-pointer">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 5l7 7m0 0l-7 7m7-7H3"/></svg>
      </button>
    </form>
  </div>
'''

if "pcware-ai-widget" not in html:
    html = html.replace('</body>', floating_ai_widget + '\n</body>')

# 5. Add Laptop / Workstation Dynamic Upgrade Modal
modal_laptop_upgrade = '''
  <!-- MODAL: DYNAMIC LAPTOP / WORKSTATION CUSTOMIZER & UPGRADE -->
  <div id="modal-laptop-upgrade" class="fixed inset-0 z-50 overflow-y-auto hidden">
    <div class="fixed inset-0 bg-slate-900/60 backdrop-blur-sm" onclick="closeModal('modal-laptop-upgrade')"></div>
    <div class="relative min-h-screen flex items-center justify-center p-4">
      <div class="relative bg-white rounded-3xl max-w-2xl w-full p-6 shadow-2xl border border-slate-200 space-y-5">
        <div class="flex items-center justify-between pb-3 border-b border-slate-100">
          <div class="flex items-center gap-2.5">
            <span class="text-2xl">⚡</span>
            <div>
              <h3 class="text-base font-bold text-slate-900" id="upgrade-modal-title">Laptop Customizer & Upgrades</h3>
              <p class="text-xs text-slate-500">RAM, SSD, Antivirus અને Warranty પસંદ કરો — ભાવ લાઈવ અપડેટ થશે</p>
            </div>
          </div>
          <button type="button" onclick="closeModal('modal-laptop-upgrade')" class="text-slate-400 hover:text-slate-700 cursor-pointer text-lg">✕</button>
        </div>

        <!-- Product Base Info -->
        <div class="p-3.5 bg-slate-50 rounded-2xl border border-slate-200 flex items-center gap-3.5">
          <img id="upgrade-base-img" src="" class="w-16 h-16 object-contain rounded-xl bg-white p-1 border border-slate-200">
          <div class="flex-1">
            <h4 class="font-bold text-xs text-slate-900" id="upgrade-base-name">Laptop Name</h4>
            <p class="text-[11px] text-slate-500 mt-0.5" id="upgrade-base-specs">Base Specs</p>
            <div class="mt-1 flex items-center gap-2">
              <span class="text-xs font-bold text-slate-700">બેઝ કિંમત:</span>
              <span class="text-sm font-black text-slate-900" id="upgrade-base-price">₹0</span>
            </div>
          </div>
        </div>

        <!-- Upgrades Form -->
        <div class="space-y-4 text-xs">
          <!-- 1. RAM Upgrade -->
          <div class="space-y-1.5">
            <label class="font-bold text-slate-800 flex items-center justify-between">
              <span>💾 RAM (મેમરી) અપગ્રેડ:</span>
              <span class="text-[11px] text-brand-600 font-semibold" id="lbl-ram-delta">+₹0</span>
            </label>
            <div class="grid grid-cols-2 sm:grid-cols-4 gap-2">
              <label class="p-2.5 border border-slate-200 rounded-xl cursor-pointer hover:border-brand-500 flex items-center gap-2">
                <input type="radio" name="opt_ram" value="0" data-name="Base RAM" checked onchange="recalculateUpgradePrice()">
                <div><div class="font-bold text-[11px]">Base RAM</div><div class="text-[10px] text-slate-400">Included (₹0)</div></div>
              </label>
              <label class="p-2.5 border border-slate-200 rounded-xl cursor-pointer hover:border-brand-500 flex items-center gap-2">
                <input type="radio" name="opt_ram" value="2500" data-name="16GB RAM Upgrade" onchange="recalculateUpgradePrice()">
                <div><div class="font-bold text-[11px]">16GB RAM</div><div class="text-[10px] text-emerald-600">+₹2,500</div></div>
              </label>
              <label class="p-2.5 border border-slate-200 rounded-xl cursor-pointer hover:border-brand-500 flex items-center gap-2">
                <input type="radio" name="opt_ram" value="5800" data-name="32GB RAM Upgrade" onchange="recalculateUpgradePrice()">
                <div><div class="font-bold text-[11px]">32GB RAM</div><div class="text-[10px] text-emerald-600">+₹5,800</div></div>
              </label>
              <label class="p-2.5 border border-slate-200 rounded-xl cursor-pointer hover:border-brand-500 flex items-center gap-2">
                <input type="radio" name="opt_ram" value="12500" data-name="64GB RAM Upgrade" onchange="recalculateUpgradePrice()">
                <div><div class="font-bold text-[11px]">64GB RAM</div><div class="text-[10px] text-emerald-600">+₹12,500</div></div>
              </label>
            </div>
          </div>

          <!-- 2. Storage SSD Upgrade -->
          <div class="space-y-1.5">
            <label class="font-bold text-slate-800 flex items-center justify-between">
              <span>💽 સ્ટોરેજ (NVMe SSD) અપગ્રેડ:</span>
              <span class="text-[11px] text-brand-600 font-semibold" id="lbl-ssd-delta">+₹0</span>
            </label>
            <div class="grid grid-cols-1 sm:grid-cols-3 gap-2">
              <label class="p-2.5 border border-slate-200 rounded-xl cursor-pointer hover:border-brand-500 flex items-center gap-2">
                <input type="radio" name="opt_ssd" value="0" data-name="Base SSD" checked onchange="recalculateUpgradePrice()">
                <div><div class="font-bold text-[11px]">Base SSD (512GB/256GB)</div><div class="text-[10px] text-slate-400">Included (₹0)</div></div>
              </label>
              <label class="p-2.5 border border-slate-200 rounded-xl cursor-pointer hover:border-brand-500 flex items-center gap-2">
                <input type="radio" name="opt_ssd" value="3500" data-name="1TB Gen4 NVMe Upgrade" onchange="recalculateUpgradePrice()">
                <div><div class="font-bold text-[11px]">1TB Gen4 NVMe SSD</div><div class="text-[10px] text-emerald-600">+₹3,500</div></div>
              </label>
              <label class="p-2.5 border border-slate-200 rounded-xl cursor-pointer hover:border-brand-500 flex items-center gap-2">
                <input type="radio" name="opt_ssd" value="7500" data-name="2TB Gen4 NVMe Upgrade" onchange="recalculateUpgradePrice()">
                <div><div class="font-bold text-[11px]">2TB Gen4 NVMe SSD</div><div class="text-[10px] text-emerald-600">+₹7,500</div></div>
              </label>
            </div>
          </div>

          <!-- 3. Antivirus & Security -->
          <div class="space-y-1.5">
            <label class="font-bold text-slate-800 flex items-center justify-between">
              <span>🔒 એન્ટિવાયરસ & સિક્યુરિટી સોફ્ટવેર:</span>
              <span class="text-[11px] text-brand-600 font-semibold" id="lbl-av-delta">+₹0</span>
            </label>
            <div class="grid grid-cols-1 sm:grid-cols-3 gap-2">
              <label class="p-2.5 border border-slate-200 rounded-xl cursor-pointer hover:border-brand-500 flex items-center gap-2">
                <input type="radio" name="opt_av" value="0" data-name="No Antivirus" checked onchange="recalculateUpgradePrice()">
                <div><div class="font-bold text-[11px]">કોઈ એન્ટિવાયરસ નહીં</div><div class="text-[10px] text-slate-400">₹0</div></div>
              </label>
              <label class="p-2.5 border border-slate-200 rounded-xl cursor-pointer hover:border-brand-500 flex items-center gap-2">
                <input type="radio" name="opt_av" value="699" data-name="1-Year Quick Heal Total Security" onchange="recalculateUpgradePrice()">
                <div><div class="font-bold text-[11px]">Quick Heal 1 Year</div><div class="text-[10px] text-emerald-600">+₹699</div></div>
              </label>
              <label class="p-2.5 border border-slate-200 rounded-xl cursor-pointer hover:border-brand-500 flex items-center gap-2">
                <input type="radio" name="opt_av" value="1499" data-name="3-Year Quick Heal Total Security" onchange="recalculateUpgradePrice()">
                <div><div class="font-bold text-[11px]">Quick Heal 3 Years</div><div class="text-[10px] text-emerald-600">+₹1,499</div></div>
              </label>
            </div>
          </div>

          <!-- 4. Extended Warranty & AMC -->
          <div class="space-y-1.5">
            <label class="font-bold text-slate-800 flex items-center justify-between">
              <span>🛡️ વોરંટી & PCWARE કેર AMC:</span>
              <span class="text-[11px] text-brand-600 font-semibold" id="lbl-wty-delta">+₹0</span>
            </label>
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-2">
              <label class="p-2.5 border border-slate-200 rounded-xl cursor-pointer hover:border-brand-500 flex items-center gap-2">
                <input type="radio" name="opt_wty" value="0" data-name="Standard Store Warranty" checked onchange="recalculateUpgradePrice()">
                <div><div class="font-bold text-[11px]">સ્ટાન્ડર્ડ સ્ટોર વોરંટી</div><div class="text-[10px] text-slate-400">Included (₹0)</div></div>
              </label>
              <label class="p-2.5 border border-slate-200 rounded-xl cursor-pointer hover:border-brand-500 flex items-center gap-2">
                <input type="radio" name="opt_wty" value="2500" data-name="1-Year Comprehensive PCWARE Care AMC" onchange="recalculateUpgradePrice()">
                <div><div class="font-bold text-[11px]">૧ વર્ષ ફુલ AMC સપોર્ટ</div><div class="text-[10px] text-emerald-600">+₹2,500 (Free Servicing)</div></div>
              </label>
            </div>
          </div>
        </div>

        <!-- Calculated Live Total Bar & Buttons -->
        <div class="p-4 bg-gradient-to-r from-slate-900 to-indigo-950 text-white rounded-2xl flex flex-wrap items-center justify-between gap-3">
          <div>
            <span class="text-[10px] text-indigo-300 font-bold uppercase tracking-wider block">કુલ રકમ (GST શામેલ):</span>
            <span class="text-2xl font-black text-white" id="upgrade-calc-total">₹0</span>
          </div>
          <div class="flex items-center gap-2">
            <button type="button" onclick="confirmCustomUpgradeWhatsApp()" class="bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs py-2.5 px-4 rounded-xl shadow transition flex items-center gap-1.5 cursor-pointer">
              <span>📱 Book on WhatsApp</span>
            </button>
            <button type="button" onclick="addCustomUpgradeToCart()" class="bg-brand-600 hover:bg-brand-700 text-white font-bold text-xs py-2.5 px-4 rounded-xl shadow transition flex items-center gap-1.5 cursor-pointer">
              <span>🛒 Add to Cart</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- MODAL: DIRECT WHATSAPP BOOKING & LEAD GENERATION -->
  <div id="modal-whatsapp-booking" class="fixed inset-0 z-50 overflow-y-auto hidden">
    <div class="fixed inset-0 bg-slate-900/60 backdrop-blur-sm" onclick="closeModal('modal-whatsapp-booking')"></div>
    <div class="relative min-h-screen flex items-center justify-center p-4">
      <div class="relative bg-white rounded-3xl max-w-lg w-full p-6 shadow-2xl border border-slate-200 space-y-4">
        <div class="flex items-center justify-between pb-3 border-b border-slate-100">
          <div class="flex items-center gap-2.5">
            <span class="text-2xl">📱</span>
            <div>
              <h3 class="text-base font-bold text-slate-900">WhatsApp ડાયરેક્ટ બુકિંગ & પૂછપરછ</h3>
              <p class="text-xs text-slate-500">ઓનલાઇન પેમેન્ટ વગર બુક કરો — અમારા એક્ઝિક્યુટિવ તમને ફોન કરશે</p>
            </div>
          </div>
          <button type="button" onclick="closeModal('modal-whatsapp-booking')" class="text-slate-400 hover:text-slate-700 cursor-pointer text-lg">✕</button>
        </div>

        <form id="form-whatsapp-booking" onsubmit="handleWhatsAppBookingSubmit(event)" class="space-y-3.5 text-xs">
          <!-- Item Summary Badge -->
          <div class="p-3 bg-emerald-50 rounded-xl border border-emerald-200 space-y-1">
            <div class="flex justify-between items-center">
              <strong class="text-emerald-950 font-bold" id="wa-book-item-name">Product Name</strong>
              <span class="font-black text-emerald-800 text-sm" id="wa-book-price">₹0</span>
            </div>
            <p class="text-[11px] text-emerald-700" id="wa-book-specs"></p>
          </div>

          <div>
            <label class="block font-semibold text-slate-700 mb-1">ગ્રાહકનું પૂરું નામ *</label>
            <input type="text" id="wa-cust-name" class="w-full text-xs p-2.5 rounded-lg border border-slate-300" required placeholder="દા.ત. રમેશભાઈ પટેલ">
          </div>

          <div>
            <label class="block font-semibold text-slate-700 mb-1">મોબાઈલ નંબર (WhatsApp Phone) *</label>
            <input type="tel" id="wa-cust-phone" class="w-full text-xs p-2.5 rounded-lg border border-slate-300" required placeholder="દા.ત. 9825012345">
          </div>

          <div>
            <label class="block font-semibold text-slate-700 mb-1">સરનામું / શહેર *</label>
            <input type="text" id="wa-cust-addr" class="w-full text-xs p-2.5 rounded-lg border border-slate-300" required placeholder="દા.ત. કાલાવડ રોડ, રાજકોટ">
          </div>

          <div>
            <label class="block font-semibold text-slate-700 mb-1.5">ડિલિવરી પદ્ધતિ (Fulfillment Mode) *</label>
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-2">
              <label class="p-2.5 border border-slate-200 rounded-xl cursor-pointer hover:border-brand-500 flex items-center gap-2">
                <input type="radio" name="wa_fulfillment" value="SHOWROOM_VISIT" checked>
                <div>
                  <div class="font-bold text-[11px]">🏪 Showroom Visit</div>
                  <div class="text-[10px] text-slate-400">શોરૂમે લાઈવ ડેમો જોઈને લેવું છે</div>
                </div>
              </label>
              <label class="p-2.5 border border-slate-200 rounded-xl cursor-pointer hover:border-brand-500 flex items-center gap-2">
                <input type="radio" name="wa_fulfillment" value="COURIER_DISPATCH">
                <div>
                  <div class="font-bold text-[11px]">📦 Courier Dispatch</div>
                  <div class="text-[10px] text-slate-400">કુરિયર પાર્સલ દ્વારા મંગાવવું છે</div>
                </div>
              </label>
            </div>
          </div>

          <div class="pt-2">
            <button type="submit" class="w-full bg-emerald-600 hover:bg-emerald-700 text-white font-bold py-3 px-4 rounded-xl shadow-lg transition flex items-center justify-center gap-2 cursor-pointer text-sm">
              <span>🚀 Confirm Booking on WhatsApp</span>
            </button>
            <p class="text-[10px] text-center text-slate-400 mt-2">ક્લિક કરતાં સીધું WhatsApp ખુલશે અને ERP માં તમારી લીડ નોંધાઈ જશે.</p>
          </div>
        </form>
      </div>
    </div>
  </div>

  <!-- MODAL: ADD STAFF MEMBER -->
  <div id="modal-new-staff" class="fixed inset-0 z-50 overflow-y-auto hidden">
    <div class="fixed inset-0 bg-slate-900/60 backdrop-blur-sm" onclick="closeModal('modal-new-staff')"></div>
    <div class="relative min-h-screen flex items-center justify-center p-4">
      <div class="relative bg-white rounded-3xl max-w-md w-full p-6 shadow-2xl border border-slate-200 space-y-4">
        <div class="flex items-center justify-between pb-3 border-b border-slate-100">
          <h3 class="text-base font-bold text-slate-900">+ નવો સ્ટાફ મેમ્બર ઉમેરો</h3>
          <button type="button" onclick="closeModal('modal-new-staff')" class="text-slate-400 hover:text-slate-700 cursor-pointer">✕</button>
        </div>
        <form id="form-new-staff" onsubmit="handleCreateStaffSubmit(event)" class="space-y-3 text-xs">
          <div>
            <label class="block font-semibold text-slate-700 mb-1">કર્મચારીનું પૂરું નામ *</label>
            <input type="text" id="staff-name" class="w-full text-xs p-2.5 rounded-lg border border-slate-300" required placeholder="દા.ત. અજય પંડ્યા">
          </div>
          <div>
            <label class="block font-semibold text-slate-700 mb-1">હોદ્દો (Role / Designation) *</label>
            <input type="text" id="staff-role" class="w-full text-xs p-2.5 rounded-lg border border-slate-300" required placeholder="દા.ત. Junior Hardware Engineer">
          </div>
          <div>
            <label class="block font-semibold text-slate-700 mb-1">ડિપાર્ટમેન્ટ (Department) *</label>
            <select id="staff-dept" class="w-full text-xs p-2.5 rounded-lg border border-slate-300 bg-white" required>
              <option value="Sales & Inquiries">Sales & Inquiries (સેલ્સ)</option>
              <option value="Lab & Service">Lab & Service (સર્વિસ લેબ)</option>
              <option value="Assembly & QC">Assembly & QC (પીસી એસેમ્બલી)</option>
              <option value="Networking & AMC">Networking & AMC (નેટવર્કિંગ)</option>
              <option value="Logistics & Stock">Logistics & Stock (ગોડાઉન)</option>
              <option value="Accounts & Finance">Accounts & Finance (એકાઉન્ટ્સ)</option>
            </select>
          </div>
          <div>
            <label class="block font-semibold text-slate-700 mb-1">મોબાઈલ નંબર *</label>
            <input type="tel" id="staff-phone" class="w-full text-xs p-2.5 rounded-lg border border-slate-300" required placeholder="દા.ત. 9825011223">
          </div>
          <div>
            <label class="block font-semibold text-slate-700 mb-1">ઈમેઈલ (Email)</label>
            <input type="email" id="staff-email" class="w-full text-xs p-2.5 rounded-lg border border-slate-300" placeholder="staff@pcware.in">
          </div>
          <div class="pt-2 flex justify-end gap-2">
            <button type="button" onclick="closeModal('modal-new-staff')" class="px-4 py-2 border border-slate-300 rounded-lg font-medium text-slate-700 hover:bg-slate-50 cursor-pointer">રદ કરો</button>
            <button type="submit" class="px-4 py-2 bg-brand-600 hover:bg-brand-700 text-white rounded-lg font-semibold shadow cursor-pointer">+ ઉમેરો</button>
          </div>
        </form>
      </div>
    </div>
  </div>
'''

if "modal-laptop-upgrade" not in html:
    html = html.replace('</body>', modal_laptop_upgrade + '\n</body>')

with open("static/index.html", "w", encoding="utf-8") as f:
    f.write(html)

print("static/index.html updated successfully with AI widget, Modals, Staff & Warehouse tabs!")
