"""FastAPI application exposing deterministic mock ERP tools."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException

from src.simulator.database import SimulatorError, store
from src.simulator.schemas import (
    ApprovalRecord,
    ApprovalRequest,
    AuditResponse,
    GoodsReceiptResponse,
    HoldRequest,
    Invoice,
    MutationRequest,
    PurchaseOrder,
    SeedCase,
)

app = FastAPI(
    title="P2P Agentic AI Mock ERP",
    version="0.1.0",
    description="Deterministic local procurement simulator; no real payments are made.",
)


def _call(action: Any) -> Any:
    """Translate domain errors to their declared HTTP status."""
    try:
        return action()
    except SimulatorError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


@app.get("/health")
def health() -> dict[str, str]:
    """Report service readiness."""
    return {"status": "ok"}


@app.post("/admin/reset")
def reset_seed(cases: list[SeedCase]) -> dict[str, int]:
    """Reset local simulator state; intended only for local experiments."""
    store.reset([case.model_dump(mode="json") for case in cases])
    return {"seeded_cases": len(cases)}


@app.get("/admin/cases/{case_id}")
def get_seeded_case(case_id: str) -> dict[str, Any]:
    """Return simulator state and ground truth for the local evaluator."""
    return _call(lambda: store.get_case(case_id))


@app.get("/purchase-orders/{po_item_id}", response_model=PurchaseOrder)
def get_purchase_order(po_item_id: str) -> dict[str, Any]:
    """Read purchase-order item values and status."""
    return _call(lambda: store.get_po(po_item_id))


@app.get("/invoices/{invoice_id}", response_model=Invoice)
def get_invoice(invoice_id: str) -> dict[str, Any]:
    """Read invoice values and verification/clearing state."""
    return _call(lambda: store.get_invoice(invoice_id))


@app.get("/goods-receipts/{po_item_id}", response_model=GoodsReceiptResponse)
def get_goods_receipts(po_item_id: str) -> dict[str, Any]:
    """Read receipt events and verified receipt quantity."""
    return _call(lambda: store.get_receipts(po_item_id))


@app.post("/goods-receipts/{po_item_id}/verify")
def verify_goods_receipts(
    po_item_id: str, request: MutationRequest
) -> dict[str, Any]:
    """Verify complete receipt evidence idempotently."""
    return _call(lambda: store.verify_receipts(po_item_id, request.idempotency_key))


@app.post("/invoices/{invoice_id}/clear")
def clear_invoice(invoice_id: str, request: MutationRequest) -> dict[str, Any]:
    """Simulate invoice clearing after server-side precondition checks."""
    return _call(lambda: store.clear_invoice(invoice_id, request.idempotency_key))


@app.post("/cases/{case_id}/approval", response_model=ApprovalRecord)
def record_approval(
    case_id: str, request: ApprovalRequest
) -> dict[str, Any]:
    """Record an explicit human approval or rejection."""
    return _call(
        lambda: store.record_approval(
            case_id,
            request.decision,
            request.rationale,
            request.evidence_reference,
        )
    )


@app.post("/cases/{case_id}/hold")
def hold_case(case_id: str, request: HoldRequest) -> dict[str, str]:
    """Move an unresolved invoice to held state for review."""
    return _call(lambda: _hold(case_id, request.reason, request.idempotency_key))


def _hold(case_id: str, reason: str, key: str) -> dict[str, str]:
    """Validate and record a hold request."""
    try:
        store.mark_held(case_id, reason, key)
        return {"case_id": case_id, "status": "held", "reason": reason}
    except SimulatorError:
        raise
    except KeyError as exc:
        raise SimulatorError(404, "Case not found") from exc


@app.get("/cases/{case_id}/audit", response_model=AuditResponse)
def get_audit(case_id: str) -> dict[str, Any]:
    """Return full tool-call and state-transition history."""
    return _call(lambda: store.get_audit(case_id))

