import sys

with open("static/app.js", "r", encoding="utf-8") as f:
    code = f.read()

# 1. Update renderProductsGrid to include Customize & Upgrade button and WhatsApp Booking button
old_render_grid_start = "function renderProductsGrid() {"
old_render_grid_end = "function toggleCartDrawer(open) {"

idx_start = code.find(old_render_grid_start)
idx_end = code.find(old_render_grid_end)

if idx_start == -1 or idx_end == -1:
    print("Could not find renderProductsGrid boundaries!", idx_start, idx_end)
    sys.exit(1)

new_render_grid = '''function renderProductsGrid() {
  const container = document.getElementById("products-grid");
  if (!container) return;

  if (state.filteredProducts.length === 0) {
    container.innerHTML = `
      <div class="col-span-full py-12 text-center text-slate-500">
        <p class="font-semibold text-slate-700">${t('no_products')}</p>
        <p class="text-xs text-slate-400">${t('no_products_desc')}</p>
      </div>
    `;
    return;
  }

  container.innerHTML = state.filteredProducts.map(p => {
    const isLowStock = p.stock_quantity <= p.low_stock_threshold;
    const isOutOfStock = p.stock_quantity <= 0;
    const isCustomizable = (p.category === "laptop" || p.category === "workstation");

    return `
      <div class="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-sm hover:shadow-md transition group flex flex-col justify-between">
        <div class="relative h-48 bg-slate-100 overflow-hidden flex items-center justify-center p-3">
          <img src="${p.image_url || 'https://images.unsplash.com/photo-1591799264318-7e6ef8ddb7ea?w=400'}" alt="${p.name}" loading="lazy" class="max-h-full max-w-full object-contain group-hover:scale-105 transition duration-300">
          <span class="absolute top-2 left-2 bg-slate-900/80 backdrop-blur text-white text-[10px] font-bold px-2 py-0.5 rounded uppercase">
            ${p.brand}
          </span>
          <span class="absolute top-2 right-2 text-[10px] font-bold px-2 py-0.5 rounded ${
            isOutOfStock ? 'bg-rose-100 text-rose-700 border border-rose-200' :
            isLowStock ? 'bg-amber-100 text-amber-700 border border-amber-200' :
            'bg-emerald-100 text-emerald-700 border border-emerald-200'
          }">
            ${isOutOfStock ? t('out_of_stock') : t('stock_prefix') + p.stock_quantity}
          </span>
        </div>

        <div class="p-4 flex-1 flex flex-col justify-between space-y-3">
          <div class="space-y-1">
            <div class="flex items-center gap-1.5 flex-wrap">
              <span class="text-[10px] font-bold px-1.5 py-0.5 bg-brand-50 text-brand-700 rounded uppercase tracking-wider">${p.category}</span>
              ${p.socket ? `<span class="text-[9px] px-1.5 py-0.5 bg-emerald-50 text-emerald-700 rounded font-semibold font-mono">${p.socket}</span>` : ''}
              ${p.memory_type ? `<span class="text-[9px] px-1.5 py-0.5 bg-teal-50 text-teal-700 rounded font-semibold font-mono">${p.memory_type}</span>` : ''}
              ${isCustomizable ? `<span class="text-[9px] px-1.5 py-0.5 bg-amber-50 text-amber-700 rounded font-bold">⚡ Upgradeable</span>` : ''}
            </div>
            <h3 class="font-bold text-slate-900 text-sm leading-snug line-clamp-2" title="${p.name}">${p.name}</h3>
            ${p.specs ? `<p class="text-xs text-slate-500 line-clamp-2">${p.specs}</p>` : ''}
          </div>

          <div class="pt-2 border-t border-slate-100 space-y-2">
            <div class="flex items-center justify-between">
              <div>
                <span class="text-[11px] text-slate-400 block font-medium leading-tight">${t('incl_gst')}</span>
                <span class="text-lg font-black text-slate-900">₹${p.selling_price.toLocaleString('en-IN')}</span>
              </div>
              <button type="button" onclick="addToCart(${p.id})" ${isOutOfStock ? 'disabled' : ''} class="bg-brand-600 hover:bg-brand-700 disabled:bg-slate-300 text-white font-semibold text-xs px-3 py-1.5 rounded-xl shadow-sm transition flex items-center gap-1 cursor-pointer">
                <span>🛒 ${t('add_to_cart')}</span>
              </button>
            </div>

            <!-- Action Buttons: WhatsApp Booking & Customize Upgrade -->
            <div class="grid ${isCustomizable ? 'grid-cols-2' : 'grid-cols-1'} gap-1.5 pt-1">
              ${isCustomizable ? `
                <button type="button" onclick="openLaptopUpgradeModal(${p.id})" class="w-full bg-amber-50 hover:bg-amber-100 text-amber-800 border border-amber-200 font-bold text-[11px] py-1.5 px-2 rounded-xl transition flex items-center justify-center gap-1 cursor-pointer">
                  <span>⚡ Customize</span>
                </button>
              ` : ''}
              <button type="button" onclick="openWhatsAppBookingModal(${p.id})" class="w-full bg-emerald-50 hover:bg-emerald-100 text-emerald-800 border border-emerald-200 font-bold text-[11px] py-1.5 px-2 rounded-xl transition flex items-center justify-center gap-1 cursor-pointer">
                <span>📱 Book on WhatsApp</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    `;
  }).join("");
}

'''

