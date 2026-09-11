import json
from database import query_all, query_one, execute_commit

def list_products(filters=None):
    filters = filters or {}
    query = """
        SELECT p.*, c.name as category_name, c.slug as category_slug, 
               b.name as brand_name, b.slug as brand_slug,
               (SELECT COUNT(*) FROM serialized_units su WHERE su.product_id = p.id AND su.current_status = 'available') as available_serials_count
        FROM products p
        JOIN categories c ON p.category_id = c.id
        JOIN brands b ON p.brand_id = b.id
        WHERE p.is_active = 1
    """
    params = []
    
    if filters.get("category_slug"):
        query += " AND c.slug = ?"
        params.append(filters["category_slug"])
    if filters.get("product_type"):
        query += " AND p.product_type = ?"
        params.append(filters["product_type"])
    if filters.get("brand_slug"):
        query += " AND b.slug = ?"
        params.append(filters["brand_slug"])
    if filters.get("condition_grade"):
        query += " AND p.condition_grade = ?"
        params.append(filters["condition_grade"])
    if filters.get("featured"):
        query += " AND p.featured = 1"
    if filters.get("search"):
        q = f"%{filters['search'].strip()}%"
        query += " AND (p.title LIKE ? OR p.sku LIKE ? OR p.description LIKE ?)"
        params.extend([q, q, q])
    if filters.get("min_price"):
        query += " AND p.selling_price >= ?"
        params.append(float(filters["min_price"]))
    if filters.get("max_price"):
        query += " AND p.selling_price <= ?"
        params.append(float(filters["max_price"]))
        
    query += " ORDER BY p.featured DESC, p.id DESC"
    products = query_all(query, tuple(params))
    
    # Attach specifications to products
    for p in products:
        spec = query_one("SELECT * FROM product_specifications WHERE product_id = ?", (p["id"],))
        if spec:
            if spec.get("raw_specs_json"):
                try:
                    spec["raw_specs"] = json.loads(spec["raw_specs_json"])
                except:
                    spec["raw_specs"] = {}
            p["specifications"] = spec
        else:
            p["specifications"] = {}
            
    return products

def get_product_by_slug(slug: str):
    product = query_one("""
        SELECT p.*, c.name as category_name, c.slug as category_slug, 
               b.name as brand_name, b.slug as brand_slug,
               (SELECT COUNT(*) FROM serialized_units su WHERE su.product_id = p.id AND su.current_status = 'available') as available_serials_count
        FROM products p
        JOIN categories c ON p.category_id = c.id
        JOIN brands b ON p.brand_id = b.id
        WHERE p.slug = ?
    """, (slug,))
    if not product:
        return None
        
    # Specifications
    spec = query_one("SELECT * FROM product_specifications WHERE product_id = ?", (product["id"],))
    if spec:
        if spec.get("raw_specs_json"):
            try:
                spec["raw_specs"] = json.loads(spec["raw_specs_json"])
            except:
                spec["raw_specs"] = {}
        product["specifications"] = spec
    else:
        product["specifications"] = {}
        
    # Upgrades available for this base product
    upgrades = query_all("""
        SELECT uo.*, cp.title as component_title, cp.selling_price as component_market_price
        FROM upgrade_options uo
        LEFT JOIN products cp ON uo.component_product_id = cp.id
        WHERE uo.base_product_id = ? AND uo.is_compatible = 1
        ORDER BY uo.sort_order ASC
    """, (product["id"],))
    product["upgrade_options"] = upgrades
    
    # Available serial numbers list (if authenticated staff view)
    serials = query_all("""
        SELECT id, serial_number, asset_tag, location_rack, condition_grade, current_status
        FROM serialized_units
        WHERE product_id = ? AND current_status = 'available'
    """, (product["id"],))
    product["available_serials"] = serials
    
    return product

def get_product_by_id(product_id: int):
    p = query_one("SELECT slug FROM products WHERE id = ?", (product_id,))
    if p:
        return get_product_by_slug(p["slug"])
    return None

def list_categories():
    categories = query_all("""
        SELECT c.*, (SELECT COUNT(*) FROM products p WHERE p.category_id = c.id AND p.is_active = 1) as product_count
        FROM categories c
        WHERE c.is_active = 1
        ORDER BY c.id ASC
    """)
    return categories

def list_brands():
    brands = query_all("""
        SELECT b.*, (SELECT COUNT(*) FROM products p WHERE p.brand_id = b.id AND p.is_active = 1) as product_count
        FROM brands b
        WHERE b.is_active = 1
        ORDER BY b.name ASC
    """)
    return brands
