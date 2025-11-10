import logging
import time
from typing import Dict

from prometheus_client import Gauge, start_http_server

from gpus import amd
from gpus import nvidia

def setup_metrics() -> Dict[str, Gauge]:
    labels = ["vendor", "gpu_id", "name", "pci_bus"]

    gauges = {
        "power_w": Gauge("gpu_power_watts", "Power consumption in watts", labels),
        "gpu_temp_c": Gauge("gpu_temperature_celsius", "GPU temperature in Celsius", labels),
        "gpu_clock_mhz": Gauge("gpu_clock_mhz", "GPU core clock speed in MHz", labels),
        "mem_clock_mhz": Gauge("gpu_memory_clock_mhz", "GPU memory clock speed in MHz", labels),
        "fan_speed_percent": Gauge("gpu_fan_speed_percent", "Fan speed percentage", labels),
        "gpu_util_percent": Gauge("gpu_utilization_percent", "GPU utilization percent", labels),
        "mem_util_percent": Gauge("gpu_memory_utilization_percent", "GPU memory utilization percent", labels),
        "memory_used_mib": Gauge("gpu_memory_used_mib", "Used memory in MiB", labels),
        "memory_total_mib": Gauge("gpu_memory_total_mib", "Total memory in MiB", labels),
    }

    return gauges

# One gauge per process, updated per collection
gpu_process_info = Gauge(
    "gpu_process_info",
    "GPU process usage (1 = present). Labels contain metadata.",
    ["vendor", "gpu_id", "gpu_name", "pid", "proc_name", "used_memory_mib", "gpu_util_percent"]
)

def update_metrics(gauges: Dict[str, Gauge]) -> None:
    all_gpus = amd.extract_amd_gpu_info() + nvidia.extract_nvidia_gpu_info()

    for gpu in all_gpus:
        labels = {
            "vendor": gpu.get("vendor", "unknown"),
            "gpu_id": gpu.get("gpu_id", "unknown"),
            "name": gpu.get("name", "unknown"),
            "pci_bus": gpu.get("pci_bus", "unknown"),
        }

        for key, gauge in gauges.items():
            value = gpu.get(key)
            gauge.labels(**labels).set(value if value is not None else 0)

    # Clear all previous process metrics to avoid duplication
    gpu_process_info.clear()

    # Add fresh process info
    for proc in amd.extract_amd_processes() + nvidia.extract_nvidia_processes():
        gpu_process_info.labels(
            vendor=proc["vendor"],
            gpu_id=proc["gpu_id"],
            gpu_name=proc["gpu_name"],
            pid=str(proc["pid"]),
            proc_name=proc["name"],
            used_memory_mib=str(proc.get("used_memory_mib", 0)),
            gpu_util_percent=str(proc.get("gpu_util_percent", 0)),
        ).set(1)

def main() -> None:
    logging.basicConfig(level=logging.INFO)
    port = 8000
    start_http_server(port)
    logging.info(f"Starting GPU exporter on http://localhost:{port}/metrics")

    gauges = setup_metrics()

    try:
        while True:
            update_metrics(gauges)
            time.sleep(10)
    except KeyboardInterrupt:
        logging.info("Exporter stopped by user")

if __name__ == "__main__":
    main()
