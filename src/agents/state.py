"""Typed state carried by an agent during one procurement case."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class AgentState(BaseModel):
    """A compact, auditable snapshot of a ReAct run."""

    model_config = ConfigDict(extra="forbid")

    case_id: str
    po_item_id: str
    invoice_id: str
    phase: Literal[
        "initialized", "evidence_retrieved", "receipt_verified", "held", "cleared"
    ] = "initialized"
    observations: list[dict[str, Any]] = Field(default_factory=list)
    actions: list[dict[str, Any]] = Field(default_factory=list)
    estimated_input_tokens: int = 0
    estimated_output_tokens: int = 0
    intervention_required: bool = False
    policy_violations: list[str] = Field(default_factory=list)