code = code[:idx_start] + new_render_grid + code[idx_end:]

# 2. Add New Enterprise Modules at the bottom of the script
enterprise_js = '''
// ============================================================================
// ENTERPRISE FEATURE 1: DYNAMIC LAPTOP / WORKSTATION UPGRADE MODAL
// ============================================================================
let currentCustomBuild = null;

function openLaptopUpgradeModal(productId) {
  const p = (state.products || []).find(item => item.id === productId);
  if (!p) return;

  currentCustomBuild = {
    product: p,
    basePrice: Number(p.selling_price),
    ramDelta: 0,
    ramLabel: "Base RAM",
    ssdDelta: 0,
    ssdLabel: "Base SSD",
    avDelta: 0,
    avLabel: "No Antivirus",
    wtyDelta: 0,
    wtyLabel: "Standard Store Warranty",
    totalPrice: Number(p.selling_price)
  };

  const modalTitle = document.getElementById("upgrade-modal-title");
  const baseImg = document.getElementById("upgrade-base-img");
  const baseName = document.getElementById("upgrade-base-name");
  const baseSpecs = document.getElementById("upgrade-base-specs");
  const basePrice = document.getElementById("upgrade-base-price");
  const calcTotal = document.getElementById("upgrade-calc-total");

  if (modalTitle) modalTitle.textContent = `${p.name} — Customizer & Upgrades`;
  if (baseImg) baseImg.src = p.image_url || "";
  if (baseName) baseName.textContent = p.name;
  if (baseSpecs) baseSpecs.textContent = p.specs || "";
  if (basePrice) basePrice.textContent = `₹${p.selling_price.toLocaleString('en-IN')}`;
  if (calcTotal) calcTotal.textContent = `₹${p.selling_price.toLocaleString('en-IN')}`;

  // Reset radio selections to default 0
  const resetRadio = (name) => {
    const r = document.querySelector(`input[name="${name}"][value="0"]`);
    if (r) r.checked = true;
  };
  resetRadio("opt_ram");
  resetRadio("opt_ssd");
  resetRadio("opt_av");
  resetRadio("opt_wty");

  document.getElementById("lbl-ram-delta").textContent = "+₹0";
  document.getElementById("lbl-ssd-delta").textContent = "+₹0";
  document.getElementById("lbl-av-delta").textContent = "+₹0";
  document.getElementById("lbl-wty-delta").textContent = "+₹0";

  openModal("modal-laptop-upgrade");
}

function recalculateUpgradePrice() {
  if (!currentCustomBuild) return;

  const getSelected = (name) => {
    const el = document.querySelector(`input[name="${name}"]:checked`);
    if (!el) return { val: 0, name: "" };
    return { val: Number(el.value), name: el.getAttribute("data-name") || "" };
  };

  const ram = getSelected("opt_ram");
  const ssd = getSelected("opt_ssd");
  const av = getSelected("opt_av");
  const wty = getSelected("opt_wty");

  currentCustomBuild.ramDelta = ram.val;
  currentCustomBuild.ramLabel = ram.name;
  currentCustomBuild.ssdDelta = ssd.val;
  currentCustomBuild.ssdLabel = ssd.name;
  currentCustomBuild.avDelta = av.val;
  currentCustomBuild.avLabel = av.name;
  currentCustomBuild.wtyDelta = wty.val;
  currentCustomBuild.wtyLabel = wty.name;

  const total = currentCustomBuild.basePrice + ram.val + ssd.val + av.val + wty.val;
  currentCustomBuild.totalPrice = total;

  const calcTotal = document.getElementById("upgrade-calc-total");
  if (calcTotal) calcTotal.textContent = `₹${total.toLocaleString('en-IN')}`;

  document.getElementById("lbl-ram-delta").textContent = ram.val > 0 ? `+₹${ram.val.toLocaleString('en-IN')}` : "+₹0";
  document.getElementById("lbl-ssd-delta").textContent = ssd.val > 0 ? `+₹${ssd.val.toLocaleString('en-IN')}` : "+₹0";
  document.getElementById("lbl-av-delta").textContent = av.val > 0 ? `+₹${av.val.toLocaleString('en-IN')}` : "+₹0";
  document.getElementById("lbl-wty-delta").textContent = wty.val > 0 ? `+₹${wty.val.toLocaleString('en-IN')}` : "+₹0";
}

function confirmCustomUpgradeWhatsApp() {
  if (!currentCustomBuild) return;
  const p = currentCustomBuild.product;
  const specsSummary = `RAM: ${currentCustomBuild.ramLabel} | SSD: ${currentCustomBuild.ssdLabel} | Security: ${currentCustomBuild.avLabel} | Warranty: ${currentCustomBuild.wtyLabel}`;
  closeModal("modal-laptop-upgrade");
  openWhatsAppBookingModal(p.id, specsSummary, currentCustomBuild.totalPrice);
}

function addCustomUpgradeToCart() {
  if (!currentCustomBuild) return;
  const p = currentCustomBuild.product;
  const specsSummary = `${currentCustomBuild.ramLabel}, ${currentCustomBuild.ssdLabel}, ${currentCustomBuild.avLabel}, ${currentCustomBuild.wtyLabel}`;
  
  state.cart.push({
    id: p.id,
    sku: p.sku + "-CUST",
    name: `${p.name} [Upgrades: ${specsSummary}]`,
    price: currentCustomBuild.totalPrice,
    image_url: p.image_url,
    category: p.category,
    qty: 1
  });

  saveCart();
  updateCartUI();
  closeModal("modal-laptop-upgrade");
  showToast(`કસ્ટમાઇઝ્ડ લેપટોપ કાર્ટમાં ઉમેર્યું: ₹${currentCustomBuild.totalPrice.toLocaleString('en-IN')}`);
}

// ============================================================================
// ENTERPRISE FEATURE 2: WHATSAPP DIRECT BOOKING & AUTOMATIC ERP LEAD
// ============================================================================
let currentBookingItem = null;

function openWhatsAppBookingModal(productId, customSpecsStr = "", calculatedPrice = null) {
  const p = (state.products || []).find(item => item.id === productId);
  if (!p) return;

  const finalPrice = (calculatedPrice !== null) ? calculatedPrice : Number(p.selling_price);

  currentBookingItem = {
    product: p,
    price: finalPrice,
    specs: customSpecsStr || p.specs || ""
  };

  const nameEl = document.getElementById("wa-book-item-name");
  const priceEl = document.getElementById("wa-book-price");
  const specsEl = document.getElementById("wa-book-specs");

  if (nameEl) nameEl.textContent = p.name;
  if (priceEl) priceEl.textContent = `₹${finalPrice.toLocaleString('en-IN')}`;
  if (specsEl) specsEl.textContent = currentBookingItem.specs;

  // Clear previous customer fields
  const nameInput = document.getElementById("wa-cust-name");
  const phoneInput = document.getElementById("wa-cust-phone");
  const addrInput = document.getElementById("wa-cust-addr");
  if (nameInput) nameInput.value = "";
  if (phoneInput) phoneInput.value = "";
  if (addrInput) addrInput.value = "";

  openModal("modal-whatsapp-booking");
}

async function handleWhatsAppBookingSubmit(e) {
  e.preventDefault();
  if (!currentBookingItem) return;

  const custName = document.getElementById("wa-cust-name").value.trim();
  const custPhone = document.getElementById("wa-cust-phone").value.trim();
  const custAddr = document.getElementById("wa-cust-addr").value.trim();
  const fulfillmentMode = document.querySelector('input[name="wa_fulfillment"]:checked')?.value || "SHOWROOM_VISIT";

  const payload = {
    customer_name: custName,
    customer_phone: custPhone,
    customer_address: custAddr,
    requirement_type: currentBookingItem.product.category.toUpperCase(),
    items_requested: currentBookingItem.product.name,
    custom_specs: currentBookingItem.specs,
    estimated_budget: currentBookingItem.price,
    fulfillment_mode: fulfillmentMode,
    notes: `Customer requested booking from website. Preferred mode: ${fulfillmentMode}`
  };

  showToast(state.lang === 'en' ? "Creating inquiry and connecting to WhatsApp..." : "પૂછપરછ નોંધીને WhatsApp ખોલી રહ્યા છીએ...", "info");

  const res = await apiPost("whatsapp-booking", payload);

  closeModal("modal-whatsapp-booking");

  if (res && res.whatsapp_url) {
    window.open(res.whatsapp_url, "_blank");
    showToast(state.lang === 'en' ? `Inquiry ${res.inquiry_number} created! Staff ${res.assigned_staff} will contact you.` : `પૂછપરછ ${res.inquiry_number} નોંધાઈ ગઈ! એક્ઝિક્યુટિવ ${res.assigned_staff} સંપર્ક કરશે.`, "success");
  } else {
    // Fallback direct WhatsApp URL
    const ceoPhone = "9426183934";
    const modeStr = fulfillmentMode === "SHOWROOM_VISIT" ? "Showroom Visit" : "Courier Dispatch";
    const waText = `Hello PCWARE! I want to book: ${currentBookingItem.product.name} (₹${currentBookingItem.price.toLocaleString('en-IN')}) - ${modeStr} - Name: ${custName}, Phone: ${custPhone}, City: ${custAddr}`;
    window.open(`https://wa.me/91${ceoPhone}?text=${encodeURIComponent(waText)}`, "_blank");
  }

  // Reload inquiries in ERP if on that tab
  if (state.currentView === "admin") {
    loadInquiriesAndOrders();
  }
}

// ============================================================================
// ENTERPRISE FEATURE 3: GOOGLE GEMINI AI ASSISTANT CHATBOT WIDGET
// ============================================================================
let aiChatHistory = [];

function toggleAIChatWindow() {
  const win = document.getElementById("pcware-ai-chat-window");
  if (!win) return;
  win.classList.toggle("hidden");
  if (!win.classList.contains("hidden")) {
    const input = document.getElementById("ai-user-input");
    if (input) input.focus();
  }
}

function sendAIChip(chipText) {
  const input = document.getElementById("ai-user-input");
  if (!input) return;
  input.value = chipText;
  handleAIChatSubmit(new Event("submit"));
}

async function handleAIChatSubmit(e) {
  if (e) e.preventDefault();
  const input = document.getElementById("ai-user-input");
  const container = document.getElementById("ai-chat-messages");
  if (!input || !container) return;

  const text = input.value.trim();
  if (!text) return;
  input.value = "";

  // Append user message
  const userMsgHtml = `
    <div class="flex gap-2.5 justify-end">
      <div class="bg-indigo-600 text-white p-3 rounded-2xl rounded-tr-none shadow-sm space-y-1 max-w-[85%]">
        <p>${text}</p>
      </div>
    </div>
  `;
  container.insertAdjacentHTML("beforeend", userMsgHtml);
  container.scrollTop = container.scrollHeight;

  // Append Typing Indicator
  const typingId = "ai-typing-" + Date.now();
  const typingHtml = `
    <div id="${typingId}" class="flex gap-2.5">
      <div class="w-7 h-7 rounded-lg bg-indigo-100 text-indigo-700 flex items-center justify-center font-bold shrink-0 text-sm">🤖</div>
      <div class="bg-white p-3 rounded-2xl rounded-tl-none border border-slate-200 shadow-sm text-slate-400 italic text-xs">
        <span class="animate-pulse">PCWARE AI વિચારી રહ્યું છે... Typing...</span>
      </div>
    </div>
  `;
  container.insertAdjacentHTML("beforeend", typingHtml);
  container.scrollTop = container.scrollHeight;

  try {
    const res = await apiPost("gemini/chat", { message: text, history: aiChatHistory });
    const typingEl = document.getElementById(typingId);
    if (typingEl) typingEl.remove();

    const replyText = (res && res.reply) ? res.reply : "હું તમારી પૂછપરછ સમજી રહ્યો છું. વધુ વિગતો માટે +91 94261 83934 પર સંપર્ક કરો.";
    const recs = (res && res.recommendations) ? res.recommendations : [];

    let recsHtml = "";
    if (recs && recs.length > 0) {
      recsHtml = `
        <div class="pt-2 border-t border-slate-100 space-y-1.5 mt-2">
          <p class="font-bold text-[10px] text-slate-500 uppercase tracking-wider">ઉપલબ્ધ સ્ટોક ભલામણો:</p>
          <div class="space-y-1.5">
            ${recs.map(item => `
              <div class="p-2 bg-slate-50 rounded-xl border border-slate-200 flex items-center justify-between gap-2">
                <div class="truncate">
                  <p class="font-bold text-[11px] text-slate-900 truncate">${item.name}</p>
                  <span class="text-[10px] font-black text-brand-600">₹${Number(item.selling_price).toLocaleString('en-IN')}</span>
                </div>
                <button type="button" onclick="openWhatsAppBookingModal(${item.id})" class="bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-[10px] px-2.5 py-1 rounded-lg shrink-0 cursor-pointer">
                  Book
                </button>
              </div>
            `).join("")}
          </div>
        </div>
      `;
    }

    const aiMsgHtml = `
      <div class="flex gap-2.5">
        <div class="w-7 h-7 rounded-lg bg-indigo-100 text-indigo-700 flex items-center justify-center font-bold shrink-0 text-sm">🤖</div>
        <div class="bg-white p-3 rounded-2xl rounded-tl-none border border-slate-200 shadow-sm text-slate-800 space-y-2 max-w-[88%] leading-relaxed">
          <p class="whitespace-pre-line">${replyText}</p>
          ${recsHtml}
        </div>
      </div>
    `;
    container.insertAdjacentHTML("beforeend", aiMsgHtml);
    container.scrollTop = container.scrollHeight;

    aiChatHistory.push({ role: "user", text });
    aiChatHistory.push({ role: "model", text: replyText });
  } catch (err) {
    const typingEl = document.getElementById(typingId);
    if (typingEl) typingEl.remove();
    container.insertAdjacentHTML("beforeend", `
      <div class="flex gap-2.5">
        <div class="w-7 h-7 rounded-lg bg-rose-100 text-rose-700 flex items-center justify-center font-bold shrink-0 text-sm">⚠️</div>
        <div class="bg-white p-3 rounded-2xl rounded-tl-none border border-rose-200 shadow-sm text-rose-800 text-xs">
          ક્ષમા કરશો, AI સર્વિસ સાથે જોડાણ થઈ શક્યું નથી. કૃપા કરીને 9426183934 પર સીધો સંપર્ક કરો.
        </div>
      </div>
    `);
  }
}

// ============================================================================
// ENTERPRISE FEATURE 4: 8-STAFF TEAM MANAGEMENT & DIRECTORY
// ============================================================================
async function loadStaff() {
  const data = await apiGet("staff");
  if (data && Array.isArray(data)) {
    state.staff = data;
  }
  renderStaffTab();
}

function renderStaffTab() {
  const container = document.getElementById("staff-cards-grid");
  if (!container) return;

  const staffList = state.staff || DEFAULT_SEED_DATA.staff || [];

  container.innerHTML = staffList.map(s => `
    <div class="bg-white rounded-2xl border border-slate-200 p-4 shadow-sm hover:shadow-md transition space-y-3">
      <div class="flex items-center justify-between">
        <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-brand-600 to-indigo-700 text-white flex items-center justify-center font-bold text-sm">
          ${s.name.split(" ").map(n => n[0]).join("")}
        </div>
        <span class="text-[10px] font-bold px-2 py-0.5 rounded-full ${s.status === 'ACTIVE' ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-slate-100 text-slate-600'}">
          ${s.status}
        </span>
      </div>

      <div>
        <h4 class="font-bold text-xs text-slate-900">${s.name}</h4>
        <p class="text-[11px] font-semibold text-brand-600 mt-0.5">${s.role}</p>
        <span class="text-[10px] text-slate-400 block">${s.department}</span>
      </div>

      <div class="pt-2 border-t border-slate-100 flex items-center justify-between text-[11px]">
        <span class="text-slate-500">📞 ${s.phone}</span>
        <span class="text-[10px] px-2 py-0.5 bg-amber-50 text-amber-800 rounded font-bold">
          ${s.active_leads_count || 0} લીડ્સ
        </span>
      </div>
    </div>
  `).join("");
}

function openNewStaffModal() {
  openModal("modal-new-staff");
}

async function handleCreateStaffSubmit(e) {
  e.preventDefault();
  const name = document.getElementById("staff-name").value.trim();
  const role = document.getElementById("staff-role").value.trim();
  const dept = document.getElementById("staff-dept").value;
  const phone = document.getElementById("staff-phone").value.trim();
  const email = document.getElementById("staff-email").value.trim();

  const payload = { name, role, department: dept, phone, email, status: "ACTIVE" };
  const res = await apiPost("staff", payload);

  closeModal("modal-new-staff");
  showToast("નવો સ્ટાફ મેમ્બર સફળતાપૂર્વક ઉમેરાયો!");
  loadStaff();
}

// ============================================================================
// ENTERPRISE FEATURE 5: MULTI-GODOWN & INTER-GODOWN STOCK TRANSFERS
// ============================================================================
async function loadWarehousesAndStocks() {
  const whData = await apiGet("warehouses");
  if (whData && Array.isArray(whData)) state.warehouses = whData;

  const stockData = await apiGet("warehouse-stock");
  if (stockData && Array.isArray(stockData)) state.warehouseStocks = stockData;

  const trfData = await apiGet("stock-transfers");
  if (trfData && Array.isArray(trfData)) state.stockTransfers = trfData;

  renderWarehousesTab();
}

function renderWarehousesTab() {
  const showroomEl = document.getElementById("wh-showroom-units");
  const godown1El = document.getElementById("wh-godown1-units");
  const labEl = document.getElementById("wh-lab-units");

  const stocks = state.warehouseStocks || [];
  const showroomTotal = stocks.filter(s => s.warehouse_id === 1).reduce((acc, s) => acc + (s.quantity || 0), 0);
  const godown1Total = stocks.filter(s => s.warehouse_id === 2).reduce((acc, s) => acc + (s.quantity || 0), 0);
  const labTotal = stocks.filter(s => s.warehouse_id === 3).reduce((acc, s) => acc + (s.quantity || 0), 0);

  if (showroomEl) showroomEl.textContent = `કુલ સ્ટોક: ${showroomTotal} નંગ યુનિટ્સ`;
  if (godown1El) godown1El.textContent = `કુલ સ્ટોક: ${godown1Total} નંગ યુનિટ્સ`;
  if (labEl) labEl.textContent = `કુલ સ્ટોક: ${labTotal} નંગ યુનિટ્સ`;

  // Populate product dropdown
  const prodSelect = document.getElementById("transfer-product-id");
  if (prodSelect) {
    prodSelect.innerHTML = (state.products || []).map(p => `
      <option value="${p.id}">${p.name} [કુલ સ્ટોક: ${p.stock_quantity}]</option>
    `).join("");
  }

  // Populate stock transfers history table
  const tbody = document.getElementById("stock-transfers-table-body");
  if (tbody) {
    const trfs = state.stockTransfers || [];
    if (trfs.length === 0) {
      tbody.innerHTML = `<tr><td colspan="8" class="p-4 text-center text-slate-400">હજુ સુધી કોઈ સ્ટોક ટ્રાન્સફર થયેલ નથી.</td></tr>`;
      return;
    }

    tbody.innerHTML = trfs.map(t => `
      <tr class="hover:bg-slate-50 transition border-b border-slate-100">
        <td class="p-3 font-mono font-bold text-slate-900">${t.transfer_no}</td>
        <td class="p-3 font-semibold text-amber-700">${t.from_warehouse_name || 'Godown'}</td>
        <td class="p-3 font-semibold text-brand-700">${t.to_warehouse_name || 'Showroom'}</td>
        <td class="p-3 font-medium text-slate-800">${t.product_name}</td>
        <td class="p-3 text-center font-bold text-slate-900">${t.quantity}</td>
        <td class="p-3 text-slate-600">${t.transferred_by}</td>
        <td class="p-3 text-slate-400 font-mono text-[10px]">${t.created_at ? t.created_at.substring(0, 10) : ''}</td>
        <td class="p-3 text-center">
          <span class="px-2 py-0.5 bg-emerald-50 text-emerald-700 rounded font-bold text-[10px]">
            ${t.status}
          </span>
        </td>
      </tr>
    `).join("");
  }
}

async function handleStockTransferSubmit(e) {
  e.preventDefault();
  const fromWh = document.getElementById("transfer-from-wh").value;
  const toWh = document.getElementById("transfer-to-wh").value;
  const prodId = document.getElementById("transfer-product-id").value;
  const qty = document.getElementById("transfer-qty").value;

  if (fromWh === toWh) {
    showToast("ક્યાંથી અને ક્યાં બંને સરખા ગોડાઉન ન હોઈ શકે!", "error");
    return;
  }

  const payload = {
    from_warehouse_id: fromWh,
    to_warehouse_id: toWh,
    product_id: prodId,
    quantity: qty,
    transferred_by: "Sanjay Rathod (Store Keeper)",
    notes: "Inter-godown transfer logged"
  };

  const res = await apiPost("stock-transfers", payload);
  if (res && res.error) {
    showToast(res.error, "error");
    return;
  }

  showToast(`સ્ટોક ટ્રાન્સફર ${res.transfer_no} સફળતાપૂર્વક પૂર્ણ થયું!`, "success");
  loadWarehousesAndStocks();
}

// ============================================================================
// ENTERPRISE FEATURE 6: INQUIRY REASSIGNMENT & FULFILLMENT MODES
// ============================================================================
async function reassignInquiryStaff(inqId, staffId) {
  await apiPut(`inquiries/${inqId}/assign`, { staff_id: staffId });
  showToast("લીડ સફળતાપૂર્વક સ્ટાફ મેમ્બરને સોંપવામાં આવી.");
  loadInquiriesAndOrders();
}

async function updateInquiryFulfillment(inqId, mode, trackingNo = "") {
  await apiPut(`inquiries/${inqId}/fulfillment`, { fulfillment_mode: mode, delivery_tracking_no: trackingNo });
  showToast("ડિલિવરી પદ્ધતિ અપડેટ થઈ.");
  loadInquiriesAndOrders();
}
'''

