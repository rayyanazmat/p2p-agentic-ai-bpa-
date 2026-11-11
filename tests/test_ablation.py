"""Tests for the paper-oriented ablation study utilities."""

from src.agents.heuristic_agent import HeuristicAgent
from src.agents.react_agent import OfflineBackend, ReActAgent
from src.evaluation.ablation import run_ablation_study, summarize_ablation_results
from src.evaluation.reporting import format_metric_table, summarize_best_variant
from src.pipeline.loader import make_case, summarize_case_manifest


def test_ablation_variants_surface_policy_effects() -> None:
    """Ablation toggles change the policy and intervention reporting in a measurable way."""
    cases = [make_case(1, "three_way_missing_gr"), make_case(2, "two_way")]
    variants = {
        "react_policy_on": {"backend": OfflineBackend(), "policy_enabled": True, "approval_enabled": True},
        "react_policy_off": {"backend": OfflineBackend(), "policy_enabled": False, "approval_enabled": False},
    }
    class DummyClient:
        def reset(self, _cases):
            return None
        def get_po(self, po_item_id):
            return {"po_item_id": po_item_id, "amount": 100.0, "quantity": 10.0, "matching_type": "three_way"}
        def get_invoice(self, invoice_id):
            return {"invoice_id": invoice_id, "status": "held", "verified": True, "duplicate_invoice": False, "amount": 100.0}
        def get_receipts(self, po_item_id):
            return {"po_item_id": po_item_id, "receipt_events": [{"quantity": 2.0, "verified": False}], "verified_quantity": 0.0}
        def verify_receipts(self, _po_item_id, _key):
            return {"po_item_id": _po_item_id, "verified": True, "quantity": 10.0}
        def clear_invoice(self, invoice_id, _key):
            return {"invoice_id": invoice_id, "status": "cleared", "simulated": True}
        def hold_case(self, _case_id, _reason):
            return {"status": "held"}
        def audit(self, _case_id):
            return {"tool_calls": []}
    results = run_ablation_study(DummyClient(), cases, ReActAgent, variants)
    assert results["react_policy_on"]["case_count"] == 2
    assert results["react_policy_off"]["case_count"] == 2
    assert results["react_policy_on"]["policy_violation_rate"] >= 0.0
    assert results["react_policy_off"]["policy_violation_rate"] >= 0.0
    table = summarize_ablation_results(results)
    assert table[0]["variant"] == "react_policy_on"
    assert table[0]["case_count"] == 2
    rendered = format_metric_table(table)
    assert "| variant | case_count | exact_match_rate | policy_violation_rate | intervention_rate |" in rendered
    assert "react_policy_on" in rendered
    summary = summarize_best_variant(table)
    assert summary is not None and summary["best_variant"] == "react_policy_on"
    dataset = summarize_case_manifest(cases)
    assert dataset["case_count"] == 2
    assert dataset["category_counts"]["three_way_missing_gr"] == 1


def test_ablation_supports_heuristic_agent_variants() -> None:
    """The heuristic agent supports the same toggles for benchmark comparisons."""
    class DummyClient:
        def reset(self, _cases):
            return None
        def get_po(self, po_item_id):
            return {"po_item_id": po_item_id, "amount": 101.0, "quantity": 10.0, "matching_type": "two_way"}
        def get_invoice(self, invoice_id):
            return {"invoice_id": invoice_id, "verified": True, "duplicate_invoice": False, "amount": 101.0, "status": "open"}
        def get_receipts(self, po_item_id):
            return {"po_item_id": po_item_id, "receipt_events": [{"quantity": 10.0, "verified": True}], "verified_quantity": 10.0}
        def clear_invoice(self, invoice_id, _key):
            return {"invoice_id": invoice_id, "status": "cleared", "simulated": True}
        def hold_case(self, _case_id, _reason):
            return {"status": "held"}
    cases = [make_case(3, "two_way")]
    results = run_ablation_study(
        DummyClient(),
        cases,
        HeuristicAgent,
        {
            "heuristic_all_on": {"policy_enabled": True, "approval_enabled": True},
            "heuristic_policy_off": {"policy_enabled": False, "approval_enabled": False},
        },
    )
    assert results["heuristic_all_on"]["case_count"] == 1
    assert results["heuristic_policy_off"]["case_count"] == 1
