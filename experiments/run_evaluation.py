#!/usr/bin/env python3
"""Run the project’s Phase 2 evaluation workflow and save reproducible JSON artifacts."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
RESULTS.mkdir(exist_ok=True)


def run_script(name: str) -> dict[str, object]:
    """Run one experiment script and report its artifact."""
    completed = subprocess.run(
        [sys.executable, f"experiments/{name}.py"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode:
        raise RuntimeError(
            f"{name} failed ({completed.returncode}):\n"
            f"{completed.stdout}\n{completed.stderr}"
        )
    return {"script": name, "stdout": completed.stdout.strip()}


def main() -> None:
    experiments = {}
    for script in (
        "e1_baseline",
        "e2_base_paper",
        "e3_proposed_system",
        "export_representative_traces",
        "e4_gapwise",
        "e5_ablation",
        "e6_efficiency",
    ):
        experiments[script] = run_script(script)
    summary = {
        "project": "Policy-Grounded Agentic AI for Safe Purchase-to-Pay Automation",
        "phase": "Phase 2",
        "case_count": 100,
        "experiments": experiments,
    }
    output_path = RESULTS / "phase2_experiments.json"
    output_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(f"Saved evaluation summary to {output_path}")


if __name__ == "__main__":
    main()