# Find insertion before switchAdminTab
admin_tab_anchor = "function switchAdminTab(tabName) {"
idx_admin_tab = code.find(admin_tab_anchor)

if idx_admin_tab != -1 and "function openLaptopUpgradeModal" not in code:
    code = code[:idx_admin_tab] + enterprise_js + "\n" + code[idx_admin_tab:]

# Update switchAdminTab to handle staff and warehouses
old_switch_tabs = 'const tabs = ["overview", "jobsheets", "inventory", "serials", "billing", "amc", "inquiries_orders", "purchase_shortage", "accounts_ledger"];'
new_switch_tabs = 'const tabs = ["overview", "jobsheets", "inventory", "serials", "billing", "amc", "inquiries_orders", "purchase_shortage", "accounts_ledger", "staff", "warehouses"];'
if old_switch_tabs in code:
    code = code.replace(old_switch_tabs, new_switch_tabs)

# Inside switchAdminTab, if tab is staff or warehouses, trigger loading
tab_load_anchor = 'if (tabName === "accounts_ledger") {'
new_tab_loads = '''if (tabName === "staff") {
    loadStaff();
  }
  if (tabName === "warehouses") {
    loadWarehousesAndStocks();
  }
  '''
if tab_load_anchor in code and 'tabName === "staff"' not in code:
    code = code.replace(tab_load_anchor, new_tab_loads + tab_load_anchor)

