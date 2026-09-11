// PC WARE 10-Step Interactive Custom PC Builder Engine
let currentStep = 1;
const buildParts = {
  cpu: null,
  mb: null,
  ram: null,
  storage: null,
  gpu: null,
  psu: null,
  cabinet: null,
  cooler: null,
  os: "Windows 11 Pro 64-bit Genuine Digital License",
  assembly_charge: 2500
};

const STEPS = [
  { step: 1, key: "cpu", label: "Processor (CPU)", category: "processors" },
  { step: 2, key: "mb", label: "Motherboard", category: "motherboards" },
  { step: 3, key: "ram", label: "Memory (RAM)", category: "ram" },
  { step: 4, key: "storage", label: "Storage (NVMe SSD)", category: "storage" },
  { step: 5, key: "gpu", label: "Graphics Card (GPU)", category: "gpus" },
  { step: 6, key: "psu", label: "Power Supply (PSU)", category: "psus" },
  { step: 7, key: "cabinet", label: "Cabinet / Chassis", category: "cabinets" },
  { step: 8, key: "cooler", label: "CPU Cooler", category: "cooling" },
  { step: 9, key: "os", label: "OS & Software", category: null },
  { step: 10, key: "review", label: "Review & Order", category: null }
];

async function loadStep(stepNumber) {
  currentStep = stepNumber;
  renderStepNav();
  
  const stepDef = STEPS.find(s => s.step === stepNumber);
  document.getElementById("step-title").textContent = `Step ${stepDef.step}: Select ${stepDef.label}`;
  
  const container = document.getElementById("step-component-list");
  container.innerHTML = `<div style="padding: 2rem; text-align: center; color: #64748b;">Loading compatible components...</div>`;
  
  if (stepDef.category) {
    try {
      const items = await api.get(`/api/v1/catalog/products?category_slug=${stepDef.category}`);
      renderComponentCards(items, stepDef.key, container);
    } catch (e) {
      container.innerHTML = `<div style="color: #ef4444; padding: 2rem;">Failed to load components: ${e.message}</div>`;
    }
  } else if (stepNumber === 9) {
    renderOSStep(container);
  } else if (stepNumber === 10) {
    renderReviewStep(container);
  }
  
  updateSummarySidebar();
}

function renderComponentCards(items, partKey, container) {
  if (!items || items.length === 0) {
    container.innerHTML = `<div style="padding: 2rem; text-align: center; color: #64748b;">No components found in this category.</div>`;
    return;
  }
  
  container.innerHTML = "";
  items.forEach(prod => {
    // Check compatibility of this product if selected
    const testParts = { ...buildParts, [partKey]: prod };
    const compat = CompatibilityEngine.checkCompatibility(testParts);
    const isSelected = buildParts[partKey] && buildParts[partKey].id === prod.id;
    
    const card = document.createElement("div");
    card.className = `card ${isSelected ? 'selected-build-card' : ""}`;
    card.style.display = "flex";
    card.style.flexDirection = "column";
    card.style.justifyContent = "space-between";
    card.style.border = isSelected ? "2px solid #0284c7" : !compat.isCompatible ? "1px solid #fee2e2" : "1px solid #e2e8f0";
    card.style.backgroundColor = !compat.isCompatible ? "#fef2f2" : "#ffffff";
    
    let compatBadge = "";
    if (!compat.isCompatible) {
      compatBadge = `<div class="badge badge-qc-fail" style="margin-bottom: 0.5rem;">⚠️ Incompatible: ${compat.mismatches[0].message}</div>`;
    } else {
      compatBadge = `<div class="badge badge-qc-pass" style="margin-bottom: 0.5rem;">✓ Compatible</div>`;
    }
    
    card.innerHTML = `
      <div>
        ${compatBadge}
        <img src="${prod.image_url || 'https://images.unsplash.com/photo-1591799264318-7e6ef8ddb7ea?w=400'}" style="width: 100%; height: 140px; object-fit: cover; border-radius: 6px; margin-bottom: 0.75rem;">
        <h4 style="font-size: 0.95rem; font-weight: 700; margin-bottom: 0.25rem;">${prod.title}</h4>
        <p style="font-size: 0.8rem; color: #64748b; margin-bottom: 0.5rem;">${prod.brand_name} | SKU: ${prod.sku}</p>
        <div style="font-size: 1.15rem; font-weight: 800; color: #0f172a;">₹${prod.selling_price.toLocaleString("en-IN")}</div>
      </div>
      <div style="margin-top: 1rem;">
        <button class="btn btn-sm ${isSelected ? 'btn-primary' : 'btn-outline'}" style="width: 100%;" ${!compat.isCompatible ? 'disabled' : ""} onclick="selectPart('${partKey}', ${JSON.stringify(prod).replace(/"/g, "&quot;")})">
          ${isSelected ? "✓ Selected" : !compat.isCompatible ? "Incompatible" : "Select Component"}
        </button>
      </div>
    `;
    container.appendChild(card);
  });
}

