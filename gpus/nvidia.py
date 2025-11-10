import subprocess
import csv
import logging

def safe_float(value):
    try:
        return float(value)
    except Exception:
        return None

def extract_nvidia_gpu_info():
    query_fields = [
        "index", "uuid", "name", "temperature.gpu", "utilization.gpu",
        "utilization.memory", "pstate", "memory.total", "memory.used",
        "fan.speed", "power.draw", "clocks.current.graphics", "clocks.current.memory",
        "pci.bus_id"
    ]
    cmd = [
        "/usr/bin/nvidia-smi",
        f"--query-gpu={','.join(query_fields)}",
        "--format=csv,noheader,nounits"
    ]
    try:
        output = subprocess.check_output(cmd, encoding="utf-8")
    except Exception as e:
        logging.error(f"Error running nvidia-smi: {e}")
        return []

    reader = csv.reader(output.strip().split("\n"))
    gpu_list = []

    for row in reader:
        values = dict(zip(query_fields, row))
        mem_total = safe_float(values["memory.total"])
        mem_used = safe_float(values["memory.used"])
        mem_util = (mem_used / mem_total * 100) if mem_used and mem_total else None

        gpu_info = {
            "vendor": "nvidia",
            "gpu_id": f'gpu{values["index"]}',
            "uuid": values["uuid"],
            "name": values["name"],
            "pci_bus": values["pci.bus_id"],
            "gpu_temp_c": safe_float(values["temperature.gpu"]),
            "fan_speed_percent": safe_float(values["fan.speed"]),
            "power_w": safe_float(values["power.draw"]),
            "gpu_clock_mhz": safe_float(values["clocks.current.graphics"]),
            "mem_clock_mhz": safe_float(values["clocks.current.memory"]),
            "gpu_util_percent": safe_float(values["utilization.gpu"]),
            "mem_util_percent": mem_util,
            "memory_used_mib": mem_used,
            "memory_total_mib": mem_total,
        }
        gpu_list.append(gpu_info)

    return gpu_list

def extract_nvidia_processes():
    try:
        output = subprocess.check_output([
            "/usr/bin/nvidia-smi", "--query-compute-apps=pid,process_name,used_gpu_memory,gpu_uuid",
            "--format=csv,noheader,nounits"
        ], encoding="utf-8")
    except Exception as e:
        logging.error(f"Error fetching NVIDIA processes: {e}")
        return []

    processes = []
    for line in output.strip().splitlines():
        parts = [p.strip() for p in line.split(",")]
        if len(parts) != 4:
            continue
        pid, name, mem, uuid = parts
        processes.append({
            "vendor": "nvidia",
            "pid": int(pid),
            "name": name,
            "gpu_id": uuid,
            "gpu_name": "N/A",  # Optionally map UUID to name
            "used_memory_mib": float(mem),
            "gpu_util_percent": 0  # NVIDIA does not expose per-process utilization directly
        })

    return processes
