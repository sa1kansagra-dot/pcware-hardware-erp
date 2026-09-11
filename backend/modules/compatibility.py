import json
from database import query_all, query_one

def validate_system_compatibility(parts: dict):
    """
    Authoritative 8-Vector Hardware Compatibility Validator
    parts dict keys: cpu_id, mb_id, ram_id, storage_id, gpu_id, psu_id, cabinet_id, cooler_id
    """
    results = {
        "is_compatible": True,
        "mismatches": [],
        "warnings": [],
        "specs_evaluated": {},
        "power_analysis": {}
    }
    
    # 1. Fetch Specs
    cpu = query_one("""
        SELECT p.title, ps.* FROM products p 
        JOIN product_specifications ps ON p.id = ps.product_id 
        WHERE p.id = ?
    """, (parts.get("cpu_id"),)) if parts.get("cpu_id") else None
    
    mb = query_one("""
        SELECT p.title, ps.* FROM products p 
        JOIN product_specifications ps ON p.id = ps.product_id 
        WHERE p.id = ?
    """, (parts.get("mb_id"),)) if parts.get("mb_id") else None
    
    ram = query_one("""
        SELECT p.title, ps.* FROM products p 
        JOIN product_specifications ps ON p.id = ps.product_id 
        WHERE p.id = ?
    """, (parts.get("ram_id"),)) if parts.get("ram_id") else None
    
    storage = query_one("""
        SELECT p.title, ps.* FROM products p 
        JOIN product_specifications ps ON p.id = ps.product_id 
        WHERE p.id = ?
    """, (parts.get("storage_id"),)) if parts.get("storage_id") else None
    
    gpu = query_one("""
        SELECT p.title, ps.* FROM products p 
        JOIN product_specifications ps ON p.id = ps.product_id 
        WHERE p.id = ?
    """, (parts.get("gpu_id"),)) if parts.get("gpu_id") else None
    
    psu = query_one("""
        SELECT p.title, ps.* FROM products p 
        JOIN product_specifications ps ON p.id = ps.product_id 
        WHERE p.id = ?
    """, (parts.get("psu_id"),)) if parts.get("psu_id") else None
    
    cabinet = query_one("""
        SELECT p.title, ps.* FROM products p 
        JOIN product_specifications ps ON p.id = ps.product_id 
        WHERE p.id = ?
    """, (parts.get("cabinet_id"),)) if parts.get("cabinet_id") else None
    
    cooler = query_one("""
        SELECT p.title, ps.* FROM products p 
        JOIN product_specifications ps ON p.id = ps.product_id 
        WHERE p.id = ?
    """, (parts.get("cooler_id"),)) if parts.get("cooler_id") else None

    # Calculate Total Wattage
    cpu_watts = (cpu["cpu_tdp_watts"] if cpu and cpu.get("cpu_tdp_watts") else 65)
    gpu_watts = (gpu["gpu_length_mm"] if gpu and gpu.get("gpu_length_mm") else 0)  # default check
    if gpu:
        try:
            raw_g = json.loads(gpu.get("raw_specs_json") or "{}")
            gpu_watts = raw_g.get("gpu_tdp_watts", 200)
        except:
            gpu_watts = 200
    else:
        gpu_watts = 0
        
    mb_watts = 50
    ram_watts = 15
    storage_watts = 10
    fans_cooler_watts = 30
    total_watts = cpu_watts + gpu_watts + mb_watts + ram_watts + storage_watts + fans_cooler_watts
    recommended_psu = int(total_watts * 1.30)
    
    results["power_analysis"] = {
        "estimated_total_watts": total_watts,
        "recommended_psu_watts": recommended_psu,
        "cpu_watts": cpu_watts,
        "gpu_watts": gpu_watts
    }

    # RULE 1: CPU Socket vs Motherboard Socket
    if cpu and mb:
        cpu_sock = (cpu.get("cpu_socket") or "").strip().upper()
        mb_sock = (mb.get("cpu_socket") or "").strip().upper()
        if cpu_sock and mb_sock and cpu_sock != mb_sock:
            results["is_compatible"] = False
            results["mismatches"].append({
                "rule": "CPU_SOCKET_MISMATCH",
                "severity": "FATAL",
                "message": f"CPU socket '{cpu_sock}' is physically incompatible with Motherboard socket '{mb_sock}'. Example: AM5 CPUs cannot fit in LGA1700 Motherboards."
            })
            
    # RULE 2: Motherboard RAM Generation vs RAM Generation
    if mb and ram:
        mb_ram_gen = (mb.get("ram_gen") or "").strip().upper()
        ram_gen = (ram.get("ram_gen") or "").strip().upper()
        if mb_ram_gen and ram_gen and mb_ram_gen != ram_gen:
            results["is_compatible"] = False
            results["mismatches"].append({
                "rule": "RAM_GENERATION_MISMATCH",
                "severity": "FATAL",
                "message": f"Motherboard supports '{mb_ram_gen}' memory, but selected RAM is '{ram_gen}'. DDR4 and DDR5 have different notch positions and voltages."
            })

    # RULE 3: Motherboard Form Factor vs Cabinet Form Factor
    if mb and cabinet:
        mb_ff = (mb.get("form_factor") or "").strip().upper()
        cab_raw = json.loads(cabinet.get("raw_specs_json") or "{}")
        supported_mb = [s.upper() for s in cab_raw.get("supported_mb", ["ATX", "MICRO-ATX", "MINI-ITX"])]
        if mb_ff and mb_ff not in supported_mb:
            results["is_compatible"] = False
            results["mismatches"].append({
                "rule": "CHASSIS_FORM_FACTOR_INCOMPATIBLE",
                "severity": "FATAL",
                "message": f"Motherboard form factor '{mb_ff}' does not fit in selected Cabinet (supports {supported_mb})."
            })

    # RULE 4: GPU Length vs Cabinet Clearance
    if gpu and cabinet:
        cab_raw = json.loads(cabinet.get("raw_specs_json") or "{}")
        max_gpu_len = cab_raw.get("max_gpu_len_mm", 360)
        gpu_len = gpu.get("gpu_length_mm") or 270
        if gpu_len > max_gpu_len:
            results["is_compatible"] = False
            results["mismatches"].append({
                "rule": "GPU_LENGTH_CLEARANCE_EXCEEDED",
                "severity": "FATAL",
                "message": f"GPU length ({gpu_len}mm) exceeds Cabinet maximum clearance ({max_gpu_len}mm)."
            })

    # RULE 5: Power Supply Headroom Rule (Non-negotiable)
    if psu:
        psu_raw = json.loads(psu.get("raw_specs_json") or "{}")
        rated_watts = psu_raw.get("rated_watts") or psu.get("psu_wattage") or 500
        results["power_analysis"]["psu_rated_watts"] = rated_watts
        if rated_watts < total_watts:
            results["is_compatible"] = False
            results["mismatches"].append({
                "rule": "PSU_WATTAGE_CRITICAL_DEFICIT",
                "severity": "FATAL",
                "message": f"PSU rated at {rated_watts}W is LOWER than estimated system power consumption ({total_watts}W). System will shut down under load."
            })
        elif rated_watts < recommended_psu:
            results["warnings"].append({
                "rule": "PSU_HEADROOM_TIGHT",
                "severity": "WARNING",
                "message": f"PSU has {rated_watts}W. While above base consumption ({total_watts}W), 30% headroom recommends {recommended_psu}W."
            })

    # RULE 6: CPU Cooler Socket Support
    if cpu and cooler:
        cpu_sock = (cpu.get("cpu_socket") or "").strip().upper()
        cooler_raw = json.loads(cooler.get("raw_specs_json") or "{}")
        supp_sockets = [s.upper() for s in cooler_raw.get("supported_sockets", ["AM5", "AM4", "LGA1700", "LGA1200"])]
        if cpu_sock and cpu_sock not in supp_sockets:
            results["is_compatible"] = False
            results["mismatches"].append({
                "rule": "COOLER_SOCKET_INCOMPATIBLE",
                "severity": "FATAL",
                "message": f"CPU Cooler mounting bracket does not support socket '{cpu_sock}'."
            })

    return results