function selectPart(partKey, prod) {
  buildParts[partKey] = prod;
  showToast(`Selected ${prod.title}`, "success");
  if (currentStep < 10) {
    loadStep(currentStep + 1);
  } else {
    loadStep(10);
  }
}

function renderOSStep(container) {
  container.innerHTML = `
    <div class="card" style="padding: 1.5rem;">
      <h3 style="margin-bottom: 1rem;">Operating System & Professional Assembly Services</h3>
      <div style="margin-bottom: 1.25rem;">
        <label style="font-weight: 600; display: block; margin-bottom: 0.5rem;">Operating System Installation:</label>
        <select class="form-control" onchange="buildParts.os = this.value; updateSummarySidebar();">
          <option value="Windows 11 Pro 64-bit Genuine Digital License" selected>Windows 11 Pro 64-bit Genuine Digital License (Included)</option>
          <option value="Windows 10 Pro 64-bit Genuine Digital License">Windows 10 Pro 64-bit Genuine Digital License</option>
          <option value="Ubuntu Linux 24.04 LTS Long Term Support">Ubuntu Linux 24.04 LTS (Open Source)</option>
          <option value="Proxmox VE / VMware ESXi Hypervisor Ready">Proxmox VE Virtualization Environment</option>
        </select>
      </div>
      <div style="background: #f0f9ff; border: 1px solid #bae6fd; padding: 1rem; border-radius: 8px;">
        <h4 style="color: #0369a1; margin-bottom: 0.25rem;">✓ Professional White-Glove PC Assembly Included (₹2,500)</h4>
        <p style="font-size: 0.85rem; color: #0284c7;">Includes Arctic MX-4 premium thermal paste application, precision cable management, latest BIOS update, XMP/EXPO profile verification, and 1-hour burn-in stress testing in our Cleanroom Lab.</p>
      </div>
      <div style="margin-top: 1.5rem; display: flex; justify-content: flex-end;">
        <button class="btn btn-primary" onclick="loadStep(10)">Proceed to Final Review →</button>
      </div>
    </div>
  `;
}

