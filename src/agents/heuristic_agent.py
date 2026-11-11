"""Baseline 2: deterministic procurement state machine."""

from __future__ import annotations

from typing import Any

from src.agents.react_agent import ToolClient, ToolError
from src.orchestration.controller import ApprovalController
from src.policies.engine import PolicyEngine


class HeuristicAgent:
    """Fixed branching workflow used as a non-LLM comparison baseline."""

    def __init__(
        self,
        client: ToolClient,
        policy_enabled: bool = True,
        approval_enabled: bool = True,
    ) -> None:
        self.client = client
        self.policy_enabled = policy_enabled
        self.approval_enabled = approval_enabled

    def run(self, case: dict[str, Any]) -> dict[str, Any]:
        """Execute fixed checks and clear or hold the invoice."""
        policy_report = PolicyEngine.evaluate(case) if self.policy_enabled else None
        approval = ApprovalController.decide(case) if self.approval_enabled else None
        actions: list[dict[str, Any]] = []
        po = self.client.get_po(case["po_item_id"])
        invoice = self.client.get_invoice(case["invoice_id"])
        receipts = self.client.get_receipts(case["po_item_id"])
        reason = "Policy checks passed"
        if not invoice["verified"]:
            reason = "Invoice is not verified"
        elif invoice["duplicate_invoice"]:
            reason = "Duplicate invoice evidence requires review"
        elif invoice["amount"] != po["amount"]:
            reason = "Invoice and PO amounts do not match"
        elif po["matching_type"] in {"three_way", "consignment"}:
            total = sum(item["quantity"] for item in receipts["receipt_events"])
            if total < po["quantity"]:
                reason = "Required receipt quantity is incomplete"
            else:
                try:
                    self.client.verify_receipts(
                        case["po_item_id"], f"{case['case_id']}-heuristic-verify"
                    )
                    actions.append({"action": "verify_receipts", "result": "ok"})
                except ToolError as exc:
                    reason = exc.detail
        policy_violations = (
            [item.rule for item in policy_report.violations]
            if policy_report is not None
            else []
        )
        if approval is not None and approval.decision != "approve":
            reason = approval.reasoning
        if reason == "Policy checks passed":
            try:
                self.client.clear_invoice(
                    case["invoice_id"], f"{case['case_id']}-heuristic-clear"
                )
                actions.append({"action": "clear", "result": "ok"})
                return {
                    "case_id": case["case_id"],
                    "outcome": "cleared",
                    "backend": "deterministic-heuristic",
                    "actions": actions,
                    "policy_violations": policy_violations,
                    "intervention_required": bool(policy_violations)
                    or (approval is not None and approval.decision != "approve"),
                    "input_tokens": 0,
                    "output_tokens": 0,
                }
            except ToolError as exc:
                reason = exc.detail
        self.client.hold_case(case["case_id"], reason)
        actions.append({"action": "hold", "reason": reason})
        return {
            "case_id": case["case_id"],
            "outcome": "held",
            "backend": "deterministic-heuristic",
            "actions": actions,
            "policy_violations": policy_violations,
            "intervention_required": True,
            "input_tokens": 0,
            "output_tokens": 0,
        }

