"""
Orchestrator — wires the modules together into the flow from the brief:

  Goal Manager -> Reasoning Engine -> Simulation (risk estimate)
      -> Safety & Constitutional Guard -> [ALLOW: execute | ESCALATE/BLOCK: hold for human]

Run this directly for a demo:  python main.py
"""

from core.audit_log import AuditLog
from core.goal_manager import GoalManager
from core.reasoning_engine import ReasoningEngine
from core.simulation import estimate_risk
from core.safety_guard import SafetyGuard, Verdict
from core.sandbox import Sandbox
from core.governance import Governance
from core.memory_store import MemoryStore


class AutonomousSystem:
    def __init__(self):
        self.audit_log = AuditLog(path="audit_log.jsonl")
        self.goals = GoalManager(self.audit_log)
        self.reasoning = ReasoningEngine(self.audit_log)
        self.safety = SafetyGuard(self.audit_log)
        self.sandbox = Sandbox(self.audit_log)
        self.governance = Governance(self.audit_log)
        self.memory = MemoryStore(self.audit_log)

    def pursue_goal(self, description: str, submitted_by: str = "user") -> dict:
        goal = self.goals.submit(description, submitted_by)
        plan = self.reasoning.plan(description)

        results = []
        for action in plan:
            risk = estimate_risk(action)
            verdict = self.safety.review(action)

            record = {
                "action_type": action.action_type,
                "description": action.description,
                "risk": risk,
                "verdict": verdict.value,
            }

            if verdict == Verdict.ALLOW:
                record["result"] = f"[executed] {action.description}"
                self.memory.set(f"last_result::{action.action_type}", record["result"])
            else:
                record["result"] = "HELD FOR HUMAN REVIEW"

            results.append(record)

        self.goals.close(goal.id, outcome="plan produced, see results")
        return {"goal": goal.description, "results": results}


def demo():
    system = AutonomousSystem()

    print("=== Demo: benign goal ===")
    out = system.pursue_goal("Summarize this week's team notes into a short digest")
    for r in out["results"]:
        print(f"- [{r['verdict']}] {r['description']} -> {r['result']}")

    print("\n=== Demo: sensitive goal (should escalate) ===")
    out = system.pursue_goal("Delete the old customer records and modify the deployment config")
    for r in out["results"]:
        print(f"- [{r['verdict']}] {r['description']} -> {r['result']}")

    print(f"\nAudit chain intact: {system.audit_log.verify_chain()}")
    print(f"Audit entries written: {len(system.audit_log.read_all())}")


if __name__ == "__main__":
    demo()
