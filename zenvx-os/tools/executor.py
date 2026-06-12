"""executor.py - safe shell command execution with a blocklist."""
import re
import subprocess

BLOCKED_PATTERNS = [
    r"rm\s+-rf\s+/",
    r"\bmkfs\b",
    r"\bdd\s+if=",
    r":\(\)\s*\{.*\};\s*:",  # fork bomb
    r"chmod\s+777\s+/",
    r"chown\s+root",
    r"\beval\b",
    r"\bexec\b",
]


class SafeExecutor:
    def __init__(self, timeout=30):
        self.timeout = timeout
        self._blocked = [re.compile(p) for p in BLOCKED_PATTERNS]

    def is_blocked(self, command):
        return any(p.search(command) for p in self._blocked)

    def run(self, command):
        if self.is_blocked(command):
            return {"success": False, "stdout": "", "stderr":
                    "Blocked: command matched a dangerous pattern.",
                    "returncode": -1}
        try:
            proc = subprocess.run(
                command, shell=True, capture_output=True, text=True,
                timeout=self.timeout)
            return {"success": proc.returncode == 0, "stdout": proc.stdout,
                    "stderr": proc.stderr, "returncode": proc.returncode}
        except subprocess.TimeoutExpired:
            return {"success": False, "stdout": "", "stderr":
                    f"Timed out after {self.timeout}s", "returncode": -1}
        except Exception as exc:  # noqa: BLE001
            return {"success": False, "stdout": "", "stderr": str(exc),
                    "returncode": -1}
