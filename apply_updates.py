import sys

with open('build_app.py', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Update PC Builder section
builder_start = 'async function renderPCBuilder() {'
builder_end = 'function updatePCBuilderSummary() {'

idx_start = text.find(builder_start)
idx_end = text.find(builder_end)

if idx_start == -1 or idx_end == -1:
    print('Error finding PC builder boundaries!', idx_start, idx_end)
    sys.exit(1)

new_builder_code = '''function getActiveCompatibility() {{
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

'''

text = text[:idx_start] + new_builder_code + text[idx_end:]

# 2. Update printGSTInvoice
inv_start = 'async function printGSTInvoice(id) {'
inv_end = 'function showToast('

idx_inv_start = text.find(inv_start)
idx_inv_end = text.find(inv_end)

if idx_inv_start == -1 or idx_inv_end == -1:
    print('Error finding printGSTInvoice boundaries!', idx_inv_start, idx_inv_end)
    sys.exit(1)

new_inv_code = '''async function printGSTInvoice(id) {{
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

'''

text = text[:idx_inv_start] + new_inv_code + text[idx_inv_end:]

# 3. Update printQuotation
qt_start = 'async function printQuotation(quoteId) {'
qt_end = 'async function printPartyLedger(partyId) {'
idx_qt_start = text.find(qt_start)
idx_qt_end = text.find(qt_end)

if idx_qt_start != -1 and idx_qt_end != -1:
    old_qt = text[idx_qt_start:idx_qt_end]
    old_qt = old_qt.replace('TechPulse Computer Hardware & Services', 'PCWARE')
    old_qt = old_qt.replace('TechPulse Computer Hardware', 'PCWARE')
    old_qt = old_qt.replace('TechPulse Hardware & Services', 'PCWARE')
    old_qt = old_qt.replace('શોપ નં. 104-106, શિવમ આર્કેડ, એસ.જી. હાઇવે, અમદાવાદ - 380054', 'Shop No. SF, 47, 48, 49, Suvarnabhumi Complex, Mota Mava, Rajkot - 360005')
    old_qt = old_qt.replace('24AAACT1234F1Z5', '24AABCP1234F1Z5')
    old_qt = old_qt.replace('+91 98250 11223', '+91 94261 83934 / 70167 37271')
    old_qt = old_qt.replace('402983719283', '50200094261839')
    old_qt = old_qt.replace('SBIN0004128', 'HDFC0001234')
    old_qt = old_qt.replace('techpulse@sbi', '9426183934@upi')
    old_qt = old_qt.replace('TechPulse Central Warehouse / Lab', 'PCWARE Central Warehouse / Lab, Suvarnabhumi Complex, Rajkot')
    old_qt = old_qt.replace('અમદાવાદ, ગુજરાત - 380054', 'Rajkot, Gujarat - 360005')
    text = text[:idx_qt_start] + old_qt + text[idx_qt_end:]

# 4. Update printPartyLedger
old_pl_start = 'async function printPartyLedger(partyId) {'
old_pl_end = 'async function openPaymentModal(partyId) {'
idx_pl_start = text.find(old_pl_start)
idx_pl_end = text.find(old_pl_end)
if idx_pl_start != -1 and idx_pl_end != -1:
    old_pl = text[idx_pl_start:idx_pl_end]
    old_pl = old_pl.replace('TechPulse Computer Hardware & Services', 'PCWARE')
    old_pl = old_pl.replace('TechPulse Computer Hardware', 'PCWARE')
    old_pl = old_pl.replace('શોપ નં. 104-106, શિવમ આર્કેડ, એસ.જી. હાઇવે, અમદાવાદ - 380054', 'Shop No. SF, 47, 48, 49, Suvarnabhumi Complex, Mota Mava, Rajkot - 360005')
    old_pl = old_pl.replace('24AAACT1234F1Z5', '24AABCP1234F1Z5')
    old_pl = old_pl.replace('+91 98250 11223', '+91 94261 83934')
    text = text[:idx_pl_start] + old_pl + text[idx_pl_end:]

# 5. Export resetCompatibilityFilters to window
if 'window.resetCompatibilityFilters' not in text:
    text = text.replace('window.resetPCBuilder = resetPCBuilder;', 'window.resetPCBuilder = resetPCBuilder;\nwindow.resetCompatibilityFilters = resetCompatibilityFilters;')

# 6. Any other stray TechPulse strings
text = text.replace('TechPulse Hardware E-Commerce & Service ERP Engine', 'PCWARE Hardware E-Commerce & Service ERP Engine')
text = text.replace('TechPulse App engine loaded with full window bindings.', 'PCWARE App engine loaded with full window bindings.')

with open('build_app.py', 'w', encoding='utf-8') as f:
    f.write(text)

print('apply_updates.py executed successfully!')
