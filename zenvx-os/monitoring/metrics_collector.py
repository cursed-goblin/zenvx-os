"""metrics_collector.py - collects runtime metrics (RAM, CPU, tokens/sec)."""
import json
import os
import time
from collections import deque

try:
    import psutil
    _HAS_PSUTIL = True
except Exception:  # noqa: BLE001
    _HAS_PSUTIL = False

METRICS_DIR = "/var/lib/zenvx/metrics"


class MetricsCollector:
    def __init__(self, metrics_dir=METRICS_DIR, window=120):
        self.metrics_dir = metrics_dir
        os.makedirs(self.metrics_dir, exist_ok=True)
        self.tps_history = deque(maxlen=window)
        self.latency_history = deque(maxlen=window)
        self.request_count = 0
        self.error_count = 0
        self.start_time = time.time()

    def record_inference(self, tokens_per_second, latency_s):
        self.tps_history.append(tokens_per_second)
        self.latency_history.append(latency_s)
        self.request_count += 1

    def record_error(self):
        self.error_count += 1

    def system_metrics(self):
        if _HAS_PSUTIL:
            vm = psutil.virtual_memory()
            return {"cpu_percent": psutil.cpu_percent(interval=None),
                    "ram_used_mb": int(vm.used / (1024 * 1024)),
                    "ram_total_mb": int(vm.total / (1024 * 1024)),
                    "ram_percent": vm.percent}
        return {"cpu_percent": 0.0, "ram_used_mb": 0,
                "ram_total_mb": 0, "ram_percent": 0.0}

    def snapshot(self):
        sys_m = self.system_metrics()
        avg_tps = (sum(self.tps_history) / len(self.tps_history)
                   if self.tps_history else 0.0)
        avg_lat = (sum(self.latency_history) / len(self.latency_history)
                   if self.latency_history else 0.0)
        return {
            "uptime_s": int(time.time() - self.start_time),
            "requests": self.request_count,
            "errors": self.error_count,
            "avg_tokens_per_second": round(avg_tps, 2),
            "avg_latency_s": round(avg_lat, 3),
            **sys_m,
        }

    def persist(self):
        path = os.path.join(self.metrics_dir, "current.json")
        with open(path, "w") as f:
            json.dump(self.snapshot(), f, indent=2)
        return path
