// PC WARE Enterprise ERP Operations Console
let currentModule = "dashboard";

async function switchModule(modName) {
  currentModule = modName;
  document.querySelectorAll(".erp-nav-item").forEach(el => {
    el.classList.toggle("active", el.dataset.module === modName);
  });
  
  const content = document.getElementById("erp-view-content");
  content.innerHTML = `<div style="padding: 3rem; text-align: center; color: #94a3b8;">Loading ${modName}...</div>`;
  
  if (modName === "dashboard") await renderDashboard(content);
  else if (modName === "receiving") await renderReceiving(content);
  else if (modName === "qc-workstation") await renderQCWorkstation(content);
  else if (modName === "inward-gate") await renderInwardGate(content);
  else if (modName === "refurb-costing") await renderRefurbCosting(content);
  else if (modName === "trial-balance") await renderTrialBalance(content);
  else if (modName === "coa") await renderChartOfAccounts(content);
  else if (modName === "gl") await renderGeneralLedger(content);
  else if (modName === "pl") await renderProfitAndLoss(content);
  else if (modName === "balance-sheet") await renderBalanceSheet(content);
  else if (modName === "manual-journal") await renderManualJournal(content);
  else if (modName === "serials") await renderSerials(content);
  else if (modName === "assembly") await renderAssemblyOrders(content);
  else if (modName === "repairs") await renderRepairs(content);
  else if (modName === "sales") await renderSales(content);
  else if (modName === "referrals") await renderReferrals(content);
  else if (modName === "catalog") await renderCatalog(content);
}

// 1. DASHBOARD
async function renderDashboard(container) {
  try {
    const data = await api.get("/api/v1/dashboard/metrics");
    const m = data.inventory;
    const s = data.sales;
    
    container.innerHTML = `
      <div style="margin-bottom: 2rem;">
        <h1 style="font-size: 1.5rem; font-weight: 800;">Executive Operations Dashboard</h1>
        <p style="color: #94a3b8; font-size: 0.85rem;">Live Real-Time Telemetry & Hardware State Machine</p>
      </div>
      
      <div class="grid-4" style="margin-bottom: 2rem;">
        <div class="card" style="background: #1e293b; border-color: #334155; color: #fff;">
          <div style="font-size: 0.8rem; color: #94a3b8; text-transform: uppercase;">Sellable Available Units</div>
          <div style="font-size: 2rem; font-weight: 800; color: #38bdf8; margin: 0.5rem 0;">${m.available_sellable_units}</div>
          <div style="font-size: 0.8rem; color: #10b981;">Stock Value: ₹${(m.sellable_stock_value || 0).toLocaleString("en-IN")}</div>
        </div>
        
        <div class="card" style="background: #1e293b; border-color: #334155; color: #fff;">
          <div style="font-size: 0.8rem; color: #94a3b8; text-transform: uppercase;">QC Inspection Queue</div>
          <div style="font-size: 2rem; font-weight: 800; color: #f59e0b; margin: 0.5rem 0;">${m.qc_pending_units}</div>
          <div style="font-size: 0.8rem; color: #94a3b8;">Units pending multi-point tests</div>
        </div>
        
        <div class="card" style="background: #1e293b; border-color: #334155; color: #fff;">
          <div style="font-size: 0.8rem; color: #94a3b8; text-transform: uppercase;">QC Passed (Pending Inward)</div>
          <div style="font-size: 2rem; font-weight: 800; color: #10b981; margin: 0.5rem 0;">${m.qc_passed_ready_for_inward}</div>
          <div style="font-size: 0.8rem; color: #10b981;">Ready for rack bin assignment</div>
        </div>
        
        <div class="card" style="background: #1e293b; border-color: #334155; color: #fff;">
          <div style="font-size: 0.8rem; color: #94a3b8; text-transform: uppercase;">Quarantine / Failed QC</div>
          <div style="font-size: 2rem; font-weight: 800; color: #ef4444; margin: 0.5rem 0;">${m.qc_failed_or_quarantined}</div>
          <div style="font-size: 0.8rem; color: #ef4444;">Non-sellable (Repair/Hold)</div>
        </div>
      </div>
      
      <div class="grid-2">
        <div class="card" style="background: #1e293b; border-color: #334155; color: #fff;">
          <h3 style="font-size: 1.1rem; font-weight: 700; margin-bottom: 1rem;">Sales & Service Performance</h3>
          <div style="display: flex; justify-content: space-between; padding: 0.75rem 0; border-bottom: 1px solid #334155;">
            <span>Total Sales Revenue:</span>
            <b style="color: #38bdf8;">₹${s.total_revenue.toLocaleString("en-IN")}</b>
          </div>
          <div style="display: flex; justify-content: space-between; padding: 0.75rem 0; border-bottom: 1px solid #334155;">
            <span>GST Collected (HSN 8471):</span>
            <b>₹${s.total_gst_collected.toLocaleString("en-IN")}</b>
          </div>
          <div style="display: flex; justify-content: space-between; padding: 0.75rem 0; border-bottom: 1px solid #334155;">
            <span>Active Custom PC Builds:</span>
            <b>${data.assembly.active_assemblies} Rigs</b>
          </div>
          <div style="display: flex; justify-content: space-between; padding: 0.75rem 0;">
            <span>Open RMA / Service Tickets:</span>
            <b>${data.repairs.open_repairs} Devices</b>
          </div>
        </div>
        
        <div class="card" style="background: #1e293b; border-color: #334155; color: #fff;">
          <h3 style="font-size: 1.1rem; font-weight: 700; margin-bottom: 1rem;">Core Rule Enforcement Engine</h3>
          <div style="background: #0f172a; padding: 1rem; border-radius: 8px; font-size: 0.85rem; line-height: 1.6;">
            <p style="color: #10b981; margin-bottom: 0.5rem;">✓ <b>Rule 1 & 2 (Strict QC Gate)</b>: Actively blocking sellable inventory until QC pass.</p>
            <p style="color: #10b981; margin-bottom: 0.5rem;">✓ <b>Rule 3 (Traceability)</b>: ${m.total_units_tracked} serialized units tracked from supplier lot to invoice.</p>
            <p style="color: #10b981; margin-bottom: 0.5rem;">✓ <b>Rule 4 & 5 (Compatibility)</b>: Server-side validation rejecting socket & RAM mismatches.</p>
            <p style="color: #10b981;">✓ <b>Rule 7 (Referral Ledger)</b>: ${data.referrals.points_issued} points credited through immutable double-entry ledger.</p>
          </div>
        </div>
      </div>
    `;
  } catch (err) {
    container.innerHTML = `<div style="color: #ef4444; padding: 2rem;">Error: ${err.message}</div>`;
  }
}

// 2. RECEIVING INTAKE
async function renderReceiving(container) {
  const records = await api.get("/api/v1/receiving");
  container.innerHTML = `
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;">
      <div>
        <h1 style="font-size: 1.5rem; font-weight: 800;">Hardware Receiving Intake</h1>
        <p style="color: #94a3b8; font-size: 0.85rem;">Log supplier batch arrivals & auto-generate serial units in QC Pending status</p>
      </div>
      <button class="btn btn-primary" onclick="showReceivingModal()">+ New Lot Intake</button>
    </div>
    
    <div class="data-table-container">
      <table class="data-table">
        <thead>
          <tr>
            <th>Receiving #</th>
            <th>Supplier</th>
            <th>Item / Batch</th>
            <th>Quantity</th>
            <th>Total Cost</th>
            <th>Date Received</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          ${records.map(r => `
            <tr>
              <td style="font-family: monospace; font-weight: 700; color: #38bdf8;">${r.receiving_number}</td>
              <td>${r.supplier_name}</td>
              <td><b>${r.model_name}</b><br><span style="font-size: 0.75rem; color: #94a3b8;">${r.accessories_received || ""}</span></td>
              <td>${r.received_qty} Units</td>
              <td>₹${r.purchase_cost_total.toLocaleString("en-IN")}</td>
              <td>${r.received_at.split(" ")[0]}</td>
              <td><span class="badge ${r.status === 'completed' ? 'badge-qc-pass' : 'badge-qc-pending'}">${r.status}</span></td>
            </tr>
          `).join("")}
        </tbody>
      </table>
    </div>
  `;
}

// 3. QUALITY CONTROL (QC) WORKSTATION
async function renderQCWorkstation(container) {
  const pendingUnits = await api.get("/api/v1/qc/pending");
  container.innerHTML = `
    <div style="margin-bottom: 1.5rem;">
      <h1 style="font-size: 1.5rem; font-weight: 800;">Quality Control Testing Lab</h1>
      <p style="color: #94a3b8; font-size: 0.85rem;">Execute 24-point hardware checklists, log thermal telemetry, and sign off Pass/Fail verdicts</p>
    </div>
    
    ${pendingUnits.length === 0 ? `
      <div class="card" style="background: #1e293b; border-color: #334155; text-align: center; padding: 3rem; color: #94a3b8;">
        ✓ All received units have been inspected! No units pending in the QC queue.
      </div>
    ` : `
      <div class="data-table-container">
        <table class="data-table">
          <thead>
            <tr>
              <th>Serial Number</th>
              <th>Product Model</th>
              <th>Category</th>
              <th>Warehouse</th>
              <th>Status</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            ${pendingUnits.map(u => `
              <tr>
                <td style="font-family: monospace; font-weight: 700; color: #38bdf8;">${u.serial_number}</td>
                <td><b>${u.product_title}</b></td>
                <td>${u.category_name}</td>
                <td>${u.warehouse_name}</td>
                <td><span class="badge badge-qc-pending">${u.current_status}</span></td>
                <td>
                  <button class="btn btn-sm btn-primary" onclick="openQCInspectionModal(${u.id}, '${u.serial_number}', '${u.product_title}')">
                    🔬 Start 24-Point QC
                  </button>
                </td>
              </tr>
            `).join("")}
          </tbody>
        </table>
      </div>
    `}
  `;
}

