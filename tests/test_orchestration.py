"""Tests for approval orchestration and human review decisions."""

from src.orchestration.controller import ApprovalController
from src.pipeline.loader import make_case


def test_approval_allows_clean_case() -> None:
    """Low-risk consistent evidence passes without human review."""
    case = make_case(1, "two_way")
    decision = ApprovalController.decide(case)
    assert decision.decision == "approve"
    assert decision.risk_level == "low"
    assert decision.blocked_by == []


def test_approval_requires_review_for_amount_mismatch() -> None:
    """A mismatched invoice needs human review, and often an outright hold when multiple signals are present."""
    case = make_case(2, "fault_injected", "amount_mismatch")
    decision = ApprovalController.decide(case)
    assert decision.decision in {"review", "hold"}
    assert decision.risk_score >= 40
    assert "amount_mismatch" in decision.blocked_by


def test_approval_holds_high_risk_cases() -> None:
    """Critical evidence patterns trigger a hold rather than approval."""
    case = make_case(3, "fault_injected", "duplicate_invoice")
    decision = ApprovalController.decide(case)
    assert decision.decision == "hold"
    assert decision.risk_level in {"high", "critical"}
    assert "duplicate_invoice" in decision.blocked_by


def test_risk_score_distinguishes_missing_receipt() -> None:
    """Incomplete three-way evidence raises a significant risk score."""
    case = make_case(4, "three_way_missing_gr")
    decision = ApprovalController.decide(case)
    assert decision.risk_score >= 35
    assert decision.decision in {"review", "hold"}
    assert "incomplete_receipt" in decision.blocked_by