# Window exports at the bottom
window_exports = '''
// Enterprise Features Window Bindings
window.openLaptopUpgradeModal = openLaptopUpgradeModal;
window.recalculateUpgradePrice = recalculateUpgradePrice;
window.confirmCustomUpgradeWhatsApp = confirmCustomUpgradeWhatsApp;
window.addCustomUpgradeToCart = addCustomUpgradeToCart;

window.openWhatsAppBookingModal = openWhatsAppBookingModal;
window.handleWhatsAppBookingSubmit = handleWhatsAppBookingSubmit;

window.toggleAIChatWindow = toggleAIChatWindow;
window.handleAIChatSubmit = handleAIChatSubmit;
window.sendAIChip = sendAIChip;

window.loadStaff = loadStaff;
window.renderStaffTab = renderStaffTab;
window.openNewStaffModal = openNewStaffModal;
window.handleCreateStaffSubmit = handleCreateStaffSubmit;

window.loadWarehousesAndStocks = loadWarehousesAndStocks;
window.renderWarehousesTab = renderWarehousesTab;
window.handleStockTransferSubmit = handleStockTransferSubmit;

window.reassignInquiryStaff = reassignInquiryStaff;
window.updateInquiryFulfillment = updateInquiryFulfillment;
'''

bottom_anchor = 'console.log("PCWARE App engine loaded with full window bindings.");'
if bottom_anchor in code and "window.openLaptopUpgradeModal" not in code:
    code = code.replace(bottom_anchor, window_exports + "\n" + bottom_anchor)

with open("static/app.js", "w", encoding="utf-8") as f:
    f.write(code)

print("static/app.js successfully updated with all enterprise features!")
