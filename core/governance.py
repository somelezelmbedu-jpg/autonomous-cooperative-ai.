"""
Governance Layer — versions, approvals, and deployment gating.
"""

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Optional


class ProposalStatus(Enum):
    PROPOSED = "proposed"
    SANDBOX_TESTED = "sandbox_tested"
    HUMAN_APPROVED = "human_approved"
    REJECTED = "rejected"
    DEPLOYED = "deployed"


@dataclass
class Proposal:
    id: str
    description: str
    sandbox_result: Optional[Dict] = None
    status: ProposalStatus = ProposalStatus.PROPOSED
    reviewer_notes: str = ""
    created_at: float = field(default_factory=time.time)


class Governance:
    def __init__(self, audit_log):
        self.audit_log = audit_log
        self.proposals: Dict[str, Proposal] = {}

    def submit_proposal(self, description: str) -> Proposal:
        p = Proposal(id=str(uuid.uuid4())[:8], description=description)
        self.proposals[p.id] = p
        self.audit_log.record("proposal_submitted", {"id": p.id, "description": description})
        return p

    def attach_sandbox_result(self, proposal_id: str, sandbox_result: Dict):
        p = self.proposals[proposal_id]
        p.sandbox_result = sandbox_result
        p.status = ProposalStatus.SANDBOX_TESTED
        self.audit_log.record("proposal_sandbox_tested", {"id": proposal_id, "result": sandbox_result})

    def approve(self, proposal_id: str, human_reviewer: str, notes: str = "") -> Proposal:
        """This is the ONLY function that can move a proposal toward deployment,
        and it must be called by a named human reviewer, never by the AI itself."""
        p = self.proposals[proposal_id]
        if p.status != ProposalStatus.SANDBOX_TESTED:
            raise ValueError("Proposal must pass sandbox testing before approval.")
        if not p.sandbox_result or not p.sandbox_result.get("success"):
            raise ValueError("Cannot approve a proposal whose sandbox test failed.")
        p.status = ProposalStatus.HUMAN_APPROVED
        p.reviewer_notes = notes
        self.audit_log.record(
            "proposal_approved",
            {"id": proposal_id, "reviewer": human_reviewer, "notes": notes},
            severity="warn",
        )
        return p

    def reject(self, proposal_id: str, human_reviewer: str, notes: str = "") -> Proposal:
        p = self.proposals[proposal_id]
        p.status = ProposalStatus.REJECTED
        p.reviewer_notes = notes
        self.audit_log.record(
            "proposal_rejected", {"id": proposal_id, "reviewer": human_reviewer, "notes": notes}
        )
        return p

    def mark_deployed(self, proposal_id: str, human_reviewer: str) -> Proposal:
        p = self.proposals[proposal_id]
        if p.status != ProposalStatus.HUMAN_APPROVED:
            raise ValueError("Proposal must be human-approved before deployment.")
        p.status = ProposalStatus.DEPLOYED
        self.audit_log.record(
            "proposal_deployed", {"id": proposal_id, "reviewer": human_reviewer}, severity="warn"
        )
        return p
