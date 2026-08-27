"""
Safety & Constitutional Guard — the gatekeeper.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List


class Verdict(Enum):
    ALLOW = "allow"
    BLOCK = "block"
    ESCALATE = "escalate"  # needs human sign-off


@dataclass
class ActionRequest:
    action_type: str          # e.g. "read_data", "send_message", "modify_code", "deploy"
    description: str
    reversible: bool
    touches_personal_data: bool = False
    self_modifying: bool = False


HARD_ESCALATION_TYPES = {"modify_code", "deploy", "delete_data", "grant_permission", "self_modify"}

BLOCKED_KEYWORDS = [
    "bypass safety", "disable logging", "hide from audit", "delete audit",
    "impersonate", "without consent", "exfiltrate",
]


class SafetyGuard:
    def __init__(self, audit_log):
        self.audit_log = audit_log

    def review(self, action: ActionRequest) -> Verdict:
        text = f"{action.action_type} {action.description}".lower()

        for kw in BLOCKED_KEYWORDS:
            if kw in text:
                verdict = Verdict.BLOCK
                self._log(action, verdict, reason=f"blocked keyword: '{kw}'")
                return verdict

        if action.action_type in HARD_ESCALATION_TYPES or action.self_modifying:
            verdict = Verdict.ESCALATE
            self._log(action, verdict, reason="action type requires human governance approval")
            return verdict

        if not action.reversible:
            verdict = Verdict.ESCALATE
            self._log(action, verdict, reason="irreversible action requires human approval")
            return verdict

        if action.touches_personal_data:
            verdict = Verdict.ESCALATE
            self._log(action, verdict, reason="touches personal data — requires consent check")
            return verdict

        verdict = Verdict.ALLOW
        self._log(action, verdict, reason="passed automatic checks")
        return verdict

    def _log(self, action: ActionRequest, verdict: Verdict, reason: str):
        self.audit_log.record(
            event_type="safety_review",
            detail={
                "action_type": action.action_type,
                "description": action.description,
                "verdict": verdict.value,
                "reason": reason,
            },
            severity="warn" if verdict != Verdict.ALLOW else "info",
        )
