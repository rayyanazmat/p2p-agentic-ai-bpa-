"""Unit tests for policy evaluation and approval gating."""

from src.pipeline.loader import make_case
from src.policies.engine import PolicyEngine


def test_policy_allows_clean_three_way_case() -> None:
    """A valid three-way match remains allowed and low risk."""
    case = make_case(1, "three_way_complete")
    report = PolicyEngine.evaluate(case)
    assert report.allowed is True
    assert report.risk_level == "low"
    assert report.violations == []


def test_policy_rejects_amount_mismatch_and_missing_receipt() -> None:
    """Policy violations are surfaced with clear structured evidence."""
    case = make_case(2, "fault_injected", "amount_mismatch")
    report = PolicyEngine.evaluate(case)
    assert report.allowed is False
    assert report.risk_level == "high"
    rules = {item.rule for item in report.violations}
    assert "amount_mismatch" in rules

    incomplete = make_case(3, "three_way_missing_gr")
    incomplete_report = PolicyEngine.evaluate(incomplete)
    assert incomplete_report.allowed is False
    assert "incomplete_receipt" in {item.rule for item in incomplete_report.violations}


def test_policy_flags_duplicate_and_unverified_invoice() -> None:
    """Unsafe process evidence triggers a policy failure before action executes."""
    dup = make_case(4, "fault_injected", "duplicate_invoice")
    report = PolicyEngine.evaluate(dup)
    assert report.allowed is False
    assert "duplicate_invoice" in {item.rule for item in report.violations}

    unverified = make_case(5, "fault_injected", "unverified_invoice")
    report = PolicyEngine.evaluate(unverified)
    assert report.allowed is False
    assert "invoice_unverified" in {item.rule for item in report.violations}


def test_policy_serializes_to_json_safe_output() -> None:
    """The report can be converted to JSON-like dictionaries for audits and logs."""
    case = make_case(6, "fault_injected", "amount_mismatch")
    report = PolicyEngine.evaluate(case)
    payload = report.as_dict()
    assert payload["allowed"] is False
    assert payload["risk_level"] in {"high", "medium", "critical"}
    assert payload["violations"]
