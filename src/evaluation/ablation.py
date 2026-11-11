"""Simple ablation study utilities for benchmarking policy and approval effects."""

from __future__ import annotations

import statistics
import time
from typing import Any, Callable

from src.agents.react_agent import ToolClient


def run_ablation_study(
    client: ToolClient,
    cases: list[dict[str, Any]],
    agent_factory: Callable[..., Any],
    variants: dict[str, dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """Run a compact benchmark across toggled policy/approval variants."""
    results: dict[str, dict[str, Any]] = {}
    for variant_name, kwargs in variants.items():
        client.reset(cases)
        outcomes: list[dict[str, Any]] = []
        latencies: list[float] = []
        total_tool_calls = total_tokens = 0
        for case in cases:
            agent = agent_factory(client, **kwargs)
            started = time.perf_counter()
            # Keep frozen evaluation labels outside the controller's input.
            decision_case = {
                key: value for key, value in case.items() if key != "expected_state"
            }
            result = agent.run(decision_case)
            latency = time.perf_counter() - started
            invoice = client.get_invoice(case["invoice_id"])
            audit_method = getattr(client, "audit", None)
            audit = audit_method(case["case_id"]) if audit_method else {"tool_calls": []}
            tool_calls = len(audit.get("tool_calls", []))
            token_count = int(result.get("input_tokens", 0)) + int(
                result.get("output_tokens", 0)
            )
            latencies.append(latency)
            total_tool_calls += tool_calls
            total_tokens += token_count
            expected_status = case["expected_state"]["invoice_status"]
            actual_status = invoice["status"]
            outcomes.append(
                {
                    "case_id": case["case_id"],
                    "expected_status": expected_status,
                    "actual_status": actual_status,
                    "exact_match": actual_status == expected_status,
                    "outcome": result.get("outcome"),
                    "policy_violations": result.get("policy_violations", []),
                    "intervention_required": result.get("intervention_required", False),
                    "unsafe_mutation": (
                        actual_status == "cleared" and expected_status != "cleared"
                    ),
                    "latency_seconds": round(latency, 6),
                    "tool_call_count": tool_calls,
                    "token_count": token_count,
                    "agent": result,
                    "audit": audit,
                }
            )
        exact = sum(1 for item in outcomes if item["exact_match"])
        violations = sum(1 for item in outcomes if item["policy_violations"])
        interventions = sum(1 for item in outcomes if item["intervention_required"])
        unsafe = sum(1 for item in outcomes if item["unsafe_mutation"])
        results[variant_name] = {
            "case_count": len(cases),
            "exact_match_rate": exact / len(cases) if cases else 0.0,
            "policy_violation_rate": violations / len(cases) if cases else 0.0,
            "unsafe_mutation_rate": unsafe / len(cases) if cases else 0.0,
            "intervention_rate": interventions / len(cases) if cases else 0.0,
            "mean_latency_seconds": statistics.mean(latencies) if latencies else 0.0,
            "p95_latency_seconds": (
                sorted(latencies)[max(0, int(0.95 * len(latencies) + 0.999999) - 1)]
                if latencies
                else 0.0
            ),
            "tool_calls_per_case": total_tool_calls / len(cases) if cases else 0.0,
            "token_count": total_tokens,
            "outcomes": outcomes,
        }
    return results


def summarize_ablation_results(results: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    """Return a paper-friendly summary table ready for report insertion."""
    rows: list[dict[str, Any]] = []
    for variant_name, summary in results.items():
        rows.append(
            {
                "variant": variant_name,
                "case_count": summary["case_count"],
                "exact_match_rate": round(summary["exact_match_rate"], 4),
                "policy_violation_rate": round(summary["policy_violation_rate"], 4),
                "intervention_rate": round(summary["intervention_rate"], 4),
            }
        )
    return rows
