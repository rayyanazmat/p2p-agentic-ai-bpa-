"""Paired baseline execution and case-level operational metrics."""

from __future__ import annotations

import json
import os
import statistics
import time
from pathlib import Path
from typing import Any, Callable

from src.agents.react_agent import ToolClient


AgentFactory = Callable[[ToolClient], Any]


def _percentile_95(values: list[float]) -> float:
    """Return nearest-rank p95, defined for non-empty observations."""
    if not values:
        return 0.0
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, int(0.95 * len(ordered) + 0.999999) - 1))
    return round(ordered[index], 4)


class Evaluator:
    """Run a baseline against a frozen synthetic or real case manifest."""

    def __init__(self, client: ToolClient) -> None:
        self.client = client

    def run(
        self,
        name: str,
        cases: list[dict[str, Any]],
        agent_factory: AgentFactory,
    ) -> dict[str, Any]:
        """Reset the simulator, execute cases, and compute aggregate metrics."""
        self.client.reset(cases)
        runs: list[dict[str, Any]] = []
        latencies: list[float] = []
        exact = violations = unsafe = interventions = total_tokens = 0
        hosted_input_tokens = hosted_output_tokens = 0
        has_hosted_model = False
        total_calls = 0
        for case in cases:
            agent = agent_factory(self.client)
            start = time.perf_counter()
            # Keep frozen evaluation labels outside the controller's input.
            decision_case = {
                key: value for key, value in case.items() if key != "expected_state"
            }
            run = agent.run(decision_case)
            latency = time.perf_counter() - start
            latencies.append(latency)
            actual = self.client.request(
                "GET", f"/invoices/{case['invoice_id']}"
            )
            audit = self.client.audit(case["case_id"])
            expected_status = case["expected_state"]["invoice_status"]
            matched = actual["status"] == expected_status
            exact += int(matched)
            case_violation = bool(run.get("policy_violations")) or any(
                call["status_code"] == 409
                and call["tool"] in {"clear_invoice", "verify_goods_receipts"}
                for call in audit["tool_calls"]
            )
            violations += int(case_violation)
            # Server-side invariants prevent unsafe state changes. Count any
            # unexpected clear of a case whose frozen oracle requires a hold.
            unsafe_case = (
                actual["status"] == "cleared" and expected_status != "cleared"
            )
            unsafe += int(unsafe_case)
            interventions += int(run.get("intervention_required", False))
            input_tokens = int(run.get("input_tokens", 0))
            output_tokens = int(run.get("output_tokens", 0))
            total_tokens += input_tokens + output_tokens
            if run.get("backend") in {"openai-compatible", "ollama-local"}:
                has_hosted_model = True
                hosted_input_tokens += input_tokens
                hosted_output_tokens += output_tokens
            total_calls += len(audit["tool_calls"])
            runs.append(
                {
                    "case_id": case["case_id"],
                    "expected_status": expected_status,
                    "actual_status": actual["status"],
                    "exact_match": matched,
                    "policy_violation": case_violation,
                    "unsafe_mutation": unsafe_case,
                    "intervention_required": bool(
                        run.get("intervention_required", False)
                    ),
                    "latency_seconds": round(latency, 4),
                    "agent": run,
                    "audit": audit,
                }
            )
        count = len(cases)
        input_rate = os.getenv("OPENAI_INPUT_USD_PER_MILLION")
        output_rate = os.getenv("OPENAI_OUTPUT_USD_PER_MILLION")
        backends = {run["agent"].get("backend") for run in runs}
        has_local_model = backends == {"ollama-local"}
        if has_local_model or not has_hosted_model:
            cost_per_case: float | None = 0.0
        elif input_rate is not None and output_rate is not None:
            total_cost = (
                hosted_input_tokens * float(input_rate)
                + hosted_output_tokens * float(output_rate)
            ) / 1_000_000
            cost_per_case = total_cost / count if count else 0.0
        else:
            cost_per_case = None
        summary = {
            "system": name,
            "case_count": count,
            "end_state_exact_match": exact / count if count else 0.0,
            "policy_violation_rate": violations / count if count else 0.0,
            "unsafe_mutation_rate": unsafe / count if count else 0.0,
            "intervention_rate": interventions / count if count else 0.0,
            "cost_per_case_usd": cost_per_case,
            "token_count": total_tokens,
            "p95_latency_seconds": _percentile_95(latencies),
            "mean_latency_seconds": statistics.mean(latencies) if latencies else 0.0,
            "tool_calls_per_case": total_calls / count if count else 0.0,
            "runs": runs,
        }
        return summary

    @staticmethod
    def save(summary_list: list[dict[str, Any]], path: Path) -> None:
        """Save metrics and per-case full tool audit trails as JSON."""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(summary_list, indent=2) + "\n", encoding="utf-8")
