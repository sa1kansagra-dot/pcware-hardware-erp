// PC WARE Enterprise API Client
const API_BASE = "";

function showToast(message, type = "info") {
  let container = document.getElementById("toast-container");
  if (!container) {
    container = document.createElement("div");
    container.id = "toast-container";
    document.body.appendChild(container);
  }
  const toast = document.createElement("div");
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `<span>${type === "error" ? "⚠️" : type === "success" ? "✅" : "ℹ️"}</span> <span>${message}</span>`;
  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateX(100%)";
    toast.style.transition = "all 0.3s ease";
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

async function apiRequest(endpoint, method = "GET", body = null) {
  const headers = { "Content-Type": "application/json" };
  const token = localStorage.getItem("pcware_token");
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const options = { method, headers };
  if (body && (method === "POST" || method === "PUT")) {
    options.body = JSON.stringify(body);
  }

  try {
    const res = await fetch(`${API_BASE}${endpoint}`, options);
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      const errMsg = data.error || `HTTP ${res.status}: ${res.statusText}`;
      if (res.status === 422 && data.code === "QC_RULE_VIOLATION") {
        showToast(`QC RULE ENFORCED: ${errMsg}`, "error");
      } else if (res.status === 422 && data.code === "COMPATIBILITY_ERROR") {
        showToast(`COMPATIBILITY MISMATCH: ${errMsg}`, "error");
      }
      throw new Error(errMsg);
    }
    return data;
  } catch (err) {
    console.error(`API Error on [${method}] ${endpoint}:`, err);
    throw err;
  }
}

const api = {
  get: (url) => apiRequest(url, "GET"),
  post: (url, data) => apiRequest(url, "POST", data),
  getAuthUser: () => {
    try {
      return JSON.parse(localStorage.getItem("pcware_user") || "null");
    } catch {
      return null;
    }
  },
  setAuth: (token, user) => {
    localStorage.setItem("pcware_token", token);
    localStorage.setItem("pcware_user", JSON.stringify(user));
  },
  logout: () => {
    localStorage.removeItem("pcware_token");
    localStorage.removeItem("pcware_user");
    window.location.href = "/login";
  }
};

window.api = api;
window.showToast = showToast;