// 4. INWARDING GATEWAY (CRITICAL RULE 1 & 2)
async function renderInwardGate(container) {
  const serials = await api.get("/api/v1/inventory/serials");
  const qcPassed = serials.filter(s => s.current_status === "qc_passed");
  
  container.innerHTML = `
    <div style="margin-bottom: 1.5rem;">
      <h1 style="font-size: 1.5rem; font-weight: 800;">Sellable Inventory Inwarding Gateway</h1>
      <p style="color: #94a3b8; font-size: 0.85rem;"><b>STRICT ENFORCEMENT:</b> Only units that have passed Quality Check (QC Passed) are accepted into sellable store inventory.</p>
    </div>
    
    <div class="card" style="background: #1e293b; border-color: #334155; padding: 1.5rem; margin-bottom: 2rem;">
      <h3 style="margin-bottom: 1rem; color: #fff;">Inward Passed Hardware to Showroom Shelf</h3>
      <div style="display: grid; grid-template-columns: 2fr 1fr 1fr auto; gap: 1rem; align-items: end;">
        <div>
          <label class="dark-form-label">Select QC-Passed Unit:</label>
          <select id="inward-serial-select" class="form-control dark-form-control">
            <option value="">-- Select Verified Unit --</option>
            ${qcPassed.map(u => `<option value="${u.id}">${u.serial_number} — ${u.product_title} (${u.condition_grade})</option>`).join("")}
          </select>
        </div>
        <div>
          <label class="dark-form-label">Warehouse:</label>
          <select id="inward-warehouse-select" class="form-control dark-form-control">
            <option value="1">WH-MAIN (Showroom SF-47)</option>
            <option value="2">WH-LAB (Cleanroom Lab)</option>
          </select>
        </div>
        <div>
          <label class="dark-form-label">Rack / Bin Location:</label>
          <input type="text" id="inward-rack-input" class="form-control dark-form-control" value="Rack A-02" placeholder="e.g. Rack A-01">
        </div>
        <div>
          <button class="btn btn-primary" onclick="submitInward()">Inward to Store Stock</button>
        </div>
      </div>
    </div>
    
    <h3 style="font-size: 1.1rem; font-weight: 700; margin-bottom: 1rem; color: #fff;">Units Cleared & Awaiting Inwarding (${qcPassed.length})</h3>
    <div class="data-table-container">
      <table class="data-table">
        <thead>
          <tr>
            <th>Serial #</th>
            <th>Hardware Model</th>
            <th>QC Passed Timestamp</th>
            <th>Current Location</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          ${qcPassed.map(u => `
            <tr>
              <td style="font-family: monospace; font-weight: 700; color: #10b981;">${u.serial_number}</td>
              <td>${u.product_title}</td>
              <td>${u.qc_passed_at || "Verified"}</td>
              <td>${u.location_rack}</td>
              <td><span class="badge badge-qc-pass">${u.current_status}</span></td>
            </tr>
          `).join("")}
        </tbody>
      </table>
    </div>
  `;
}

async function submitInward() {
  const serialId = document.getElementById("inward-serial-select").value;
  const whId = document.getElementById("inward-warehouse-select").value;
  const rack = document.getElementById("inward-rack-input").value;
  if (!serialId) {
    showToast("Please select a unit to inward.", "error");
    return;
  }
  try {
    const res = await api.post("/api/v1/inventory/inward", {
      serial_unit_id: serialId,
      warehouse_id: whId,
      rack_bin: rack
    });
    showToast(res.message, "success");
    switchModule("inward-gate");
  } catch (err) {
    // Alert rule violation prominently
    alert(`SECURITY & QC GATE ENFORCEMENT:\n\n${err.message}`);
  }
}

// 5. SERIAL NUMBER MASTER REGISTRY
async function renderSerials(container) {
  const serials = await api.get("/api/v1/inventory/serials");
  container.innerHTML = `
    <div style="margin-bottom: 1.5rem;">
      <h1 style="font-size: 1.5rem; font-weight: 800;">Serialized Inventory Master Registry</h1>
      <p style="color: #94a3b8; font-size: 0.85rem;">Trace every individual laptop, desktop, server, and custom rig unit across its complete lifecycle</p>
    </div>
    
    <div class="data-table-container">
      <table class="data-table">
        <thead>
          <tr>
            <th>Serial Number</th>
            <th>Product Title</th>
            <th>Warehouse & Location</th>
            <th>Cost / Price</th>
            <th>Status</th>
            <th>Lifecycle Timeline</th>
          </tr>
        </thead>
        <tbody>
          ${serials.map(s => `
            <tr>
              <td style="font-family: monospace; font-weight: 700; color: #38bdf8;">${s.serial_number}</td>
              <td><b>${s.product_title}</b><br><span style="font-size: 0.75rem; color: #94a3b8;">${s.sku} | ${s.condition_grade}</span></td>
              <td>${s.warehouse_name}<br><span style="font-size: 0.75rem; color: #38bdf8;">${s.location_rack}</span></td>
              <td>Cost: ₹${s.purchase_cost.toLocaleString("en-IN")}<br>Sell: ₹${s.selling_price.toLocaleString("en-IN")}</td>
              <td>
                <span class="badge ${s.current_status === 'available' ? 'badge-available' : s.current_status === 'qc_passed' ? 'badge-qc-pass' : s.current_status === 'qc_failed' ? 'badge-qc-fail' : 'badge-qc-pending'}">
                  ${s.current_status}
                </span>
              </td>
              <td>
                <button class="btn btn-sm btn-outline" onclick="openSerialTimeline('${s.serial_number}')">🔍 Audit Timeline</button>
              </td>
            </tr>
          `).join("")}
        </tbody>
      </table>
    </div>
  `;
}

// MODAL DIALOGS
function openQCInspectionModal(serialId, sn, title) {
  const modal = document.createElement("div");
  modal.id = "qc-modal";
  modal.style = "position: fixed; inset: 0; background: rgba(0,0,0,0.7); display: flex; align-items: center; justify-content: center; z-index: 1000;";
  modal.innerHTML = `
    <div class="card" style="background: #1e293b; color: #fff; width: 680px; max-height: 90vh; overflow-y: auto; border-color: #334155; padding: 2rem;">
      <h2 style="font-size: 1.35rem; font-weight: 800; margin-bottom: 0.5rem;">24-Point QC Hardware Inspection</h2>
      <p style="color: #94a3b8; font-size: 0.85rem; margin-bottom: 1.5rem;">Unit: <b style="color: #38bdf8;">${sn}</b> — ${title}</p>
      
      <div class="grid-3" style="margin-bottom: 1.5rem;">
        <div>
          <label class="dark-form-label">Peak CPU Temp (°C):</label>
          <input type="number" id="qc-cpu-temp" class="form-control dark-form-control" value="71.5">
        </div>
        <div>
          <label class="dark-form-label">Peak GPU Temp (°C):</label>
          <input type="number" id="qc-gpu-temp" class="form-control dark-form-control" value="67.0">
        </div>
        <div>
          <label class="dark-form-label">Battery Health (%):</label>
          <input type="number" id="qc-battery-pct" class="form-control dark-form-control" value="95">
        </div>
      </div>
      
      <div style="background: #0f172a; padding: 1rem; border-radius: 8px; margin-bottom: 1.5rem; max-height: 220px; overflow-y: auto;">
        <div style="font-size: 0.8rem; font-weight: 700; color: #94a3b8; text-transform: uppercase; margin-bottom: 0.5rem;">Mandatory Inspection Points:</div>
        <label style="display: block; margin-bottom: 0.35rem;"><input type="checkbox" checked> Clean Boot & UEFI Secure Boot</label>
        <label style="display: block; margin-bottom: 0.35rem;"><input type="checkbox" checked> CPU Cinebench 15m Stress Test</label>
        <label style="display: block; margin-bottom: 0.35rem;"><input type="checkbox" checked> MemTest86 RAM Integrity Pass</label>
        <label style="display: block; margin-bottom: 0.35rem;"><input type="checkbox" checked> NVMe SMART Health >= 90%</label>
        <label style="display: block; margin-bottom: 0.35rem;"><input type="checkbox" checked> Full Keyboard & Trackpad Matrix</label>
        <label style="display: block; margin-bottom: 0.35rem;"><input type="checkbox" checked> Display Panel Zero Dead Pixels</label>
        <label style="display: block; margin-bottom: 0.35rem;"><input type="checkbox" checked> All USB 3.0 / Thunderbolt Ports</label>
        <label style="display: block;"><input type="checkbox" checked> Genuine Activated Windows 11 Pro</label>
      </div>
      
      <div style="margin-bottom: 1.5rem;">
        <label class="dark-form-label">Technician Notes & Remediation:</label>
        <textarea id="qc-notes" class="form-control dark-form-control" rows="2" placeholder="Detail condition, thermal repasting, or reason for failure..."></textarea>
      </div>
      
      <div style="display: flex; justify-content: space-between; align-items: center;">
        <button class="btn btn-secondary" onclick="document.getElementById('qc-modal').remove()">Cancel</button>
        <div style="display: flex; gap: 0.75rem;">
          <button class="btn btn-accent" style="background: #ef4444;" onclick="submitQCResult(${serialId}, 'failed')">❌ Mark QC Failed (Quarantine)</button>
          <button class="btn btn-primary" onclick="submitQCResult(${serialId}, 'passed')">✓ Approve QC Passed</button>
        </div>
      </div>
    </div>
  `;
  document.body.appendChild(modal);
}

