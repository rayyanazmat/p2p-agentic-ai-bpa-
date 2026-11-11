# Phase 2 experiment summary

Generated from the refreshed 2026-11-12 runs on the fixed 100-case synthetic manifest (`seed=2019`), plus the 100-case BPI-derived replay manifest. These are deterministic local simulator results. Expected terminal labels are withheld from agent, policy, approval, and compensation decisions and used only by the evaluator after each run. BPI-derived invoice fields and expected statuses are reconstructed proxy labels, not observed invoice ground truth.

| Experiment | Cases | Agent/configuration | Exact match | Policy-risk alert rate | Unsafe mutation | Intervention | p95 latency | Tool calls/case |
|---|---:|---|---:|---:|---:|---:|---:|---:|
| E1 baseline | 100 synthetic | ReAct, policy off, approval off | 1.00 | 0.00 (detector disabled) | 0.00 | 0.40 | 0.0137 s | 6.20 |
| E2 domain comparator | 100 synthetic | Heuristic, policy on, approval on | 1.00 | 0.40 | 0.00 | 0.40 | 0.0112 s | 5.40 |
| E3 proposed system | 100 synthetic | ReAct, policy on, approval on | 1.00 | 0.40 | 0.00 | 0.40 | 0.0114 s | 6.20 |
| E4 transfer | 100 BPI-derived proxy | ReAct, policy on, approval on | 1.00* | 0.55 | 0.00* | 0.55 | 0.0111 s | 6.17 |

`Policy-risk alert rate` is the fraction of cases where the enabled policy layer flagged risky input evidence; it is not the fraction of unsafe transactions that completed. The server-side invariant blocked unsafe mutations in these runs. The 0.00 E1 alert rate means its detector was disabled, not that risky inputs were absent.

`*` BPI-derived expected outcomes are proxy labels reconstructed from the event log. Do not interpret these as invoice-level source truth or generalization accuracy on verified invoices.

## E5: 100-case one-factor ablation

All entries use the same fixed synthetic manifest and offline deterministic ReAct or heuristic agent. The factorial design switches policy and approval independently, rather than removing both together.

| Agent | Policy | Approval | Exact match | Policy-risk alert rate | Unsafe mutation | Intervention |
|---|---:|---:|---:|---:|---:|---:|
| ReAct | On | On | 1.00 | 0.40 | 0.00 | 0.40 |
| ReAct | Off | On | 1.00 | 0.00 | 0.00 | 0.40 |
| ReAct | On | Off | 1.00 | 0.40 | 0.00 | 0.40 |
| ReAct | Off | Off | 1.00 | 0.00 | 0.00 | 0.40 |
| Heuristic | On | On | 1.00 | 0.40 | 0.00 | 0.40 |
| Heuristic | Off | On | 1.00 | 0.00 | 0.00 | 0.40 |
| Heuristic | On | Off | 1.00 | 0.40 | 0.00 | 0.40 |
| Heuristic | Off | Off | 1.00 | 0.00 | 0.00 | 0.40 |

The policy toggle changes whether risk is surfaced, but not terminal-state accuracy, mutation safety, or interventions in this benchmark. Approval toggle did not change these aggregate metrics. These results do not establish that the components reduce unsafe completed transactions; the simulator already rejects unsafe actions, and the fixture is deterministic.

## E6: local efficiency and reliability

- ReAct all-controls-on, 100 synthetic cases: exact match 1.00, unsafe mutation 0.00, 20,180 estimated tokens, 6.20 tool calls/case, mean latency 0.00805 s, p95 latency 0.0119 s.
- Heuristic all-controls-on, 100 synthetic cases: exact match 1.00, unsafe mutation 0.00, zero model tokens, 5.40 tool calls/case, mean latency 0.00645 s, p95 latency 0.0098 s.
- Provider cost is recorded as $0 for the offline deterministic backend; this is not a hosted-model cost estimate.

## E2 base-paper comparability

The selected Phase 1 base paper evaluates LLM translation of Declare constraints with symbolic semantic checks. The present P2P simulator does not implement that translation method. E2 is therefore a heuristic domain comparator, **not a reproduction of the base-paper method or its results**. A valid like-for-like E2 remains an open limitation.

## Evidence files

- `results/E1_baseline.json` through `results/E6_efficiency.json`
- `results/ablation_run.json`
- `results/phase2_experiments.json`
- `data/processed/baseline_run.json`
- `data/processed/bpi_baseline_run.json`
- `logs/`
