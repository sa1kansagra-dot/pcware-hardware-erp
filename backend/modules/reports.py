from database import query_all, query_one

def get_dashboard_metrics():
    # 1. Serialized Hardware Units Breakdown
    counts = query_all("""
        SELECT current_status, COUNT(*) as cnt, SUM(purchase_cost) as total_cost, SUM(selling_price) as total_value
        FROM serialized_units
        GROUP BY current_status
    """)
    status_map = {row["current_status"]: row for row in counts}
    
    total_received = sum(r["cnt"] for r in counts)
    avail_units = status_map.get("available", {}).get("cnt", 0)
    avail_value = status_map.get("available", {}).get("total_value", 0.0) or 0.0
    qc_pending = (status_map.get("qc_pending", {}).get("cnt", 0) + 
                  status_map.get("qc_testing", {}).get("cnt", 0))
    qc_passed_ready_for_inward = status_map.get("qc_passed", {}).get("cnt", 0)
    qc_failed = (status_map.get("qc_failed", {}).get("cnt", 0) + 
                 status_map.get("repair_required", {}).get("cnt", 0) + 
                 status_map.get("hold", {}).get("cnt", 0))
    sold_units = status_map.get("sold", {}).get("cnt", 0)
    
    # 2. Sales & Revenue
    sales_agg = query_one("""
        SELECT COUNT(*) as total_orders, 
               COALESCE(SUM(grand_total), 0) as total_revenue,
               COALESCE(SUM(tax_amount), 0) as total_gst
        FROM sales_orders
        WHERE payment_status = 'paid'
    """)
    
    # 3. Purchases & Lot Inwarding Cost
    purchases_agg = query_one("""
        SELECT COUNT(*) as total_receiving_batches,
               COALESCE(SUM(purchase_cost_total), 0) as total_procurement_cost
        FROM receiving_records
    """)
    
    # 4. Custom PC Assembly Orders
    asm_agg = query_one("""
        SELECT COUNT(*) as total_assemblies,
               COUNT(CASE WHEN status != 'delivered' AND status != 'cancelled' THEN 1 END) as active_assemblies,
               COUNT(CASE WHEN status = 'ready' THEN 1 END) as ready_assemblies
        FROM assembly_orders
    """)
    
    # 5. Service & RMA Repair Tickets
    repairs_agg = query_one("""
        SELECT COUNT(*) as total_repairs,
               COUNT(CASE WHEN repair_status NOT IN ('delivered', 'cancelled') THEN 1 END) as open_repairs,
               COUNT(CASE WHEN repair_status = 'repaired' THEN 1 END) as repaired_ready
        FROM repair_tickets
    """)
    
    # 6. Referral Program Metrics
    referrals_agg = query_one("""
        SELECT COUNT(*) as total_referral_accounts,
               COALESCE(SUM(points_in), 0) as total_points_issued,
               COALESCE(SUM(points_out), 0) as total_points_redeemed
        FROM referral_point_ledger
    """)
    
    return {
        "inventory": {
            "total_units_tracked": total_received,
            "available_sellable_units": avail_units,
            "sellable_stock_value": avail_value,
            "qc_pending_units": qc_pending,
            "qc_passed_ready_for_inward": qc_passed_ready_for_inward,
            "qc_failed_or_quarantined": qc_failed,
            "sold_units": sold_units
        },
        "sales": {
            "total_orders": sales_agg["total_orders"],
            "total_revenue": sales_agg["total_revenue"],
            "total_gst_collected": sales_agg["total_gst"]
        },
        "procurement": {
            "total_batches": purchases_agg["total_receiving_batches"],
            "total_procurement_cost": purchases_agg["total_procurement_cost"]
        },
        "assembly": {
            "total_assemblies": asm_agg["total_assemblies"],
            "active_assemblies": asm_agg["active_assemblies"],
            "ready_assemblies": asm_agg["ready_assemblies"]
        },
        "repairs": {
            "total_repairs": repairs_agg["total_repairs"],
            "open_repairs": repairs_agg["open_repairs"],
            "repaired_ready": repairs_agg["repaired_ready"]
        },
        "referrals": {
            "total_transactions": referrals_agg["total_referral_accounts"],
            "points_issued": referrals_agg["total_points_issued"],
            "points_redeemed": referrals_agg["total_points_redeemed"],
            "net_active_points": (referrals_agg["total_points_issued"] - referrals_agg["total_points_redeemed"])
        }
    }

def get_recent_movements():
    return query_all("""
        SELECT im.*, p.title as product_title, su.serial_number, u.full_name as moved_by_name
        FROM inventory_movements im
        JOIN products p ON im.product_id = p.id
        LEFT JOIN serialized_units su ON im.serial_unit_id = su.id
        LEFT JOIN users u ON im.moved_by = u.id
        ORDER BY im.id DESC LIMIT 20
    """)
