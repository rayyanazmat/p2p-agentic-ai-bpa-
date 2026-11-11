#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments._runner import RESULTS, run_and_save

if __name__ == "__main__":
    baseline_output = run_and_save(
        "E6_efficiency_baseline_run",
        ["main.py", "--run-baseline", "--cases", "100"],
    )
    baseline_runs = json.loads(
        (ROOT / "data" / "processed" / "baseline_run.json").read_text(
            encoding="utf-8"
        )
    )
    ablation_path = RESULTS / "ablation_run.json"
    if not ablation_path.exists():
        raise FileNotFoundError(
            "Run experiments/e5_ablation.py before e6_efficiency.py; "
            "the measured ablation metrics are required."
        )
    ablation_runs = json.loads(ablation_path.read_text(encoding="utf-8"))
    metrics = (
        "case_count",
        "exact_match_rate",
        "policy_violation_rate",
        "unsafe_mutation_rate",
        "intervention_rate",
        "mean_latency_seconds",
        "p95_latency_seconds",
        "tool_calls_per_case",
        "token_count",
    )
    payload = {
        "label": "E6_efficiency",
        "case_count": 100,
        "baseline_run_artifact": str(
            ROOT / "data" / "processed" / "baseline_run.json"
        ),
        "ablation_run_artifact": str(ablation_path),
        "baseline_metrics": [
            {
                key: item[key]
                for key in (
                    "system",
                    "case_count",
                    "end_state_exact_match",
                    "policy_violation_rate",
                    "unsafe_mutation_rate",
                    "intervention_rate",
                    "cost_per_case_usd",
                    "token_count",
                    "mean_latency_seconds",
                    "p95_latency_seconds",
                    "tool_calls_per_case",
                )
            }
            for item in baseline_runs
        ],
        "ablation_metrics": {
            variant: {key: values[key] for key in metrics}
            for variant, values in ablation_runs.items()
        },
        "interpretation_note": (
            "Offline deterministic runs report zero provider cost; this is not "
            "a hosted-model cost estimate. Latency is local simulator wall time."
        ),
    }
    output_path = RESULTS / "E6_efficiency.json"
    output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Saved measured efficiency and reliability metrics to {output_path}")
    print(f"Full baseline capture: {baseline_output}")
