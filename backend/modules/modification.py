from database import query_all, query_one

def get_product_upgrades(product_id: int):
    base_prod = query_one("""
        SELECT p.*, ps.ram_gen, ps.ram_type, ps.max_ram_supported_gb, ps.ram_slots_free, 
               ps.storage_interface, ps.m2_slots, ps.sata_ports
        FROM products p
        LEFT JOIN product_specifications ps ON p.id = ps.product_id
        WHERE p.id = ?
    """, (product_id,))
    
    if not base_prod:
        return None
        
    upgrades = query_all("""
        SELECT uo.*, cp.title as component_title, cp.image_url as component_image
        FROM upgrade_options uo
        LEFT JOIN products cp ON uo.component_product_id = cp.id
        WHERE uo.base_product_id = ? AND uo.is_compatible = 1
        ORDER BY uo.upgrade_type ASC, uo.sort_order ASC
    """, (product_id,))
    
    grouped = {}
    for u in upgrades:
        t = u["upgrade_type"]
        if t not in grouped:
            grouped[t] = []
        grouped[t].append(u)
        
    return {
        "base_product": base_prod,
        "grouped_upgrades": grouped,
        "all_upgrades": upgrades
    }

def calculate_configured_price(base_product_id: int, selected_upgrade_ids: list):
    """
    SERVER-SIDE FINANCIAL INTEGRITY (NON-NEGOTIABLE RULE 8)
    Formula: Base Price + Upgrade Cost + Labour Charge + Applicable GST
    """
    base_prod = query_one("""
        SELECT id, title, sku, selling_price, discount_price, condition_grade
        FROM products 
        WHERE id = ?
    """, (base_product_id,))
    
    if not base_prod:
        raise ValueError(f"Product with ID {base_product_id} not found.")
        
    base_price = base_prod["discount_price"] if base_prod.get("discount_price") else base_prod["selling_price"]
    
    total_upgrade_cost = 0.0
    total_labour_charge = 0.0
    applied_upgrades = []
    
    if selected_upgrade_ids:
        placeholders = ",".join(["?"] * len(selected_upgrade_ids))
        upgrades = query_all(f"""
            SELECT * FROM upgrade_options
            WHERE id IN ({placeholders}) AND base_product_id = ? AND is_compatible = 1
        """, tuple(selected_upgrade_ids) + (base_product_id,))
        
        for u in upgrades:
            total_upgrade_cost += float(u["additional_cost"])
            total_labour_charge += float(u["labour_charge"])
            applied_upgrades.append({
                "upgrade_id": u["id"],
                "type": u["upgrade_type"],
                "title": u["title"],
                "spec_change": u["spec_change"],
                "cost": float(u["additional_cost"]),
                "labour": float(u["labour_charge"])
            })
            
    subtotal = base_price + total_upgrade_cost + total_labour_charge
    gst_rate = 18.0
    cgst_rate = 9.0
    sgst_rate = 9.0
    cgst_amount = round(subtotal * (cgst_rate / 100.0), 2)
    sgst_amount = round(subtotal * (sgst_rate / 100.0), 2)
    total_tax = round(cgst_amount + sgst_amount, 2)
    grand_total = round(subtotal + total_tax, 2)
    
    return {
        "base_product_id": base_prod["id"],
        "base_product_title": base_prod["title"],
        "base_price": base_price,
        "total_upgrade_cost": total_upgrade_cost,
        "total_labour_charge": total_labour_charge,
        "subtotal": subtotal,
        "cgst_amount": cgst_amount,
        "sgst_amount": sgst_amount,
        "total_tax": total_tax,
        "grand_total": grand_total,
        "applied_upgrades": applied_upgrades
    }
