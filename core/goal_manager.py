"""
Goal & Task Manager — accepts a human-provided objective and tracks its
lifecycle.
"""

import time
import uuid
from dataclasses import dataclass, field
from typing import List


@dataclass
class Goal:
    id: str
    description: str
    submitted_by: str
    created_at: float = field(default_factory=time.time)
    status: str = "open"


class GoalManager:
    def __init__(self, audit_log):
        self.audit_log = audit_log
        self.goals: List[Goal] = []

    def submit(self, description: str, submitted_by: str) -> Goal:
        goal = Goal(id=str(uuid.uuid4())[:8], description=description, submitted_by=submitted_by)
        self.goals.append(goal)
        self.audit_log.record("goal_submitted", {"id": goal.id, "description": description, "by": submitted_by})
        return goal

    def close(self, goal_id: str, outcome: str):
        for g in self.goals:
            if g.id == goal_id:
                g.status = f"closed: {outcome}"
                self.audit_log.record("goal_closed", {"id": goal_id, "outcome": outcome})
                return g
        raise ValueError("Goal not found")
