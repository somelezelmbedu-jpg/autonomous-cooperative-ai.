"""
Reasoning Engine — analyzes a goal and proposes a plan of ActionRequests.
"""

import os
import json
from typing import List

from .safety_guard import ActionRequest
from .constitution import as_prompt_block

try:
    import anthropic
    _HAS_SDK = True
except ImportError:
    _HAS_SDK = False


class ReasoningEngine:
    def __init__(self, audit_log, model: str = "claude-sonnet-4-6"):
        self.audit_log = audit_log
        self.model = model
        self.client = None
        if _HAS_SDK and os.environ.get("ANTHROPIC_API_KEY"):
            self.client = anthropic.Anthropic()

    def plan(self, goal: str) -> List[ActionRequest]:
        if self.client:
            actions = self._plan_with_llm(goal)
        else:
            actions = self._plan_with_rules(goal)

        self.audit_log.record(
            "plan_generated",
            {"goal": goal, "num_actions": len(actions), "used_llm": bool(self.client)},
        )
        return actions

    def _plan_with_llm(self, goal: str) -> List[ActionRequest]:
        system = (
            as_prompt_block()
            + "\n\nGiven a goal, break it into a short list of concrete actions. "
            "Respond ONLY with JSON: a list of objects with fields "
            "action_type, description, reversible (bool), touches_personal_data (bool), "
            "self_modifying (bool). No prose, no markdown fences."
        )
        resp = self.client.messages.create(
            model=self.model,
            max_tokens=1000,
            system=system,
            messages=[{"role": "user", "content": f"Goal: {goal}"}],
        )
        text = "".join(b.text for b in resp.content if hasattr(b, "text"))
        try:
            raw = json.loads(text.strip().strip("`"))
        except json.JSONDecodeError:
            return self._plan_with_rules(goal)

        return [
            ActionRequest(
                action_type=item.get("action_type", "unknown"),
                description=item.get("description", ""),
                reversible=item.get("reversible", False),
                touches_personal_data=item.get("touches_personal_data", False),
                self_modifying=item.get("self_modifying", False),
            )
            for item in raw
        ]

    def _plan_with_rules(self, goal: str) -> List[ActionRequest]:
        """Minimal, dependency-free fallback so the system is runnable/testable
        without an API key."""
        sensitive_words = ("delete", "deploy", "modify", "personal", "email", "password")
        touches_sensitive = any(w in goal.lower() for w in sensitive_words)
        return [
            ActionRequest(
                action_type="analyze",
                description=f"Analyze goal: {goal}",
                reversible=True,
                touches_personal_data=touches_sensitive,
                self_modifying=False,
            )
        ]
