"""logger.py - JSON-lines audit logging."""
import json
import os
import time

AUDIT_LOG = "/var/log/zenvx/audit.log"


class AuditLogger:
    def __init__(self, path=AUDIT_LOG):
        self.path = path
        os.makedirs(os.path.dirname(self.path), exist_ok=True)

    def log(self, action, thought="", parameters=None, confidence=0.0,
            result="", success=True):
        entry = {
            "timestamp": time.time(),
            "action": action,
            "thought": str(thought)[:200],
            "parameters": parameters or {},
            "confidence": round(float(confidence), 3),
            "result": str(result)[:300],
            "success": bool(success),
        }
        try:
            with open(self.path, "a") as f:
                f.write(json.dumps(entry) + "\n")
        except OSError:
            pass
        return entry
