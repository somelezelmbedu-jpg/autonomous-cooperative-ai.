"""
Audit Log — append-only record of every significant action.
"""

import json
import os
import time
import hashlib
from typing import Any, Dict, Optional


class AuditLog:
    def __init__(self, path: str = "audit_log.jsonl"):
        self.path = path
        self._last_hash = self._load_last_hash()

    def _load_last_hash(self) -> str:
        if not os.path.exists(self.path):
            return "0" * 64
        last = "0" * 64
        with open(self.path, "r") as f:
            for line in f:
                if line.strip():
                    last = json.loads(line)["hash"]
        return last

    def record(self, event_type: str, detail: Dict[str, Any], severity: str = "info") -> Dict[str, Any]:
        """Append a tamper-evident entry (each entry hashes the previous one)."""
        entry = {
            "timestamp": time.time(),
            "event_type": event_type,
            "severity": severity,
            "detail": detail,
            "prev_hash": self._last_hash,
        }
        payload = json.dumps(entry, sort_keys=True).encode("utf-8")
        entry["hash"] = hashlib.sha256(payload).hexdigest()
        with open(self.path, "a") as f:
            f.write(json.dumps(entry) + "\n")
        self._last_hash = entry["hash"]
        return entry

    def verify_chain(self) -> bool:
        """Check the hash chain hasn't been tampered with."""
        if not os.path.exists(self.path):
            return True
        prev = "0" * 64
        with open(self.path, "r") as f:
            for line in f:
                if not line.strip():
                    continue
                entry = json.loads(line)
                claimed_hash = entry.pop("hash")
                if entry["prev_hash"] != prev:
                    return False
                payload = json.dumps(entry, sort_keys=True).encode("utf-8")
                if hashlib.sha256(payload).hexdigest() != claimed_hash:
                    return False
                prev = claimed_hash
        return True

    def read_all(self):
        if not os.path.exists(self.path):
            return []
        with open(self.path, "r") as f:
            return [json.loads(line) for line in f if line.strip()]
