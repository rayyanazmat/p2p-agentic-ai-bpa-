# Policy-Grounded Agentic AI for Safe Purchase-to-Pay Automation

**Course:** AI4015 — Agentic Artificial Intelligence
**Project code:** AI4015
**Phase:** 2 — Policy-Grounded Workflow Hardening and Validation

## Overview

This project studies agentic automation for purchase-to-pay (P2P) workflows. The repository provides a local procurement simulator, two baseline agents, a data pipeline for synthetic and BPI Challenge 2019 cases, and an evaluation harness.

The simulator is deterministic and does not connect to an ERP or make payments. BPI Challenge 2019 contains historical purchase-order item events, not invoice-level transaction records. Where replay cases require invoice IDs, amounts, quantities, or expected terminal states, those fields are reconstructed and must be treated as synthetic or proxy labels.

## Current implementation

- **FastAPI/Pydantic simulator:** purchase-order, invoice, goods-receipt, approval, hold, reset, and audit endpoints.
- **ReAct baseline:** structured action output with offline, OpenAI-compatible, and local Ollama backends. Offline is the default.
- **Heuristic baseline:** deterministic workflow rules for comparison.
- **Data pipeline:** synthetic fixture generation and XES/CSV loading; optional BPI trace profiling and replay-manifest generation.
- **Policy engine:** explicit rule evaluation for invoice verification, duplicate evidence, amount mismatches, and incomplete receipts.
- **Approval orchestration:** risk-based review/hold decisions for human-in-the-loop governance.
- **Compensation safeguards:** corrective plans for unsafe clearances, incomplete receipts, and policy violations.
- **Evaluation:** end-state match, policy violations, unsafe mutations, interventions, token use, cost, latency, and tool-call metrics.

The project now includes a concrete safety layer in addition to the baseline workflow, providing explicit review and intervention steps before unsafe automation is allowed to proceed.

## Changes since Phase 1

This Phase 2 revision keeps the original Phase 1 baseline, but extends it in the ways required by the official Phase 2 rubric:

- [x] Added a policy-aware decision layer for invoice verification, amount mismatch, incomplete receipt, and duplicate evidence conditions.
- [x] Added a hold/review orchestration layer and safer escalation logic for human-in-the-loop control.
- [x] Added compensating safeguards for unsafe or inconsistent states.
- [x] Added benchmark and ablation reporting utilities for paper-ready tables.
- [x] Added reproducible result and dataset-summary tooling and a lighter Phase 2 experiment package.
- [x] Added a development log and environment template to match repository expectations for the semester project.

## Architecture diagram

```text
+--------------------+     +--------------------------+
| Synthetic / BPI    | --> | Data Loader / Manifest   |
| cases and labels   |     | generator                |
+--------------------+     +-------------+------------+
                                          |
                                          v
                            +---------------------------+
                            | Simulator / Tool Service  |
                            | PO, invoice, GR, hold     |
                            +-------------+-------------+
                                          |
                                          v
                         +-------------------------------+
                         | Policy Engine / Approval      |
                         | review / hold / escalate      |
                         +---------------+---------------+
                                         |
                                         v
                           +-------------------------------+
                           | Agent Loop (ReAct / Heuristic)|
                           | tool usage + reasoning        |
                           +---------------+---------------+
                                           |
                                           v
                              +-------------------------+
                              | Evaluation + Ablation    |
                              | metrics, tables, logs   |
                              +-------------------------+
```

## Quick start

Requires Python 3.10 or later.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Run a quick repository smoke test before large evaluation runs:

```bash
python main.py --smoke-test
# or
python main.py --validate
```

Run a compact paper-oriented benchmark comparing policy and approval variants:

```bash
python main.py --paper-benchmark --cases 10
# or
python main.py --ablation-study --cases 10
```

Run the Phase 2 evaluation workflow and save reproducible JSON to `results/phase2_experiments.json`:

```bash
python experiments/run_evaluation.py
```

Run each required experiment individually (E1–E6):

```bash
python experiments/e1_baseline.py
python experiments/e2_base_paper.py
python experiments/e3_proposed_system.py
python experiments/e4_gapwise.py
python experiments/e5_ablation.py
python experiments/e6_efficiency.py
```

Run both baselines on the default balanced sample:

```bash
python main.py --run-baseline
```

Run the complete synthetic 100-case fixture:

```bash
python main.py --run-baseline --cases 100
```

Summarize the dataset and generate a paper-friendly appendix snapshot:

```bash
python main.py --dataset-summary
```

The CLI starts the local simulator if it is not already running. Results and audit traces are written to `data/processed/baseline_run.json`, while the smoke test writes `data/processed/smoke_test.json`. Ablation runs print a markdown-ready comparison table designed for paper reporting. A compact summary of the saved experiment outputs is in `results/phase2_summary.md`, the machine-readable evidence file is in `results/phase2_evidence.json`, representative success and policy-risk traces are in `logs/`, and the working paper source is in `submission/`. To start the API separately, run `python main.py --serve`; interactive API documentation is available at `http://127.0.0.1:8000/docs`.

