"""Tests for compensation and rollback guidance."""

from src.pipeline.loader import make_case
from src.safeguards.compensation import CompensationEngine


def test_compensation_plan_is_empty_for_clean_case() -> None:
    """A clean case does not require any compensating steps."""
    case = make_case(1, "three_way_complete")
    plan = CompensationEngine.plan(case)
    assert plan.required is False
    assert plan.actions == []


def test_compensation_plan_requests_review_for_unsafe_case() -> None:
    """Inconsistent evidence triggers the corrective actions required for safety."""
    case = make_case(2, "fault_injected", "amount_mismatch")
    plan = CompensationEngine.plan(case)
    assert plan.required is True
    actions = {item.action for item in plan.actions}
    assert "reject_invoice" in actions


def test_compensation_plan_reverts_illegal_clearance() -> None:
    """A case that has been cleared when the oracle expects a hold should be rolled back."""
    case = make_case(3, "fault_injected", "amount_mismatch")
    case["invoice_status"] = "cleared"
    plan = CompensationEngine.plan(case)
    assert plan.required is True
    assert any(item.action == "revert_clearance" for item in plan.actions)


def test_compensation_plan_handles_missing_receipt_flow() -> None:
    """Three-way cases with incomplete evidence get a corrective receipt action."""
    case = make_case(4, "three_way_missing_gr")
    plan = CompensationEngine.plan(case)
    assert plan.required is True
    assert any(item.action == "request_receipt" for item in plan.actions)
