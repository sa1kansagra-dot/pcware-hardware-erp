// PC WARE Client-Side Instant Compatibility Engine
const CompatibilityEngine = {
  checkCompatibility: function(parts) {
    // parts: { cpu, mb, ram, storage, gpu, psu, cabinet, cooler }
    const mismatches = [];
    const warnings = [];
    
    // 1. Socket Check
    if (parts.cpu && parts.mb) {
      const cpuSock = (parts.cpu.cpu_socket || "").trim().toUpperCase();
      const mbSock = (parts.mb.cpu_socket || "").trim().toUpperCase();
      if (cpuSock && mbSock && cpuSock !== mbSock) {
        mismatches.push({
          rule: "SOCKET_MISMATCH",
          message: `CPU Socket (${cpuSock}) does not match Motherboard Socket (${mbSock}).`
        });
      }
    }
    
    // 2. RAM Generation Check
    if (parts.mb && parts.ram) {
      const mbRamGen = (parts.mb.ram_gen || "").trim().toUpperCase();
      const ramGen = (parts.ram.ram_gen || "").trim().toUpperCase();
      if (mbRamGen && ramGen && mbRamGen !== ramGen) {
        mismatches.push({
          rule: "RAM_GEN_MISMATCH",
          message: `Motherboard requires ${mbRamGen} RAM, but selected RAM is ${ramGen}.`
        });
      }
    }
    
    // 3. Power Analysis
    const cpuWatts = parts.cpu ? (parts.cpu.cpu_tdp_watts || 65) : 65;
    const gpuWatts = parts.gpu ? (parts.gpu.gpu_tdp_watts || 200) : 0;
    const baseSystemWatts = 90; // MB + RAM + NVMe + Fans
    const totalWatts = cpuWatts + gpuWatts + baseSystemWatts;
    const recommendedPsu = Math.round(totalWatts * 1.30);
    
    if (parts.psu) {
      const psuWatts = parts.psu.rated_watts || parts.psu.psu_wattage || 500;
      if (psuWatts < totalWatts) {
        mismatches.push({
          rule: "PSU_DEFICIT",
          message: `PSU (${psuWatts}W) is lower than estimated system power consumption (${totalWatts}W).`
        });
      } else if (psuWatts < recommendedPsu) {
        warnings.push({
          rule: "PSU_HEADROOM",
          message: `PSU (${psuWatts}W) operates close to limit. 30% headroom recommends ${recommendedPsu}W.`
        });
      }
    }
    
    return {
      isCompatible: mismatches.length === 0,
      mismatches,
      warnings,
      estimatedWatts: totalWatts,
      recommendedPsuWatts: recommendedPsu
    };
  }
};

window.CompatibilityEngine = CompatibilityEngine;
