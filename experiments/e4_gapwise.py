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
        "E4_gapwise_bpi_transfer",
        ["main.py", "--run-bpi-baseline", "--cases", "100"],
    )
    result.with_name("E4_gapwise.json").write_text(
        result.read_text(encoding="utf-8").replace(
            '"label": "E4_gapwise_bpi_transfer"',
            '"label": "E4_gapwise_bpi_transfer",\n'
            '  "status": "proxy_label_transfer_test",\n'
            '  "gap": "transfer from synthetic/formal evaluation to procurement traces",\n'
            '  "caveat": "The BPI-derived manifest reconstructs invoice fields and expected outcomes; these are proxy labels, not observed invoice ground truth."',
        ),
        encoding="utf-8",
    )
    result.unlink()
    print(f"Saved BPI transfer experiment to {result.with_name('E4_gapwise.json')}")
