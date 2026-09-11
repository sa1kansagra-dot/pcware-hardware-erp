// PC WARE Store & Cart Manager
const Cart = {
  getItems: function() {
    try {
      return JSON.parse(localStorage.getItem("pcware_cart") || "[]");
    } catch {
      return [];
    }
  },
  saveItems: function(items) {
    localStorage.setItem("pcware_cart", JSON.stringify(items));
    this.updateBadge();
  },
  addItem: function(product, selectedUpgrades = []) {
    const items = this.getItems();
    const existingIndex = items.findIndex(i => i.product.id === product.id && JSON.stringify(i.selectedUpgrades) === JSON.stringify(selectedUpgrades));
    if (existingIndex > -1) {
      items[existingIndex].quantity += 1;
    } else {
      items.push({
        product: product,
        selectedUpgrades: selectedUpgrades,
        quantity: 1
      });
    }
    this.saveItems(items);
    showToast(`Added '${product.title}' to cart.`, "success");
  },
  removeItem: function(index) {
    const items = this.getItems();
    items.splice(index, 1);
    this.saveItems(items);
    if (window.renderCart) window.renderCart();
  },
  updateBadge: function() {
    const items = this.getItems();
    const count = items.reduce((sum, i) => sum + i.quantity, 0);
    const badges = document.querySelectorAll(".cart-count-badge");
    badges.forEach(b => {
      b.textContent = count;
      b.style.display = count > 0 ? "inline-flex" : "none";
    });
  }
};

document.addEventListener("DOMContentLoaded", () => {
  Cart.updateBadge();
  
  // Header User Session Sync
  const user = api.getAuthUser();
  const authNav = document.getElementById("nav-auth-section");
  if (authNav) {
    if (user) {
      authNav.innerHTML = `
        <div style="display: flex; align-items: center; gap: 0.75rem;">
          <a href="/account" class="btn btn-sm btn-secondary">👤 ${user.full_name.split(" ")[0]}</a>
          ${user.role_id <= 7 ? '<a href="/erp" class="btn btn-sm btn-primary">⚙️ ERP</a>' : ""}
          <button onclick="api.logout()" class="btn btn-sm btn-outline" style="border:none; color:#ef4444;">Logout</button>
        </div>
      `;
    } else {
      authNav.innerHTML = `
        <a href="/login" class="nav-link" style="margin-right: 0.5rem;">Sign In</a>
        <a href="/register" class="btn btn-sm btn-primary">Register</a>
      `;
    }
  }
});

window.Cart = Cart;
