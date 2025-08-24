import os
import time
import psutil
import requests
import statistics as stats


BASE_URL = os.environ.get("TEST_BASE_URL", "http://localhost:5000")


def measure_latency(path: str, n: int = 25):
    latencies = []
    for _ in range(n):
        t0 = time.perf_counter()
        r = requests.get(f"{BASE_URL}{path}")
        r.raise_for_status()
        latencies.append((time.perf_counter() - t0) * 1000)
    return {
        "min_ms": min(latencies),
        "p50_ms": stats.median(latencies),
        "avg_ms": sum(latencies) / len(latencies),
        "p95_ms": sorted(latencies)[int(0.95 * len(latencies)) - 1],
        "max_ms": max(latencies),
    }


def test_health_latency_smoke():
    metrics = measure_latency("/health", n=20)
    assert metrics["p95_ms"] < float(os.getenv("TARGET_HEALTH_P95_MS", "100"))


def test_system_health_latency_smoke():
    metrics = measure_latency("/api/system/health", n=10)
    # Allow looser bound since it might check external deps
    assert metrics["p95_ms"] < float(os.getenv("TARGET_SYS_HEALTH_P95_MS", "1200"))


def test_resource_usage_smoke():
    # Sanity check that process stays within thresholds during simple calls
    process = psutil.Process()
    cpu = process.cpu_percent(interval=0.5)
    mem = process.memory_info().rss / (1024 * 1024)
    assert mem < float(os.getenv("TARGET_MEM_MB", "800"))


