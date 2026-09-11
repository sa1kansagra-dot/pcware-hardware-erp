import sys
import os
sys.path.insert(0, os.path.abspath("backend"))
from modules.compatibility import validate_system_compatibility

def run_tests():
    print(">>> Running 8-Vector Hardware Compatibility Engine Tests (Rules 4 & 5)...")
    
    # 1. Test Incompatible CPU & Motherboard (AM5 CPU 7 + Intel LGA1700 MB 11)
    incompat_socket = validate_system_compatibility({
        "cpu_id": 7,  # AMD Ryzen 5 7600X (AM5)
        "mb_id": 11   # MSI PRO B760M-A (LGA1700)
    })
    assert incompat_socket["is_compatible"] == False, "Expected socket mismatch failure"
    assert any(m["rule"] == "CPU_SOCKET_MISMATCH" for m in incompat_socket["mismatches"])
    print("  [PASS] Correctly rejected AM5 CPU with Intel LGA1700 Motherboard.")

    # 2. Test Incompatible RAM & Motherboard (DDR4 RAM 13 + DDR5 Motherboard 10)
    incompat_ram = validate_system_compatibility({
        "cpu_id": 7,   # AM5
        "mb_id": 10,   # ASUS B650 (DDR5)
        "ram_id": 13   # Crucial 16GB DDR4
    })
    assert incompat_ram["is_compatible"] == False, "Expected RAM generation mismatch failure"
    assert any(m["rule"] == "RAM_GENERATION_MISMATCH" for m in incompat_ram["mismatches"])
    print("  [PASS] Correctly rejected DDR4 RAM with DDR5 Motherboard.")

    # 3. Test Compatible Build (AM5 + B650 + DDR5 + NVMe + RTX 4070S + 850W Gold PSU)
    compat_build = validate_system_compatibility({
        "cpu_id": 7,       # AMD Ryzen 5 7600X (AM5)
        "mb_id": 10,       # ASUS B650 (AM5, DDR5, ATX)
        "ram_id": 12,      # Kingston Fury 16GB DDR5
        "storage_id": 15,  # Samsung 980 Pro 1TB NVMe
        "gpu_id": 17,      # ASUS RTX 4070 Super 12GB
        "psu_id": 18,      # Corsair RM850e 850W Gold
        "cabinet_id": 19,  # DeepCool CC560 ATX
        "cooler_id": 20    # DeepCool AK400
    })
    assert compat_build["is_compatible"] == True, f"Expected compatible build, got errors: {compat_build['mismatches']}"
    assert len(compat_build["mismatches"]) == 0
    assert compat_build["power_analysis"]["psu_rated_watts"] == 850
    print("  [PASS] Verified 100% compatible custom gaming rig configuration.")
    print("ALL COMPATIBILITY ENGINE TESTS PASSED SUCCESSFULLY!\n")

if __name__ == "__main__":
    run_tests()
