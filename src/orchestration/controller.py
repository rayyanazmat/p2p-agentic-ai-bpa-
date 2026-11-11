"""Risk-based approval orchestration for procurement workflow actions."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.policies.engine import PolicyEngine


@dataclass(frozen=True)
class ApprovalDecision:
    """Action recommendation to take for a case."""

    decision: str
    risk_score: int
    risk_level: str
    reasoning: str
    blocked_by: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        """Serialize the decision into a JSON-safe payload."""
        return {
            "decision": self.decision,
            "risk_score": self.risk_score,
            "risk_level": self.risk_level,
            "reasoning": self.reasoning,
            "blocked_by": self.blocked_by,
        }


class ApprovalController:
    """Choose whether to auto-approve, hold, or escalate a case to a human reviewer."""

    @staticmethod
    def risk_score(case: dict[str, Any]) -> int:
        """Score the current risk of a case based on evidence and policy failures."""
        score = 0
        if not case.get("invoice_verified", True):
            score += 35
        if case.get("duplicate_invoice", False):
            score += 55
        if case.get("invoice_amount") is not None and case.get("po_amount") is not None:
            if case["invoice_amount"] != case["po_amount"]:
                score += 40
        matching_type = case.get("matching_type")
        po_quantity = case.get("po_quantity")
        if matching_type in {"three_way", "consignment"} and po_quantity is not None:
            received = sum(float(item.get("quantity", 0)) for item in case.get("receipt_events", []))
            if received < float(po_quantity):
                score += 35
        if case.get("invoice_status") == "held":
            score += 20
        return min(score, 100)

    @staticmethod
    def decide(case: dict[str, Any]) -> ApprovalDecision:
        """Return the recommended approval action using policy and risk scoring."""
        policy_report = PolicyEngine.evaluate(case)
        decision_score = ApprovalController.risk_score(case)
        if policy_report.allowed and decision_score < 30:
            return ApprovalDecision(
                decision="approve",
                risk_score=decision_score,
                risk_level="low",
                reasoning="Evidence is consistent and no policy rule has been violated.",
                blocked_by=[],
            )

        blocked_by = [violation.rule for violation in policy_report.violations]
        if decision_score >= 60 or policy_report.risk_level == "critical":
            return ApprovalDecision(
                decision="hold",
                risk_score=decision_score,
                risk_level=policy_report.risk_level if policy_report.risk_level != "low" else "high",
                reasoning="High-risk or policy-violating case requires human review before proceeding.",
                blocked_by=blocked_by,
            )

        if blocked_by:
            return ApprovalDecision(
                decision="review",
                risk_score=decision_score,
                risk_level=policy_report.risk_level,
                reasoning="Policy mismatches are present; a reviewer must confirm the next step.",
                blocked_by=blocked_by,
            )

        return ApprovalDecision(
            decision="approve",
            risk_score=decision_score,
            risk_level="medium",
            reasoning="Workflow evidence is acceptable for automatic approval.",
            blocked_by=[],
        )