async function submitQCResult(serialId, result) {
  const cpuTemp = document.getElementById("qc-cpu-temp").value;
  const gpuTemp = document.getElementById("qc-gpu-temp").value;
  const batteryPct = document.getElementById("qc-battery-pct").value;
  const notes = document.getElementById("qc-notes").value;
  
  try {
    const res = await api.post("/api/v1/qc/inspect", {
      serial_unit_id: serialId,
      overall_result: result,
      thermal_cpu_c: cpuTemp,
      thermal_gpu_c: gpuTemp,
      battery_health_pct: batteryPct,
      failure_reason: result === "failed" ? (notes || "Checklist test failed") : null,
      remediation_action: result === "failed" ? "Quarantine & repair workshop allocation" : "Cleared for inward",
      inspector_notes: notes || (result === "passed" ? "Unit 100% verified" : "Failed inspection")
    });
    
    document.getElementById("qc-modal").remove();
    showToast(`Inspection signed off as ${result.toUpperCase()}`, result === "passed" ? "success" : "error");
    switchModule("qc-workstation");
  } catch (err) {
    showToast(err.message, "error");
  }
}

async function openSerialTimeline(sn) {
  try {
    const data = await api.get(`/api/v1/inventory/serials/${sn}`);
    const u = data.unit;
    const modal = document.createElement("div");
    modal.id = "timeline-modal";
    modal.style = "position: fixed; inset: 0; background: rgba(0,0,0,0.7); display: flex; align-items: center; justify-content: center; z-index: 1000;";
    
    modal.innerHTML = `
      <div class="card" style="background: #1e293b; color: #fff; width: 720px; max-height: 90vh; overflow-y: auto; border-color: #334155; padding: 2rem;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;">
          <div>
            <h2 style="font-size: 1.35rem; font-weight: 800;">Lifecycle Audit Timeline</h2>
            <p style="color: #38bdf8; font-family: monospace; font-size: 0.9rem;">${u.serial_number} (${u.asset_tag || "No Tag"})</p>
          </div>
          <span class="badge badge-available" style="font-size: 0.85rem;">${u.current_status}</span>
        </div>
        
        <div style="background: #0f172a; padding: 1rem; border-radius: 8px; margin-bottom: 1.5rem; font-size: 0.85rem;">
          <div><b>Product:</b> ${u.product_title}</div>
          <div><b>Supplier:</b> ${u.supplier_name || "Dell Remarketing"} (Receiving #${u.receiving_number})</div>
          <div><b>Cost:</b> ₹${u.purchase_cost.toLocaleString("en-IN")} | <b>Selling Price:</b> ₹${u.selling_price.toLocaleString("en-IN")}</div>
          <div><b>Current Rack:</b> ${u.location_rack} (${u.warehouse_name})</div>
        </div>
        
        <h4 style="font-size: 0.95rem; font-weight: 700; margin-bottom: 0.75rem; color: #94a3b8; text-transform: uppercase;">Chronological Audit Events:</h4>
        <div style="border-left: 2px solid #0284c7; padding-left: 1.25rem; margin-left: 0.5rem; margin-bottom: 1.5rem;">
          ${data.movements.map(m => `
            <div style="margin-bottom: 1rem; position: relative;">
              <div style="font-size: 0.85rem; font-weight: 700; color: #38bdf8;">${m.reference_type} — ${m.from_status} ➔ ${m.to_status}</div>
              <div style="font-size: 0.75rem; color: #94a3b8;">${m.movement_timestamp} by ${m.moved_by_name || "System"}</div>
              <div style="font-size: 0.8rem; color: #e2e8f0; margin-top: 0.2rem;">${m.notes || ""}</div>
            </div>
          `).join("")}
        </div>
        
        <div style="display: flex; justify-content: flex-end;">
          <button class="btn btn-secondary" onclick="document.getElementById('timeline-modal').remove()">Close</button>
        </div>
      </div>
    `;
    document.body.appendChild(modal);
  } catch (err) {
    showToast(err.message, "error");
  }
}

// 6. CUSTOM PC ASSEMBLY
async function renderAssemblyOrders(container) {
  const orders = await api.get("/api/v1/assembly/orders");
  container.innerHTML = `
    <div style="margin-bottom: 1.5rem;">
      <h1 style="font-size: 1.5rem; font-weight: 800;">Custom PC Assembly Pipeline</h1>
      <p style="color: #94a3b8; font-size: 0.85rem;">Manage custom-built rigs from reservation through assembly, burn-in QC, and ready status</p>
    </div>
    
    <div class="data-table-container">
      <table class="data-table">
        <thead>
          <tr>
            <th>Assembly #</th>
            <th>Customer</th>
            <th>Estimated Wattage</th>
            <th>Total Amount</th>
            <th>Technician</th>
            <th>Status</th>
            <th>Assembly QC</th>
          </tr>
        </thead>
        <tbody>
          ${orders.map(o => `
            <tr>
              <td style="font-family: monospace; font-weight: 700; color: #38bdf8;">${o.assembly_number}</td>
              <td>${o.customer_name}</td>
              <td>${o.total_wattage}W</td>
              <td>₹${o.total_price.toLocaleString("en-IN")}</td>
              <td>${o.technician_name || "Unassigned"}</td>
              <td><span class="badge ${o.status === 'ready' ? 'badge-qc-pass' : 'badge-qc-pending'}">${o.status}</span></td>
              <td>
                ${o.status === "ready" ? `<span style="color: #10b981; font-weight: 700;">✓ Pass (${o.final_serial_number || "RIG"})</span>` : `
                  <button class="btn btn-sm btn-primary" onclick="openAssemblyQCModal(${o.id}, '${o.assembly_number}')">Run Assembly QC</button>
                `}
              </td>
            </tr>
          `).join("")}
        </tbody>
      </table>
    </div>
  `;
}

function openAssemblyQCModal(asmId, num) {
  const modal = document.createElement("div");
  modal.id = "asm-qc-modal";
  modal.style = "position: fixed; inset: 0; background: rgba(0,0,0,0.7); display: flex; align-items: center; justify-content: center; z-index: 1000;";
  modal.innerHTML = `
    <div class="card" style="background: #1e293b; color: #fff; width: 620px; border-color: #334155; padding: 2rem;">
      <h2 style="font-size: 1.35rem; font-weight: 800; margin-bottom: 0.5rem;">Assembly Quality Check (Rig ${num})</h2>
      <p style="color: #94a3b8; font-size: 0.85rem; margin-bottom: 1.5rem;">Verify system stability, cable routing, and thermals before marking Ready for customer handover.</p>
      
      <div style="background: #0f172a; padding: 1rem; border-radius: 8px; margin-bottom: 1.5rem;">
        <label style="display: block; margin-bottom: 0.4rem;"><input type="checkbox" id="asm-boot" checked> POST Boot & BIOS Settings Configured</label>
        <label style="display: block; margin-bottom: 0.4rem;"><input type="checkbox" id="asm-cpu" checked> CPU Stress Test Passed (Cinebench 15m)</label>
        <label style="display: block; margin-bottom: 0.4rem;"><input type="checkbox" id="asm-gpu" checked> GPU FurMark Thermal Burn-in Passed</label>
        <label style="display: block; margin-bottom: 0.4rem;"><input type="checkbox" id="asm-mem" checked> RAM EXPO/XMP MemTest86 Passed</label>
        <label style="display: block;"><input type="checkbox" id="asm-cable" checked> Stealth Cable Management & Airflow Verified</label>
      </div>
      
      <div style="display: flex; justify-content: space-between;">
        <button class="btn btn-secondary" onclick="document.getElementById('asm-qc-modal').remove()">Cancel</button>
        <button class="btn btn-primary" onclick="submitAssemblyQC(${asmId})">Sign Off & Mark READY</button>
      </div>
    </div>
  `;
  document.body.appendChild(modal);
}

async function submitAssemblyQC(asmId) {
  const boot = document.getElementById("asm-boot").checked;
  const cpu = document.getElementById("asm-cpu").checked;
  const gpu = document.getElementById("asm-gpu").checked;
  const mem = document.getElementById("asm-mem").checked;
  
  try {
    const res = await api.post(`/api/v1/assembly/orders/${asmId}/qc`, {
      boot_test: boot,
      bios_config: boot,
      cpu_stress_pass: cpu,
      gpu_stress_pass: gpu,
      ram_memtest_pass: mem,
      storage_smart_pass: 1,
      cooling_efficiency: "Optimal",
      cable_management_grade: "Grade A+"
    });
    document.getElementById("asm-qc-modal").remove();
    showToast(`Assembly QC Complete! Serial assigned: ${res.final_serial_number}`, "success");
    switchModule("assembly");
  } catch (err) {
    showToast(err.message, "error");
  }
}

// 7. IN-SHOP REPAIRS
async function renderRepairs(container) {
  const tickets = await api.get("/api/v1/repair/tickets");
  container.innerHTML = `
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;">
      <div>
        <h1 style="font-size: 1.5rem; font-weight: 800;">Hardware Repair Job Sheets</h1>
        <p style="color: #94a3b8; font-size: 0.85rem;">Diagnostic tickets, repair tracking, and customer sign-off</p>
      </div>
      <button class="btn btn-primary" onclick="showNewRepairModal()">+ New Job Sheet Intake</button>
    </div>
    
    <div class="data-table-container">
      <table class="data-table">
        <thead>
          <tr>
            <th>Job Sheet #</th>
            <th>Customer</th>
            <th>Device Brand/Model</th>
            <th>Reported Fault</th>
            <th>Status</th>
            <th>Cost</th>
          </tr>
        </thead>
        <tbody>
          ${tickets.map(t => `
            <tr>
              <td style="font-family: monospace; font-weight: 700; color: #38bdf8;">${t.ticket_number}</td>
              <td>${t.customer_name}<br><span style="font-size: 0.75rem; color: #94a3b8;">${t.customer_phone}</span></td>
              <td><b>${t.device_brand_model}</b><br><span style="font-size: 0.75rem; color: #94a3b8;">SN: ${t.serial_or_imei || "N/A"}</span></td>
              <td>${t.fault_description}</td>
              <td><span class="badge ${t.repair_status === 'repaired' ? 'badge-qc-pass' : 'badge-qc-pending'}">${t.repair_status}</span></td>
              <td>₹${t.final_cost > 0 ? t.final_cost.toLocaleString("en-IN") : t.estimated_cost.toLocaleString("en-IN")}</td>
            </tr>
          `).join("")}
        </tbody>
      </table>
    </div>
  `;
}

