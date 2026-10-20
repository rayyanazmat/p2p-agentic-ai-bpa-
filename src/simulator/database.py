"""In-memory deterministic simulator state and business invariants."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from threading import RLock
from typing import Any


class SimulatorError(Exception):
    """Expected simulator error with an HTTP status code."""

    def __init__(self, status_code: int, detail: str) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


class ProcurementStore:
    """Thread-safe in-memory PO, invoice, receipt, and audit store."""

    def __init__(self) -> None:
        self._lock = RLock()
        self.reset([])

    def reset(self, cases: list[dict[str, Any]]) -> None:
        """Replace all state with a deep-copied list of seeded cases."""
        with self._lock:
            self.cases = {case["case_id"]: deepcopy(case) for case in cases}
            self.po_to_case = {
                case["po_item_id"]: case["case_id"] for case in cases
            }
            self.invoice_to_case = {
                case["invoice_id"]: case["case_id"] for case in cases
            }
            self.idempotency: dict[str, dict[str, Any]] = {}
            self.tool_calls: dict[str, list[dict[str, Any]]] = {
                case["case_id"]: [] for case in cases
            }
            self.transitions: dict[str, list[dict[str, Any]]] = {
                case["case_id"]: [] for case in cases
            }
            self.compensations: dict[str, list[dict[str, Any]]] = {
                case["case_id"]: [] for case in cases
            }
            self.approvals: dict[str, dict[str, Any]] = {}

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def _case_for_po(self, po_item_id: str) -> dict[str, Any]:
        case_id = self.po_to_case.get(po_item_id)
        if case_id is None:
            raise SimulatorError(404, "Purchase-order item not found")
        return self.cases[case_id]

    def _case_for_invoice(self, invoice_id: str) -> dict[str, Any]:
        case_id = self.invoice_to_case.get(invoice_id)
        if case_id is None:
            raise SimulatorError(404, "Invoice not found")
        return self.cases[case_id]

    def _record_call(
        self,
        case_id: str,
        tool: str,
        inputs: dict[str, Any],
        outcome: str,
        status_code: int,
    ) -> None:
        calls = self.tool_calls.setdefault(case_id, [])
        calls.append(
            {
                "sequence": len(calls) + 1,
                "tool": tool,
                "input": deepcopy(inputs),
                "outcome": outcome,
                "status_code": status_code,
                "timestamp": self._now(),
            }
        )

    def _transition(
        self, case_id: str, entity: str, before: str, after: str, reason: str
    ) -> None:
        records = self.transitions.setdefault(case_id, [])
        records.append(
            {
                "sequence": len(records) + 1,
                "entity": entity,
                "before": before,
                "after": after,
                "reason": reason,
                "timestamp": self._now(),
            }
        )

    def get_po(self, po_item_id: str) -> dict[str, Any]:
        with self._lock:
            case = self._case_for_po(po_item_id)
            self._record_call(case["case_id"], "get_purchase_order", {}, "ok", 200)
            return {
                "case_id": case["case_id"],
                "po_item_id": case["po_item_id"],
                "quantity": case["po_quantity"],
                "amount": case["po_amount"],
                "currency": case["currency"],
                "matching_type": case["matching_type"],
                "status": case["po_status"],
            }

    def get_invoice(self, invoice_id: str) -> dict[str, Any]:
        with self._lock:
            case = self._case_for_invoice(invoice_id)
            self._record_call(case["case_id"], "get_invoice", {}, "ok", 200)
            return {
                "case_id": case["case_id"],
                "invoice_id": case["invoice_id"],
                "po_item_id": case["po_item_id"],
                "amount": case["invoice_amount"],
                "currency": case["currency"],
                "verified": case["invoice_verified"],
                "duplicate_invoice": case.get("duplicate_invoice", False),
                "status": case["invoice_status"],
            }

    def get_receipts(self, po_item_id: str) -> dict[str, Any]:
        with self._lock:
            case = self._case_for_po(po_item_id)
            receipts = deepcopy(case["receipt_events"])
            verified_quantity = sum(
                receipt["quantity"]
                for receipt in receipts
                if receipt.get("verified", False)
            )
            self._record_call(case["case_id"], "get_goods_receipts", {}, "ok", 200)
            return {
                "po_item_id": po_item_id,
                "receipt_events": receipts,
                "verified_quantity": verified_quantity,
            }

    def verify_receipts(self, po_item_id: str, key: str) -> dict[str, Any]:
        with self._lock:
            case = self._case_for_po(po_item_id)
            idem_key = f"verify:{case['case_id']}:{key}"
            if idem_key in self.idempotency:
                result = deepcopy(self.idempotency[idem_key])
                self._record_call(
                    case["case_id"], "verify_goods_receipts", {"key": key},
                    "idempotent_replay", 200
                )
                return result
            quantity = sum(r["quantity"] for r in case["receipt_events"])
            if not case["receipt_events"] or quantity < case["po_quantity"]:
                self._record_call(
                    case["case_id"], "verify_goods_receipts", {"key": key},
                    "insufficient_receipt", 409
                )
                raise SimulatorError(409, "Receipt evidence is absent or incomplete")
            before = str(any(r.get("verified") for r in case["receipt_events"]))
            for receipt in case["receipt_events"]:
                receipt["verified"] = True
            self._transition(
                case["case_id"], "goods_receipts", before, "True", "verified"
            )
            result = {"po_item_id": po_item_id, "verified": True, "quantity": quantity}
            self.idempotency[idem_key] = deepcopy(result)
            self._record_call(
                case["case_id"], "verify_goods_receipts", {"key": key}, "ok", 200
            )
            return result

    def clear_invoice(self, invoice_id: str, key: str) -> dict[str, Any]:
        with self._lock:
            case = self._case_for_invoice(invoice_id)
            idem_key = f"clear:{case['case_id']}:{key}"
            if idem_key in self.idempotency:
                result = deepcopy(self.idempotency[idem_key])
                self._record_call(
                    case["case_id"], "clear_invoice", {"key": key},
                    "idempotent_replay", 200
                )
                return result
            reason = self._clear_precondition_error(case)
            if reason:
                self._record_call(
                    case["case_id"], "clear_invoice", {"key": key}, reason, 409
                )
                raise SimulatorError(409, reason)
            before = case["invoice_status"]
            case["invoice_status"] = "cleared"
            self._transition(
                case["case_id"],
                "invoice",
                before,
                "cleared",
                "policy preconditions met",
            )
            result = {"invoice_id": invoice_id, "status": "cleared", "simulated": True}
            self.idempotency[idem_key] = deepcopy(result)
            self._record_call(
                case["case_id"], "clear_invoice", {"key": key}, "ok", 200
            )
            return result

    @staticmethod
    def _clear_precondition_error(case: dict[str, Any]) -> str | None:
        if case["invoice_status"] == "cleared":
            return "Invoice is already cleared"
        if not case["invoice_verified"]:
            return "Invoice is not verified"
        if case.get("duplicate_invoice", False):
            return "Duplicate invoice evidence requires review"
        if case["invoice_amount"] != case["po_amount"]:
            return "Invoice and purchase-order amounts do not match"
        if case["matching_type"] in {"three_way", "consignment"}:
            verified = sum(
                r["quantity"] for r in case["receipt_events"] if r.get("verified")
            )
            if verified < case["po_quantity"]:
                return "Required verified goods receipt is missing or incomplete"
        return None

    def record_approval(
        self, case_id: str, decision: str, rationale: str, evidence_reference: str
    ) -> dict[str, Any]:
        with self._lock:
            if case_id not in self.cases:
                raise SimulatorError(404, "Case not found")
            record = {
                "case_id": case_id,
                "decision": decision,
                "rationale": rationale,
                "evidence_reference": evidence_reference,
                "recorded_at": self._now(),
            }
            self.approvals[case_id] = record
            self._record_call(
                case_id, "record_approval", {"decision": decision}, "ok", 200
            )
            self._transition(case_id, "approval", "none", decision, rationale)
            return deepcopy(record)

    def get_audit(self, case_id: str) -> dict[str, Any]:
        with self._lock:
            if case_id not in self.cases:
                raise SimulatorError(404, "Case not found")
            return {
                "case_id": case_id,
                "tool_calls": deepcopy(self.tool_calls.get(case_id, [])),
                "transitions": deepcopy(self.transitions.get(case_id, [])),
                "compensations": deepcopy(self.compensations.get(case_id, [])),
            }

    def get_case(self, case_id: str) -> dict[str, Any]:
        with self._lock:
            if case_id not in self.cases:
                raise SimulatorError(404, "Case not found")
            return deepcopy(self.cases[case_id])

    def mark_held(self, case_id: str, reason: str, key: str) -> None:
        with self._lock:
            if case_id not in self.cases:
                raise SimulatorError(404, "Case not found")
            idem_key = f"hold:{case_id}:{key}"
            if idem_key in self.idempotency:
                self._record_call(
                    case_id, "hold_case", {"reason": reason, "key": key},
                    "idempotent_replay", 200
                )
                return
            case = self.cases[case_id]
            before = case["invoice_status"]
            case["invoice_status"] = "held"
            self._transition(case_id, "invoice", before, "held", reason)
            self._record_call(
                case_id, "hold_case", {"reason": reason, "key": key}, "ok", 200
            )
            self.idempotency[idem_key] = {"status": "held", "reason": reason}


store = ProcurementStore()

