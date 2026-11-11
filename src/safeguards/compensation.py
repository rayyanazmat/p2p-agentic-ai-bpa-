"""Compensating actions for unsafe purchase-to-pay states."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class CompensationAction:
    """A single compensating or corrective action."""

    action: str
    reason: str
    severity: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "action": self.action,
            "reason": self.reason,
            "severity": self.severity,
        }


@dataclass
class CompensationPlan:
    """Structured response describing how to neutralize a risky state."""

    required: bool
    actions: list[CompensationAction] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "required": self.required,
            "actions": [action.as_dict() for action in self.actions],
        }


class CompensationEngine:
    """Recommend the minimal compensation plan needed to keep the workflow safe."""

    @staticmethod
    def plan(case: dict[str, Any]) -> CompensationPlan:
        """Choose a corrective pathway based on the current case evidence."""
        actions: list[CompensationAction] = []
        invoice_status = case.get("invoice_status")

        if case.get("invoice_verified") is False:
            actions.append(
                CompensationAction(
                    action="hold_case",
                    reason="Invoice verification was missing; stop the workflow until evidence is restored.",
                    severity="high",
                )
            )

        if case.get("duplicate_invoice"):
            actions.append(
                CompensationAction(
                    action="escalate_manual_review",
                    reason="Duplicate invoice evidence requires a human review before settlement.",
                    severity="high",
                )
            )

        if case.get("invoice_amount") is not None and case.get("po_amount") is not None:
            if case["invoice_amount"] != case["po_amount"]:
                actions.append(
                    CompensationAction(
                        action="reject_invoice",
                        reason="Amounts differ from the purchase order and cannot be cleared without approval.",
                        severity="high",
                    )
                )

        if case.get("matching_type") in {"three_way", "consignment"}:
            received = sum(float(item.get("quantity", 0)) for item in case.get("receipt_events", []))
            required = float(case.get("po_quantity", 0))
            if received < required:
                actions.append(
                    CompensationAction(
                        action="request_receipt",
                        reason="Required goods receipt evidence is incomplete.",
                        severity="medium",
                    )
                )

        missing_receipt = False
        if case.get("matching_type") in {"three_way", "consignment"}:
            received = sum(
                float(item.get("quantity", 0))
                for item in case.get("receipt_events", [])
            )
            missing_receipt = received < float(case.get("po_quantity", 0))

        if invoice_status == "cleared" and (
            case.get("invoice_verified") is False
            or case.get("duplicate_invoice")
            or missing_receipt
            or (
                case.get("invoice_amount") is not None
                and case.get("po_amount") is not None
                and case["invoice_amount"] != case["po_amount"]
            )
        ):
            actions.append(
                CompensationAction(
                    action="revert_clearance",
                    reason="Cleared state conflicts with invoice evidence and must be rolled back for review.",
                    severity="critical",
                )
            )

        return CompensationPlan(required=bool(actions), actions=actions)
