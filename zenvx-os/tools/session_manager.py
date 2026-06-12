"""session_manager.py - encrypted session storage using Fernet."""
import json
import os

KEY_PATH = "/var/lib/zenvx/.session.key"

try:
    from cryptography.fernet import Fernet
    _HAS_CRYPTO = True
except Exception:  # noqa: BLE001
    _HAS_CRYPTO = False


class SessionManager:
    def __init__(self, key_path=KEY_PATH):
        self.key_path = key_path
        self._fernet = None
        if _HAS_CRYPTO:
            self._fernet = Fernet(self._load_or_create_key())

    def _load_or_create_key(self):
        if os.path.exists(self.key_path):
            with open(self.key_path, "rb") as f:
                return f.read()
        key = Fernet.generate_key()
        os.makedirs(os.path.dirname(self.key_path), exist_ok=True)
        with open(self.key_path, "wb") as f:
            f.write(key)
        os.chmod(self.key_path, 0o600)
        return key

    def save(self, path, session_dict):
        raw = json.dumps(session_dict).encode("utf-8")
        if self._fernet is not None:
            data = self._fernet.encrypt(raw)
        else:
            data = raw  # plain fallback
        with open(path, "wb") as f:
            f.write(data)

    def load(self, path):
        if not os.path.exists(path):
            return {}
        with open(path, "rb") as f:
            data = f.read()
        try:
            if self._fernet is not None:
                data = self._fernet.decrypt(data)
            return json.loads(data.decode("utf-8"))
        except Exception:  # noqa: BLE001
            return {}
