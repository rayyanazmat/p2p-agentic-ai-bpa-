#!/usr/bin/env python3
"""Export representative successful and policy-risk trajectories from E3."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUN_PATH = ROOT / "data" / "processed" / "baseline_run.json"
MANIFEST_PATH = ROOT / "data" / "test_manifest_100.json"
LOGS = ROOT / "logs"


def main() -> None:
    summaries = json.loads(RUN_PATH.read_text(encoding="utf-8"))
    cases = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))["cases"]
    cases_by_id = {case["case_id"]: case for case in cases}
    react_summary = next(
        (item for item in summaries if "ReAct" in item["system"]), None
    )
    if react_summary is None:
        raise RuntimeError(f"No ReAct trajectory found in {RUN_PATH}")

    successes = [
        run
        for run in react_summary["runs"]
        if run["exact_match"] and not run["policy_violation"]
    ][:2]
    risk_cases = []
    seen_risk_categories: set[str] = set()
    for run in react_summary["runs"]:
        if not run["policy_violation"]:
            continue
        case = cases_by_id[run["case_id"]]
        category = case.get("fault") or case.get("category") or "unspecified"
        if category not in seen_risk_categories:
            risk_cases.append(run)
            seen_risk_categories.add(category)
        if len(risk_cases) == 2:
            break
    if len(risk_cases) < 2:
        risk_cases.extend(
            run
            for run in react_summary["runs"]
            if run["policy_violation"]
            and run["case_id"] not in {item["case_id"] for item in risk_cases}
        )
        risk_cases = risk_cases[:2]
    if len(successes) < 2 or len(risk_cases) < 2:
        raise RuntimeError(
            "Need at least two observed successful and two policy-risk traces; "
            f"found {len(successes)} and {len(risk_cases)}."
        )

    LOGS.mkdir(parents=True, exist_ok=True)
    for run in successes:
        case_id = run["case_id"]
        payload = {
            "classification": "successful_case",
            "source_experiment": "E3_proposed_system",
            "case": cases_by_id[case_id],
            "trajectory": run,
        }
        (LOGS / f"success_case_{case_id}.json").write_text(
            json.dumps(payload, indent=2) + "\n", encoding="utf-8"
        )
    risk_cases_all = [
        item for item in react_summary["runs"] if item["policy_violation"]
    ]
    categories: Counter[str] = Counter()
    for run in risk_cases_all:
        case = cases_by_id[run["case_id"]]
        category = case.get("fault") or case.get("category") or "unspecified"
        categories[category] += 1
    for run in risk_cases:
        case_id = run["case_id"]
        case = cases_by_id[case_id]
        payload = {
            "classification": "policy_risk_case",
            "classification_note": (
                "A detected policy-violation condition. It is not necessarily an "
                "end-state mismatch; see the recorded metrics and trajectory."
            ),
            "source_experiment": "E3_proposed_system",
            "case": case,
            "trajectory": run,
        }
        (LOGS / f"failure_case_{case_id}.json").write_text(
            json.dumps(payload, indent=2) + "\n", encoding="utf-8"
        )

    failures = [
        run for run in react_summary["runs"] if not run["exact_match"]
    ]
    policy_risks = risk_cases_all
    summary = {
        "source_experiment": "E3_proposed_system",
        "case_count": react_summary["case_count"],
        "end_state_mismatch_count": len(failures),
        "policy_violation_case_count": len(policy_risks),
        "policy_violation_category_counts": dict(categories),
        "representative_success_cases": [run["case_id"] for run in successes],
        "representative_policy_risk_cases": [
            run["case_id"] for run in risk_cases
        ],
        "interpretation": (
            "Policy-risk cases are reported separately from end-state mismatches. "
            "This synthetic benchmark's fault composition must not be interpreted "
            "as production failure prevalence."
        ),
    }
    (LOGS / "failure_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
