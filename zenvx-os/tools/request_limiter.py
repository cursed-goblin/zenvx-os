"""request_limiter.py - token bucket rate limiter per key."""
import threading
import time


class _Bucket:
    def __init__(self, rate, burst):
        self.rate = rate
        self.capacity = burst
        self.tokens = burst
        self.updated = time.time()

    def _refill(self):
        now = time.time()
        self.tokens = min(self.capacity,
                          self.tokens + (now - self.updated) * self.rate)
        self.updated = now


class RequestLimiter:
    def __init__(self, rate=1.0, burst=5):
        self.rate = rate
        self.burst = burst
        self._buckets = {}
        self._lock = threading.Lock()

    def _bucket(self, key):
        if key not in self._buckets:
            self._buckets[key] = _Bucket(self.rate, self.burst)
        return self._buckets[key]

    def allow(self, key="default"):
        """Non-blocking: returns True if a token was available."""
        with self._lock:
            b = self._bucket(key)
            b._refill()
            if b.tokens >= 1:
                b.tokens -= 1
                return True
            return False

    def acquire(self, key="default"):
        """Blocking: waits until a token is available."""
        while not self.allow(key):
            time.sleep(1.0 / self.rate if self.rate else 0.1)
        return True
