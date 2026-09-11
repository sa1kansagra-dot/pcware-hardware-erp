import json
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "hardware_erp.db")
BACKEND_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "pcware_production.db")

def get_db():
    target_path = DB_PATH if os.path.exists(DB_PATH) else BACKEND_DB_PATH
    conn = sqlite3.connect(target_path)
    conn.row_factory = sqlite3.Row
    return conn

def process_bulk_upload(items_list):
    """
    Processes a list of items parsed from CSV and inserts/updates them in the products table.
    """
    if not isinstance(items_list, list) or len(items_list) == 0:
        raise ValueError("No product items provided for bulk upload.")

    success_count = 0
    updated_count = 0
    errors = []

    conn = get_db()
    cursor = conn.cursor()

    for idx, item in enumerate(items_list, 1):
        name = (item.get("name") or item.get("Product Name") or "").strip()
        if not name:
            errors.append(f"Row {idx}: Missing product name")
            continue

        category = (item.get("category") or item.get("Category") or "laptop").lower().strip()
        brand = (item.get("brand") or item.get("Brand") or "PCWARE").strip()
        
        try:
            purchase_price = float(item.get("purchase_price") or item.get("Purchase Price") or item.get("cost_price") or 0)
        except Exception: purchase_price = 0.0

        try:
            selling_price = float(item.get("selling_price") or item.get("Selling Price") or 0)
        except Exception: selling_price = 0.0

        try:
            stock_qty = int(item.get("stock_quantity") or item.get("Stock Quantity") or item.get("quantity") or 1)
        except Exception: stock_qty = 1

        hsn_sac = str(item.get("hsn_sac") or item.get("HSN Code") or "8471").strip()
        
        try:
            gst_rate = float(item.get("gst_rate") or item.get("GST Rate") or 18.0)
        except Exception: gst_rate = 18.0

        description = (item.get("description") or item.get("Description") or f"{brand} {name} Original Serialized Hardware Item").strip()
        specs = (item.get("specs") or item.get("Specifications") or f"Brand: {brand}, Warranty: 1-Year Official").strip()

        # Inspect table columns
        table_cols = [r["name"] for r in cursor.execute("PRAGMA table_info(products)").fetchall()]
        title_col = "title" if "title" in table_cols else "name"
        stock_col = "stock_quantity" if "stock_quantity" in table_cols else "stock"
        price_col = "selling_price" if "selling_price" in table_cols else "price"
        cat_col = "category" if "category" in table_cols else "category_slug"
        specs_col = "specs" if "specs" in table_cols else "specs_json"

        existing = cursor.execute(f"SELECT id, {stock_col}, {price_col} FROM products WHERE LOWER({title_col}) = LOWER(?)", (name,)).fetchone()
        
        if existing:
            current_stock = existing[stock_col] or 0
            new_qty = current_stock + stock_qty
            current_price = existing[price_col] or 0
            update_price = selling_price if selling_price > 0 else current_price

            update_sql = f"UPDATE products SET {stock_col} = ?, {price_col} = ?, description = ? WHERE id = ?"
            cursor.execute(update_sql, (new_qty, update_price, description, existing["id"]))
            updated_count += 1
        else:
            image_url = item.get("image_url") or "https://images.unsplash.com/photo-1591799264318-7e6ef8ddb7ea?w=400"
            if "name" in table_cols and "stock_quantity" in table_cols:
                hsn_col = "hsn_code" if "hsn_code" in table_cols else ("hsn_sac" if "hsn_sac" in table_cols else None)
                cols = ["name", "selling_price", "stock_quantity", "image_url"]
                vals = [name, selling_price, stock_qty, image_url]

                if "description" in table_cols:
                    cols.append("description")
                    vals.append(description)
                if "sku" in table_cols:
                    cols.append("sku")
                    vals.append(f"SKU-PCW-{os.urandom(3).hex().upper()}")
                if "cost_price" in table_cols:
                    cols.append("cost_price")
                    vals.append(purchase_price or round(selling_price * 0.8, 2))

                if "category" in table_cols:
                    cols.append("category")
                    vals.append(category)
                if "brand" in table_cols:
                    cols.append("brand")
                    vals.append(brand)
                if hsn_col:
                    cols.append(hsn_col)
                    vals.append(hsn_sac)
                if "gst_rate" in table_cols:
                    cols.append("gst_rate")
                    vals.append(gst_rate)
                if "specs" in table_cols:
                    cols.append("specs")
                    vals.append(specs)
                if "low_stock_threshold" in table_cols:
                    cols.append("low_stock_threshold")
                    vals.append(5)

                col_str = ", ".join(cols)
                val_str = ", ".join(["?"] * len(vals))
                cursor.execute(f"INSERT INTO products ({col_str}) VALUES ({val_str})", vals)
            else:
                cursor.execute("""
                    INSERT INTO products (
                        title, category_slug, price, original_price, cost_price, stock, 
                        image_url, description, rating, reviews_count, specs_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (name, category, selling_price, round(selling_price * 1.2), purchase_price, stock_qty, image_url, description, 4.9, 120, specs))
            success_count += 1

    conn.commit()
    conn.close()

    return {
        "success": True,
        "message": f"Bulk import processed: {success_count} new products created, {updated_count} existing stock quantities updated.",
        "created": success_count,
        "updated": updated_count,
        "errors": errors
    }