## Optional model backends

The default ReAct backend is a deterministic offline planner; its output is not an LLM evaluation.

For an OpenAI-compatible hosted model, set `P2P_MODEL_PROVIDER=openai` and `OPENAI_API_KEY`. Optionally set `OPENAI_MODEL` (default: `gpt-4o-mini`) and `OPENAI_BASE_URL` for a compatible service.

For a local Ollama model, ensure Ollama is running and set:

```bash
export P2P_MODEL_PROVIDER=ollama
export OLLAMA_MODEL=qwen3.5:0.8b
export OLLAMA_NUM_CTX=2048
export OLLAMA_NUM_THREADS=2
python main.py --run-baseline --cases 1
```

Hosted calls may incur provider charges. Keep credentials in environment variables and out of Git.

## BPI Challenge 2019 replay

The raw event log is excluded from Git. Place the expanded IEEE-XES file at `data/raw/BPI_Challenge_2019.xes`, then build and run the trace-derived replay fixture:

```bash
python main.py --build-bpi-fixture
python main.py --run-bpi-baseline --cases 100
```

The fixture groups cases by purchase-order document to avoid item-level leakage. The log does not provide invoice-level IDs, amounts, quantities, or approval decisions; reconstructed transaction fields and proxy outcomes must not be reported as source ground truth. Dataset record and license: [BPI Challenge 2019, 4TU.ResearchData](https://doi.org/10.4121/uuid:d06aff4b-79f0-45e6-8ec8-e19730c248f1), CC BY 4.0.

## Architecture

`src/simulator/` implements the deterministic tool service; `src/agents/` contains the ReAct and heuristic baselines; `src/pipeline/` loads cases and builds fixtures; `src/policies/` checks the safety rules; `src/orchestration/` guides approve/review/hold decisions; `src/safeguards/` defines compensating actions; and `src/evaluation/` runs agents and computes metrics. The CLI entry point is `main.py`.

| Method | Endpoint | Purpose |
| :--- | :--- | :--- |
| `GET` | `/purchase-orders/{po_item_id}` | Read purchase-order item state. |
| `GET` | `/invoices/{invoice_id}` | Read invoice state. |
| `GET` | `/goods-receipts/{po_item_id}` | Read receipt evidence. |
| `POST` | `/goods-receipts/{po_item_id}/verify` | Verify receipt evidence idempotently. |
| `POST` | `/invoices/{invoice_id}/clear` | Simulate invoice clearing after server-side checks. |
| `POST` | `/cases/{case_id}/approval` | Record an approval or rejection. |
| `GET` | `/cases/{case_id}/audit` | Read tool calls and state transitions. |

## Gap-resolution table

| Gap | Method / component | Metric | Base paper result | Our result | Addressed? |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Safety and policy compliance | Policy engine + approval gate + simulator guards | risk alerts, unsafe mutation, intervention | Not reproduced in the saved experiments | E3 flags 40/100 synthetic cases; unsafe mutation and terminal mismatches are 0. Alerts are not completed unsafe transactions, and server-side guards remain enabled in every variant. | Partial |
| Human-in-the-loop oversight | Approval and hold orchestration | intervention rate, auditability | Not reproduced in the saved experiments | Expected terminal labels are withheld from agent decisions; E5's approval toggle still has no aggregate effect in the fixed run, and no human-review study was conducted. | Partial |
| Transfer to procurement event traces | BPI Challenge 2019 replay | exact match, risk alerts | No like-for-like comparison is recorded | E4 replays 100 trace-derived cases with 1.00 agreement against reconstructed proxy labels and a 0.55 alert rate; this is not invoice ground truth. | Partial |
| Joint evaluation and reporting | E1–E6 scripts, ablation, logs, manuscript | correctness, safety, oversight, efficiency | E2 is not a base-paper reproduction | Eight-page, 8–10 page-format manuscript includes the rubric sections, gap table, 30 cited sources, and result tables. Group review, AI-use permission confirmation, Turnitin, and final release packaging remain pending. | In progress |

These are deterministic local prototype results, not estimates of production performance. The E2 experiment is a heuristic comparator, not a reproduction of the selected Declare-translation paper, and BPI-derived results use proxy labels rather than invoice ground truth.

## Tests

Run the repository test suite with:

```bash
pytest -q
```

## References

[1] V. Fionda, A. Ielo, and F. Ricca, “Are Large Language Models Fluent in Declarative Process Mining?,” in *Proc. 34th Int. Joint Conf. Artificial Intelligence (IJCAI)*, 2025, pp. 4500–4508, doi: 10.24963/ijcai.2025/501.

[2] B. F. van Dongen, “BPI Challenge 2019,” 4TU.ResearchData, 2019, doi: 10.4121/uuid:d06aff4b-79f0-45e6-8ec8-e19730c248f1. [Online]. Available: https://doi.org/10.4121/uuid:d06aff4b-79f0-45e6-8ec8-e19730c248f1.
