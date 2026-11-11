#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments._runner import run_and_save

if __name__ == "__main__":
    result = run_and_save(
        "E1_baseline",
        [
            "main.py",
            "--run-baseline",
            "--baseline-agent",
            "react",
            "--no-policy-enabled",
            "--no-approval-enabled",
            "--cases",
            "100",
        ],
    )
    print(f"Saved baseline experiment output to {result}")
