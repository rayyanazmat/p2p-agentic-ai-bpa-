"""Minimal policy evaluation for purchase-to-pay safety checks."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class PolicyViolation:
    """Single policy rule violation with machine-readable metadata."""

    rule: str
    severity: str
    message: str
    evidence: dict[str, Any] = field(default_factory=dict)


@dataclass
class PolicyReport:
    """Structured output from policy evaluation."""

    allowed: bool
    risk_level: str
    violations: list[PolicyViolation] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        """Serialize to a JSON-friendly dictionary."""
        return {
            "allowed": self.allowed,
            "risk_level": self.risk_level,
            "violations": [
                {
                    "rule": violation.rule,
                    "severity": violation.severity,
                    "message": violation.message,
                    "evidence": violation.evidence,
                }
                for violation in self.violations
            ],
        }


class PolicyEngine:
    """Validate the standard procurement safety constraints used by the local workflow."""

    @staticmethod
    def evaluate(case: dict[str, Any]) -> PolicyReport:
        """Return whether the case is safe and which rules it violates."""
        violations: list[PolicyViolation] = []

        if not case.get("invoice_verified", True):
            violations.append(
                PolicyViolation(
                    rule="invoice_unverified",
                    severity="high",
                    message="Invoice verification is required before processing.",
                    evidence={"invoice_verified": case.get("invoice_verified")},
                )
            )

        if case.get("duplicate_invoice", False):
            violations.append(
                PolicyViolation(
                    rule="duplicate_invoice",
                    severity="high",
                    message="Duplicate invoice evidence requires manual review.",
                    evidence={"duplicate_invoice": True},
                )
            )

        invoice_amount = case.get("invoice_amount")
        po_amount = case.get("po_amount")
        if invoice_amount is not None and po_amount is not None and invoice_amount != po_amount:
            violations.append(
                PolicyViolation(
                    rule="amount_mismatch",
                    severity="high",
                    message="Invoice amount must match the purchase order amount.",
                    evidence={
                        "invoice_amount": invoice_amount,
                        "po_amount": po_amount,
                    },
                )
            )

        matching_type = case.get("matching_type")
        po_quantity = case.get("po_quantity")
        receipt_events = case.get("receipt_events") or []
        if matching_type in {"three_way", "consignment"} and po_quantity is not None:
            total_receipt = sum(
                float(receipt.get("quantity", 0))
                for receipt in receipt_events
            )
            if total_receipt < float(po_quantity):
                violations.append(
                    PolicyViolation(
                        rule="incomplete_receipt",
                        severity="high",
                        message="Required receipt quantity is missing for three-way or consignment matching.",
                        evidence={
                            "po_quantity": po_quantity,
                            "received_quantity": total_receipt,
                            "matching_type": matching_type,
                        },
                    )
                )

        allowed = not violations
        if violations:
            severities = {violation.severity for violation in violations}
            if "critical" in severities:
                risk_level = "critical"
            elif "high" in severities:
                risk_level = "high"
            else:
                risk_level = "medium"
        else:
            risk_level = "low"

        return PolicyReport(
            allowed=allowed,
            risk_level=risk_level,
            violations=violations,
        )