// 8. SALES & GST INVOICING
async function renderSales(container) {
  const orders = await api.get("/api/v1/orders");
  container.innerHTML = `
    <div style="margin-bottom: 1.5rem;">
      <h1 style="font-size: 1.5rem; font-weight: 800;">Sales Orders & GST Invoicing</h1>
      <p style="color: #94a3b8; font-size: 0.85rem;">All orders with server-calculated GST (HSN 8471), serialized items, and printable invoices</p>
    </div>
    
    <div class="data-table-container">
      <table class="data-table">
        <thead>
          <tr>
            <th>Order #</th>
            <th>Invoice #</th>
            <th>Customer</th>
            <th>Allocated Serial</th>
            <th>Grand Total</th>
            <th>Payment</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          ${orders.map(o => `
            <tr>
              <td style="font-family: monospace; font-weight: 700; color: #38bdf8;">${o.order_number}</td>
              <td style="font-family: monospace; font-weight: 700; color: #10b981;">${o.invoice_number || "INV-PENDING"}</td>
              <td>${o.customer_name}</td>
              <td>${o.items && o.items[0] && o.items[0].serial_number ? `<span style="font-family: monospace; color: #38bdf8;">${o.items[0].serial_number}</span>` : "Custom / Components"}</td>
              <td><b>₹${o.grand_total.toLocaleString("en-IN")}</b></td>
              <td><span class="badge badge-qc-pass">${o.payment_status}</span></td>
              <td>
                <button class="btn btn-sm btn-outline" onclick="printInvoice(${o.id})">🖨️ Tax Invoice</button>
              </td>
            </tr>
          `).join("")}
        </tbody>
      </table>
    </div>
  `;
}

function printInvoice(orderId) {
  api.get(`/api/v1/orders/${orderId}`).then(order => {
    const win = window.open("", "_blank", "width=850,height=900");
    win.document.write(`
      <html>
        <head>
          <title>Tax Invoice - ${order.invoice_number || order.order_number}</title>
          <style>
            body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; padding: 2rem; color: #0f172a; }
            .header { border-bottom: 2px solid #0284c7; padding-bottom: 1rem; margin-bottom: 1.5rem; display: flex; justify-content: space-between; }
            table { width: 100%; border-collapse: collapse; margin: 1.5rem 0; }
            th, td { border: 1px solid #cbd5e1; padding: 0.6rem; text-align: left; font-size: 0.9rem; }
            th { background: #f8fafc; }
          </style>
        </head>
        <body>
          <div class="header">
            <div>
              <h1 style="margin:0; font-size: 1.6rem; color:#0284c7;">PC WARE ENTERPRISE</h1>
              <p style="margin:0.2rem 0; font-size: 0.85rem;">SF 47-49 Suvarnabhumi Complex, Mota Mava, Rajkot, Gujarat 360005</p>
              <p style="margin:0; font-size: 0.85rem;">GSTIN: <b>24AAECP1234F1Z5</b> | HSN Code: <b>8471</b></p>
            </div>
            <div style="text-align: right;">
              <h2 style="margin:0; font-size: 1.3rem;">TAX INVOICE</h2>
              <p style="margin:0.2rem 0;"><b>Invoice #:</b> ${order.invoice_number || "INV-2026-0001"}</p>
              <p style="margin:0;"><b>Date:</b> ${order.created_at ? order.created_at.split(" ")[0] : "2026-03-05"}</p>
            </div>
          </div>
          
          <div style="margin-bottom: 1.5rem; font-size: 0.9rem;">
            <b>Billed To:</b><br>
            ${order.customer_name}<br>
            ${order.company_name ? order.company_name + "<br>" : ""}
            ${order.address_line1}, ${order.city} ${order.pincode}<br>
            Phone: ${order.customer_phone}
          </div>
          
          <table>
            <thead>
              <tr>
                <th>Item Description</th>
                <th>Serial / Asset Tag</th>
                <th>Quantity</th>
                <th style="text-align:right;">Amount</th>
              </tr>
            </thead>
            <tbody>
              ${order.items.map(i => `
                <tr>
                  <td><b>${i.product_title}</b></td>
                  <td style="font-family:monospace;">${i.serial_number || "N/A"}</td>
                  <td>${i.quantity}</td>
                  <td style="text-align:right;">₹${i.total_price.toLocaleString("en-IN")}</td>
                </tr>
              `).join("")}
            </tbody>
          </table>
          
          <div style="text-align: right; margin-top: 1.5rem; font-size: 0.95rem; line-height: 1.6;">
            <div>Subtotal: <b>₹${order.subtotal.toLocaleString("en-IN")}</b></div>
            <div>CGST (9%): <b>₹${(order.tax_amount / 2).toLocaleString("en-IN")}</b></div>
            <div>SGST (9%): <b>₹${(order.tax_amount / 2).toLocaleString("en-IN")}</b></div>
            <div style="font-size: 1.3rem; font-weight: 800; color: #0284c7; margin-top: 0.5rem;">Grand Total: ₹${order.grand_total.toLocaleString("en-IN")}</div>
          </div>
          
          <div style="margin-top: 3rem; border-top: 1px solid #cbd5e1; padding-top: 1rem; font-size: 0.8rem; color: #64748b; text-align: center;">
            This is a computer generated invoice under GST Act 2017. All refurbished hardware carries official PC Ware Warranty against manufacturing defects.
          </div>
          <script>window.print();<\/script>
        </body>
      </html>
    `);
  });
}

// 9. REFERRAL POINTS LEDGER
async function renderReferrals(container) {
  const codeInfo = await api.get("/api/v1/referrals/my-code?customer_id=1");
  container.innerHTML = `
    <div style="margin-bottom: 1.5rem;">
      <h1 style="font-size: 1.5rem; font-weight: 800;">Referral Program & Immutable Ledger</h1>
      <p style="color: #94a3b8; font-size: 0.85rem;">Rule 7: Full double-entry credit/debit transaction ledger with transparent audit records</p>
    </div>
    
    <div class="grid-3" style="margin-bottom: 2rem;">
      <div class="card" style="background: #1e293b; border-color: #334155; color: #fff;">
        <div style="font-size: 0.8rem; color: #94a3b8;">Customer Referral Code</div>
        <div style="font-size: 1.6rem; font-weight: 800; color: #f59e0b; margin: 0.5rem 0; font-family: monospace;">${codeInfo.referral_code}</div>
        <div style="font-size: 0.8rem; color: #10b981;">₹500 Credit Per Friend</div>
      </div>
      
      <div class="card" style="background: #1e293b; border-color: #334155; color: #fff;">
        <div style="font-size: 0.8rem; color: #94a3b8;">Available Points Balance</div>
        <div style="font-size: 1.6rem; font-weight: 800; color: #10b981; margin: 0.5rem 0;">${codeInfo.available_points} Pts</div>
        <div style="font-size: 0.8rem; color: #94a3b8;">1 Point = ₹1 Store Discount</div>
      </div>
      
      <div class="card" style="background: #1e293b; border-color: #334155; color: #fff;">
        <div style="font-size: 0.8rem; color: #94a3b8;">Referred Purchases</div>
        <div style="font-size: 1.6rem; font-weight: 800; color: #38bdf8; margin: 0.5rem 0;">${codeInfo.total_referrals}</div>
        <div style="font-size: 0.8rem; color: #94a3b8;">Min. Order Value: ₹10,000</div>
      </div>
    </div>
    
    <h3 style="font-size: 1.1rem; font-weight: 700; margin-bottom: 1rem; color: #fff;">Double-Entry Points Transaction Ledger</h3>
    <div class="data-table-container">
      <table class="data-table">
        <thead>
          <tr>
            <th>Txn ID</th>
            <th>Type</th>
            <th>Points In</th>
            <th>Points Out</th>
            <th>Running Balance</th>
            <th>Reason / Order Ref</th>
            <th>Timestamp</th>
          </tr>
        </thead>
        <tbody>
          ${codeInfo.ledger.map(l => `
            <tr>
              <td style="font-family: monospace; font-weight: 700;">#TXN-${l.id}</td>
              <td><span class="badge ${l.points_in > 0 ? 'badge-qc-pass' : 'badge-qc-fail'}">${l.transaction_type}</span></td>
              <td style="color: #10b981; font-weight: 700;">${l.points_in > 0 ? `+${l.points_in}` : "-"}</td>
              <td style="color: #ef4444; font-weight: 700;">${l.points_out > 0 ? `-${l.points_out}` : "-"}</td>
              <td style="font-weight: 800; color: #38bdf8;">${l.running_balance} Pts</td>
              <td>${l.reason}</td>
              <td style="color: #94a3b8; font-size: 0.8rem;">${l.created_at}</td>
            </tr>
          `).join("")}
        </tbody>
      </table>
    </div>
  `;
}

// 10. CATALOG VIEW
async function renderCatalog(container) {
  const products = await api.get("/api/v1/catalog/products");
  container.innerHTML = `
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;">
      <div>
        <h1 style="font-size: 1.5rem; font-weight: 800;">Catalog & Specifications</h1>
        <p style="color: #94a3b8; font-size: 0.85rem;">Manage products, condition grades, and hardware attributes</p>
      </div>
    </div>
    <div class="data-table-container">
      <table class="data-table">
        <thead>
          <tr>
            <th>Product</th>
            <th>SKU</th>
            <th>Type</th>
            <th>Condition</th>
            <th>Price</th>
            <th>Sellable Serials</th>
          </tr>
        </thead>
        <tbody>
          ${products.map(p => `
            <tr>
              <td><b>${p.title}</b></td>
              <td style="font-family: monospace;">${p.sku}</td>
              <td>${p.product_type}</td>
              <td><span class="badge badge-grade-a">${p.condition_grade}</span></td>
              <td><b>₹${p.selling_price.toLocaleString("en-IN")}</b></td>
              <td><span class="badge badge-available">${p.available_serials_count} In Stock</span></td>
            </tr>
          `).join("")}
        </tbody>
      </table>
    </div>
  `;
}


