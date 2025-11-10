# prometheus_exporter_gpu

![Phorge logo](https://avatars.githubusercontent.com/u/187407936?s=200&v=4)

Simple Prometheus exporter that collects and exposes GPU metrics from the local host for scraping by Prometheus.

## Features
- Exposes GPU utilization, memory, temperature and driver information.
- HTTP metrics endpoint compatible with Prometheus (/metrics).
- Small, single-binary or container-friendly.

## Prerequisites
- [Docker](https://docker.com)

## Quick start

```bash
docker compose up -d
```

Default metrics endpoint: http://localhost:8000/metrics

## Metrics

Exposed metrics:
- power_w
- gpu_temp_c
- gpu_clock_mhz
- mem_clock_mhz
- fan_speed_percent
- gpu_util_percent
- mem_util_percent
- memory_used_mib
- memory_total_mib

Check /metrics for the full list from the running exporter.

## Prometheus scrape config (example)
```yml
- job_name: 'gpu_exporter'
    static_configs:
        - targets: ['host.example:8000']
```