def get_compatible_components_list(current_selections: dict, component_category: str):
    """
    Filters the catalog to return ONLY components compatible with current selections.
    """
    # Start with all active products in that category
    products = query_all("""
        SELECT p.*, ps.* 
        FROM products p
        JOIN product_specifications ps ON p.id = ps.product_id
        JOIN categories c ON p.category_id = c.id
        WHERE p.is_active = 1 AND c.slug = ?
        ORDER BY p.selling_price ASC
    """, (component_category,))
    
    compatible_list = []
    for prod in products:
        test_parts = dict(current_selections)
        
        if component_category == "processors":
            test_parts["cpu_id"] = prod["id"]
        elif component_category == "motherboards":
            test_parts["mb_id"] = prod["id"]
        elif component_category == "ram":
            test_parts["ram_id"] = prod["id"]
        elif component_category == "storage":
            test_parts["storage_id"] = prod["id"]
        elif component_category == "gpus":
            test_parts["gpu_id"] = prod["id"]
        elif component_category == "psus":
            test_parts["psu_id"] = prod["id"]
        elif component_category == "cabinets":
            test_parts["cabinet_id"] = prod["id"]
        elif component_category == "cooling":
            test_parts["cooler_id"] = prod["id"]
            
        validation = validate_system_compatibility(test_parts)
        if validation["is_compatible"]:
            compatible_list.append(prod)
            
    return compatible_list