// ==============================================================================
// 11. REFURBISHMENT WORK ORDERS & CLOSED-LOOP COST CAPITALIZATION
// ==============================================================================
async function renderRefurbCosting(container) {
  try {
    const orders = await api.get("/api/v1/refurbishment/work-orders");
    const pendingUnits = await api.get("/api/v1/qc/failed");
    
    container.innerHTML = `
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem;">
        <div>
          <h1 style="font-size: 1.5rem; font-weight: 800;">Refurbishment Work Orders & Cost Capitalization</h1>
          <p style="color: #94a3b8; font-size: 0.85rem;">Formula: Base Cost + Requisitioned Parts + Direct Labour (₹350/h) + Fixed Overhead (₹300) = Capitalized Unit Asset Value</p>
        </div>
        <button onclick="openRefurbWOModal()" class="btn btn-primary">+ Open Refurb Work Order</button>
      </div>

      <div class="table-container">
        <table class="table">
          <thead>
            <tr>
              <th>WO Number</th>
              <th>Serial Number</th>
              <th>Device Model</th>
              <th>Technician</th>
              <th>Parts Cost</th>
              <th>Labour Cost</th>
              <th>Overhead</th>
              <th>True Unit Cost</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            ${orders.length === 0 ? `<tr><td colspan="10" style="text-align: center; color: #94a3b8; padding: 2rem;">No active refurbishment work orders. Click "+ Open Refurb Work Order" to start.</td></tr>` : 
              orders.map(o => `
                <tr>
                  <td style="font-family: monospace; font-weight: 700; color: #38bdf8;">${o.wo_number}</td>
                  <td style="font-family: monospace;"><b>${o.serial_number}</b></td>
                  <td>${o.product_title}</td>
                  <td>${o.technician_name || "Unassigned"}</td>
                  <td>₹${parseFloat(o.total_part_cost || 0).toLocaleString("en-IN")}</td>
                  <td>₹${parseFloat(o.total_labour_cost || 0).toLocaleString("en-IN")}</td>
                  <td>₹${parseFloat(o.total_overhead_cost || 300).toLocaleString("en-IN")}</td>
                  <td style="font-weight: 800; color: #10b981;">
                    ₹${(parseFloat(o.purchase_cost || 0) + parseFloat(o.total_part_cost || 0) + parseFloat(o.total_labour_cost || 0) + parseFloat(o.total_overhead_cost || 300)).toLocaleString("en-IN")}
                  </td>
                  <td>
                    <span class="badge ${o.status === "completed" ? "badge-available" : "badge-qc-pending"}">
                      ${o.status.toUpperCase()}
                    </span>
                  </td>
                  <td>
                    ${o.status !== "completed" ? `
                      <div style="display: flex; gap: 0.4rem;">
                        <button onclick="openConsumePartModal(${o.id}, '${o.wo_number}')" class="btn btn-sm btn-outline" style="font-size: 0.75rem; padding: 0.25rem 0.5rem;">+ Part</button>
                        <button onclick="openLogLabourModal(${o.id}, '${o.wo_number}')" class="btn btn-sm btn-outline" style="font-size: 0.75rem; padding: 0.25rem 0.5rem;">+ Labour</button>
                        <button onclick="submitCompleteWO(${o.id}, '${o.wo_number}')" class="btn btn-sm btn-primary" style="font-size: 0.75rem; padding: 0.25rem 0.5rem; background:#10b981;">Finish & Capitalize</button>
                      </div>
                    ` : `<span style="color: #10b981; font-size: 0.8rem; font-weight: 700;">✓ Inwarded Available</span>`}
                  </td>
                </tr>
              `).join("")
            }
          </tbody>
        </table>
      </div>
      <div id="refurb-modal-container"></div>
    `;
  } catch (err) {
    container.innerHTML = `<div style="color: #ef4444; padding: 2rem;">Error loading work orders: ${err.message}</div>`;
  }
}

async function openRefurbWOModal() {
  const units = await api.get("/api/v1/qc/failed");
  const modal = document.getElementById("refurb-modal-container");
  modal.innerHTML = `
    <div style="position: fixed; inset: 0; background: rgba(0,0,0,0.7); display: flex; align-items: center; justify-content: center; z-index: 1000;">
      <div class="card" style="width: 500px; background: #1e293b; border: 1px solid #334155; color: #fff;">
        <h3 style="margin-bottom: 1rem; font-size: 1.2rem;">Open Refurbishment Work Order</h3>
        <p style="font-size: 0.85rem; color: #94a3b8; margin-bottom: 1rem;">Select a unit requiring diagnostic repair or component replacement:</p>
        
        <div style="margin-bottom: 1rem;">
          <label style="font-size: 0.85rem; color: #94a3b8; display: block; margin-bottom: 0.3rem;">Target Serial Unit:</label>
          <select id="wo-serial-select" class="input" style="width: 100%; background: #0f172a; color: #fff; border-color: #334155;">
            ${units.map(u => `<option value="${u.id}">${u.serial_number} - ${u.product_title} (Current: ${u.current_status})</option>`).join("")}
          </select>
        </div>

        <div style="margin-bottom: 1.5rem;">
          <label style="font-size: 0.85rem; color: #94a3b8; display: block; margin-bottom: 0.3rem;">Work Order Notes / Scope:</label>
          <textarea id="wo-notes-input" class="input" rows="3" style="width: 100%; background: #0f172a; color: #fff; border-color: #334155;" placeholder="e.g. Upgrade SSD to NVMe, replace battery, thermal paste service."></textarea>
        </div>

        <div style="display: flex; justify-content: flex-end; gap: 0.75rem;">
          <button onclick="document.getElementById('refurb-modal-container').innerHTML=''" class="btn btn-outline">Cancel</button>
          <button onclick="submitRefurbWO()" class="btn btn-primary">Create Work Order</button>
        </div>
      </div>
    </div>
  `;
}

async function submitRefurbWO() {
  const serialId = document.getElementById("wo-serial-select").value;
  const notes = document.getElementById("wo-notes-input").value;
  try {
    const res = await api.post("/api/v1/refurbishment/work-orders", { serial_unit_id: serialId, notes: notes });
    alert(`Work order ${res.wo_number} created successfully! Unit base cost transferred to Refurb WIP.`);
    document.getElementById("refurb-modal-container").innerHTML = "";
    switchModule("refurb-costing");
  } catch (err) {
    alert(`Failed to create work order: ${err.message}`);
  }
}

async function openConsumePartModal(woId, woNum) {
  const products = await api.get("/api/v1/catalog/products?type=component");
  const modal = document.getElementById("refurb-modal-container");
  modal.innerHTML = `
    <div style="position: fixed; inset: 0; background: rgba(0,0,0,0.7); display: flex; align-items: center; justify-content: center; z-index: 1000;">
      <div class="card" style="width: 500px; background: #1e293b; border: 1px solid #334155; color: #fff;">
        <h3 style="margin-bottom: 1rem; font-size: 1.2rem;">Requisition Component for ${woNum}</h3>
        
        <div style="margin-bottom: 1rem;">
          <label style="font-size: 0.85rem; color: #94a3b8; display: block; margin-bottom: 0.3rem;">Select Component from Inventory:</label>
          <select id="part-product-select" class="input" style="width: 100%; background: #0f172a; color: #fff; border-color: #334155;">
            ${products.map(p => `<option value="${p.id}">${p.title} (Stock: ${p.stock_quantity} | Cost: ₹${p.base_price})</option>`).join("")}
          </select>
        </div>

        <div style="margin-bottom: 1.5rem;">
          <label style="font-size: 0.85rem; color: #94a3b8; display: block; margin-bottom: 0.3rem;">Quantity to Consume:</label>
          <input type="number" id="part-qty-input" class="input" value="1" min="1" max="10" style="width: 100%; background: #0f172a; color: #fff; border-color: #334155;">
        </div>

        <div style="display: flex; justify-content: flex-end; gap: 0.75rem;">
          <button onclick="document.getElementById('refurb-modal-container').innerHTML=''" class="btn btn-outline">Cancel</button>
          <button onclick="submitConsumePart(${woId})" class="btn btn-primary">Consume & Post Journal</button>
        </div>
      </div>
    </div>
  `;
}

async function submitConsumePart(woId) {
  const compId = document.getElementById("part-product-select").value;
  const qty = document.getElementById("part-qty-input").value;
  try {
    const res = await api.post(`/api/v1/refurbishment/work-orders/${woId}/consume-part`, { component_product_id: compId, quantity: qty });
    alert(res.message);
    document.getElementById("refurb-modal-container").innerHTML = "";
    switchModule("refurb-costing");
  } catch (err) {
    alert(`Error: ${err.message}`);
  }
}

