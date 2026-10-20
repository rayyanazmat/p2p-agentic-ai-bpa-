"""CLI for manifest generation, local API service, and baseline evaluation."""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

import uvicorn

from config import API_BASE_URL, MANIFEST_PATH, PROCESSED_DIR, RUN_CASE_LIMIT
from src.agents.heuristic_agent import HeuristicAgent
from src.agents.react_agent import ReActAgent, ToolClient
from src.evaluation.evaluator import Evaluator
from src.pipeline.loader import generate_manifest, load_manifest


def wait_for_api(base_url: str, process: subprocess.Popen[Any] | None = None) -> None:
    """Wait briefly for the local simulator to accept health requests."""
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        if process is not None and process.poll() is not None:
            raise RuntimeError("Simulator process exited before becoming ready")
        try:
            with urllib.request.urlopen(base_url.rstrip("/") + "/health", timeout=1):
                return
        except (urllib.error.URLError, TimeoutError):
            time.sleep(0.2)
    raise RuntimeError(f"Simulator did not become ready at {base_url}")


def sample_cases(cases: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    """Select a balanced demo sample, including each available scenario type."""
    if limit >= len(cases):
        return cases
    selected: list[dict[str, Any]] = []
    categories: set[str] = set()
    for case in cases:
        category = case.get("fault") or case.get("category", "unknown")
        if category not in categories:
            selected.append(case)
            categories.add(category)
        if len(selected) >= limit:
            return selected
    selected_ids = {case["case_id"] for case in selected}
    selected.extend(case for case in cases if case["case_id"] not in selected_ids)
    return selected[:limit]


def print_summary(summary: dict[str, Any]) -> None:
    """Print compact aggregate metrics and per-case action traces."""
    fields = (
        "end_state_exact_match",
        "policy_violation_rate",
        "unsafe_mutation_rate",
        "intervention_rate",
        "cost_per_case_usd",
        "token_count",
        "p95_latency_seconds",
        "tool_calls_per_case",
    )
    print(f"\n{summary['system']} ({summary['case_count']} cases)")
    for key in fields:
        print(f"  {key}: {summary[key]}")
    displayed_runs = (
        summary["runs"]
        if len(summary["runs"]) <= 10
        else summary["runs"][:5]
    )
    for run in displayed_runs:
        actions = run["agent"].get("actions", [])
        print(
            f"  {run['case_id']}: expected={run['expected_status']} "
            f"actual={run['actual_status']} actions={actions} "
            f"tool_calls={len(run['audit']['tool_calls'])}"
        )
    if len(displayed_runs) < len(summary["runs"]):
        additional = len(summary["runs"]) - len(displayed_runs)
        print(f"  ({additional} additional case traces in JSON log)")


def run_baselines(limit: int | None) -> list[dict[str, Any]]:
    """Start simulator, execute both baselines, save metrics, and stop service."""
    if not MANIFEST_PATH.exists():
        generate_manifest(MANIFEST_PATH)
    cases = load_manifest(MANIFEST_PATH)
    selected = cases if limit is None else sample_cases(cases, limit)
    base_url = API_BASE_URL
    host = base_url.split("//", 1)[-1].split(":", 1)[0]
    port = int(base_url.rsplit(":", 1)[-1])
    process: subprocess.Popen[Any] | None = None
    try:
        try:
            with urllib.request.urlopen(base_url.rstrip("/") + "/health", timeout=0.4):
                print(f"Using simulator already available at {base_url}")
        except (urllib.error.URLError, TimeoutError):
            process = subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "uvicorn",
                    "src.simulator.app:app",
                    "--host",
                    host,
                    "--port",
                    str(port),
                    "--log-level",
                    "warning",
                ],
                cwd=Path(__file__).resolve().parent,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            wait_for_api(base_url, process)
        client = ToolClient(base_url)
        evaluator = Evaluator(client)
        summaries = [
            evaluator.run("Baseline 1 — ReAct", selected, ReActAgent),
            evaluator.run("Baseline 2 — Heuristic", selected, HeuristicAgent),
        ]
        output_path = PROCESSED_DIR / "baseline_run.json"
        Evaluator.save(summaries, output_path)
        print(f"Manifest: {MANIFEST_PATH}")
        print(f"Detailed tool logs and metrics: {output_path}")
        for summary in summaries:
            print_summary(summary)
        return summaries
    finally:
        if process is not None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()


def parse_args() -> argparse.Namespace:
    """Parse CLI options."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--run-baseline", action="store_true", help="run both baselines"
    )
    parser.add_argument("--serve", action="store_true", help="serve the mock API")
    parser.add_argument(
        "--generate-manifest",
        action="store_true",
        help="regenerate the synthetic 100-case fixture",
    )
    parser.add_argument(
        "--cases", type=int, default=RUN_CASE_LIMIT,
        help="number of cases (default: balanced sample; use 100 for full fixture)",
    )
    return parser.parse_args()


def main() -> None:
    """Run requested CLI operation."""
    args = parse_args()
    if args.generate_manifest or not MANIFEST_PATH.exists():
        generated = generate_manifest(MANIFEST_PATH)
        print(f"Generated {len(generated)} synthetic cases at {MANIFEST_PATH}")
    if args.serve:
        uvicorn.run("src.simulator.app:app", host="127.0.0.1", port=8000, reload=False)
    elif args.run_baseline:
        limit = None if args.cases <= 0 or args.cases >= 100 else args.cases
        run_baselines(limit)
    elif not args.generate_manifest:
        print("Choose --serve, --run-baseline, or --generate-manifest.")


if __name__ == "__main__":
    main()

