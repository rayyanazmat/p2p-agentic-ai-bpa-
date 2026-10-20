"""Validated request and response contracts for the mock ERP API."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    """Reject undeclared fields in API contracts."""

    model_config = ConfigDict(extra="forbid")


class PurchaseOrder(StrictModel):
    case_id: str
    po_item_id: str
    quantity: float = Field(ge=0)
    amount: float = Field(ge=0)
    currency: str = Field(min_length=3, max_length=3)
    matching_type: Literal["two_way", "three_way", "consignment"]
    status: str


class Invoice(StrictModel):
    case_id: str
    invoice_id: str
    po_item_id: str
    amount: float = Field(ge=0)
    currency: str = Field(min_length=3, max_length=3)
    verified: bool
    duplicate_invoice: bool = False
    status: Literal["open", "cleared", "held"]


class GoodsReceipt(StrictModel):
    event_id: str
    quantity: float = Field(ge=0)
    verified: bool = False
    received_at: datetime | None = None


class GoodsReceiptResponse(StrictModel):
    po_item_id: str
    receipt_events: list[GoodsReceipt]
    verified_quantity: float


class MutationRequest(StrictModel):
    idempotency_key: str = Field(min_length=1, max_length=128)


class SeedCase(StrictModel):
    """Admin-only seed shape for the local simulator."""

    case_id: str
    po_item_id: str
    invoice_id: str
    po_quantity: float = Field(ge=0)
    po_amount: float = Field(ge=0)
    invoice_amount: float = Field(ge=0)
    currency: str = Field(min_length=3, max_length=3)
    matching_type: Literal["two_way", "three_way", "consignment"]
    category: str
    fault: str | None = None
    invoice_verified: bool
    invoice_status: Literal["open", "cleared", "held"]
    po_status: str
    receipt_events: list[GoodsReceipt]
    duplicate_invoice: bool = False
    expected_state: dict[str, str]
    synthetic: bool = True


class ApprovalRequest(StrictModel):
    decision: Literal["approve", "reject"]
    rationale: str = Field(min_length=1, max_length=1000)
    evidence_reference: str = Field(min_length=1, max_length=200)


class HoldRequest(StrictModel):
    """Reason for placing an invoice case on manual hold."""

    idempotency_key: str = Field(min_length=1, max_length=128)
    reason: str = Field(min_length=1, max_length=1000)


class ApprovalRecord(StrictModel):
    case_id: str
    decision: Literal["approve", "reject"]
    rationale: str
    evidence_reference: str
    recorded_at: datetime


class ToolCallRecord(StrictModel):
    sequence: int
    tool: str
    input: dict
    outcome: str
    status_code: int
    timestamp: datetime


class StateTransitionRecord(StrictModel):
    sequence: int
    entity: str
    before: str
    after: str
    reason: str
    timestamp: datetime


class AuditResponse(StrictModel):
    case_id: str
    tool_calls: list[ToolCallRecord]
    transitions: list[StateTransitionRecord]
    compensations: list[dict]

