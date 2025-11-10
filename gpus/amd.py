import json
import os
import subprocess
import logging

def get_rocm_smi_data():
    try:
        result = subprocess.run(
            ["/usr/bin/rocm-smi", "--showallinfo", "--json"],
            check=True,
            stdout=subprocess.PIPE,
            text=True
        )
        return json.loads(result.stdout)
    except Exception as e:
        logging.error(f"Error running rocm-smi: {e}")
        return {}

def get_drm_cards_by_pci():
    pci_map = {}
    drm_path = "/sys/class/drm"
    for entry in os.listdir(drm_path):
        if entry.startswith("card") and "-" not in entry:
            device_path = os.path.realpath(os.path.join(drm_path, entry, "device"))
            pci_id = os.path.basename(device_path)
            pci_map[pci_id] = entry
    return pci_map

def get_power_usage_watts(drm_card):
    hwmon_path = f"/sys/class/drm/{drm_card}/device/hwmon"
    if not os.path.exists(hwmon_path):
        return None
    try:
        hwmon_dirs = os.listdir(hwmon_path)
        if not hwmon_dirs:
            return None
        power_path = os.path.join(hwmon_path, hwmon_dirs[0], "power1_input")
        if os.path.exists(power_path):
            with open(power_path) as f:
                return int(f.read().strip()) / 1_000_000
    except Exception:
        return None
    return None

def get_mem_info_mib(drm_card):
    base_path = f"/sys/class/drm/{drm_card}/device"
    result = {}
    try:
        for field in ["mem_info_vram_total", "mem_info_vram_used"]:
            path = os.path.join(base_path, field)
            if os.path.exists(path):
                with open(path) as f:
                    result[field] = int(f.read().strip()) / (1024 * 1024)
    except Exception as e:
        logging.warning(f"Could not read AMD memory info: {e}")
    return {
        "memory_total_mib": result.get("mem_info_vram_total"),
        "memory_used_mib": result.get("mem_info_vram_used"),
        "mem_util_percent": (
            result["mem_info_vram_used"] / result["mem_info_vram_total"] * 100
            if "mem_info_vram_used" in result and "mem_info_vram_total" in result
            else None
        ),
    } if result else {}

def parse_clock(clock_str):
    if not clock_str:
        return None
    try:
        return int(clock_str.replace("(", "").replace("Mhz)", ""))
    except Exception:
        return None

def extract_amd_gpu_info():
    rocm_data = get_rocm_smi_data()
    pci_map = get_drm_cards_by_pci()

    gpu_list = []
    for card_id, data in rocm_data.items():
        if not card_id.startswith("card"):
            continue

        name = data.get("Card Series")
        pci_id = data.get("PCI Bus")
        drm_card = pci_map.get(pci_id)

        clocks = {
            "gpu_clock_mhz": parse_clock(data.get("sclk clock speed:")),
            "mem_clock_mhz": parse_clock(data.get("mclk clock speed:")),
        }

        mem_info = get_mem_info_mib(drm_card) if drm_card else {}

        gpu_info = {
            "vendor": "amd",
            "gpu_id": card_id,
            "name": name,
            "pci_bus": pci_id,
            "gpu_temp_c": float(data.get("Temperature (Sensor edge) (C)", 0)),
            "fan_speed_percent": float(data.get("Fan speed (%)", 0)),
            "power_w": get_power_usage_watts(drm_card),
            "gpu_clock_mhz": clocks["gpu_clock_mhz"],
            "mem_clock_mhz": clocks["mem_clock_mhz"],
            "gpu_util_percent": float(data.get("GPU use (%)", 0)),
            "mem_util_percent": mem_info.get("mem_util_percent"),
            "memory_used_mib": mem_info.get("memory_used_mib"),
            "memory_total_mib": mem_info.get("memory_total_mib"),
        }

        gpu_list.append(gpu_info)

    return gpu_list

def extract_amd_processes():
    rocm_data = get_rocm_smi_data()
    processes = []

    for key, val in rocm_data.get("system", {}).items():
        if key.startswith("PID"):
            pid = int(key[3:])
            parts = val.split(",")
            if len(parts) >= 5:
                name = parts[0].strip()
                gpu_id = f"card{parts[1].strip()}"
                mem_bytes = int(parts[2].strip())
                gpu_util = float(parts[4].strip())

                processes.append({
                    "vendor": "amd",
                    "pid": pid,
                    "name": name,
                    "gpu_id": gpu_id,
                    "gpu_name": rocm_data.get(gpu_id, {}).get("Card series", "Unknown"),
                    "used_memory_mib": mem_bytes / (1024 * 1024),
                    "gpu_util_percent": gpu_util,
                })

    return processes
