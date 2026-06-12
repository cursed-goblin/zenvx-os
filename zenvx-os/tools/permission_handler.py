"""permission_handler.py - gates sensitive actions behind user approval."""
import hashlib
import time

SCREEN_CAPTURE = "SCREEN_CAPTURE"
AUDIO_CAPTURE = "AUDIO_CAPTURE"
COMMAND_EXECUTION = "COMMAND_EXECUTION"
WEB_SEARCH = "WEB_SEARCH"
PAYMENT_TRANSACTION = "PAYMENT_TRANSACTION"

LOCK = "\U0001F512"
CHECK = "\u2705"
CROSS = "\u274C"


class PermissionHandler:
    def __init__(self, config=None, cache_seconds=300):
        self.config = config or {}
        self.cache_seconds = cache_seconds
        self._cache = {}
        self.audit = []

    @staticmethod
    def _hash(details):
        return hashlib.sha256(str(details).encode()).hexdigest()[:12]

    def request(self, ptype, description, details=""):
        cache_key = f"{ptype}:{self._hash(details)}"
        now = time.time()
        if cache_key in self._cache:
            decision, ts = self._cache[cache_key]
            if now - ts < self.cache_seconds:
                return decision

        print(f"\n{LOCK} PERMISSION REQUEST: {ptype}")
        print(f"   {description}")
        if details:
            print(f"   Details: {details}")
        try:
            ans = input("   Allow? [yes/no]: ").strip().lower()
        except EOFError:
            ans = "no"
        decision = ans in ("y", "yes")
        print(f"   {CHECK + ' approved' if decision else CROSS + ' denied'}")

        self._cache[cache_key] = (decision, now)
        self.audit.append({"timestamp": now, "type": ptype,
                           "details": str(details), "granted": decision})
        return decision