function renderReviewStep(container) {
  const compat = CompatibilityEngine.checkCompatibility(buildParts);
  let totalComp = 0;
  
  let partsHtml = "";
  ["cpu", "mb", "ram", "storage", "gpu", "psu", "cabinet", "cooler"].forEach(k => {
    const p = buildParts[k];
    if (p) {
      totalComp += p.selling_price;
      partsHtml += `
        <tr>
          <td style="font-weight: 600; text-transform: uppercase; font-size: 0.75rem; color: #64748b;">${k}</td>
          <td style="font-weight: 600;">${p.title}</td>
          <td style="text-align: right; font-weight: 700;">₹${p.selling_price.toLocaleString("en-IN")}</td>
        </tr>
      `;
    }
  });
  
  const subtotal = totalComp + buildParts.assembly_charge;
  const gst = Math.round(subtotal * 0.18);
  const grandTotal = subtotal + gst;
  
  container.innerHTML = `
    <div class="card" style="padding: 1.5rem;">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;">
        <div>
          <h2 style="font-size: 1.35rem; font-weight: 800;">Custom Rig Specifications Summary</h2>
          <p style="color: #64748b; font-size: 0.85rem;">Authoritative Hardware Validation & Quotation</p>
        </div>
        <div>
          ${compat.isCompatible ? '<span class="badge badge-qc-pass" style="font-size: 0.9rem; padding: 0.4rem 0.8rem;">✓ 100% HARDWARE COMPATIBLE</span>' : '<span class="badge badge-qc-fail">⚠️ HARDWARE MISMATCH DETECTED</span>'}
        </div>
      </div>
      
      <table class="data-table" style="margin-bottom: 1.5rem;">
        <thead>
          <tr>
            <th>Component</th>
            <th>Model & Specification</th>
            <th style="text-align: right;">Price</th>
          </tr>
        </thead>
        <tbody>
          ${partsHtml}
          <tr>
            <td style="font-weight: 600; text-transform: uppercase; font-size: 0.75rem; color: #0284c7;">SERVICE</td>
            <td style="font-weight: 600;">PC Ware White-Glove Assembly, Thermal Profiling & Stress Testing</td>
            <td style="text-align: right; font-weight: 700;">₹${buildParts.assembly_charge.toLocaleString("en-IN")}</td>
          </tr>
        </tbody>
      </table>
      
      <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 1.25rem; margin-bottom: 1.5rem;">
        <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem; font-size: 0.95rem;">
          <span>Components & Labour Subtotal:</span>
          <span style="font-weight: 700;">₹${subtotal.toLocaleString("en-IN")}</span>
        </div>
        <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem; font-size: 0.95rem;">
          <span>GST (9% CGST + 9% SGST - HSN 8471):</span>
          <span style="font-weight: 700;">₹${gst.toLocaleString("en-IN")}</span>
        </div>
        <div style="display: flex; justify-content: space-between; border-top: 2px solid #e2e8f0; padding-top: 0.75rem; font-size: 1.35rem; font-weight: 800; color: #0f172a;">
          <span>Grand Total:</span>
          <span style="color: #0284c7;">₹${grandTotal.toLocaleString("en-IN")}</span>
        </div>
      </div>
      
      <div style="display: flex; gap: 1rem; justify-content: flex-end;">
        <button class="btn btn-secondary" onclick="requestBuildQuote()">📄 Request Official Proforma Quote</button>
        <button class="btn btn-primary btn-lg" onclick="submitCustomBuildOrder()">🛒 Order Custom Build</button>
      </div>
    </div>
  `;
}

function updateSummarySidebar() {
  const sidebar = document.getElementById("build-sidebar-summary");
  if (!sidebar) return;
  
  let count = 0;
  let total = 0;
  ["cpu", "mb", "ram", "storage", "gpu", "psu", "cabinet", "cooler"].forEach(k => {
    if (buildParts[k]) {
      count++;
      total += buildParts[k].selling_price;
    }
  });
  
  const compat = CompatibilityEngine.checkCompatibility(buildParts);
  
  sidebar.innerHTML = `
    <div style="font-size: 0.85rem; color: #64748b; margin-bottom: 0.5rem;">Configured Components: <b>${count} of 8</b></div>
    <div style="font-size: 1.35rem; font-weight: 800; color: #0f172a; margin-bottom: 1rem;">₹${(total + (count > 0 ? buildParts.assembly_charge : 0)).toLocaleString("en-IN")}</div>
    
    <div style="background: #f1f5f9; border-radius: 8px; padding: 0.85rem; margin-bottom: 1rem; font-size: 0.85rem;">
      <div style="display: flex; justify-content: space-between; margin-bottom: 0.35rem;">
        <span>Est. System Power:</span>
        <b>${compat.estimatedWatts}W</b>
      </div>
      <div style="display: flex; justify-content: space-between;">
        <span>Recommended PSU:</span>
        <b style="color: #0284c7;">${compat.recommendedPsuWatts}W+</b>
      </div>
    </div>
    
    ${!compat.isCompatible ? `<div style="background: #fef2f2; border: 1px solid #fecaca; color: #991b1b; padding: 0.75rem; border-radius: 6px; font-size: 0.8rem; margin-bottom: 1rem;">⚠️ ${compat.mismatches[0].message}</div>` : ""}
  `;
}

