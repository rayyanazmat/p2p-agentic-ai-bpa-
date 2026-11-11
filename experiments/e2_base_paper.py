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
        "E2_base_paper_proxy",
        [
            "main.py",
            "--run-baseline",
            "--baseline-agent",
            "heuristic",
            "--cases",
            "100",
        ],
    )
    result.with_name("E2_base_paper.json").write_text(
        result.read_text(encoding="utf-8").replace(
            '"label": "E2_base_paper_proxy"',
            '"label": "E2_base_paper_proxy",\n'
            '  "status": "proxy_not_reproduction",\n'
            '  "base_paper": "Fionda, Ielo, and Ricca, IJCAI 2025",\n'
            '  "note": "The selected paper evaluates LLM translation of Declare constraints with symbolic checking, not P2P transaction execution. This deterministic heuristic is a domain comparator only; it is not a reproduction of the paper method or its results."',
        ),
        encoding="utf-8",
    )
    result.unlink()
    print(f"Saved explicit base-paper proxy evaluation to {result.with_name('E2_base_paper.json')}")