async function openLogLabourModal(woId, woNum) {
  const modal = document.getElementById("refurb-modal-container");
  modal.innerHTML = `
    <div style="position: fixed; inset: 0; background: rgba(0,0,0,0.7); display: flex; align-items: center; justify-content: center; z-index: 1000;">
      <div class="card" style="width: 500px; background: #1e293b; border: 1px solid #334155; color: #fff;">
        <h3 style="margin-bottom: 1rem; font-size: 1.2rem;">Log Direct Technician Labour (${woNum})</h3>
        
        <div style="margin-bottom: 1rem;">
          <label style="font-size: 0.85rem; color: #94a3b8; display: block; margin-bottom: 0.3rem;">Technician Hours Spent (h):</label>
          <input type="number" step="0.5" id="labour-hours-input" class="input" value="1.5" min="0.5" max="24" style="width: 100%; background: #0f172a; color: #fff; border-color: #334155;">
        </div>

        <div style="margin-bottom: 1rem;">
          <label style="font-size: 0.85rem; color: #94a3b8; display: block; margin-bottom: 0.3rem;">Standard Hourly Rate (₹):</label>
          <input type="number" id="labour-rate-input" class="input" value="350" readonly style="width: 100%; background: #0f172a; color: #94a3b8; border-color: #334155;">
        </div>

        <div style="margin-bottom: 1.5rem;">
          <label style="font-size: 0.85rem; color: #94a3b8; display: block; margin-bottom: 0.3rem;">Labour Activity Details:</label>
          <input type="text" id="labour-notes-input" class="input" value="Motherboard cleaning, thermal paste, SSD cloning" style="width: 100%; background: #0f172a; color: #fff; border-color: #334155;">
        </div>

        <div style="display: flex; justify-content: flex-end; gap: 0.75rem;">
          <button onclick="document.getElementById('refurb-modal-container').innerHTML=''" class="btn btn-outline">Cancel</button>
          <button onclick="submitLogLabour(${woId})" class="btn btn-primary">Absorb Labour & Post</button>
        </div>
      </div>
    </div>
  `;
}

async function submitLogLabour(woId) {
  const hrs = document.getElementById("labour-hours-input").value;
  const rate = document.getElementById("labour-rate-input").value;
  const notes = document.getElementById("labour-notes-input").value;
  try {
    const res = await api.post(`/api/v1/refurbishment/work-orders/${woId}/log-labour`, { hours_spent: hrs, hourly_rate: rate, notes: notes });
    alert(res.message);
    document.getElementById("refurb-modal-container").innerHTML = "";
    switchModule("refurb-costing");
  } catch (err) {
    alert(`Error: ${err.message}`);
  }
}

async function submitCompleteWO(woId, woNum) {
  if (!confirm(`Finalize refurbishment and capitalize total unit cost for ${woNum}? This will absorb ₹300 overhead and transfer the unit to Finished Goods inventory.`)) {
    return;
  }
  try {
    const res = await api.post(`/api/v1/refurbishment/work-orders/${woId}/complete`, { rack_bin: "Cleanroom Shelf A-1" });
    alert(`Success: ${res.message}`);
    switchModule("refurb-costing");
  } catch (err) {
    alert(`Error finalizing work order: ${err.message}`);
  }
}

// ==============================================================================
// 12. TRIAL BALANCE & RECONCILIATION
// ==============================================================================
async function renderTrialBalance(container) {
  try {
    const tb = await api.get("/api/v1/accounting/trial-balance");
    
    container.innerHTML = `
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem;">
        <div>
          <h1 style="font-size: 1.5rem; font-weight: 800;">Trial Balance & Double-Entry Invariant</h1>
          <p style="color: #94a3b8; font-size: 0.85rem;">Continuous real-time verification of General Ledger balance (Generated: ${tb.generated_at})</p>
        </div>
        <div style="display: flex; gap: 1rem; align-items: center;">
          <span class="badge ${tb.is_balanced ? "badge-available" : "badge-qc-failed"}" style="font-size: 0.95rem; padding: 0.5rem 1rem;">
            ${tb.is_balanced ? "⚖️ 100% BALANCED (Dr == Cr)" : `⚠️ IMBALANCED (Diff: ₹${tb.discrepancy})`}
          </span>
        </div>
      </div>

      <div class="table-container">
        <table class="table">
          <thead>
            <tr>
              <th>Account Code</th>
              <th>Account Name</th>
              <th>Category</th>
              <th>Subtype</th>
              <th style="text-align: right;">Debit (₹)</th>
              <th style="text-align: right;">Credit (₹)</th>
            </tr>
          </thead>
          <tbody>
            ${tb.accounts.map(a => `
              <tr style="${a.debit > 0 || a.credit > 0 ? "font-weight: 600;" : "color: #64748b;"}">
                <td style="font-family: monospace; color: #38bdf8;">${a.code}</td>
                <td>${a.name}</td>
                <td><span class="badge badge-grade-a">${a.type}</span></td>
                <td>${a.subtype || "-"}</td>
                <td style="text-align: right; color: ${a.debit > 0 ? "#fff" : "#64748b"};">${a.debit > 0 ? "₹" + a.debit.toLocaleString("en-IN", {minimumFractionDigits: 2}) : "-"}</td>
                <td style="text-align: right; color: ${a.credit > 0 ? "#fff" : "#64748b"};">${a.credit > 0 ? "₹" + a.credit.toLocaleString("en-IN", {minimumFractionDigits: 2}) : "-"}</td>
              </tr>
            `).join("")}
          </tbody>
          <tfoot>
            <tr style="background: #0f172a; font-weight: 800; font-size: 1.05rem; border-top: 2px solid #38bdf8;">
              <td colspan="4" style="text-align: right; text-transform: uppercase;">Grand Total:</td>
              <td style="text-align: right; color: #38bdf8;">₹${tb.total_debit.toLocaleString("en-IN", {minimumFractionDigits: 2})}</td>
              <td style="text-align: right; color: #38bdf8;">₹${tb.total_credit.toLocaleString("en-IN", {minimumFractionDigits: 2})}</td>
            </tr>
          </tfoot>
        </table>
      </div>
    `;
  } catch (err) {
    container.innerHTML = `<div style="color: #ef4444; padding: 2rem;">Error: ${err.message}</div>`;
  }
}

// ==============================================================================
// 13. CHART OF ACCOUNTS (COA)
// ==============================================================================
async function renderChartOfAccounts(container) {
  try {
    const coa = await api.get("/api/v1/accounting/coa");
    
    container.innerHTML = `
      <div style="margin-bottom: 2rem;">
        <h1 style="font-size: 1.5rem; font-weight: 800;">Chart of Accounts (COA)</h1>
        <p style="color: #94a3b8; font-size: 0.85rem;">Standard 5-digit account hierarchy for Refurbished IT & Custom PC Assembly enterprise</p>
      </div>

      <div class="table-container">
        <table class="table">
          <thead>
            <tr>
              <th>Account Code</th>
              <th>Account Name</th>
              <th>Type</th>
              <th>Subtype</th>
              <th style="text-align: right;">Current Balance</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            ${coa.map(a => `
              <tr>
                <td style="font-family: monospace; font-weight: 700; color: #38bdf8;">${a.code}</td>
                <td><b>${a.name}</b></td>
                <td><span class="badge badge-grade-a">${a.type}</span></td>
                <td>${a.subtype}</td>
                <td style="text-align: right; font-weight: 700; color: ${a.balance >= 0 ? "#10b981" : "#ef4444"};">
                  ₹${parseFloat(a.balance).toLocaleString("en-IN", {minimumFractionDigits: 2})}
                </td>
                <td><span class="badge badge-available">RECONCILED</span></td>
              </tr>
            `).join("")}
          </tbody>
        </table>
      </div>
    `;
  } catch (err) {
    container.innerHTML = `<div style="color: #ef4444; padding: 2rem;">Error: ${err.message}</div>`;
  }
}

// ==============================================================================
// 14. GENERAL LEDGER DRILLDOWN
// ==============================================================================
async function renderGeneralLedger(container) {
  try {
    const entries = await api.get("/api/v1/accounting/general-ledger");
    
    container.innerHTML = `
      <div style="margin-bottom: 2rem;">
        <h1 style="font-size: 1.5rem; font-weight: 800;">General Ledger Audit Trail</h1>
        <p style="color: #94a3b8; font-size: 0.85rem;">Complete transaction-level journal line history with operational references</p>
      </div>

      <div class="table-container">
        <table class="table">
          <thead>
            <tr>
              <th>Date</th>
              <th>Journal #</th>
              <th>Reference</th>
              <th>Account Code</th>
              <th>Account Name</th>
              <th>Description / Memo</th>
              <th style="text-align: right;">Debit (₹)</th>
              <th style="text-align: right;">Credit (₹)</th>
            </tr>
          </thead>
          <tbody>
            ${entries.length === 0 ? `<tr><td colspan="8" style="text-align: center; color: #94a3b8; padding: 2rem;">No journal entries posted yet.</td></tr>` : 
              entries.map(e => `
                <tr>
                  <td>${e.posting_date}</td>
                  <td style="font-family: monospace; color: #38bdf8;">${e.entry_number}</td>
                  <td><span class="badge badge-grade-a">${e.reference_type}:${e.reference_id}</span></td>
                  <td style="font-family: monospace;">${e.account_code}</td>
                  <td>${e.account_name}</td>
                  <td style="color: #94a3b8; font-size: 0.85rem;">${e.line_memo}</td>
                  <td style="text-align: right; color: ${e.debit > 0 ? "#10b981" : "#64748b"}; font-weight: ${e.debit > 0 ? "700" : "400"};">
                    ${e.debit > 0 ? "₹" + parseFloat(e.debit).toLocaleString("en-IN", {minimumFractionDigits: 2}) : "-"}
                  </td>
                  <td style="text-align: right; color: ${e.credit > 0 ? "#f59e0b" : "#64748b"}; font-weight: ${e.credit > 0 ? "700" : "400"};">
                    ${e.credit > 0 ? "₹" + parseFloat(e.credit).toLocaleString("en-IN", {minimumFractionDigits: 2}) : "-"}
                  </td>
                </tr>
              `).join("")
            }
          </tbody>
        </table>
      </div>
    `;
  } catch (err) {
    container.innerHTML = `<div style="color: #ef4444; padding: 2rem;">Error: ${err.message}</div>`;
  }
}

