"""
Simulation & Prediction Module — a lightweight pre-check that estimates
the consequences of an action before it runs.
"""

from typing import Dict
from .safety_guard import ActionRequest

RISK_WEIGHTS = {
    "irreversible": 0.4,
    "personal_data": 0.3,
    "self_modifying": 0.5,
}


def estimate_risk(action: ActionRequest) -> Dict:
    score = 0.0
    reasons = []

    if not action.reversible:
        score += RISK_WEIGHTS["irreversible"]
        reasons.append("action is irreversible")
    if action.touches_personal_data:
        score += RISK_WEIGHTS["personal_data"]
        reasons.append("action touches personal data")
    if action.self_modifying:
        score += RISK_WEIGHTS["self_modifying"]
        reasons.append("action modifies the system itself")

    score = min(score, 1.0)
    return {
        "action_type": action.action_type,
        "risk_score": round(score, 2),
        "reasons": reasons,
        "recommendation": "escalate_to_human" if score > 0 else "proceed",
    }
