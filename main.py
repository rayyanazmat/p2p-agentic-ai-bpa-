"""CLI for manifest generation, local API service, and baseline evaluation."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

import uvicorn

from config import (
    API_BASE_URL,
    BPI_LOG_PATH,
    BPI_MANIFEST_PATH,
    MANIFEST_PATH,
    PROCESSED_DIR,
    RUN_CASE_LIMIT,
)
from src.agents.heuristic_agent import HeuristicAgent
from src.agents.react_agent import OfflineBackend, ReActAgent, ToolClient
from src.evaluation.ablation import run_ablation_study, summarize_ablation_results
from src.evaluation.reporting import format_metric_table, summarize_variant_statistics
from src.evaluation.evaluator import Evaluator
from src.pipeline.loader import generate_manifest, load_manifest, summarize_case_manifest
from src.pipeline.bpi import profile_and_build_manifest


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


def smoke_test(limit: int = 1) -> dict[str, Any]:
    """Run a short end-to-end validation against the local simulator."""
    manifest = MANIFEST_PATH
    if not manifest.exists():
        generate_manifest(manifest)
    cases = load_manifest(manifest)
    selected = sample_cases(cases, min(limit, len(cases)) if cases else 0)
    if not selected:
        raise RuntimeError(f"No cases available in manifest: {manifest}")
    summary = run_baselines(len(selected), manifest_path=manifest, output_name="smoke_test.json")
    return {
        "ok": True,
        "input_case_count": len(selected),
        "manifest_case_count": len(cases),
        "result_count": len(summary),
        "output_path": str(PROCESSED_DIR / "smoke_test.json"),
    }


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


def run_baselines(
    limit: int | None,
    manifest_path: Path = MANIFEST_PATH,
    output_name: str = "baseline_run.json",
    baseline_agent: str = "both",
    policy_enabled: bool = True,
    approval_enabled: bool = True,
) -> list[dict[str, Any]]:
    """Run selected baseline agents, save metrics, and stop the simulator."""
    if not manifest_path.exists():
        if manifest_path == MANIFEST_PATH:
            generate_manifest(MANIFEST_PATH)
        elif manifest_path == BPI_MANIFEST_PATH:
            if not BPI_LOG_PATH.exists():
                raise FileNotFoundError(
                    f"BPI XES not found at {BPI_LOG_PATH}; acquire it first"
                )
            profile_and_build_manifest(BPI_LOG_PATH, BPI_MANIFEST_PATH)
        else:
            raise FileNotFoundError(f"Evaluation manifest not found: {manifest_path}")
    cases = load_manifest(manifest_path)
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
        factories = {
            "react": (
                "Baseline — ReAct",
                lambda active_client: ReActAgent(
                    active_client,
                    policy_enabled=policy_enabled,
                    approval_enabled=approval_enabled,
                ),
            ),
            "heuristic": (
                "Baseline — Heuristic",
                lambda active_client: HeuristicAgent(
                    active_client,
                    policy_enabled=policy_enabled,
                    approval_enabled=approval_enabled,
                ),
            ),
        }
        selected_agents = (
            list(factories.items())
            if baseline_agent == "both"
            else [(baseline_agent, factories[baseline_agent])]
        )
        summaries = [
            evaluator.run(name, selected, factory)
            for _, (name, factory) in selected_agents
        ]
        output_path = PROCESSED_DIR / output_name
        Evaluator.save(summaries, output_path)
        print(f"Manifest: {manifest_path}")
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


def run_ablation_cli(limit: int = 5, manifest_path: Path = MANIFEST_PATH) -> dict[str, Any]:
    """Run a factorial ablation study across policy and approval controls."""
    if not manifest_path.exists():
        generate_manifest(manifest_path)
    cases = load_manifest(manifest_path)
    selected = sample_cases(cases, min(limit, len(cases)))
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
        study = {}
        react_variants = {
            "react_policy_on_approval_on": {"backend": OfflineBackend(), "policy_enabled": True, "approval_enabled": True},
            "react_policy_off_approval_on": {"backend": OfflineBackend(), "policy_enabled": False, "approval_enabled": True},
            "react_policy_on_approval_off": {"backend": OfflineBackend(), "policy_enabled": True, "approval_enabled": False},
            "react_policy_off_approval_off": {"backend": OfflineBackend(), "policy_enabled": False, "approval_enabled": False},
        }
        study.update(run_ablation_study(client, selected, ReActAgent, react_variants))
        heuristic_variants = {
            "heuristic_policy_on_approval_on": {"policy_enabled": True, "approval_enabled": True},
            "heuristic_policy_off_approval_on": {"policy_enabled": False, "approval_enabled": True},
            "heuristic_policy_on_approval_off": {"policy_enabled": True, "approval_enabled": False},
            "heuristic_policy_off_approval_off": {"policy_enabled": False, "approval_enabled": False},
        }
        study.update(run_ablation_study(client, selected, HeuristicAgent, heuristic_variants))
        results_path = Path(__file__).resolve().parent / "results" / "ablation_run.json"
        results_path.parent.mkdir(parents=True, exist_ok=True)
        results_path.write_text(json.dumps(study, indent=2) + "\n", encoding="utf-8")
        print(f"Detailed ablation results: {results_path}")
        rows = summarize_ablation_results(study)
        print("\nAblation summary table:")
        print(format_metric_table(rows))
        stats = summarize_variant_statistics(rows)
        print("\nExact match summary:")
        print(json.dumps(stats, sort_keys=True))
        for variant_name, summary in study.items():
            print(
                f"\n{variant_name}: exact_match={summary['exact_match_rate']:.2f} "
                f"policy_violation_rate={summary['policy_violation_rate']:.2f} "
                f"intervention_rate={summary['intervention_rate']:.2f}"
            )
        return study
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
    parser.add_argument(
        "--baseline-agent",
        choices=("both", "react", "heuristic"),
        default="both",
        help="select the baseline agent for --run-baseline",
    )
    parser.add_argument(
        "--policy-enabled",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="enable or disable explicit policy checks for baseline runs",
    )
    parser.add_argument(
        "--approval-enabled",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="enable or disable approval review for baseline runs",
    )
    parser.add_argument(
        "--ablation-study",
        action="store_true",
        help="run a compact policy/approval ablation study for research benchmarking",
    )
    parser.add_argument(
        "--paper-benchmark",
        action="store_true",
        help="run the paper-oriented benchmark across baseline and safety variants",
    )
    parser.add_argument("--serve", action="store_true", help="serve the mock API")
    parser.add_argument(
        "--generate-manifest",
        action="store_true",
        help="regenerate the synthetic 100-case fixture",
    )
    parser.add_argument(
        "--build-bpi-fixture",
        action="store_true",
        help="profile BPI XES and create a trace-derived 100-case fixture",
    )
    parser.add_argument(
        "--run-bpi-baseline",
        action="store_true",
        help="run both baselines on the BPI trace-derived fixture",
    )
    parser.add_argument(
        "--smoke-test",
        action="store_true",
        help="run a compact end-to-end validation against the local simulator",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="alias for --smoke-test used in CI and quality gates",
    )
    parser.add_argument(
        "--dataset-summary",
        action="store_true",
        help="summarize the synthetic manifest for research documentation and data appendix tables",
    )
    parser.add_argument(
        "--benchmark-suite",
        action="store_true",
        help="generate a larger reproducible synthetic benchmark suite for paper evaluation",
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
    elif args.benchmark_suite:
        suite_path = PROCESSED_DIR / "paper_benchmark_suite.json"
        suite = generate_manifest(suite_path, seed=2019, size=max(100, args.cases))
        print(f"Generated benchmark suite with {len(suite)} synthetic cases at {suite_path}")
        print(json.dumps(summarize_case_manifest(suite), indent=2, sort_keys=True))
    elif args.dataset_summary:
        cases = load_manifest(MANIFEST_PATH)
        summary = summarize_case_manifest(cases)
        print(json.dumps(summary, indent=2, sort_keys=True))
    elif args.smoke_test or args.validate:
        result = smoke_test(limit=max(1, min(args.cases, 5)))
        print(f"Smoke test OK: {result}")
    elif args.run_baseline:
        limit = None if args.cases <= 0 or args.cases >= 100 else args.cases
        run_baselines(
            limit,
            baseline_agent=args.baseline_agent,
            policy_enabled=args.policy_enabled,
            approval_enabled=args.approval_enabled,
        )
    elif args.ablation_study or args.paper_benchmark:
        run_ablation_cli(limit=max(1, args.cases))
    elif args.build_bpi_fixture:
        profile, manifest = profile_and_build_manifest(
            BPI_LOG_PATH, BPI_MANIFEST_PATH
        )
        print(f"Parsed {profile['trace_count']} BPI traces / {profile['event_count']} events")
        print(f"Category counts: {profile['matching_category_case_counts']}")
        print(f"Simple-case candidates: {profile['simple_replay_eligible_counts']}")
        print(f"Built {manifest['case_count']} cases at {BPI_MANIFEST_PATH}")
        print(f"Full profile: {PROCESSED_DIR / 'bpi_profile.json'}")
    elif args.run_bpi_baseline:
        limit = None if args.cases <= 0 or args.cases >= 100 else args.cases
        run_baselines(limit, BPI_MANIFEST_PATH, "bpi_baseline_run.json")
    elif not args.generate_manifest:
        print("Choose --serve, --run-baseline, --ablation-study, --paper-benchmark, --generate-manifest, --smoke-test, or --validate.")


if __name__ == "__main__":
    main()
