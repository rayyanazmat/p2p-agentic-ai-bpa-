"""Shared helpers for individual Phase 2 evaluation scripts."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
RESULTS.mkdir(exist_ok=True)


def run_and_save(label: str, args: list[str]) -> Path:
    """Run a command and save the output JSON next to the repo results directory."""
    completed = subprocess.run(
        [sys.executable, *args],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    payload = {
        "label": label,
        "command": [sys.executable, *args],
        "returncode": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
    }
    output_path = RESULTS / f"{label}.json"
    output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    if completed.returncode:
        raise RuntimeError(
            f"{label} failed with exit code {completed.returncode}; "
            f"see {output_path} for captured output"
        )
    return output_path