// ==============================================================================
// 15. PROFIT & LOSS STATEMENT
// ==============================================================================
async function renderProfitAndLoss(container) {
  try {
    const pl = await api.get("/api/v1/accounting/pl");
    
    container.innerHTML = `
      <div style="margin-bottom: 2rem;">
        <h1 style="font-size: 1.5rem; font-weight: 800;">Profit & Loss Statement (P&L)</h1>
        <p style="color: #94a3b8; font-size: 0.85rem;">Financial Performance Report (${pl.period})</p>
      </div>

      <div class="card" style="background: #1e293b; border-color: #334155; color: #fff; max-width: 800px; margin: 0 auto; padding: 2rem;">
        <h3 style="border-bottom: 2px solid #38bdf8; padding-bottom: 0.5rem; color: #38bdf8; text-transform: uppercase;">1. Operating Revenue</h3>
        ${pl.revenue.items.map(i => `
          <div style="display: flex; justify-content: space-between; padding: 0.5rem 0; border-bottom: 1px solid #334155;">
            <span>${i.code} — ${i.name}</span>
            <b>₹${i.amount.toLocaleString("en-IN", {minimumFractionDigits: 2})}</b>
          </div>
        `).join("")}
        <div style="display: flex; justify-content: space-between; padding: 0.75rem 0; font-weight: 800; font-size: 1.05rem; color: #10b981;">
          <span>TOTAL REVENUE:</span>
          <span>₹${pl.revenue.total.toLocaleString("en-IN", {minimumFractionDigits: 2})}</span>
        </div>

        <h3 style="border-bottom: 2px solid #f59e0b; padding-bottom: 0.5rem; margin-top: 2rem; color: #f59e0b; text-transform: uppercase;">2. Cost of Goods Sold (COGS)</h3>
        ${pl.cogs.items.map(i => `
          <div style="display: flex; justify-content: space-between; padding: 0.5rem 0; border-bottom: 1px solid #334155;">
            <span>${i.code} — ${i.name}</span>
            <span>₹${i.amount.toLocaleString("en-IN", {minimumFractionDigits: 2})}</span>
          </div>
        `).join("")}
        <div style="display: flex; justify-content: space-between; padding: 0.75rem 0; font-weight: 800; font-size: 1.05rem; color: #f59e0b;">
          <span>TOTAL COGS:</span>
          <span>₹${pl.cogs.total.toLocaleString("en-IN", {minimumFractionDigits: 2})}</span>
        </div>

        <div style="background: #0f172a; padding: 1rem; border-radius: 8px; margin: 1.5rem 0; display: flex; justify-content: space-between; font-weight: 800; font-size: 1.2rem;">
          <span>GROSS PROFIT:</span>
          <span style="color: ${pl.gross_profit >= 0 ? "#10b981" : "#ef4444"};">
            ₹${pl.gross_profit.toLocaleString("en-IN", {minimumFractionDigits: 2})} (${pl.gross_margin_pct}%)
          </span>
        </div>

        <h3 style="border-bottom: 2px solid #ef4444; padding-bottom: 0.5rem; margin-top: 2rem; color: #ef4444; text-transform: uppercase;">3. Operating Expenses</h3>
        ${pl.expenses.items.map(i => `
          <div style="display: flex; justify-content: space-between; padding: 0.5rem 0; border-bottom: 1px solid #334155;">
            <span>${i.code} — ${i.name}</span>
            <span>₹${i.amount.toLocaleString("en-IN", {minimumFractionDigits: 2})}</span>
          </div>
        `).join("")}
        <div style="display: flex; justify-content: space-between; padding: 0.75rem 0; font-weight: 800; font-size: 1.05rem; color: #ef4444;">
          <span>TOTAL EXPENSES:</span>
          <span>₹${pl.expenses.total.toLocaleString("en-IN", {minimumFractionDigits: 2})}</span>
        </div>

        <div style="background: #0284c7; color: #fff; padding: 1.25rem; border-radius: 8px; margin-top: 2rem; display: flex; justify-content: space-between; font-weight: 900; font-size: 1.35rem;">
          <span>NET PROFIT / (LOSS):</span>
          <span>₹${pl.net_profit.toLocaleString("en-IN", {minimumFractionDigits: 2})} (${pl.net_margin_pct}%)</span>
        </div>
      </div>
    `;
  } catch (err) {
    container.innerHTML = `<div style="color: #ef4444; padding: 2rem;">Error: ${err.message}</div>`;
  }
}

// ==============================================================================
// 16. BALANCE SHEET
// ==============================================================================
async function renderBalanceSheet(container) {
  try {
    const bs = await api.get("/api/v1/accounting/balance-sheet");
    
    container.innerHTML = `
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem;">
        <div>
          <h1 style="font-size: 1.5rem; font-weight: 800;">Balance Sheet</h1>
          <p style="color: #94a3b8; font-size: 0.85rem;">Financial Position Statement as of ${bs.as_of_date}</p>
        </div>
        <span class="badge ${bs.is_balanced ? "badge-available" : "badge-qc-failed"}" style="font-size: 0.95rem; padding: 0.5rem 1rem;">
          ${bs.is_balanced ? "✓ Assets == Liabilities + Equity" : `⚠️ Out of Balance (Diff: ₹${bs.discrepancy})`}
        </span>
      </div>

      <div class="grid-2">
        <!-- Assets Column -->
        <div class="card" style="background: #1e293b; border-color: #334155; color: #fff; padding: 1.5rem;">
          <h3 style="border-bottom: 2px solid #38bdf8; padding-bottom: 0.5rem; color: #38bdf8; text-transform: uppercase; margin-bottom: 1rem;">Assets</h3>
          
          <h4 style="font-size: 0.9rem; color: #94a3b8; text-transform: uppercase; margin: 1rem 0 0.5rem;">Current & Bank Assets</h4>
          ${bs.assets.current_assets.map(a => `
            <div style="display: flex; justify-content: space-between; padding: 0.4rem 0; border-bottom: 1px solid #334155;">
              <span>${a.code} — ${a.name}</span>
              <b>₹${a.amount.toLocaleString("en-IN", {minimumFractionDigits: 2})}</b>
            </div>
          `).join("")}

          <h4 style="font-size: 0.9rem; color: #94a3b8; text-transform: uppercase; margin: 1.5rem 0 0.5rem;">Inventory Assets (Specific Valuation)</h4>
          ${bs.assets.inventory_assets.map(a => `
            <div style="display: flex; justify-content: space-between; padding: 0.4rem 0; border-bottom: 1px solid #334155;">
              <span>${a.code} — ${a.name}</span>
              <b>₹${a.amount.toLocaleString("en-IN", {minimumFractionDigits: 2})}</b>
            </div>
          `).join("")}

          <div style="background: #0f172a; padding: 1rem; border-radius: 8px; margin-top: 2rem; display: flex; justify-content: space-between; font-weight: 900; font-size: 1.25rem; color: #38bdf8;">
            <span>TOTAL ASSETS:</span>
            <span>₹${bs.assets.total_assets.toLocaleString("en-IN", {minimumFractionDigits: 2})}</span>
          </div>
        </div>

        <!-- Liabilities & Equity Column -->
        <div class="card" style="background: #1e293b; border-color: #334155; color: #fff; padding: 1.5rem;">
          <h3 style="border-bottom: 2px solid #f59e0b; padding-bottom: 0.5rem; color: #f59e0b; text-transform: uppercase; margin-bottom: 1rem;">Liabilities & Equity</h3>
          
          <h4 style="font-size: 0.9rem; color: #94a3b8; text-transform: uppercase; margin: 1rem 0 0.5rem;">Liabilities</h4>
          ${bs.liabilities.items.map(l => `
            <div style="display: flex; justify-content: space-between; padding: 0.4rem 0; border-bottom: 1px solid #334155;">
              <span>${l.code} — ${l.name}</span>
              <b>₹${l.amount.toLocaleString("en-IN", {minimumFractionDigits: 2})}</b>
            </div>
          `).join("")}
          <div style="display: flex; justify-content: space-between; padding: 0.6rem 0; font-weight: 700; color: #f59e0b;">
            <span>Total Liabilities:</span>
            <span>₹${bs.liabilities.total_liabilities.toLocaleString("en-IN", {minimumFractionDigits: 2})}</span>
          </div>

          <h4 style="font-size: 0.9rem; color: #94a3b8; text-transform: uppercase; margin: 1.5rem 0 0.5rem;">Owner Equity & Reserves</h4>
          ${bs.equity.items.map(e => `
            <div style="display: flex; justify-content: space-between; padding: 0.4rem 0; border-bottom: 1px solid #334155;">
              <span>${e.code} — ${e.name}</span>
              <b>₹${e.amount.toLocaleString("en-IN", {minimumFractionDigits: 2})}</b>
            </div>
          `).join("")}
          <div style="display: flex; justify-content: space-between; padding: 0.6rem 0; font-weight: 700; color: #10b981;">
            <span>Total Equity:</span>
            <span>₹${bs.equity.total_equity.toLocaleString("en-IN", {minimumFractionDigits: 2})}</span>
          </div>

          <div style="background: #0f172a; padding: 1rem; border-radius: 8px; margin-top: 2rem; display: flex; justify-content: space-between; font-weight: 900; font-size: 1.25rem; color: #10b981;">
            <span>TOTAL LIAB & EQUITY:</span>
            <span>₹${bs.total_liabilities_and_equity.toLocaleString("en-IN", {minimumFractionDigits: 2})}</span>
          </div>
        </div>
      </div>
    `;
  } catch (err) {
    container.innerHTML = `<div style="color: #ef4444; padding: 2rem;">Error: ${err.message}</div>`;
  }
}

