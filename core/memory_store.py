"""
Memory & Context Store — long-term memory with correction + audit.
"""

import time
from typing import Any, Dict, List


class MemoryStore:
    def __init__(self, audit_log):
        self.audit_log = audit_log
        self._store: Dict[str, Any] = {}
        self._history: Dict[str, List[Dict]] = {}

    def set(self, key: str, value: Any, reason: str = ""):
        old = self._store.get(key)
        self._store[key] = value
        self._history.setdefault(key, []).append(
            {"timestamp": time.time(), "old": old, "new": value, "reason": reason}
        )
        self.audit_log.record("memory_write", {"key": key, "reason": reason})

    def get(self, key: str, default=None):
        return self._store.get(key, default)

    def correct(self, key: str, corrected_value: Any, reason: str):
        """Explicit correction path, distinct from a normal write, so audits
        can tell 'the world changed' apart from 'we were wrong before'."""
        old = self._store.get(key)
        self._store[key] = corrected_value
        self._history.setdefault(key, []).append(
            {"timestamp": time.time(), "old": old, "new": corrected_value, "reason": f"CORRECTION: {reason}"}
        )
        self.audit_log.record("memory_correction", {"key": key, "reason": reason}, severity="warn")

    def history(self, key: str) -> List[Dict]:
        return self._history.get(key, [])
