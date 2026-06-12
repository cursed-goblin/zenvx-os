"""integration.py - wires the metrics collector into the agent loop."""
import time

from .metrics_collector import MetricsCollector


class MonitoringIntegration:
    def __init__(self, config=None):
        self.collector = MetricsCollector()
        self.config = config or {}

    def instrument(self, func):
        """Decorator that records latency and request counts."""
        def wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            except Exception:
                self.collector.record_error()
                raise
            finally:
                latency = time.time() - start
                tps = getattr(func, "last_tps", 0.0)
                self.collector.record_inference(tps, latency)
                self.collector.persist()
        return wrapper

    def record(self, tps, latency):
        self.collector.record_inference(tps, latency)
        self.collector.persist()

    def snapshot(self):
        return self.collector.snapshot()