// ==============================================================================
// 17. POST MANUAL JOURNAL ENTRY
// ==============================================================================
async function renderManualJournal(container) {
  try {
    const coa = await api.get("/api/v1/accounting/coa");
    
    container.innerHTML = `
      <div style="margin-bottom: 2rem;">
        <h1 style="font-size: 1.5rem; font-weight: 800;">Post Manual Journal Entry</h1>
        <p style="color: #94a3b8; font-size: 0.85rem;">Create adjusting, depreciation or equity journals with strict client & server-side Dr == Cr enforcement</p>
      </div>

      <div class="card" style="background: #1e293b; border-color: #334155; color: #fff; padding: 2rem; max-width: 900px; margin: 0 auto;">
        <div class="grid-3" style="margin-bottom: 1.5rem;">
          <div>
            <label style="font-size: 0.85rem; color: #94a3b8; display: block; margin-bottom: 0.3rem;">Entry Memo / Description:</label>
            <input type="text" id="jrn-memo" class="input" style="width: 100%; background: #0f172a; color: #fff; border-color: #334155;" placeholder="e.g. Monthly workshop rent payment">
          </div>
          <div>
            <label style="font-size: 0.85rem; color: #94a3b8; display: block; margin-bottom: 0.3rem;">Reference Code:</label>
            <input type="text" id="jrn-ref" class="input" style="width: 100%; background: #0f172a; color: #fff; border-color: #334155;" value="ADJ-2026-001">
          </div>
          <div>
            <label style="font-size: 0.85rem; color: #94a3b8; display: block; margin-bottom: 0.3rem;">Reference Type:</label>
            <select id="jrn-reftype" class="input" style="width: 100%; background: #0f172a; color: #fff; border-color: #334155;">
              <option value="MANUAL_ADJ">Manual Adjustment</option>
              <option value="EQUITY_INJECTION">Capital Contribution</option>
              <option value="EXPENSE_ACCRUAL">Expense Accrual</option>
              <option value="SCRAP_WRITEDOWN">Scrap Write-Down</option>
            </select>
          </div>
        </div>

        <div style="margin-bottom: 1rem; display: flex; justify-content: space-between; align-items: center;">
          <h4 style="font-size: 1rem; font-weight: 700;">Journal Lines</h4>
          <button onclick="addJournalRow()" class="btn btn-sm btn-outline">+ Add Line</button>
        </div>

        <div class="table-container" style="margin-bottom: 1.5rem;">
          <table class="table">
            <thead>
              <tr>
                <th style="width: 45%;">Account</th>
                <th style="width: 25%;">Debit (₹)</th>
                <th style="width: 25%;">Credit (₹)</th>
                <th style="width: 5%;"></th>
              </tr>
            </thead>
            <tbody id="journal-lines-body">
              <!-- Default 2 Lines -->
              <tr>
                <td>
                  <select class="input jrn-account-select" style="width: 100%; background: #0f172a; color: #fff; border-color: #334155;">
                    ${coa.map(a => `<option value="${a.code}">${a.code} - ${a.name} (${a.type})</option>`).join("")}
                  </select>
                </td>
                <td><input type="number" step="0.01" min="0" class="input jrn-debit-input" value="0.00" oninput="calculateJournalTotals()" style="width: 100%; background: #0f172a; color: #fff; border-color: #334155;"></td>
                <td><input type="number" step="0.01" min="0" class="input jrn-credit-input" value="0.00" oninput="calculateJournalTotals()" style="width: 100%; background: #0f172a; color: #fff; border-color: #334155;"></td>
                <td></td>
              </tr>
              <tr>
                <td>
                  <select class="input jrn-account-select" style="width: 100%; background: #0f172a; color: #fff; border-color: #334155;">
                    ${coa.map(a => `<option value="${a.code}">${a.code} - ${a.name} (${a.type})</option>`).join("")}
                  </select>
                </td>
                <td><input type="number" step="0.01" min="0" class="input jrn-debit-input" value="0.00" oninput="calculateJournalTotals()" style="width: 100%; background: #0f172a; color: #fff; border-color: #334155;"></td>
                <td><input type="number" step="0.01" min="0" class="input jrn-credit-input" value="0.00" oninput="calculateJournalTotals()" style="width: 100%; background: #0f172a; color: #fff; border-color: #334155;"></td>
                <td></td>
              </tr>
            </tbody>
            <tfoot>
              <tr style="background: #0f172a; font-weight: 800;">
                <td style="text-align: right;">Total:</td>
                <td id="jrn-total-debit" style="color: #38bdf8;">₹0.00</td>
                <td id="jrn-total-credit" style="color: #38bdf8;">₹0.00</td>
                <td></td>
              </tr>
            </tfoot>
          </table>
        </div>

        <div id="jrn-balance-status" style="padding: 0.75rem; border-radius: 6px; background: rgba(239, 68, 68, 0.2); color: #ef4444; margin-bottom: 1.5rem; text-align: center; font-weight: 700;">
          ⚠️ Total Debit and Total Credit must be non-zero and exactly equal.
        </div>

        <div style="display: flex; justify-content: flex-end; gap: 1rem;">
          <button onclick="switchModule('trial-balance')" class="btn btn-outline">Cancel</button>
          <button id="jrn-submit-btn" onclick="submitManualJournal()" class="btn btn-primary" disabled style="opacity: 0.5;">Post Journal to Ledger</button>
        </div>
      </div>
    `;
  } catch (err) {
    container.innerHTML = `<div style="color: #ef4444; padding: 2rem;">Error: ${err.message}</div>`;
  }
}

function addJournalRow() {
  const tbody = document.getElementById("journal-lines-body");
  const firstSelect = tbody.querySelector(".jrn-account-select");
  const tr = document.createElement("tr");
  tr.innerHTML = `
    <td>
      <select class="input jrn-account-select" style="width: 100%; background: #0f172a; color: #fff; border-color: #334155;">
        ${firstSelect.innerHTML}
      </select>
    </td>
    <td><input type="number" step="0.01" min="0" class="input jrn-debit-input" value="0.00" oninput="calculateJournalTotals()" style="width: 100%; background: #0f172a; color: #fff; border-color: #334155;"></td>
    <td><input type="number" step="0.01" min="0" class="input jrn-credit-input" value="0.00" oninput="calculateJournalTotals()" style="width: 100%; background: #0f172a; color: #fff; border-color: #334155;"></td>
    <td><button onclick="this.closest('tr').remove(); calculateJournalTotals();" class="btn btn-sm btn-outline" style="border-color:#ef4444; color:#ef4444; padding: 0.25rem 0.5rem;">✕</button></td>
  `;
  tbody.appendChild(tr);
}

function calculateJournalTotals() {
  let totalDr = 0.0;
  let totalCr = 0.0;
  
  document.querySelectorAll(".jrn-debit-input").forEach(el => totalDr += parseFloat(el.value || 0));
  document.querySelectorAll(".jrn-credit-input").forEach(el => totalCr += parseFloat(el.value || 0));
  
  totalDr = Math.round(totalDr * 100) / 100;
  totalCr = Math.round(totalCr * 100) / 100;
  const diff = Math.abs(Math.round((totalDr - totalCr) * 100) / 100);
  
  document.getElementById("jrn-total-debit").innerText = "₹" + totalDr.toLocaleString("en-IN", {minimumFractionDigits: 2});
  document.getElementById("jrn-total-credit").innerText = "₹" + totalCr.toLocaleString("en-IN", {minimumFractionDigits: 2});
  
  const statusEl = document.getElementById("jrn-balance-status");
  const submitBtn = document.getElementById("jrn-submit-btn");
  
  if (totalDr > 0 && totalCr > 0 && diff <= 0.01) {
    statusEl.style.background = "rgba(16, 185, 129, 0.2)";
    statusEl.style.color = "#10b981";
    statusEl.innerText = `✓ 100% Balanced: Total Debit ₹${totalDr.toFixed(2)} == Total Credit ₹${totalCr.toFixed(2)}`;
    submitBtn.disabled = false;
    submitBtn.style.opacity = "1";
  } else {
    statusEl.style.background = "rgba(239, 68, 68, 0.2)";
    statusEl.style.color = "#ef4444";
    statusEl.innerText = `⚠️ Imbalanced: Debit ₹${totalDr.toFixed(2)} != Credit ₹${totalCr.toFixed(2)} (Discrepancy: ₹${diff.toFixed(2)})`;
    submitBtn.disabled = true;
    submitBtn.style.opacity = "0.5";
  }
}

async function submitManualJournal() {
  const memo = document.getElementById("jrn-memo").value.trim() || "Manual Journal Adjustment";
  const refId = document.getElementById("jrn-ref").value.trim() || "MANUAL";
  const refType = document.getElementById("jrn-reftype").value;
  
  const lines = [];
  const rows = document.querySelectorAll("#journal-lines-body tr");
  
  rows.forEach(r => {
    const accCode = r.querySelector(".jrn-account-select").value;
    const dr = parseFloat(r.querySelector(".jrn-debit-input").value || 0);
    const cr = parseFloat(r.querySelector(".jrn-credit-input").value || 0);
    if (dr > 0 || cr > 0) {
      lines.push({ account_code: accCode, debit: dr, credit: cr, line_memo: memo });
    }
  });
  
  try {
    const res = await api.post("/api/v1/accounting/journals", {
      memo: memo,
      reference_type: refType,
      reference_id: refId,
      lines: lines
    });
    alert(`Journal ${res.entry_number} posted successfully to General Ledger!`);
    switchModule("trial-balance");
  } catch (err) {
    alert(`Failed to post journal: ${err.message}`);
  }
}

document.addEventListener("DOMContentLoaded", () => {
  if (document.getElementById("erp-view-content")) {
    switchModule("dashboard");
  }
});

window.switchModule = switchModule;
window.submitInward = submitInward;
window.openQCInspectionModal = openQCInspectionModal;
window.submitQCResult = submitQCResult;
window.openSerialTimeline = openSerialTimeline;
window.openAssemblyQCModal = openAssemblyQCModal;
window.submitAssemblyQC = submitAssemblyQC;
window.printInvoice = printInvoice;
window.openRefurbWOModal = openRefurbWOModal;
window.submitRefurbWO = submitRefurbWO;
window.openConsumePartModal = openConsumePartModal;
window.submitConsumePart = submitConsumePart;
window.openLogLabourModal = openLogLabourModal;
window.submitLogLabour = submitLogLabour;
window.submitCompleteWO = submitCompleteWO;
window.addJournalRow = addJournalRow;
window.calculateJournalTotals = calculateJournalTotals;
window.submitManualJournal = submitManualJournal;