function renderStepNav() {
  const nav = document.getElementById("builder-step-nav");
  if (!nav) return;
  nav.innerHTML = "";
  STEPS.forEach(s => {
    const item = document.createElement("div");
    const isDone = s.step < currentStep || (buildParts[s.key] !== null && s.key !== "review");
    const isCurrent = s.step === currentStep;
    item.className = `step-indicator ${isCurrent ? 'active' : isDone ? 'done' : ""}`;
    item.style.padding = "0.5rem 0.75rem";
    item.style.borderRadius = "6px";
    item.style.cursor = "pointer";
    item.style.fontSize = "0.85rem";
    item.style.fontWeight = isCurrent ? "700" : "500";
    item.style.backgroundColor = isCurrent ? "#0284c7" : isDone ? "#e0f2fe" : "#f1f5f9";
    item.style.color = isCurrent ? "#ffffff" : isDone ? "#0369a1" : "#64748b";
    item.textContent = `${s.step}. ${s.label}`;
    item.onclick = () => loadStep(s.step);
    nav.appendChild(item);
  });
}

async function submitCustomBuildOrder() {
  const parts = {
    cpu_id: buildParts.cpu ? buildParts.cpu.id : null,
    mb_id: buildParts.mb ? buildParts.mb.id : null,
    ram_id: buildParts.ram ? buildParts.ram.id : null,
    storage_id: buildParts.storage ? buildParts.storage.id : null,
    gpu_id: buildParts.gpu ? buildParts.gpu.id : null,
    psu_id: buildParts.psu ? buildParts.psu.id : null,
    cabinet_id: buildParts.cabinet ? buildParts.cabinet.id : null,
    cooler_id: buildParts.cooler ? buildParts.cooler.id : null
  };
  
  try {
    const res = await api.post("/api/v1/assembly/orders", {
      parts: parts,
      notes: `Custom PC configuration with ${buildParts.os}`
    });
    showToast(`Assembly Order ${res.assembly_number} created successfully!`, "success");
    setTimeout(() => {
      window.location.href = `/account`;
    }, 1500);
  } catch (err) {
    showToast(`Failed: ${err.message}`, "error");
  }
}

async function requestBuildQuote() {
  let totalComp = 0;
  ["cpu", "mb", "ram", "storage", "gpu", "psu", "cabinet", "cooler"].forEach(k => {
    if (buildParts[k]) totalComp += buildParts[k].selling_price;
  });
  const subtotal = totalComp + buildParts.assembly_charge;
  try {
    const res = await api.post("/api/v1/quotations", { subtotal });
    showToast(`Quotation ${res.quotation_number} generated! Valid until ${res.valid_until}`, "success");
  } catch (e) {
    showToast(`Quotation error: ${e.message}`, "error");
  }
}

document.addEventListener("DOMContentLoaded", () => {
  if (document.getElementById("builder-step-nav")) {
    loadStep(1);
  }
});

window.loadStep = loadStep;
window.selectPart = selectPart;
window.submitCustomBuildOrder = submitCustomBuildOrder;
window.requestBuildQuote = requestBuildQuote;
