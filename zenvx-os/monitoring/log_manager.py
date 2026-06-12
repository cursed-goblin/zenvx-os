"""log_manager.py - log rotation and retention for /var/log/zenvx."""
import gzip
import os
import shutil
import time

LOG_DIR = "/var/log/zenvx"


class LogManager:
    def __init__(self, config=None):
        config = config or {}
        perf = config.get("logging", {})
        self.log_dir = perf.get("log_dir", LOG_DIR)
        self.max_bytes = perf.get("max_bytes", 10 * 1024 * 1024)
        self.retention_days = perf.get("retention_days", 7)

    def _logs(self):
        if not os.path.isdir(self.log_dir):
            return []
        return [os.path.join(self.log_dir, f)
                for f in os.listdir(self.log_dir) if f.endswith(".log")]

    def rotate(self):
        rotated = []
        for path in self._logs():
            try:
                if os.path.getsize(path) < self.max_bytes:
                    continue
                stamp = time.strftime("%Y%m%d-%H%M%S")
                gz = f"{path}.{stamp}.gz"
                with open(path, "rb") as src, gzip.open(gz, "wb") as dst:
                    shutil.copyfileobj(src, dst)
                open(path, "w").close()
                rotated.append(gz)
            except OSError:
                continue
        return rotated

    def prune(self):
        cutoff = time.time() - self.retention_days * 86400
        removed = []
        if not os.path.isdir(self.log_dir):
            return removed
        for f in os.listdir(self.log_dir):
            if not f.endswith(".gz"):
                continue
            path = os.path.join(self.log_dir, f)
            try:
                if os.path.getmtime(path) < cutoff:
                    os.remove(path)
                    removed.append(path)
            except OSError:
                continue
        return removed

    def run_maintenance(self):
        rotated = self.rotate()
        removed = self.prune()
        return {"rotated": rotated, "removed": removed}
